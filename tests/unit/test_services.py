from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy.exc import DatabaseError, IntegrityError
from sqlalchemy.orm import Session

from event_ledger_api.errors import EventIdConflictError
from event_ledger_api.models import TransactionEvent
from event_ledger_api.money import canonical_payload_hash
from event_ledger_api.schemas import EventSubmission, submission_to_event_dict
from event_ledger_api.services import (
    SubmitResult,
    _duplicate_or_conflict,
    _is_insert_race_error,
    _serialize_metadata,
    submit_event,
)


def _submission(**overrides) -> EventSubmission:
    data = {
        "eventId": "evt-svc-1",
        "accountId": "acct-svc",
        "type": "CREDIT",
        "amount": 10.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z",
    }
    data.update(overrides)
    return EventSubmission.model_validate(data)


def test_serialize_metadata_none():
    assert _serialize_metadata(None) is None


def test_serialize_metadata_sorts_keys():
    assert _serialize_metadata({"b": 2, "a": 1}) == '{"a": 1, "b": 2}'


def test_is_insert_race_integrity_error():
    assert _is_insert_race_error(IntegrityError("stmt", {}, Exception("unique"))) is True


def test_is_insert_race_database_error_with_unique_orig():
    orig = Exception("UNIQUE constraint failed: event_id")
    exc = DatabaseError("stmt", {}, orig)
    assert _is_insert_race_error(exc) is True


def test_is_insert_race_database_error_with_another_row_message():
    orig = Exception("another row available")
    exc = DatabaseError("stmt", {}, orig)
    assert _is_insert_race_error(exc) is True


def test_is_insert_race_database_error_without_orig():
    exc = DatabaseError("stmt", {}, None)
    assert _is_insert_race_error(exc) is False


def test_is_insert_race_database_error_unrelated_message():
    orig = Exception("disk I/O error")
    exc = DatabaseError("stmt", {}, orig)
    assert _is_insert_race_error(exc) is False


def test_is_insert_race_other_exception():
    assert _is_insert_race_error(ValueError("nope")) is False


def test_submit_event_non_sqlite_skips_thread_lock(db_session: Session, monkeypatch):
    monkeypatch.setattr(
        "event_ledger_api.services.get_settings",
        lambda: type("S", (), {"database_url": "postgresql://localhost/ledger"})(),
    )
    with patch("event_ledger_api.services._sqlite_submit_lock"):
        result = submit_event(db_session, _submission(eventId="evt-pg-path"))
    assert result.created is True


def test_submit_raises_non_race_database_error(db_session: Session, monkeypatch):
    submission = _submission(eventId="evt-db-fail")

    def boom():
        raise DatabaseError("stmt", {}, Exception("disk full"))

    monkeypatch.setattr(db_session, "commit", boom)
    with pytest.raises(DatabaseError):
        submit_event(db_session, submission)


def test_duplicate_or_conflict_returns_idempotent_duplicate(db_session: Session):
    submission = _submission(eventId="evt-dup-path")
    payload_hash = canonical_payload_hash(submission_to_event_dict(submission))
    first = submit_event(db_session, submission)
    assert first.created is True

    db_session.rollback()
    result = _duplicate_or_conflict(
        db_session, submission, payload_hash, allow_retry=True
    )
    assert result.created is False
    assert result.event.eventId == submission.eventId


def test_duplicate_or_conflict_raises_when_row_missing_and_no_retry(db_session: Session):
    submission = _submission(eventId="evt-missing")
    payload_hash = canonical_payload_hash(submission_to_event_dict(submission))
    db_session.rollback()

    with pytest.raises(RuntimeError, match="row not found after rollback"):
        _duplicate_or_conflict(
            db_session, submission, payload_hash, allow_retry=False
        )


def test_duplicate_or_conflict_raises_on_payload_mismatch(db_session: Session):
    submission = _submission(eventId="evt-conflict-path")
    submit_event(db_session, submission)
    other = _submission(eventId="evt-conflict-path", amount=99.0)
    payload_hash = canonical_payload_hash(submission_to_event_dict(other))
    db_session.rollback()

    with pytest.raises(EventIdConflictError):
        _duplicate_or_conflict(db_session, other, payload_hash, allow_retry=True)


def test_submit_recovers_after_integrity_error_race(db_session: Session, monkeypatch):
    submission = _submission(eventId="evt-race-recover")
    payload_hash = canonical_payload_hash(submission_to_event_dict(submission))
    stored = TransactionEvent(
        event_id=submission.eventId,
        account_id=submission.accountId,
        type=submission.type,
        amount=Decimal("10.0"),
        currency=submission.currency,
        event_timestamp=submission.eventTimestamp,
        metadata_json=None,
        payload_hash=payload_hash,
        received_at=datetime.now(UTC),
    )
    db_session.add(stored)
    db_session.commit()

    import event_ledger_api.services as services

    original_load = services._load_existing_event
    load_calls = {"n": 0}

    def patched_load(session: Session, event_id: str):
        load_calls["n"] += 1
        if load_calls["n"] == 1:
            return None
        return original_load(session, event_id)

    commit_calls = {"n": 0}
    original_commit = db_session.commit

    def patched_commit():
        commit_calls["n"] += 1
        if commit_calls["n"] == 1:
            raise IntegrityError("INSERT", {}, Exception("UNIQUE constraint failed"))
        original_commit()

    monkeypatch.setattr(services, "_load_existing_event", patched_load)
    monkeypatch.setattr(db_session, "commit", patched_commit)

    db_session.expunge_all()
    result = submit_event(db_session, submission)
    assert isinstance(result, SubmitResult)
    assert result.created is False
    assert result.event.eventId == submission.eventId


def test_submit_retries_impl_when_race_row_not_visible_yet(db_session: Session, monkeypatch):
    submission = _submission(eventId="evt-retry-impl")
    import event_ledger_api.services as services

    original_load = services._load_existing_event
    load_calls = {"n": 0}

    def patched_load(session: Session, event_id: str):
        load_calls["n"] += 1
        if load_calls["n"] <= 2:
            return None
        return original_load(session, event_id)

    commit_calls = {"n": 0}
    original_commit = db_session.commit

    def patched_commit():
        commit_calls["n"] += 1
        if commit_calls["n"] == 1:
            raise IntegrityError("INSERT", {}, Exception("UNIQUE constraint failed"))
        original_commit()

    monkeypatch.setattr(services, "_load_existing_event", patched_load)
    monkeypatch.setattr(db_session, "commit", patched_commit)

    result = submit_event(db_session, submission)
    assert result.created is True
    assert result.event.eventId == submission.eventId
