import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from event_ledger_api.database import get_db
from event_ledger_api.errors import ValidationAppError, app_error_handler
from event_ledger_api.schemas import EventListResponse, EventResponse, EventSubmission
from event_ledger_api.services import (
    get_account_balance,
    get_event,
    list_account_events,
    submit_event,
)

logger = logging.getLogger(__name__)

router = APIRouter()

OPENAPI_CONTRACT_PATH = (
    Path(__file__).resolve().parent / "contracts" / "openapi.yaml"
)

_EVENT_RESPONSES = {
    201: {"description": "New event accepted and stored."},
    200: {"description": "Exact duplicate accepted idempotently; original event returned."},
    409: {"description": "Event ID already exists with different content."},
    422: {"description": "Event payload failed validation."},
}


@router.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns service readiness for load balancers and container orchestration.",
)
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/events",
    response_model=EventResponse,
    tags=["Events"],
    summary="Submit a transaction event",
    description=(
        "Accepts a financial transaction event. Duplicate submissions with the same "
        "`eventId` and identical payload are idempotent (HTTP 200). Reusing an `eventId` "
        "with different content returns HTTP 409. Concurrent duplicate POSTs are handled "
        "safely via database uniqueness and idempotent recovery."
    ),
    responses=_EVENT_RESPONSES,
)
def post_event(
    submission: EventSubmission,
    response: Response,
    session: Session = Depends(get_db),
) -> EventResponse:
    result = submit_event(session, submission)
    response.status_code = 201 if result.created else 200
    return EventResponse(event=result.event)


@router.get(
    "/events/{event_id}",
    response_model=EventResponse,
    tags=["Events"],
    summary="Retrieve an event by ID",
    description="Returns a single accepted event by its business `eventId`.",
    responses={
        200: {"description": "Stored event found."},
        404: {"description": "No stored event exists with this ID."},
    },
)
def get_event_by_id(event_id: str, session: Session = Depends(get_db)) -> EventResponse:
    return get_event(session, event_id)


@router.get(
    "/events",
    response_model=EventListResponse,
    tags=["Events"],
    summary="List events for an account",
    description=(
        "Returns accepted events for the account ordered by `eventTimestamp` ascending, "
        "then `eventId` ascending. Optional `limit` and `offset` enable offset pagination; "
        "omit `limit` to return the full history."
    ),
    responses={
        200: {"description": "Accepted events for the account."},
        422: {"description": "Missing or invalid query parameters."},
    },
)
def list_events(
    account: str | None = Query(default=None, description="Account identifier."),
    limit: int | None = Query(
        default=None,
        ge=1,
        le=1000,
        description="Maximum events per page (omit to return all events).",
    ),
    offset: int = Query(default=0, ge=0, description="Events to skip before returning results."),
    session: Session = Depends(get_db),
) -> EventListResponse:
    if account is None or not account.strip():
        raise ValidationAppError("Query parameter 'account' is required")
    return list_account_events(session, account, limit=limit, offset=offset)


@router.get(
    "/accounts/{account_id}/balance",
    tags=["Accounts"],
    summary="Get account balance",
    description=(
        "Computes net balance per currency from accepted unique events: "
        "sum(CREDIT) − sum(DEBIT)."
    ),
    responses={200: {"description": "Current balance derived from accepted unique events."}},
)
def account_balance(account_id: str, session: Session = Depends(get_db)):
    return get_account_balance(session, account_id)


@router.get(
    "/openapi.yaml",
    tags=["Health"],
    summary="OpenAPI contract (YAML)",
    description="Static OpenAPI 3.1 contract maintained alongside the implementation.",
    include_in_schema=False,
)
def openapi_contract() -> FileResponse:
    return FileResponse(OPENAPI_CONTRACT_PATH, media_type="application/yaml")


def register_exception_handlers(app) -> None:
    from event_ledger_api.errors import AppError

    app.add_exception_handler(AppError, app_error_handler)

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(_request, exc: RequestValidationError):
        details = [
            {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        error = ValidationAppError("Request validation failed", details=details)
        return await app_error_handler(_request, error)
