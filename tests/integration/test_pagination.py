def _event(event_id: str, amount: float = 1.0) -> dict:
    return {
        "eventId": event_id,
        "accountId": "acct-page",
        "type": "CREDIT",
        "amount": amount,
        "currency": "USD",
        "eventTimestamp": f"2026-05-15T{10 + int(event_id[-1]):02d}:00:00Z",
    }


def _seed_events(client, count: int = 5) -> None:
    for index in range(count):
        client.post("/events", json=_event(f"evt-{index}"))


def test_list_without_limit_returns_all_with_pagination_meta(client):
    _seed_events(client, 3)
    response = client.get("/events", params={"account": "acct-page"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["events"]) == 3
    assert body["pagination"]["total"] == 3
    assert body["pagination"]["limit"] is None
    assert body["pagination"]["offset"] == 0
    assert body["pagination"]["hasMore"] is False


def test_paginated_first_page(client):
    _seed_events(client, 5)
    response = client.get("/events", params={"account": "acct-page", "limit": 2, "offset": 0})
    assert response.status_code == 200
    body = response.json()
    assert len(body["events"]) == 2
    assert body["pagination"]["total"] == 5
    assert body["pagination"]["limit"] == 2
    assert body["pagination"]["offset"] == 0
    assert body["pagination"]["hasMore"] is True
    assert [event["eventId"] for event in body["events"]] == ["evt-0", "evt-1"]


def test_paginated_last_page(client):
    _seed_events(client, 5)
    response = client.get("/events", params={"account": "acct-page", "limit": 2, "offset": 4})
    assert response.status_code == 200
    body = response.json()
    assert len(body["events"]) == 1
    assert body["pagination"]["hasMore"] is False
    assert body["events"][0]["eventId"] == "evt-4"


def test_empty_account_pagination(client):
    response = client.get("/events", params={"account": "acct-empty-page", "limit": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["events"] == []
    assert body["pagination"]["total"] == 0
    assert body["pagination"]["hasMore"] is False


def test_invalid_limit_rejected(client):
    response = client.get("/events", params={"account": "acct-page", "limit": 0})
    assert response.status_code == 422


def test_invalid_offset_rejected(client):
    response = client.get("/events", params={"account": "acct-page", "offset": -1})
    assert response.status_code == 422
