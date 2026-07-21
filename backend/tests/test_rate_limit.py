from app.core.rate_limit import REQUEST_LIMIT


def test_requests_within_limit_pass(client):
    for _ in range(REQUEST_LIMIT):
        resp = client.get("/health")
        assert resp.status_code == 200


def test_requests_over_limit_are_blocked(client):
    for _ in range(REQUEST_LIMIT):
        client.get("/health")

    resp = client.get("/health")

    assert resp.status_code == 429


def test_block_persists_across_requests(client):
    for _ in range(REQUEST_LIMIT + 1):
        client.get("/health")

    resp = client.get("/health")

    assert resp.status_code == 429
