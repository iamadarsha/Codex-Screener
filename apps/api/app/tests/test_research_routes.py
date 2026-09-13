"""Route-level safety: path-traversal `run_id` rejection, missing-run 404s,
and graceful handling of a corrupted manifest on disk.

Note on path-traversal test design: a run_id containing an actual `../`
dot-segment gets collapsed away by RFC 3986 URL normalization before it
even reaches route matching (httpx/Starlette do this the same way a
browser or reverse proxy would), so a request built from
`f"/api/research/runs/{'../../etc/passwd'}"` never actually delivers a
literal `..` to our handler — it 404s for an unrelated reason (wrong
route). That's a real, useful defense layer, but it isn't OUR code being
exercised. So this file tests two things separately: (1) `resolve_run_dir`
directly, at the unit level, with real `..`/`/` payloads — proving our own
validation rejects them regardless of any URL-layer help; and (2) the
route with a malicious-looking but *single-path-segment* run_id (contains
`..` as a substring, or invalid characters) that DOES survive normalization
and reach the handler unmodified, proving `_validate_run_id_or_400`
actually fires in that case rather than falling through to a 500.
"""

from __future__ import annotations

import json

import pytest

from app.research.artifacts import resolve_run_dir


# ---------------------------------------------------------------------------
# Unit-level: resolve_run_dir itself, unaffected by any URL normalization
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_run_id",
    [
        "../../etc/passwd",
        "../secret",
        "..",
        "a/b",
        "",
        "a" * 200,
    ],
)
def test_resolve_run_dir_rejects_traversal_and_malformed_ids(research_runs_root, bad_run_id):
    with pytest.raises(ValueError):
        resolve_run_dir(bad_run_id)


def test_resolve_run_dir_accepts_a_well_formed_id(research_runs_root):
    run_dir = resolve_run_dir("20260101_000000_abcdef12")
    assert run_dir.is_relative_to(research_runs_root.resolve())


# ---------------------------------------------------------------------------
# Route-level: a malicious-looking but single-segment run_id that survives
# URL normalization and actually reaches our handler
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_run_id", ["..hidden", "bad;id", "bad id", "a" * 200])
async def test_route_rejects_malformed_run_id_with_4xx_not_500(
    api_client, research_runs_root, bad_run_id
):
    resp = await api_client.get(f"/api/research/runs/{bad_run_id}")
    assert 400 <= resp.status_code < 500


async def test_route_rejects_malformed_run_id_on_evidence_endpoint(api_client, research_runs_root):
    resp = await api_client.get("/api/research/runs/..hidden/evidence")
    assert 400 <= resp.status_code < 500


async def test_route_rejects_malformed_run_id_on_results_endpoint(api_client, research_runs_root):
    resp = await api_client.get("/api/research/runs/..hidden/results")
    assert 400 <= resp.status_code < 500


# ---------------------------------------------------------------------------
# Missing-run 404s
# ---------------------------------------------------------------------------


async def test_nonexistent_run_returns_404(api_client, research_runs_root):
    resp = await api_client.get("/api/research/runs/20260101_000000_deadbeef")
    assert resp.status_code == 404


async def test_nonexistent_run_evidence_returns_404(api_client, research_runs_root):
    resp = await api_client.get("/api/research/runs/20260101_000000_deadbeef/evidence")
    assert resp.status_code == 404


async def test_nonexistent_run_results_returns_404(api_client, research_runs_root):
    resp = await api_client.get("/api/research/runs/20260101_000000_deadbeef/results")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Corrupted-manifest handling
# ---------------------------------------------------------------------------


async def test_manifest_failing_schema_validation_does_not_crash_the_route(
    api_client, research_runs_root
):
    run_id = "20260101_000000_badmanifest"
    run_dir = resolve_run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    # Valid JSON, but missing every field RunManifest requires.
    (run_dir / "manifest.json").write_text(json.dumps({"not": "a valid manifest"}))

    resp = await api_client.get(f"/api/research/runs/{run_id}")
    assert resp.status_code == 500
    assert "detail" in resp.json()


async def test_malformed_json_manifest_does_not_crash_the_route(api_client, research_runs_root):
    run_id = "20260101_000000_badjson"
    run_dir = resolve_run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text("{not valid json::")

    resp = await api_client.get(f"/api/research/runs/{run_id}")
    assert resp.status_code == 500
    assert "detail" in resp.json()


# ---------------------------------------------------------------------------
# Results route: invalid evidence must never be presented as trustworthy
# ---------------------------------------------------------------------------


async def test_results_route_flags_invalid_evidence_clearly(api_client, research_runs_root):
    from app.research.store import ResearchRunStore

    store = ResearchRunStore()
    run_id = "20260101_000000_invalidev"
    run_dir = resolve_run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    store.write_evidence(run_id, {"status": "invalid", "errors": ["future data detected"]})
    store.write_results(run_id, {"status": "FAILED", "signals": []})

    resp = await api_client.get(f"/api/research/runs/{run_id}/results")
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is False
    assert "Historical replay unavailable" in body["message"]
