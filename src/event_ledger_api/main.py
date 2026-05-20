import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from event_ledger_api.api import register_exception_handlers, router
from event_ledger_api.config import get_settings
from event_ledger_api.database import configure_database, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

API_DESCRIPTION = """
Local Event Ledger API for financial transaction events.

**Idempotency:** Submitting the same `eventId` with an identical payload returns the stored
event (HTTP 200) without mutating ledger state.

**Ordering:** Events may arrive out of order; listings are always sorted by
`eventTimestamp`, then `eventId`.

**Concurrency:** Simultaneous POSTs for the same `eventId` are resolved via database
uniqueness and idempotent recovery (no duplicate rows or balance drift).
"""


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from event_ledger_api.database import _engine

    if _engine is None:
        configure_database()
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description=API_DESCRIPTION,
        version="0.1.0",
        contact={"name": "Event Ledger API"},
        license_info={"name": "MIT"},
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.include_router(router)
    register_exception_handlers(app)
    return app


app = create_app()
