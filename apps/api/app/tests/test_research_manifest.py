"""`RunManifest` construction, `code_version` git-fallback behavior, and
`ResearchRunStore`'s atomic-write correctness."""

from __future__ import annotations

import subprocess
from datetime import datetime

import pytest

from app.research.artifacts import read_json, resolve_run_dir
from app.research.run_manifest import RunManifest, get_code_version
from app.research.run_state import RunStatus
from app.research.store import ResearchRunStore
from app.utils.time import IST


def _ts(hour=9, minute=15) -> datetime:
    return datetime(2026, 9, 10, hour, minute, tzinfo=IST)


def test_run_manifest_constructs_with_expected_defaults():
    manifest = RunManifest(
        run_id="20260910_091500_abcd1234",
        created_at=_ts(),
        as_of=_ts(9, 10),
        universe="nifty50",
        scan_hash="deadbeefcafef00d",
        timeframe="1d",
    )
    assert manifest.run_type == "scan_replay"
    assert manifest.timezone == "Asia/Kolkata"
    assert manifest.status == RunStatus.CREATED
    assert manifest.data_source == ["stored_1m"]
    assert isinstance(manifest.code_version, str) and manifest.code_version


def test_get_code_version_returns_git_sha_when_available():
    sha = get_code_version()
    # Either a real 40-char hex SHA (this repo IS a git repo) or the
    # documented fallback — never an exception, never empty.
    assert sha == "unknown" or (len(sha) >= 7 and all(c in "0123456789abcdef" for c in sha))


def test_get_code_version_falls_back_when_git_binary_missing(monkeypatch):
    def _raise(*args, **kwargs):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(subprocess, "run", _raise)
    assert get_code_version() == "unknown"


def test_get_code_version_falls_back_when_git_command_fails(monkeypatch):
    class _FakeCompletedProcess:
        returncode = 128
        stdout = ""

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeCompletedProcess())
    assert get_code_version() == "unknown"


def test_get_code_version_falls_back_on_timeout(monkeypatch):
    def _raise(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="git", timeout=5)

    monkeypatch.setattr(subprocess, "run", _raise)
    assert get_code_version() == "unknown"


# ---------------------------------------------------------------------------
# ResearchRunStore / atomic write correctness
# ---------------------------------------------------------------------------


def test_create_run_writes_manifest_request_and_state(research_runs_root):
    store = ResearchRunStore()
    manifest = store.create_run(
        scan_definition={"conditions": [{"indicator": "rsi_14", "operator": "lt", "value": 30}]},
        universe="nifty50",
        as_of=_ts(),
        timeframe="1d",
    )

    run_dir = resolve_run_dir(manifest.run_id)
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "request.json").exists()
    assert (run_dir / "state.json").exists()
    # No leftover .tmp file after a successful atomic write.
    assert not (run_dir / "manifest.json.tmp").exists()

    read_back = store.read_manifest(manifest.run_id)
    assert read_back == manifest

    state = store.read_state(manifest.run_id)
    assert state["status"] == RunStatus.CREATED.value


def test_update_state_overwrites_state_json(research_runs_root):
    store = ResearchRunStore()
    manifest = store.create_run(
        scan_definition={"pattern": "bullish_engulfing"},
        universe="nifty50",
        as_of=_ts(),
        timeframe="1d",
    )

    store.update_state(manifest.run_id, RunStatus.RUNNING)
    assert store.read_state(manifest.run_id)["status"] == RunStatus.RUNNING.value

    store.update_state(manifest.run_id, RunStatus.SUCCEEDED, extra={"signals": 3})
    final_state = store.read_state(manifest.run_id)
    assert final_state["status"] == RunStatus.SUCCEEDED.value
    assert final_state["signals"] == 3


def test_write_and_read_evidence_and_results_round_trip(research_runs_root):
    store = ResearchRunStore()
    manifest = store.create_run(
        scan_definition={"pattern": "hammer"},
        universe="nifty50",
        as_of=_ts(),
        timeframe="1d",
    )

    evidence = {"status": "valid", "checks": {"future_bar_check": True}}
    results = {"status": "SUCCEEDED", "signals": []}

    store.write_evidence(manifest.run_id, evidence)
    store.write_results(manifest.run_id, results)

    assert store.read_evidence(manifest.run_id) == evidence
    assert store.read_results(manifest.run_id) == results


def test_read_manifest_returns_none_for_unknown_run(research_runs_root):
    store = ResearchRunStore()
    assert store.read_manifest("20260910_000000_deadbeef") is None
    assert store.read_state("20260910_000000_deadbeef") is None
    assert store.read_evidence("20260910_000000_deadbeef") is None
    assert store.read_results("20260910_000000_deadbeef") is None


def test_read_json_returns_none_for_nonexistent_path(tmp_path):
    assert read_json(tmp_path / "does_not_exist.json") is None


def test_atomic_write_json_produces_correct_readable_file(tmp_path):
    from app.research.artifacts import atomic_write_json

    target = tmp_path / "nested" / "artifact.json"
    payload = {"a": 1, "b": [1, 2, 3], "c": None}

    atomic_write_json(target, payload)

    assert target.exists()
    assert not target.with_suffix(target.suffix + ".tmp").exists()
    assert read_json(target) == payload

    # A second write cleanly replaces the first (no leftover stale tmp file).
    atomic_write_json(target, {"a": 2})
    assert read_json(target) == {"a": 2}
    assert not target.with_suffix(target.suffix + ".tmp").exists()
