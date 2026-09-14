"""Provider logic that's testable without a live Upstox connection
(Phase 2.1 acceptance gate — real connectivity is Milestone 2.2, deferred
until the repo owner has Upstox credentials)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.market.provider import SubscriptionRequest, UpstoxV3Provider


def test_subscription_request_uses_full_wire_name():
    req = SubscriptionRequest(instrument_keys=["NSE_EQ|A", "NSE_EQ|B"])
    payload = json.loads(req.to_json(guid="test-guid"))

    assert payload["method"] == "sub"
    assert payload["guid"] == "test-guid"
    # Verified 2026-09-14 against the live V3 docs and live behavior:
    # "full_d5" is not a valid mode string at all — it silently produced a
    # connection that never received real ticks. "full" (5 depth levels +
    # option greeks) is the correct value.
    assert payload["data"]["mode"] == "full"
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


async def test_subscribe_sends_binary_frame_not_text():
    """Per the V3 docs' "Binary message format" note, the subscription
    request must be a binary frame. Sending it as `str` (a text frame)
    produced a connection that was accepted but never received real ticks
    — discovered via live verification on 2026-09-14."""

    async def get_token():
        return "fake-token"

    async def on_message(_msg):
        pass

    class _FakeWs:
        def __init__(self):
            self.sent = None

        async def send(self, data):
            self.sent = data

    provider = UpstoxV3Provider(
        get_token=get_token, on_message=on_message, max_subscription_keys=10
    )
    provider._subscribed_keys = ["NSE_EQ|A"]  # noqa: SLF001
    fake_ws = _FakeWs()

    await provider._subscribe(fake_ws)  # noqa: SLF001

    assert isinstance(fake_ws.sent, bytes), "subscription payload must be sent as bytes (binary frame), not str"
    payload = json.loads(fake_ws.sent.decode("utf-8"))
    assert payload["data"]["mode"] == "full"
    assert payload["data"]["instrumentKeys"] == ["NSE_EQ|A"]
