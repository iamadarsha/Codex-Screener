"""End-to-end: POST /api/screener/custom with the new `dsl` field, then
GET /api/screener/results/{scan_id} — verifies the DSL wiring into
screener_engine.py and the scan_result_key cache-key fix (Phase 3.1)."""

from __future__ import annotations

import httpx
import pytest


@pytest.mark.usefixtures("fake_redis")
async def test_custom_dsl_scan_runs_and_is_retrievable_via_results(
    fake_redis, api_client: httpx.AsyncClient
):
    # Populate a tiny universe + one symbol's indicator hash directly in
    # fakeredis, mirroring what nse_poller.py / app.market normally write.
    await fake_redis.sadd("universe:nifty500", "RELIANCE")
    await fake_redis.hset(
        "ind:RELIANCE:1d",
        mapping={"close": "2500.0", "rsi_14": "72.5", "volume": "100000"},
    )

    payload = {
        "name": "rsi overbought via DSL",
        "dsl": {"left": {"indicator": "rsi", "length": 14}, "op": "gt", "right": 70},
        "universe": "nifty500",
        "timeframe": "1d",
    }
    resp = await api_client.post("/api/screener/custom", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_matches"] == 1
    assert body["items"][0]["symbol"] == "RELIANCE"
    scan_id = body["scan_id"]
    assert scan_id.startswith("custom-")

    # The cache-key bug fix: this used to 404 unconditionally because the
    # writer and reader used different Redis keys.
    results_resp = await api_client.get(f"/api/screener/results/{scan_id}")
    assert results_resp.status_code == 200
    assert results_resp.json()["scan_id"] == scan_id
    assert results_resp.json()["total_matches"] == 1


@pytest.mark.usefixtures("fake_redis")
async def test_custom_dsl_scan_rejects_invalid_dsl_with_422(
    fake_redis, api_client: httpx.AsyncClient
):
    payload = {
        "dsl": {"left": {"indicator": "not_a_real_indicator"}, "op": "gt", "right": 1},
        "universe": "nifty500",
    }
    resp = await api_client.post("/api/screener/custom", json=payload)
    assert resp.status_code == 422


@pytest.mark.usefixtures("fake_redis")
async def test_legacy_flat_conditions_shape_still_works_unchanged(
    fake_redis, api_client: httpx.AsyncClient
):
    await fake_redis.sadd("universe:nifty500", "TCS")
    await fake_redis.hset("ind:TCS:1d", mapping={"close": "3500.0", "rsi_14": "25.0"})

    payload = {
        "conditions": [{"indicator": "rsi_14", "operator": "lt", "value": 30}],
        "universe": "nifty500",
        "timeframe": "1d",
    }
    resp = await api_client.post("/api/screener/custom", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_matches"] == 1
    assert body["items"][0]["symbol"] == "TCS"
