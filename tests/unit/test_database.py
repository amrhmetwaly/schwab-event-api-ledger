from unittest.mock import patch

import pytest

import event_ledger_api.database as database_module
from event_ledger_api.config import Settings
from event_ledger_api.database import configure_database, get_engine, get_session_factory
from tests.conftest import _reset_database_state


def test_get_engine_lazy_configures(monkeypatch):
    _reset_database_state()
    monkeypatch.setenv("EVENT_LEDGER_DATABASE_URL", "sqlite:///:memory:")
    engine = get_engine()
    assert engine is database_module._engine


def test_get_session_factory_lazy_configures(monkeypatch):
    _reset_database_state()
    monkeypatch.setenv("EVENT_LEDGER_DATABASE_URL", "sqlite:///:memory:")
    factory = get_session_factory()
    assert factory is database_module._session_factory


def test_configure_database_file_sqlite_uses_wal_pragma(tmp_path, monkeypatch):
    _reset_database_state()
    db_path = tmp_path / "ledger.db"
    url = f"sqlite:///{db_path}"
    configure_database(Settings(database_url=url))
    engine = get_engine()
    with engine.connect() as conn:
        journal = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
    assert str(journal).lower() == "wal"


def test_configure_database_non_sqlite_skips_sqlite_pool_and_pragma():
    _reset_database_state()
    try:
        with patch("event_ledger_api.database.create_engine") as mock_create_engine:
            mock_create_engine.return_value = object()
            configure_database(Settings(database_url="postgresql://localhost/ledger"))
        _, kwargs = mock_create_engine.call_args
        assert "poolclass" not in kwargs
    finally:
        _reset_database_state()
