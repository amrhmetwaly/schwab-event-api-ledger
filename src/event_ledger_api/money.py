import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any


def parse_positive_amount(value: float | int | str | Decimal) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("amount must be a positive number") from exc
    if amount <= 0:
        raise ValueError("amount must be greater than 0")
    return amount


def format_balance(amount: Decimal) -> str:
    normalized = amount.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def canonical_payload_hash(payload: dict[str, Any]) -> str:
    """Hash balance-affecting fields for idempotency comparison."""
    canonical = {
        "eventId": payload["eventId"],
        "accountId": payload["accountId"],
        "type": payload["type"],
        "amount": format_balance(parse_positive_amount(payload["amount"])),
        "currency": payload["currency"],
        "eventTimestamp": payload["eventTimestamp"],
        "metadata": payload.get("metadata"),
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
