# AI Structured Output

Adds a typed validation boundary to the existing AI-suggestions layer (`apps/api/app/services/ai_suggestions.py`), inspired by the structured-output *concept* in TradingAgents' `structured.py` — no TradingAgents code or dependency was added; this is a native reimplementation using SDKs already in `requirements.txt`.

## What changed

- **New `apps/api/app/services/ai_schemas.py`**: `NewsSource`, `AIPick`, `AIPicksResponse` — Pydantic v2 models matching exactly what the LLM-sourced picks already contain (symbol, name, sector, rationale, confidence 1-10, catalyst, target_horizon, action, target_pct, stop_loss_pct, tags, news_sources).
- **`_parse_ai_response()`** now validates the model's JSON through `AIPicksResponse` instead of a bare `json.loads` + shallow top-level-key check. A missing field, wrong type, or invalid enum value now fails validation and falls through to the existing next-layer fallback — it never gets silently coerced into a fake-valid pick.
- **Native structured-output requests**: Gemini calls now pass `response_schema=AIPicksResponse` + `response_mime_type="application/json"` (verified against `google-genai==1.75.0`, which accepts a Pydantic model directly, including this nested dict-of-lists shape). Groq and xAI calls pass `response_format={"type": "json_object"}`. The Pydantic validation step still runs afterward regardless — the SDK's structured mode is a hint to the model, not a substitute for validation.
- **Bug fix**: `source` used to be hardcoded to `"groq"` before the Groq/xAI fallback ran, so a successful xAI response was mislabeled as Groq. `_call_alternative_ai` now returns which provider actually produced the result, and `source` reflects that.

## What did not change

- The fallback chain order: deterministic technical picks → Gemini → Groq/xAI → empty.
- The external response shape (`intraday`/`weekly`/`monthly` + `generated_at`/`headline_count`/`next_refresh`/`source`) — unchanged, so no frontend or route change was needed.
- No LangChain/LangGraph dependency was added.

## Fail-closed behavior

| Condition | Result |
|---|---|
| Valid, well-typed JSON | Accepted, used |
| Missing required field | Rejected, falls through to next layer |
| Wrong field type (e.g. confidence as a string) | Rejected, falls through |
| Invalid enum (bad `action` value) | Rejected, falls through |
| Malformed (non-JSON) text | Rejected, falls through |
| Provider unsupported / no API key | Skipped, falls through |
| Structured call throws | Caught, falls through |
| All layers fail | Empty picks, deterministic response shape preserved |

See `apps/api/app/tests/test_ai_structured.py` and `test_ai_suggestions_contract.py` for the full test matrix.
