from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from event_ledger_api.schemas import EventSubmission


def _base(**overrides):
    data = {
        "eventId": "evt-1",
        "accountId": "acct-1",
        "type": "CREDIT",
        "amount": 1.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z",
    }
    data.update(overrides)
    return data


def test_valid_submission():
    model = EventSubmission.model_validate(_base())
    assert model.eventId == "evt-1"


def test_accepts_datetime_instance():
    ts = datetime(2026, 5, 15, 14, 2, 11, tzinfo=UTC)
    model = EventSubmission.model_validate(_base(eventTimestamp=ts))
    assert model.eventTimestamp == ts


def test_rejects_blank_timestamp_string():
    with pytest.raises(ValidationError):
        EventSubmission.model_validate(_base(eventTimestamp="   "))


@pytest.mark.parametrize(
    "field,value",
    [
        ("eventId", ""),
        ("accountId", ""),
        ("currency", ""),
        ("type", "TRANSFER"),
        ("amount", 0),
        ("amount", -1),
        ("eventTimestamp", "not-a-date"),
    ],
)
def test_invalid_fields(field, value):
    with pytest.raises(ValidationError):
        EventSubmission.model_validate(_base(**{field: value}))


def test_metadata_optional():
    model = EventSubmission.model_validate(_base(metadata={"k": "v"}))
    assert model.metadata == {"k": "v"}
