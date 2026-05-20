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
