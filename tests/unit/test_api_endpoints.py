from pathlib import Path

from event_ledger_api.api import OPENAPI_CONTRACT_PATH, health, openapi_contract


def test_health_returns_ok():
    assert health() == {"status": "ok"}


def test_openapi_contract_serves_yaml_file():
    response = openapi_contract()
    assert response.path == OPENAPI_CONTRACT_PATH
    assert Path(response.path).is_file()
    assert response.media_type == "application/yaml"


def test_health_endpoint_via_client(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_yaml_endpoint_via_client(client):
    response = client.get("/openapi.yaml")
    assert response.status_code == 200
    assert "openapi" in response.text
