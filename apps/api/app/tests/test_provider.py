"""Provider logic that's testable without a live Upstox connection
(Phase 2.1 acceptance gate — real connectivity is Milestone 2.2, deferred
until the repo owner has Upstox credentials)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.market.provider import SubscriptionRequest, UpstoxV3Provider


def test_subscription_request_uses_full_d5_wire_name():
    req = SubscriptionRequest(instrument_keys=["NSE_EQ|A", "NSE_EQ|B"])
    payload = json.loads(req.to_json(guid="test-guid"))

    assert payload["method"] == "sub"
    assert payload["guid"] == "test-guid"
    # "full" in Upstox's docs/UI is wire-named `full_d5` in the real
    # RequestMode enum — confirmed from the compiled .proto, not guessed.
    assert payload["data"]["mode"] == "full_d5"
    assert payload["data"]["instrumentKeys"] == ["NSE_EQ|A", "NSE_EQ|B"]


@respx.mock
async def test_authorize_extracts_redirect_uri_from_documented_response_shape():
    respx.get("https://api.upstox.com/v3/feed/market-data-feed/authorize").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "success",
                "data": {"authorized_redirect_uri": "wss://example.upstox.com/feed?code=abc"},
            },
        )
    )

    async def get_token():
        return "fake-token"

    async def on_message(_msg):
        pass

    provider = UpstoxV3Provider(get_token=get_token, on_message=on_message)
    url = await provider._authorize()  # noqa: SLF001 — testing the internal auth call directly

    assert url == "wss://example.upstox.com/feed?code=abc"


async def test_authorize_raises_without_a_token():
    async def get_token():
        return None

    async def on_message(_msg):
        pass

    provider = UpstoxV3Provider(get_token=get_token, on_message=on_message)
    with pytest.raises(RuntimeError, match="no Upstox bearer token"):
        await provider._authorize()  # noqa: SLF001


async def test_subscription_truncated_at_mode_cap():
    async def get_token():
        return "fake-token"

    async def on_message(_msg):
        pass

    provider = UpstoxV3Provider(
        get_token=get_token, on_message=on_message, max_subscription_keys=3
    )
    # Test the truncation logic directly rather than through start(), which
    # would spawn a background task making real network calls in a unit test.
    capped = provider._apply_subscription_cap([f"NSE_EQ|{i}" for i in range(10)])  # noqa: SLF001

    assert len(capped) == 3
    assert capped == ["NSE_EQ|0", "NSE_EQ|1", "NSE_EQ|2"]
