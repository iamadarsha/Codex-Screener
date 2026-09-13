"""`compute_market_regime()` truth-table tests — pure, synthetic dicts only,
no mocks, following `test_failover.py`'s convention exactly. Also covers the
new `GET /api/market/regime` route using the `fake_redis`/`api_client`
fixtures already established for other market routes."""

from __future__ import annotations

from app.market.regime import (
    BREADTH_ADVANCE_HEAVY_RATIO,
    BREADTH_DECLINE_HEAVY_RATIO,
    TREND_CHANGE_PCT_THRESHOLD,
    VIX_HIGH_VOLATILITY_THRESHOLD,
    MarketRegime,
    compute_market_regime,
)


def _indices(vix: float = 14.0, nifty_change_pct: float = 0.0) -> list[dict]:
    return [
        {
            "name": "NIFTY 50",
            "symbol": "NIFTY50",
            "last": 24000.0,
            "change": nifty_change_pct * 240,
            "change_pct": nifty_change_pct,
            "open": 24000.0,
            "high": 24100.0,
            "low": 23900.0,
            "prev_close": 24000.0,
        },
        {
            "name": "INDIA VIX",
            "symbol": "INDIAVIX",
            "last": vix,
            "change": 0.0,
            "change_pct": 0.0,
            "open": vix,
            "high": vix,
            "low": vix,
            "prev_close": vix,
        },
    ]


def _breadth(advances: int, declines: int, unchanged: int = 0) -> dict:
    total = advances + declines + unchanged
    ratio = round(advances / declines, 2) if declines > 0 else float(advances)
    return {
        "advances": advances,
        "declines": declines,
        "unchanged": unchanged,
        "total": total,
        "advance_decline_ratio": ratio,
    }


def test_high_vix_overrides_trend_and_breadth():
    # Strongly bullish trend + advance-heavy breadth, but VIX is elevated —
    # HIGH_VOLATILITY must win regardless.
    indices = _indices(vix=VIX_HIGH_VOLATILITY_THRESHOLD + 5, nifty_change_pct=2.0)
    breadth = _breadth(advances=300, declines=50)

    result = compute_market_regime(indices, breadth)

    assert result.regime == MarketRegime.HIGH_VOLATILITY
    assert result.vix_level == VIX_HIGH_VOLATILITY_THRESHOLD + 5
    assert result.nifty_change_pct == 2.0


def test_strong_bullish_trend_with_advancing_breadth():
    indices = _indices(vix=14.0, nifty_change_pct=TREND_CHANGE_PCT_THRESHOLD + 0.5)
    breadth = _breadth(advances=300, declines=100)  # ratio 3.0, well above the advance-heavy band

    result = compute_market_regime(indices, breadth)

    assert result.regime == MarketRegime.TRENDING_BULLISH
    assert result.advance_decline_ratio >= BREADTH_ADVANCE_HEAVY_RATIO


def test_strong_bearish_trend_with_declining_breadth():
    indices = _indices(vix=14.0, nifty_change_pct=-(TREND_CHANGE_PCT_THRESHOLD + 0.5))
    breadth = _breadth(advances=80, declines=320)  # ratio 0.25, well below the decline-heavy band

    result = compute_market_regime(indices, breadth)

    assert result.regime == MarketRegime.TRENDING_BEARISH
    assert result.advance_decline_ratio <= BREADTH_DECLINE_HEAVY_RATIO


def test_flat_change_and_balanced_breadth_is_choppy():
    indices = _indices(vix=14.0, nifty_change_pct=0.1)
    breadth = _breadth(advances=210, declines=200)  # roughly balanced

    result = compute_market_regime(indices, breadth)

    assert result.regime == MarketRegime.CHOPPY


def test_trend_without_confirming_breadth_is_choppy():
    # NIFTY 50 is up strongly, but breadth doesn't confirm (narrow leadership)
    # — should not be called a clean trend.
    indices = _indices(vix=14.0, nifty_change_pct=2.0)
    breadth = _breadth(advances=180, declines=200)

    result = compute_market_regime(indices, breadth)

    assert result.regime == MarketRegime.CHOPPY


def test_missing_nifty_50_falls_back_gracefully():
    indices = [
        {
            "name": "INDIA VIX",
            "last": 14.0,
            "change": 0.0,
            "change_pct": 0.0,
        }
    ]
    breadth = _breadth(advances=100, declines=100)

    result = compute_market_regime(indices, breadth)

    assert result.regime == MarketRegime.CHOPPY
    assert result.nifty_change_pct == 0.0
    assert result.extra.get("nifty_missing") is True


def test_empty_breadth_dict_falls_back_gracefully():
    indices = _indices(vix=14.0, nifty_change_pct=2.0)

    result = compute_market_regime(indices, {})

    assert result.regime == MarketRegime.CHOPPY
    assert result.advances == 0
    assert result.declines == 0
    assert result.extra.get("breadth_missing") is True


def test_malformed_indices_input_does_not_crash():
    # Neither a list nor a dict — e.g. a completely garbled Redis payload.
    result = compute_market_regime("not-a-valid-payload", {"advances": 1, "declines": 1})

    assert result.regime == MarketRegime.CHOPPY
    assert result.extra.get("indices_malformed") is True
    assert result.vix_level is None


def test_single_dict_indices_input_is_normalized_to_a_list():
    # compute_market_regime() accepts a single dict too, per its signature.
    single_index = _indices(vix=14.0, nifty_change_pct=0.0)[0]

    result = compute_market_regime(single_index, _breadth(100, 100))

    assert result.nifty_change_pct == 0.0
    assert result.vix_level is None  # no VIX row present in a single NIFTY 50 dict
    assert result.extra.get("vix_missing") is True


async def test_regime_route_returns_cached_redis_value(fake_redis, api_client):
    import json

    from app.utils.redis_keys import regime_key

    await fake_redis.set(
        regime_key(),
        json.dumps(
            {
                "regime": "trending_bullish",
                "vix_level": 13.5,
                "nifty_change_pct": 1.2,
                "advance_decline_ratio": 2.5,
                "advances": 300,
                "declines": 120,
                "unchanged": 20,
                "extra": {},
            }
        ),
    )

    resp = await api_client.get("/api/market/regime")

    assert resp.status_code == 200
    body = resp.json()
    assert body["regime"] == "trending_bullish"
    assert body["vix_level"] == 13.5
    assert body["advances"] == 300


async def test_regime_route_falls_back_to_recompute_when_cache_empty(fake_redis, api_client):
    import json

    await fake_redis.set(
        "market:indices",
        json.dumps(_indices(vix=25.0, nifty_change_pct=0.0)),
    )
    await fake_redis.set("market:breadth", json.dumps(_breadth(100, 100)))

    resp = await api_client.get("/api/market/regime")

    assert resp.status_code == 200
    body = resp.json()
    assert body["regime"] == "high_volatility"
    assert body["vix_level"] == 25.0
