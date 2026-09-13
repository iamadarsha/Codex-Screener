"""Contract tests: generate_suggestions()'s external response shape must be
unchanged by the Integration A structured-output rework.

These exercise the existing "no API key configured" deterministic path
(RSS + technical scoring, zero AI dependency) plus a regression test for the
real pre-existing bug this round fixes: `source` used to be hardcoded to
"groq" before `_call_alternative_ai` ran, mislabeling provenance whenever
Groq failed and xAI actually produced the result.

No real network/RSS calls are made — `_fetch_news_headlines` is
monkeypatched, and Redis is the `fake_redis` fixture (see conftest.py).
"""

from __future__ import annotations

import json

from app.services import ai_suggestions


async def _no_headlines() -> list[dict[str, str]]:
    return []


def _assert_common_shape(result: dict) -> None:
    assert isinstance(result["intraday"], list)
    assert isinstance(result["weekly"], list)
    assert isinstance(result["monthly"], list)
    assert "generated_at" in result
    assert "headline_count" in result


async def test_no_keys_no_data_returns_deterministic_empty_shape(monkeypatch, fake_redis):
    """No headlines, no market data at all -> the early-return branch.
    No AI provider is ever touched."""
    monkeypatch.setattr(ai_suggestions, "_fetch_news_headlines", _no_headlines)

    result = await ai_suggestions.generate_suggestions()

    _assert_common_shape(result)
    assert result["intraday"] == []
    assert result["weekly"] == []
    assert result["monthly"] == []
    assert result["headline_count"] == 0
    assert "next_refresh" in result


async def test_no_keys_with_technical_data_returns_real_technical_picks(monkeypatch, fake_redis):
    """With live price/indicator data in Redis but no AI keys configured,
    Layer 1 (deterministic technical scoring) must still produce real
    picks — this is the "no API key configured" path the brief calls out."""
    monkeypatch.setattr(ai_suggestions, "_fetch_news_headlines", _no_headlines)

    await fake_redis.set(
        "price:RELIANCE",
        json.dumps({"symbol": "RELIANCE", "ltp": 2500.0, "change_pct": 1.8, "volume": 500000}),
    )
    await fake_redis.hset(
        "ind:RELIANCE:1d",
        mapping={"rsi_14": "45", "ema_9": "2510", "ema_21": "2490"},
    )

    result = await ai_suggestions.generate_suggestions()

    _assert_common_shape(result)
    assert result["source"] == "technical-analysis"
    total_picks = sum(len(result[k]) for k in ("intraday", "weekly", "monthly"))
    assert total_picks > 0
    all_symbols = {
        p["symbol"] for k in ("intraday", "weekly", "monthly") for p in result[k]
    }
    assert "RELIANCE" in all_symbols


class _FakeSettingsXaiOnly:
    gemini_api_key = ""
    gemini_backup_api_key = ""
    groq_api_key = ""
    xai_api_key = "fake-xai-key"


async def test_source_reflects_actual_provider_not_hardcoded_groq(monkeypatch, fake_redis):
    """Regression test for the pre-existing bug: previously `source` was
    hardcoded to "groq" before `_call_alternative_ai` ran, so a successful
    xAI fallback (Groq unset/failed) was mislabeled as "groq". Layer 1 is
    starved of data so it falls through, Gemini is unconfigured, and xAI is
    made to succeed via a mocked HTTP call."""
    headlines = [
        {
            "title": "General market news that matches no NSE symbol keyword",
            "url": "https://example.com/news",
            "source": "Test Wire",
            "published_at": "2026-09-14",
        }
    ]

    async def _fake_headlines():
        return headlines

    async def _empty_technical_picks(*args, **kwargs):
        # Layer 1 is starved of data on purpose — this regression test is
        # about the Layer 3 provider-labeling bug, not Layer 1's own
        # headline-symbol matching (which is exercised elsewhere).
        return {"intraday": [], "weekly": [], "monthly": []}

    monkeypatch.setattr(ai_suggestions, "_fetch_news_headlines", _fake_headlines)
    monkeypatch.setattr(ai_suggestions, "_generate_technical_picks", _empty_technical_picks)
    monkeypatch.setattr("app.core.config.get_settings", lambda: _FakeSettingsXaiOnly())

    xai_response_text = json.dumps(
        {
            "intraday": [],
            "weekly": [],
            "monthly": [
                {
                    "symbol": "INFY",
                    "name": "Infosys",
                    "sector": "IT",
                    "rationale": "Strong positional setup with sector tailwinds building.",
                    "confidence": 7,
                    "catalyst": "Sector rotation into IT",
                    "target_horizon": "monthly",
                    "action": "BUY",
                    "target_pct": 8.0,
                    "stop_loss_pct": 4.0,
                    "tags": ["sector-rotation"],
                    "news_sources": [],
                }
            ],
        }
    )

    class _FakeResp:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": xai_response_text}}]}

    async def _fake_post(self, url, headers=None, json=None):
        return _FakeResp()

    monkeypatch.setattr("httpx.AsyncClient.post", _fake_post)

    result = await ai_suggestions.generate_suggestions()

    _assert_common_shape(result)
    assert result["source"] == "xai"
    assert result["monthly"][0]["symbol"] == "INFY"
