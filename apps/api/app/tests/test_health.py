from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_route_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")
    body = response.json()

    assert response.status_code == 200
    # "ok" requires a live Redis + running poller, neither guaranteed in a
    # test environment (previously this test hardcoded {"status": "ok"},
    # which only passed by coincidence when a local Redis happened to be
    # reachable — it would fail in CI otherwise). Assert the documented
    # shape instead of a specific infra-dependent value.
    assert body["status"] in ("ok", "degraded")
    assert body["redis"] in ("ok", "unavailable")
    assert body["poller"] in ("running", "stopped")
    assert isinstance(body["universe_size"], int)
    assert isinstance(body["uptime_seconds"], int)

