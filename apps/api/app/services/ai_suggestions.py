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
    # Google News — market overview
    "https://news.google.com/rss/search?q=indian+stock+market+NSE&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=nifty+sensex+breakout&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=india+equity+market+today&hl=en-IN&gl=IN&ceid=IN:en",
    # Google News — broker reports & research
    "https://news.google.com/rss/search?q=india+broker+report+stock+recommendation&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=motilal+oswal+OR+icici+direct+OR+hdfc+securities+stock+pick&hl=en-IN&gl=IN&ceid=IN:en",
    # Direct financial news RSS
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://www.moneycontrol.com/rss/stocksinnews.xml",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.livemint.com/rss/markets",
    "https://www.business-standard.com/rss/markets-106.rss",
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
    """Cache for 6 hours or until next trading day 9 AM, whichever is longer."""
    now = now_ist()
    next_9am = get_next_trading_day_9am()
    delta = (next_9am - now).total_seconds()
    return max(int(delta), 21600)  # minimum 6 hours


async def _fetch_news_headlines() -> list[dict[str, str]]:
    import feedparser
    import httpx

    headlines: list[dict[str, str]] = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; CodexScreener/1.0)"}
    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        for url in RSS_FEEDS:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    source_name = feed.feed.get("title", "News")
                    for entry in feed.entries[:10]:
                        title = entry.get("title", "")
                        if not title:
                            continue
                        link = entry.get("link", "")
                        published = entry.get("published", "")
                        headlines.append({
                            "title": title,
                            "url": link,
                            "source": source_name,
                            "published_at": published,
                        })
            except Exception as e:
                log.warning("rss_fetch_failed url=%s error=%s", url, e)

    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for h in headlines:
        if h["title"] not in seen:
            seen.add(h["title"])
            unique.append(h)
    return unique[:40]


async def _get_market_summary() -> str:
    """Read Nifty 50 index data and top gainers/losers from Redis."""
    from app.services.redis_cache import get_json, get_redis, hget_all

    summary_parts: list[str] = []

    # --- Index data ---
    try:
        indices = await get_json("market:indices")
        if indices:
            summary_parts.append("=== Market Indices ===")
            if isinstance(indices, list):
                for idx in indices:
                    name = idx.get("name", idx.get("symbol", ""))
                    ltp = idx.get("ltp", idx.get("last", ""))
                    chg = idx.get("change_pct", idx.get("pChange", ""))
                    summary_parts.append(f"  {name}: {ltp} ({chg}%)")
            elif isinstance(indices, dict):
                for name, data in indices.items():
                    if isinstance(data, dict):
                        ltp = data.get("ltp", data.get("last", ""))
                        chg = data.get("change_pct", data.get("pChange", ""))
                        summary_parts.append(f"  {name}: {ltp} ({chg}%)")
    except Exception as e:
        log.warning("failed to read market indices: %s", e)

    # --- Top gainers / losers from price:* keys ---
    try:
        r = await get_redis()
        price_keys = []
        async for key in r.scan_iter(match="price:*", count=500):
            price_keys.append(key)

        stocks: list[dict[str, Any]] = []
        for pk in price_keys[:300]:
            try:
                data = await hget_all(pk)
                if not data:
                    raw = await r.get(pk)
                    if raw:
                        data = json.loads(raw) if isinstance(raw, str) else {}
                if data:
                    symbol = data.get("symbol", pk.replace("price:", ""))
                    change_pct = float(data.get("change_pct", data.get("pChange", 0)) or 0)
                    ltp = data.get("ltp", data.get("last", data.get("close", "")))
                    stocks.append({"symbol": symbol, "change_pct": change_pct, "ltp": ltp})
            except Exception:
                continue

        if stocks:
            stocks.sort(key=lambda x: x["change_pct"], reverse=True)
            top_gainers = stocks[:5]
            top_losers = stocks[-5:]

            summary_parts.append("\n=== Top 5 Gainers ===")
            for s in top_gainers:
                summary_parts.append(f"  {s['symbol']}: LTP {s['ltp']} ({s['change_pct']:+.2f}%)")

            summary_parts.append("\n=== Top 5 Losers ===")
            for s in top_losers:
                summary_parts.append(f"  {s['symbol']}: LTP {s['ltp']} ({s['change_pct']:+.2f}%)")
    except Exception as e:
        log.warning("failed to read price data: %s", e)

    return "\n".join(summary_parts) if summary_parts else "Market data unavailable."


