def _event(event_id: str, event_type: str, amount: float) -> dict:
    return {
        "eventId": event_id,
        "accountId": "acct-bal",
        "type": event_type,
        "amount": amount,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z",
    }


def test_balance_response_shape(client):
    client.post("/events", json=_event("evt-c", "CREDIT", 100.0))
    client.post("/events", json=_event("evt-d", "DEBIT", 25.0))
    response = client.get("/accounts/acct-bal/balance")
    assert response.status_code == 200
    body = response.json()
    assert body["accountId"] == "acct-bal"
    assert body["eventCount"] == 2
    assert body["balances"] == [{"currency": "USD", "balance": "75"}]
