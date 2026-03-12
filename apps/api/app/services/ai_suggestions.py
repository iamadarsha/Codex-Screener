"""AI-powered stock suggestions using Gemini 2.5 Flash and RSS news feeds."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from app.utils.time import IST, now_ist

log = logging.getLogger(__name__)

REDIS_KEY = "ai:suggestions"

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=indian+stock+market+NSE&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=nifty+sensex+breakout&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=india+equity+market+today&hl=en-IN&gl=IN&ceid=IN:en",
]


def is_trading_day(dt: datetime | None = None) -> bool:
    if dt is None:
        dt = now_ist()
    return dt.weekday() < 5


def get_next_trading_day_9am() -> datetime:
    dt = now_ist().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
    while dt.weekday() > 4:
        dt += timedelta(days=1)
    return dt


def _compute_ttl_seconds() -> int:
    now = now_ist()
    next_9am = get_next_trading_day_9am()
    delta = (next_9am - now).total_seconds()
    return max(int(delta), 300)


async def _fetch_news_headlines() -> list[str]:
    import feedparser
    import httpx

    headlines: list[str] = []
    async with httpx.AsyncClient(timeout=10) as client:
        for url in RSS_FEEDS:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries[:10]:
                        title = entry.get("title", "")
                        if title:
                            headlines.append(title)
            except Exception as e:
                log.warning("rss_fetch_failed url=%s error=%s", url, e)

    seen: set[str] = set()
    unique: list[str] = []
    for h in headlines:
        if h not in seen:
            seen.add(h)
            unique.append(h)
    return unique[:30]


async def _call_gemini(headlines: list[str]) -> list[dict[str, Any]]:
    import google.generativeai as genai

    from app.core.config import get_settings

    settings = get_settings()
    if not settings.gemini_api_key:
        log.error("gemini_api_key not configured")
        return []

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    news_block = "\n".join(f"- {h}" for h in headlines)
    today = now_ist().strftime("%Y-%m-%d")

    prompt = f"""You are an expert Indian stock market analyst. Based on these recent news headlines:

{news_block}

Today's date: {today}

Suggest exactly 5 NSE-listed stocks that could see positive momentum in the next 1-3 trading sessions.

For each stock, provide:
1. symbol: The exact NSE trading symbol (e.g., RELIANCE, TCS, INFY)
2. name: Full company name
3. sector: Industry sector
4. rationale: 2-3 sentences explaining WHY, referencing specific news
5. confidence: Score from 1-10
6. catalyst: The specific news catalyst driving this pick
7. target_horizon: "intraday", "swing" (2-5 days), or "positional" (1-4 weeks)

RULES:
- Only suggest liquid NSE stocks (Nifty 500 universe)
- Never suggest penny stocks (price < Rs 50)
- Mix of large-cap and mid-cap
- Always cite which news influenced each pick

Return ONLY a valid JSON array, no markdown fences:
[{{"symbol":"...","name":"...","sector":"...","rationale":"...","confidence":8,"catalyst":"...","target_horizon":"swing"}}]"""

    try:
        response = await model.generate_content_async(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0].strip()
        return json.loads(text)
    except Exception as e:
        log.error("gemini_call_failed error=%s", e)
        return []


async def generate_suggestions() -> dict[str, Any]:
    headlines = await _fetch_news_headlines()
    log.info("fetched %d news headlines", len(headlines))

    if not headlines:
        return {
            "suggestions": [],
            "generated_at": now_ist().isoformat(),
            "headline_count": 0,
            "next_refresh": get_next_trading_day_9am().isoformat(),
        }

    suggestions = await _call_gemini(headlines)

    result = {
        "suggestions": suggestions,
        "generated_at": now_ist().isoformat(),
        "headline_count": len(headlines),
        "next_refresh": get_next_trading_day_9am().isoformat(),
    }

    try:
        from app.services.redis_cache import set_json

        ttl = _compute_ttl_seconds()
        await set_json(REDIS_KEY, result, ttl=ttl)
        log.info("ai_suggestions_cached count=%d ttl=%d", len(suggestions), ttl)
    except Exception as e:
        log.warning("failed to cache ai suggestions: %s", e)

    return result


async def get_suggestions() -> dict[str, Any] | None:
    try:
        from app.services.redis_cache import get_json

        return await get_json(REDIS_KEY)
    except Exception:
        return None
