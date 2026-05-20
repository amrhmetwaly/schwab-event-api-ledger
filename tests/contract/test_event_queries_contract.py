def _event(event_id: str, timestamp: str, amount: float = 10.0) -> dict:
    return {
        "eventId": event_id,
        "accountId": "acct-list",
        "type": "CREDIT",
        "amount": amount,
        "currency": "USD",
        "eventTimestamp": timestamp,
    }


def test_get_event_by_id(client):
    payload = _event("evt-get", "2026-05-15T10:00:00Z")
    client.post("/events", json=payload)
    response = client.get("/events/evt-get")
    assert response.status_code == 200
    assert response.json()["event"]["eventId"] == "evt-get"


def test_list_events_requires_account(client):
    response = client.get("/events")
    assert response.status_code == 422


def test_list_events_by_account(client):
    client.post("/events", json=_event("evt-b", "2026-05-15T12:00:00Z"))
    client.post("/events", json=_event("evt-a", "2026-05-15T10:00:00Z"))
    response = client.get("/events", params={"account": "acct-list"})
    assert response.status_code == 200
    body = response.json()
    assert body["accountId"] == "acct-list"
    assert [event["eventId"] for event in body["events"]] == ["evt-a", "evt-b"]
