def _valid_event(event_id: str = "evt-001") -> dict:
    return {
        "eventId": event_id,
        "accountId": "acct-123",
        "type": "CREDIT",
        "amount": 150.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z",
        "metadata": {"source": "test"},
    }


def test_post_events_created(client):
    response = client.post("/events", json=_valid_event())
    assert response.status_code == 201
    assert response.json()["event"]["eventId"] == "evt-001"


def test_post_events_duplicate_returns_200(client):
    payload = _valid_event()
    assert client.post("/events", json=payload).status_code == 201
    duplicate = client.post("/events", json=payload)
    assert duplicate.status_code == 200
    assert duplicate.json()["event"]["eventId"] == "evt-001"


def test_post_events_conflict_returns_409(client):
    assert client.post("/events", json=_valid_event()).status_code == 201
    conflict = _valid_event()
    conflict["amount"] = 99.0
    response = client.post("/events", json=conflict)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EVENT_ID_CONFLICT"


def test_post_events_validation_returns_422(client):
    invalid = _valid_event()
    invalid["amount"] = 0
    response = client.post("/events", json=invalid)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
