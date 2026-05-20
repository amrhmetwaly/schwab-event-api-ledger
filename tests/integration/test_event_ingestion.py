def _payload(event_id: str, **overrides) -> dict:
    data = {
        "eventId": event_id,
        "accountId": "acct-ingest",
        "type": "CREDIT",
        "amount": 50.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z",
    }
    data.update(overrides)
    return data


def test_valid_create_and_duplicate_no_op(client):
    first = client.post("/events", json=_payload("evt-dup"))
    second = client.post("/events", json=_payload("evt-dup"))
    assert first.status_code == 201
    assert second.status_code == 200
    listing = client.get("/events", params={"account": "acct-ingest"}).json()
    assert len(listing["events"]) == 1
    balance = client.get("/accounts/acct-ingest/balance").json()
    assert balance["eventCount"] == 1
    assert balance["balances"][0]["balance"] == "50"


def test_conflicting_id_rejected_without_mutation(client):
    assert client.post("/events", json=_payload("evt-conflict")).status_code == 201
    conflict = client.post(
        "/events",
        json=_payload("evt-conflict", amount=99.0, type="DEBIT"),
    )
    assert conflict.status_code == 409
    balance = client.get("/accounts/acct-ingest/balance").json()
    assert balance["balances"][0]["balance"] == "50"


def test_validation_error_does_not_mutate(client):
    invalid = _payload("evt-invalid", amount=-1)
    assert client.post("/events", json=invalid).status_code == 422
    listing = client.get("/events", params={"account": "acct-ingest"}).json()
    assert listing["events"] == []
