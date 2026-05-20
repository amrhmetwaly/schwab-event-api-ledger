def test_quickstart_submit_and_query_flow(client):
    payload = {
        "eventId": "evt-001",
        "accountId": "acct-123",
        "type": "CREDIT",
        "amount": 150.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z",
        "metadata": {"source": "mainframe-batch", "batchId": "B-9042"},
    }
    created = client.post("/events", json=payload)
    assert created.status_code == 201
    duplicate = client.post("/events", json=payload)
    assert duplicate.status_code == 200

    by_id = client.get("/events/evt-001")
    assert by_id.status_code == 200

    listing = client.get("/events", params={"account": "acct-123"})
    assert listing.status_code == 200
    assert len(listing.json()["events"]) == 1

    balance = client.get("/accounts/acct-123/balance")
    assert balance.status_code == 200
    assert balance.json()["balances"][0]["balance"] == "150"