async def _call_gemini(headlines: list[dict[str, str]], market_summary: str) -> dict[str, list[dict[str, Any]]]:
    import google.generativeai as genai

    from app.core.config import get_settings

    settings = get_settings()
    if not settings.gemini_api_key:
        log.error("gemini_api_key not configured")
        return {"intraday": [], "weekly": [], "monthly": []}

    genai.configure(api_key=settings.gemini_api_key)
    # Try gemini-2.0-flash (widely available), fall back to others
    model = genai.GenerativeModel("gemini-2.0-flash")

    news_block = "\n".join(
        f'[{i+1}] "{h["title"]}" ({h["source"]}) — {h["url"]}'
        for i, h in enumerate(headlines)
    )
    today = now_ist().strftime("%Y-%m-%d")

    prompt = f"""You are an expert Indian stock market analyst with deep knowledge of NSE-listed equities.

=== LIVE MARKET DATA ===
{market_summary}

=== RECENT NEWS HEADLINES (with sources) ===
{news_block}

Today's date: {today}

Generate stock picks across 3 timeframes:
1. **Intraday** (5 picks) – stocks likely to move within today's session
2. **Weekly** (5 picks) – stocks expected to perform over the next 1-5 trading sessions
3. **Monthly** (5 picks) – stocks with strong positional potential over the next 2-4 weeks

Total: 15 picks (no duplicates across timeframes).

For EACH pick, provide ALL of these fields:
- symbol: exact NSE trading symbol (e.g., RELIANCE, TCS, INFY)
- name: full company name
- sector: industry sector
- rationale: 2-3 sentences explaining WHY, referencing specific news headlines by number (e.g., "As per headline [3]...")
- confidence: score from 1 to 10 (integer)
- catalyst: the specific news or technical catalyst driving this pick
- target_horizon: "intraday", "weekly", or "monthly" (must match timeframe)
- action: "BUY" or "SELL"
- target_pct: expected % gain/loss target (positive number, e.g. 2.5 for 2.5%)
- stop_loss_pct: suggested stop-loss % from entry (positive number, e.g. 1.0 for 1%)
- tags: array of relevant tags (e.g., ["momentum", "breakout", "earnings", "sector-rotation", "news-driven"])
- news_sources: array of the specific news sources that influenced this pick, each with {{"title":"headline text","url":"link","source":"source name","published_at":"date"}}

RULES:
- Only suggest liquid NSE stocks (Nifty 500 universe)
- Never suggest penny stocks (price < Rs 50)
- Mix of large-cap and mid-cap across sectors
- Always cite which news or market data influenced each pick
- Each pick MUST include 1-3 items in news_sources referencing the actual headlines above
- Intraday picks should have tighter targets (0.5-3%) and stop-losses (0.3-1.5%)
- Weekly picks: targets 2-8%, stop-losses 1-4%
- Monthly picks: targets 5-20%, stop-losses 3-8%
- No duplicate symbols across timeframes

Return ONLY a valid JSON object (no markdown fences, no explanation outside JSON):
{{"intraday":[{{"symbol":"...","name":"...","sector":"...","rationale":"...","confidence":8,"catalyst":"...","target_horizon":"intraday","action":"BUY","target_pct":1.5,"stop_loss_pct":0.8,"tags":["momentum","news-driven"],"news_sources":[{{"title":"...","url":"...","source":"...","published_at":"..."}}]}}],"weekly":[...],"monthly":[...]}}"""

    try:
        import re

        response = await model.generate_content_async(prompt)
        text = response.text.strip()
        # Robust markdown fence removal (handles ```json, ``` etc.)
        fence_match = re.match(r"^```(?:\w+)?\s*\n(.*?)```\s*$", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()
        parsed = json.loads(text)

        # Normalize confidence to 1-10 scale if Gemini returned 0-100
        def _normalize_confidence(picks: list) -> list:
            for pick in picks:
                c = pick.get("confidence", 5)
                if isinstance(c, (int, float)) and c > 10:
                    pick["confidence"] = max(1, min(10, round(c / 10)))
            return picks

        # Validate structure
        if isinstance(parsed, dict) and all(k in parsed for k in ("intraday", "weekly", "monthly")):
            for key in ("intraday", "weekly", "monthly"):
                parsed[key] = _normalize_confidence(parsed.get(key, []))
            return parsed
        # If Gemini returned a flat list, try to bucket it
        if isinstance(parsed, list):
            parsed = _normalize_confidence(parsed)
            return {"intraday": parsed[:5], "weekly": parsed[5:10], "monthly": parsed[10:15]}
        return {"intraday": [], "weekly": [], "monthly": []}
    except Exception as e:
        log.error("gemini_call_failed error=%s type=%s", e, type(e).__name__)
        return {"intraday": [], "weekly": [], "monthly": []}


async def generate_suggestions() -> dict[str, Any]:
    headlines = await _fetch_news_headlines()
    market_summary = await _get_market_summary()
    log.info("fetched %d news headlines, market_summary_len=%d", len(headlines), len(market_summary))

    if not headlines and market_summary == "Market data unavailable.":
        return {
            "intraday": [],
            "weekly": [],
            "monthly": [],
            "generated_at": now_ist().isoformat(),
            "headline_count": 0,
            "next_refresh": get_next_trading_day_9am().isoformat(),
        }

    picks = await _call_gemini(headlines, market_summary)

    total_count = sum(len(v) for v in picks.values())

    result = {
        "intraday": picks.get("intraday", []),
        "weekly": picks.get("weekly", []),
        "monthly": picks.get("monthly", []),
        "generated_at": now_ist().isoformat(),
        "headline_count": len(headlines),
        "next_refresh": get_next_trading_day_9am().isoformat(),
    }

    # Only cache if we actually got picks (don't cache empty results)
    if total_count > 0:
        try:
            from app.services.redis_cache import set_json

            ttl = _compute_ttl_seconds()
            await set_json(REDIS_KEY, result, ttl=ttl)
            log.info("ai_suggestions_cached count=%d ttl=%d", total_count, ttl)
        except Exception as e:
            log.warning("failed to cache ai suggestions: %s", e)

    return result


async def get_suggestions() -> dict[str, Any] | None:
    try:
        from app.services.redis_cache import get_json

        cached = await get_json(REDIS_KEY)
        if cached:
            return cached
    except Exception:
        pass
    return None


async def get_or_generate_suggestions() -> dict[str, Any]:
    """Get cached suggestions or generate fresh ones. Never returns None."""
    cached = await get_suggestions()
    if cached:
        return cached
    try:
        return await generate_suggestions()
    except Exception as e:
        log.error("Failed to generate AI suggestions: %s", e)
        return {
            "intraday": [], "weekly": [], "monthly": [],
            "generated_at": now_ist().isoformat(),
            "headline_count": 0,
            "error": "Generation failed — will retry on next request",
        }
