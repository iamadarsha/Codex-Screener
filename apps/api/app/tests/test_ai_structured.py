"""Tests for the structured-output validation boundary in ai_suggestions.py.

Covers `_parse_ai_response`'s Pydantic-backed validation (`AIPicksResponse`
from `app/services/ai_schemas.py`), the native structured-output wiring in
`_call_gemini`/`_call_alternative_ai`, and `generate_suggestions()` staying
exception-safe end-to-end when a provider's structured call blows up.

No real network/API calls are made — the SDK clients (`google.genai.Client`,
`groq.AsyncGroq`, `httpx.AsyncClient.post`) are monkeypatched with fakes,
following this repo's `_FakeSession`-style mocking convention
(see `test_candles.py`).
"""

from __future__ import annotations

import json

from app.services import ai_suggestions


def _valid_pick(symbol="RELIANCE", **overrides):
    pick = {
        "symbol": symbol,
        "name": "Reliance Industries",
        "sector": "Energy",
        "rationale": "Strong momentum on high volume with a bullish EMA crossover.",
        "confidence": 8,
        "catalyst": "Q3 earnings beat",
        "target_horizon": "intraday",
        "action": "BUY",
        "target_pct": 1.5,
        "stop_loss_pct": 0.8,
        "tags": ["momentum", "earnings"],
        "news_sources": [
            {
                "title": "RIL beats Q3 estimates",
                "url": "https://example.com/a",
                "source": "ET",
                "published_at": "2026-09-14",
            }
        ],
    }
    pick.update(overrides)
    return pick


def _valid_response_text() -> str:
    return json.dumps(
        {
            "intraday": [_valid_pick("RELIANCE")],
            "weekly": [_valid_pick("TCS", target_horizon="weekly")],
            "monthly": [_valid_pick("INFY", target_horizon="monthly")],
        }
    )


# ---------------------------------------------------------------------------
# _parse_ai_response: acceptance
# ---------------------------------------------------------------------------
def test_valid_response_is_accepted_and_produces_expected_shape():
    parsed = ai_suggestions._parse_ai_response(_valid_response_text())
    assert parsed is not None
    assert parsed["intraday"][0]["symbol"] == "RELIANCE"
    assert parsed["intraday"][0]["action"] == "BUY"
    assert parsed["weekly"][0]["symbol"] == "TCS"
    assert parsed["monthly"][0]["symbol"] == "INFY"
    # news_sources round-trip through validation as plain dicts
    assert parsed["intraday"][0]["news_sources"][0]["title"] == "RIL beats Q3 estimates"


def test_markdown_fenced_valid_response_is_still_parsed():
    fenced = f"```json\n{_valid_response_text()}\n```"
    parsed = ai_suggestions._parse_ai_response(fenced)
    assert parsed is not None
    assert parsed["intraday"][0]["symbol"] == "RELIANCE"


def test_flat_list_shape_is_still_accepted_and_sliced_5_5_5():
    picks = [_valid_pick(f"SYM{i}") for i in range(12)]
    text = json.dumps(picks)
    parsed = ai_suggestions._parse_ai_response(text)
    assert parsed is not None
    assert len(parsed["intraday"]) == 5
    assert len(parsed["weekly"]) == 5
    assert len(parsed["monthly"]) == 2


# ---------------------------------------------------------------------------
# _parse_ai_response: rejection (fail closed, no silent coercion)
# ---------------------------------------------------------------------------
def test_missing_required_field_is_rejected():
    bad_pick = _valid_pick()
    del bad_pick["rationale"]
    text = json.dumps({"intraday": [bad_pick], "weekly": [], "monthly": []})
    assert ai_suggestions._parse_ai_response(text) is None


def test_wrong_field_type_confidence_as_string_is_rejected():
    bad_pick = _valid_pick(confidence="very high")
    text = json.dumps({"intraday": [bad_pick], "weekly": [], "monthly": []})
    assert ai_suggestions._parse_ai_response(text) is None


def test_invalid_action_enum_value_is_rejected():
    bad_pick = _valid_pick(action="HOLD")
    text = json.dumps({"intraday": [bad_pick], "weekly": [], "monthly": []})
    assert ai_suggestions._parse_ai_response(text) is None


