import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import event_ledger_api.database as database_module
from event_ledger_api.config import Settings, get_settings
from event_ledger_api.database import Base, configure_database, get_engine, get_session_factory, init_db
from event_ledger_api.main import create_app

TEST_DATABASE_URL = "sqlite:///:memory:"


def _reset_database_state() -> None:
    if database_module._engine is not None:
        Base.metadata.drop_all(bind=database_module._engine)
    database_module._engine = None
    database_module._session_factory = None
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def isolated_database(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("EVENT_LEDGER_DATABASE_URL", TEST_DATABASE_URL)
    _reset_database_state()
    configure_database(Settings(database_url=TEST_DATABASE_URL))
    init_db()
    yield
    _reset_database_state()


@pytest.fixture()
def db_session() -> Session:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
