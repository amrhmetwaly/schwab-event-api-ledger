from concurrent.futures import ThreadPoolExecutor, as_completed


def _payload(event_id: str, **overrides) -> dict:
    data = {
        "eventId": event_id,
        "accountId": "acct-race",
        "type": "CREDIT",
        "amount": 25.0,
        "currency": "USD",
        "eventTimestamp": "2026-05-15T14:02:11Z",
    }
    data.update(overrides)
    return data


def _parallel_post(client, payload: dict, workers: int = 8) -> list[int]:
    def _submit() -> int:
        return client.post("/events", json=payload).status_code

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_submit) for _ in range(workers)]
        return [future.result() for future in as_completed(futures)]


def test_parallel_identical_submissions_are_idempotent(client):
    payload = _payload("evt-parallel-dup")
    statuses = _parallel_post(client, payload)
    assert 201 in statuses
    assert all(status in {200, 201} for status in statuses)
    assert statuses.count(201) == 1
    assert statuses.count(200) == len(statuses) - 1

    listing = client.get("/events", params={"account": "acct-race"}).json()
    assert len(listing["events"]) == 1
    balance = client.get("/accounts/acct-race/balance").json()
    assert balance["eventCount"] == 1
    assert balance["balances"][0]["balance"] == "25"


def test_parallel_conflicting_submissions_leave_ledger_unchanged(client):
    base = _payload("evt-parallel-conflict")
    assert client.post("/events", json=base).status_code == 201

    conflict_payload = _payload("evt-parallel-conflict", amount=99.0, type="DEBIT")
    statuses = _parallel_post(client, conflict_payload)
    assert all(status == 409 for status in statuses)

    listing = client.get("/events", params={"account": "acct-race"}).json()
    assert len(listing["events"]) == 1
    balance = client.get("/accounts/acct-race/balance").json()
    assert balance["balances"][0]["balance"] == "25"


def test_parallel_new_event_single_row(client):
    payload = _payload("evt-parallel-new")
    statuses = _parallel_post(client, payload, workers=12)
    assert 500 not in statuses
    assert statuses.count(201) == 1
    listing = client.get("/events", params={"account": "acct-race"}).json()
    assert len(listing["events"]) == 1
