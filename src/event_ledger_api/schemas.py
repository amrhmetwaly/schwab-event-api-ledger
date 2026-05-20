import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from event_ledger_api.money import parse_positive_amount


class EventSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eventId: str = Field(min_length=1)
    accountId: str = Field(min_length=1)
    type: Literal["CREDIT", "DEBIT"]
    amount: float
    currency: str = Field(min_length=1)
    eventTimestamp: datetime
    metadata: dict[str, Any] | None = None

    @field_validator("eventTimestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, value: object) -> datetime:
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str) or not value.strip():
            raise ValueError("eventTimestamp must be a valid ISO 8601 datetime")
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError("eventTimestamp must be a valid ISO 8601 datetime") from exc

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        parse_positive_amount(value)
        return value


class Event(BaseModel):
    eventId: str
    accountId: str
    type: Literal["CREDIT", "DEBIT"]
    amount: float
    currency: str
    eventTimestamp: datetime
    metadata: dict[str, Any] | None = None


class EventResponse(BaseModel):
    event: Event


class PaginationMeta(BaseModel):
    total: int = Field(ge=0, description="Total accepted events for the account.")
    limit: int | None = Field(
        default=None,
        ge=1,
        description="Page size when paginating; null when all events are returned.",
    )
    offset: int = Field(ge=0, description="Number of events skipped from the start of the ordered list.")
    hasMore: bool = Field(description="True when additional pages exist after this response.")


class EventListResponse(BaseModel):
    accountId: str
    events: list[Event]
    pagination: PaginationMeta


class CurrencyBalance(BaseModel):
    currency: str
    balance: str


class BalanceResponse(BaseModel):
    accountId: str
    balances: list[CurrencyBalance]
    eventCount: int = Field(ge=0)


def submission_to_event_dict(submission: EventSubmission) -> dict[str, Any]:
    return {
        "eventId": submission.eventId,
        "accountId": submission.accountId,
        "type": submission.type,
        "amount": submission.amount,
        "currency": submission.currency,
        "eventTimestamp": submission.eventTimestamp.isoformat().replace("+00:00", "Z"),
        "metadata": submission.metadata,
    }


def model_to_event(row: Any) -> Event:
    metadata = json.loads(row.metadata_json) if row.metadata_json else None
    return Event(
        eventId=row.event_id,
        accountId=row.account_id,
        type=row.type,
        amount=float(row.amount),
        currency=row.currency,
        eventTimestamp=row.event_timestamp,
        metadata=metadata,
    )


def amount_decimal(submission: EventSubmission) -> Decimal:
    return parse_positive_amount(submission.amount)