def test_confidence_out_of_range_after_normalization_is_rejected():
    # 0 isn't rescued by _normalize_confidence (only >10 values are rescaled)
    bad_pick = _valid_pick(confidence=0)
    text = json.dumps({"intraday": [bad_pick], "weekly": [], "monthly": []})
    assert ai_suggestions._parse_ai_response(text) is None


def test_confidence_above_ten_is_rescaled_before_validation():
    # _normalize_confidence divides an out-of-range (0-100 style) score by 10
    pick = _valid_pick(confidence=85)
    text = json.dumps({"intraday": [pick], "weekly": [], "monthly": []})
    parsed = ai_suggestions._parse_ai_response(text)
    assert parsed is not None
    assert 1 <= parsed["intraday"][0]["confidence"] <= 10


def test_malformed_non_json_text_falls_back_to_none_without_raising():
    assert ai_suggestions._parse_ai_response("this is not json at all {{{") is None


def test_unrecognized_shape_is_rejected():
    assert ai_suggestions._parse_ai_response(json.dumps({"foo": "bar"})) is None


# ---------------------------------------------------------------------------
# Provider-unsupported (no API key configured) falls back gracefully
# ---------------------------------------------------------------------------
class _FakeSettingsNoKeys:
    gemini_api_key = ""
    gemini_backup_api_key = ""
    groq_api_key = ""
    xai_api_key = ""


async def test_gemini_skips_cleanly_with_no_api_keys(monkeypatch):
    monkeypatch.setattr("app.core.config.get_settings", lambda: _FakeSettingsNoKeys())
    result = await ai_suggestions._call_gemini([], "Market data unavailable.")
    assert result == {"intraday": [], "weekly": [], "monthly": []}


async def test_alternative_ai_skips_cleanly_with_no_api_keys(monkeypatch):
    monkeypatch.setattr("app.core.config.get_settings", lambda: _FakeSettingsNoKeys())
    picks, provider = await ai_suggestions._call_alternative_ai([], "Market data unavailable.")
    assert picks == {"intraday": [], "weekly": [], "monthly": []}
    assert provider == "none"


# ---------------------------------------------------------------------------
# Structured-call exceptions are caught, not propagated
# ---------------------------------------------------------------------------
class _FakeSettingsGeminiOnly:
    gemini_api_key = "fake-key"
    gemini_backup_api_key = ""
    groq_api_key = ""
    xai_api_key = ""


async def test_call_gemini_returns_empty_on_sdk_exception(monkeypatch):
    monkeypatch.setattr("app.core.config.get_settings", lambda: _FakeSettingsGeminiOnly())

    class _BoomClient:
        def __init__(self, api_key):
            raise RuntimeError("sdk exploded")

    monkeypatch.setattr("google.genai.Client", _BoomClient)

    result = await ai_suggestions._call_gemini([], "some market data")
    assert result == {"intraday": [], "weekly": [], "monthly": []}


class _FakeSettingsGroqOnly:
    gemini_api_key = ""
    gemini_backup_api_key = ""
    groq_api_key = "fake"
    xai_api_key = ""


async def test_call_alternative_ai_groq_exception_falls_through_gracefully(monkeypatch):
    monkeypatch.setattr("app.core.config.get_settings", lambda: _FakeSettingsGroqOnly())

    class _BoomGroq:
        def __init__(self, api_key):
            raise RuntimeError("groq sdk exploded")

    monkeypatch.setattr("groq.AsyncGroq", _BoomGroq)

    picks, provider = await ai_suggestions._call_alternative_ai([], "market data")
    assert picks == {"intraday": [], "weekly": [], "monthly": []}
    assert provider == "none"


class _FakeSettingsXaiOnly:
    gemini_api_key = ""
    gemini_backup_api_key = ""
    groq_api_key = ""
    xai_api_key = "fake"


async def test_call_alternative_ai_xai_exception_returns_none_provider(monkeypatch):
    monkeypatch.setattr("app.core.config.get_settings", lambda: _FakeSettingsXaiOnly())

    async def _boom_post(self, *args, **kwargs):
        raise RuntimeError("xai http exploded")

    monkeypatch.setattr("httpx.AsyncClient.post", _boom_post)

    picks, provider = await ai_suggestions._call_alternative_ai([], "market data")
    assert picks == {"intraday": [], "weekly": [], "monthly": []}
    assert provider == "none"


