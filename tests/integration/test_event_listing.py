def _event(event_id: str, timestamp: str) -> dict:
    return {
        "eventId": event_id,
        "accountId": "acct-order",
        "type": "CREDIT",
        "amount": 1.0,
        "currency": "USD",
        "eventTimestamp": timestamp,
    }


def test_out_of_order_arrival_lists_chronologically(client):
    client.post("/events", json=_event("evt-late", "2026-05-15T12:00:00Z"))
    client.post("/events", json=_event("evt-early", "2026-05-15T10:00:00Z"))
    events = client.get("/events", params={"account": "acct-order"}).json()["events"]
    assert [event["eventId"] for event in events] == ["evt-early", "evt-late"]


def test_same_timestamp_orders_by_event_id(client):
    client.post("/events", json=_event("evt-z", "2026-05-15T10:00:00Z"))
    client.post("/events", json=_event("evt-a", "2026-05-15T10:00:00Z"))
    events = client.get("/events", params={"account": "acct-order"}).json()["events"]
    assert [event["eventId"] for event in events] == ["evt-a", "evt-z"]


def test_empty_account_list(client):
    response = client.get("/events", params={"account": "acct-empty"})
    assert response.status_code == 200
    assert response.json()["events"] == []


def test_unknown_event_returns_404(client):
    response = client.get("/events/missing-id")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EVENT_NOT_FOUND"
