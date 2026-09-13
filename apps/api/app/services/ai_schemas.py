"""Pydantic schemas for validating structured AI output.

These models describe exactly what `ai_suggestions.py`'s shared prompt
(`_build_ai_prompt`) asks Gemini/Groq/xAI to return per pick — see that
function's own field spec and the JSON example at the end of the prompt.

Scope: these schemas validate ONLY the JSON that comes back from the LLM
providers (Gemini / Groq / xAI). The deterministic technical-picks path
(`_generate_technical_picks`) already produces clean, fully-controlled data
built from the same field set and does not need to pass through this
validation boundary.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class NewsSource(BaseModel):
    """A single news source cited by an AI-generated pick.

    Field names match the headline dicts produced by
    `_fetch_news_headlines()` and the `news_sources` shape the shared
    prompt asks each LLM provider to echo back.
    """

    title: str
    url: str = ""
    source: str = ""
    published_at: str = ""


class AIPick(BaseModel):
    """A single AI-generated stock pick, as emitted by Gemini/Groq/xAI.

    Field set matches `_build_ai_prompt`'s per-pick spec exactly — nothing
    invented, nothing dropped. `confidence` keeps the same 1-10 range that
    `_normalize_confidence` already coerces existing out-of-range values
    into before this model is validated.
    """

    symbol: str
    name: str | None = None
    sector: str | None = None
    rationale: str
    confidence: int = Field(ge=1, le=10)
    catalyst: str | None = None
    target_horizon: str | None = None
    action: Literal["BUY", "SELL"]
    target_pct: float | None = None
    stop_loss_pct: float | None = None
    tags: list[str] = Field(default_factory=list)
    news_sources: list[NewsSource] = Field(default_factory=list)


class AIPicksResponse(BaseModel):
    """Top-level shape returned by the AI layers: picks per timeframe bucket."""

    intraday: list[AIPick] = Field(default_factory=list)
    weekly: list[AIPick] = Field(default_factory=list)
    monthly: list[AIPick] = Field(default_factory=list)
