def _event(event_id: str, event_type: str, amount: float, currency: str = "USD", ts: str = "2026-05-15T10:00:00Z") -> dict:
    return {
        "eventId": event_id,
        "accountId": "acct-balance",
        "type": event_type,
        "amount": amount,
        "currency": currency,
        "eventTimestamp": ts,
    }


def test_credits_minus_debits(client):
    client.post("/events", json=_event("b1", "CREDIT", 100))
    client.post("/events", json=_event("b2", "DEBIT", 30))
    body = client.get("/accounts/acct-balance/balance").json()
    assert body["balances"] == [{"currency": "USD", "balance": "70"}]
    assert body["eventCount"] == 2


def test_duplicate_does_not_double_count(client):
    payload = _event("b-dup", "CREDIT", 40)
    client.post("/events", json=payload)
    client.post("/events", json=payload)
    body = client.get("/accounts/acct-balance/balance").json()
    assert body["eventCount"] == 1
    assert body["balances"][0]["balance"] == "40"


def test_out_of_order_arrival_balance_correct(client):
    client.post("/events", json=_event("late", "CREDIT", 20, ts="2026-05-15T12:00:00Z"))
    client.post("/events", json=_event("early", "DEBIT", 5, ts="2026-05-15T08:00:00Z"))
    body = client.get("/accounts/acct-balance/balance").json()
    assert body["balances"][0]["balance"] == "15"


def test_empty_account_balance(client):
    body = client.get("/accounts/acct-no-events/balance").json()
    assert body["balances"] == []
    assert body["eventCount"] == 0


def test_negative_net_balance(client):
    client.post("/events", json=_event("n1", "DEBIT", 50))
    body = client.get("/accounts/acct-balance/balance").json()
    assert body["balances"][0]["balance"] == "-50"


def test_multi_currency_grouping(client):
    client.post("/events", json=_event("m1", "CREDIT", 10, currency="USD"))
    client.post("/events", json=_event("m2", "CREDIT", 5, currency="EUR"))
    body = client.get("/accounts/acct-balance/balance").json()
    assert {entry["currency"]: entry["balance"] for entry in body["balances"]} == {
        "EUR": "5",
        "USD": "10",
    }
