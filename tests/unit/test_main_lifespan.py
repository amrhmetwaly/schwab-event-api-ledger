from fastapi.testclient import TestClient

from event_ledger_api.config import get_settings
from event_ledger_api.database import get_engine
from event_ledger_api.main import create_app
from tests.conftest import TEST_DATABASE_URL, _reset_database_state


def test_lifespan_configures_database_when_engine_unset(monkeypatch):
    _reset_database_state()
    get_settings.cache_clear()
    monkeypatch.setenv("EVENT_LEDGER_DATABASE_URL", TEST_DATABASE_URL)

    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert get_engine() is not None
