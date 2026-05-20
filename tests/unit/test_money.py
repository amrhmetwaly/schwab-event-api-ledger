from decimal import Decimal

import pytest

from event_ledger_api.money import canonical_payload_hash, format_balance, parse_positive_amount


def test_parse_positive_amount():
    assert parse_positive_amount("10.5") == Decimal("10.5")


def test_parse_rejects_non_positive():
    with pytest.raises(ValueError):
        parse_positive_amount(0)


def test_format_balance_strips_trailing_zeros():
    assert format_balance(Decimal("75.00")) == "75"
    assert format_balance(Decimal("-50")) == "-50"


def test_canonical_hash_stable_for_equivalent_payloads():
    payload_a = {
        "eventId": "evt-1",
        "accountId": "acct-1",
        "type": "CREDIT",
        "amount": 10.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z",
        "metadata": {"b": 2, "a": 1},
    }
    payload_b = dict(payload_a)
    payload_b["metadata"] = {"a": 1, "b": 2}
    assert canonical_payload_hash(payload_a) == canonical_payload_hash(payload_b)


def test_canonical_hash_differs_when_content_differs():
    base = {
        "eventId": "evt-1",
        "accountId": "acct-1",
        "type": "CREDIT",
        "amount": 10.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z",
    }
    other = dict(base)
    other["amount"] = 11.0
    assert canonical_payload_hash(base) != canonical_payload_hash(other)
