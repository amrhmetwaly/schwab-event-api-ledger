from decimal import Decimal, InvalidOperation

import pytest

from event_ledger_api.money import canonical_payload_hash, format_balance, parse_positive_amount


def test_parse_positive_amount():
    assert parse_positive_amount("10.5") == Decimal("10.5")


def test_parse_rejects_non_positive():
    with pytest.raises(ValueError, match="greater than 0"):
        parse_positive_amount(0)


def test_parse_rejects_invalid_decimal():
    with pytest.raises(ValueError, match="positive number"):
        parse_positive_amount("not-a-number")


def test_parse_rejects_invalid_operation():
    with pytest.raises(ValueError, match="positive number"):

        class BadStr:
            def __str__(self) -> str:
                raise InvalidOperation

        parse_positive_amount(BadStr())


def test_format_balance_strips_trailing_zeros():
    assert format_balance(Decimal("75.50")) == "75.5"
    assert format_balance(Decimal("-50.25")) == "-50.25"


def test_format_balance_strips_fractional_zeros_to_integer():
    assert format_balance(Decimal("10.00")) == "10"


def test_format_balance_zero_fractional_normalizes_to_zero():
    assert format_balance(Decimal("0.001")) == "0.001"
    assert format_balance(Decimal("0.100")) == "0.1"


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
