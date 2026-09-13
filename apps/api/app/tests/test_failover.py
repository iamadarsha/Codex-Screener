"""Failover state machine transitions — fully testable without a live
Upstox connection (Phase 2.1 acceptance gate)."""

from __future__ import annotations

from app.market.failover import FailoverConfig, FailoverController, FeedStatus

CONFIG = FailoverConfig(
    degraded_after_seconds=10.0,
    fallback_after_seconds=30.0,
    recovery_confirm_seconds=5.0,
)


def test_starts_primary_live_with_no_ticks_yet():
    fc = FailoverController(CONFIG)
    assert fc.status == FeedStatus.PRIMARY_LIVE
    # No primary tick has ever arrived — this is a fresh start, not staleness.
    assert fc.evaluate(now=100.0) == FeedStatus.PRIMARY_LIVE


def test_transitions_to_degraded_then_fallback_on_silence():
    fc = FailoverController(CONFIG)
    fc.record_primary_tick(now=0.0)

    assert fc.evaluate(now=5.0) == FeedStatus.PRIMARY_LIVE
    assert fc.evaluate(now=15.0) == FeedStatus.DEGRADED
    assert fc.evaluate(now=35.0) == FeedStatus.FALLBACK


def test_should_run_fallback_poller_only_when_degraded_or_fallback():
    fc = FailoverController(CONFIG)
    fc.record_primary_tick(now=0.0)

    fc.evaluate(now=5.0)
    assert fc.should_run_fallback_poller() is False

    fc.evaluate(now=15.0)
    assert fc.should_run_fallback_poller() is True

    fc.evaluate(now=35.0)
    assert fc.should_run_fallback_poller() is True


def test_recovers_after_confirm_window_once_ticks_resume():
    fc = FailoverController(CONFIG)
    fc.record_primary_tick(now=0.0)
    fc.evaluate(now=35.0)
    assert fc.status == FeedStatus.FALLBACK

    # A tick arrives again — enters RECOVERING, not immediately PRIMARY_LIVE.
    fc.record_primary_tick(now=40.0)
    assert fc.status == FeedStatus.RECOVERING
    assert fc.should_run_fallback_poller() is False

    # Not yet past the recovery confirmation window.
    assert fc.evaluate(now=42.0) == FeedStatus.RECOVERING

    # Past the confirmation window — back to primary.
    assert fc.evaluate(now=46.0) == FeedStatus.PRIMARY_LIVE


def test_recovering_resets_if_silence_resumes_before_confirmed():
    fc = FailoverController(CONFIG)
    fc.record_primary_tick(now=0.0)
    fc.evaluate(now=35.0)  # FALLBACK
    fc.record_primary_tick(now=40.0)  # RECOVERING
    # Another tick a moment later shouldn't move the recovery timer forward.
    fc.record_primary_tick(now=42.0)
    assert fc.evaluate(now=44.0) == FeedStatus.RECOVERING
    assert fc.evaluate(now=46.0) == FeedStatus.PRIMARY_LIVE