async def test_generate_suggestions_survives_structured_call_exception(monkeypatch, fake_redis):
    """If every layer's structured call throws, generate_suggestions() must
    still return a valid (empty-picks) response rather than propagating."""

    async def _boom(*args, **kwargs):
        raise RuntimeError("simulated crash")

    async def _no_headlines():
        return []

    async def _fake_market_summary():
        return "=== Market Indices ===\n  NIFTY 50: 22000 (0.5%)"

    monkeypatch.setattr(ai_suggestions, "_fetch_news_headlines", _no_headlines)
    monkeypatch.setattr(ai_suggestions, "_get_market_summary", _fake_market_summary)
    monkeypatch.setattr(ai_suggestions, "_generate_technical_picks", _boom)
    monkeypatch.setattr(ai_suggestions, "_call_gemini", _boom)
    monkeypatch.setattr(ai_suggestions, "_call_alternative_ai", _boom)

    result = await ai_suggestions.generate_suggestions()

    assert result["intraday"] == []
    assert result["weekly"] == []
    assert result["monthly"] == []
    assert "generated_at" in result
    # The bug fix: no layer succeeded, so source must not be hardcoded to
    # "groq" — it should honestly reflect that nothing produced picks.
    assert result["source"] == "none"


# ---------------------------------------------------------------------------
# Native structured-output wiring actually gets used
# ---------------------------------------------------------------------------
async def test_gemini_success_passes_structured_output_config(monkeypatch):
    monkeypatch.setattr("app.core.config.get_settings", lambda: _FakeSettingsGeminiOnly())

    captured: dict = {}

    class _FakeResponse:
        text = _valid_response_text()

    class _FakeModels:
        def generate_content(self, **kwargs):
            captured.update(kwargs)
            return _FakeResponse()

    class _FakeClient:
        def __init__(self, api_key):
            self.models = _FakeModels()

    monkeypatch.setattr("google.genai.Client", _FakeClient)

    result = await ai_suggestions._call_gemini([], "market data")
    assert result["intraday"][0]["symbol"] == "RELIANCE"

    from google.genai import types as genai_types

    from app.services.ai_schemas import AIPicksResponse

    config = captured.get("config")
    assert isinstance(config, genai_types.GenerateContentConfig)
    assert config.response_mime_type == "application/json"
    assert config.response_schema is AIPicksResponse


async def test_groq_success_returns_parsed_picks_and_response_format(monkeypatch):
    monkeypatch.setattr("app.core.config.get_settings", lambda: _FakeSettingsGroqOnly())

    captured_kwargs: dict = {}

    class _FakeMessage:
        content = _valid_response_text()

    class _FakeChoice:
        message = _FakeMessage()

    class _FakeResponse:
        choices = [_FakeChoice()]

    class _FakeCompletions:
        async def create(self, **kwargs):
            captured_kwargs.update(kwargs)
            return _FakeResponse()

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeAsyncGroq:
        def __init__(self, api_key):
            self.chat = _FakeChat()

    monkeypatch.setattr("groq.AsyncGroq", _FakeAsyncGroq)

    picks, provider = await ai_suggestions._call_alternative_ai([], "market data")
    assert provider == "groq"
    assert picks["intraday"][0]["symbol"] == "RELIANCE"
    assert captured_kwargs.get("response_format") == {"type": "json_object"}


async def test_xai_success_returns_parsed_picks_and_response_format(monkeypatch):
    monkeypatch.setattr("app.core.config.get_settings", lambda: _FakeSettingsXaiOnly())

    captured: dict = {}

    class _FakeResp:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": _valid_response_text()}}]}

    async def _fake_post(self, url, headers=None, json=None):
        captured["json"] = json
        return _FakeResp()

    monkeypatch.setattr("httpx.AsyncClient.post", _fake_post)

    picks, provider = await ai_suggestions._call_alternative_ai([], "market data")
    assert provider == "xai"
    assert picks["weekly"][0]["symbol"] == "TCS"
    assert captured["json"]["response_format"] == {"type": "json_object"}
