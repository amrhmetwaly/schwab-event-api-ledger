import json
import logging
import threading
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import DatabaseError, IntegrityError
from sqlalchemy.orm import Session

from event_ledger_api.config import get_settings
from event_ledger_api.errors import EventIdConflictError, EventNotFoundError
from event_ledger_api.models import TransactionEvent
from event_ledger_api.money import canonical_payload_hash, format_balance
from event_ledger_api.schemas import (
    BalanceResponse,
    CurrencyBalance,
    Event,
    EventListResponse,
    EventResponse,
    EventSubmission,
    PaginationMeta,
    amount_decimal,
    model_to_event,
    submission_to_event_dict,
)

logger = logging.getLogger(__name__)

# SQLite allows one writer per database file; serialize POST /events when embedded.
_sqlite_submit_lock = threading.Lock()


def _serialize_metadata(metadata: dict | None) -> str | None:
    if metadata is None:
        return None
    return json.dumps(metadata, sort_keys=True)


class SubmitResult:
    def __init__(self, event: Event, created: bool) -> None:
        self.event = event
        self.created = created


def _is_insert_race_error(exc: BaseException) -> bool:
    if isinstance(exc, IntegrityError):
        return True
    if isinstance(exc, DatabaseError):
        orig = getattr(exc, "orig", None)
        if orig is None:
            return False
        message = str(orig).lower()
        return "unique" in message or "another row available" in message
    return False


def _load_existing_event(session: Session, event_id: str) -> TransactionEvent | None:
    return session.scalar(select(TransactionEvent).where(TransactionEvent.event_id == event_id))


def _duplicate_or_conflict(
    session: Session,
    submission: EventSubmission,
    payload_hash: str,
    *,
    allow_retry: bool,
) -> SubmitResult:
    session.rollback()
    session.expire_all()
    raced = _load_existing_event(session, submission.eventId)
    if raced is None and allow_retry:
        return _submit_event_impl(session, submission, _allow_insert_retry=False)
    if raced is None:
        raise RuntimeError(
            f"insert race for event_id={submission.eventId!r} but row not found after rollback"
        )
    if raced.payload_hash != payload_hash:
        logger.warning(
            "event_id_conflict",
            extra={"event_id": submission.eventId, "account_id": submission.accountId},
        )
        raise EventIdConflictError(submission.eventId)
    logger.info(
        "event_duplicate",
        extra={"event_id": submission.eventId, "account_id": submission.accountId},
    )
    return SubmitResult(event=model_to_event(raced), created=False)


def submit_event(
    session: Session,
    submission: EventSubmission,
    *,
    _allow_insert_retry: bool = True,
) -> SubmitResult:
    if get_settings().database_url.startswith("sqlite"):
        with _sqlite_submit_lock:
            return _submit_event_impl(
                session, submission, _allow_insert_retry=_allow_insert_retry
            )
    return _submit_event_impl(session, submission, _allow_insert_retry=_allow_insert_retry)


def _submit_event_impl(
    session: Session,
    submission: EventSubmission,
    *,
    _allow_insert_retry: bool = True,
) -> SubmitResult:
    payload = submission_to_event_dict(submission)
    payload_hash = canonical_payload_hash(payload)

    existing = _load_existing_event(session, submission.eventId)
    if existing is not None:
        if existing.payload_hash != payload_hash:
            logger.warning(
                "event_id_conflict",
                extra={"event_id": submission.eventId, "account_id": submission.accountId},
            )
            raise EventIdConflictError(submission.eventId)
        logger.info(
            "event_duplicate",
            extra={"event_id": submission.eventId, "account_id": submission.accountId},
        )
        return SubmitResult(event=model_to_event(existing), created=False)

    row = TransactionEvent(
        event_id=submission.eventId,
        account_id=submission.accountId,
        type=submission.type,
        amount=amount_decimal(submission),
        currency=submission.currency,
        event_timestamp=submission.eventTimestamp,
        metadata_json=_serialize_metadata(submission.metadata),
        payload_hash=payload_hash,
        received_at=datetime.now(UTC),
    )
    try:
        session.add(row)
        session.commit()
        session.refresh(row)
    except (IntegrityError, DatabaseError) as exc:
        if not _is_insert_race_error(exc):
            raise
        return _duplicate_or_conflict(
            session,
            submission,
            payload_hash,
            allow_retry=_allow_insert_retry,
        )
    logger.info(
        "event_accepted",
        extra={"event_id": submission.eventId, "account_id": submission.accountId},
    )
    return SubmitResult(event=model_to_event(row), created=True)


def get_event(session: Session, event_id: str) -> EventResponse:
    row = session.scalar(select(TransactionEvent).where(TransactionEvent.event_id == event_id))
    if row is None:
        logger.info("event_not_found", extra={"event_id": event_id})
        raise EventNotFoundError(event_id)
    return EventResponse(event=model_to_event(row))


def list_account_events(
    session: Session,
    account_id: str,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> EventListResponse:
    account_filter = TransactionEvent.account_id == account_id
    total = session.scalar(
        select(func.count()).select_from(TransactionEvent).where(account_filter)
    )
    total = int(total or 0)

    query = (
        select(TransactionEvent)
        .where(account_filter)
        .order_by(TransactionEvent.event_timestamp.asc(), TransactionEvent.event_id.asc())
    )
    if limit is not None:
        query = query.offset(offset).limit(limit)

    rows = session.scalars(query).all()
    events = [model_to_event(row) for row in rows]

    if limit is None:
        pagination = PaginationMeta(total=total, limit=None, offset=0, hasMore=False)
    else:
        pagination = PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            hasMore=offset + len(events) < total,
        )

    logger.info(
        "events_listed",
        extra={
            "account_id": account_id,
            "count": len(events),
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )
    return EventListResponse(accountId=account_id, events=events, pagination=pagination)


def get_account_balance(session: Session, account_id: str) -> BalanceResponse:
    rows = session.scalars(
        select(TransactionEvent).where(TransactionEvent.account_id == account_id)
    ).all()

    totals: dict[str, Decimal] = {}
    for row in rows:
        delta = row.amount if row.type == "CREDIT" else -row.amount
        totals[row.currency] = totals.get(row.currency, Decimal("0")) + delta

    balances = [
        CurrencyBalance(currency=currency, balance=format_balance(total))
        for currency, total in sorted(totals.items())
    ]
    logger.info(
        "balance_computed",
        extra={"account_id": account_id, "event_count": len(rows), "currencies": list(totals)},
    )
    return BalanceResponse(
        accountId=account_id,
        balances=balances,
        eventCount=len(rows),
    )
