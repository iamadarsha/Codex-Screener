#!/usr/bin/env python3
"""Fails CI when a stale production host or a dangerous default connection
string shows up in tracked source, or in a built frontend bundle.

Catches exactly the two classes of bug that have already taken production
down once each: a committed env file baking a dead host into a build, and
an unguarded `localhost` database default silently used in production.

Usage: python3 scripts/check-config-hygiene.py
Exit code 0 = clean, 1 = violations found (see stdout for file:line).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Hosts from prior hosting migrations (Railway -> Fly.io -> Oracle VM) that
# must never appear in current source or a built bundle again.
STALE_HOSTS = [
    "breakoutscan-api.fly.dev",
    "breakoutscan-api-production.up.railway.app",
    "breakoutscan-web.up.railway.app",
]

# Connection strings that are safe as an explicit, guarded *development*
# default, but must never be reachable in a production code path.
DANGEROUS_DEFAULTS = [
    "localhost:5432",
    "127.0.0.1:5432",
]

# (relative-file-path, substring) pairs that are known, intentional, and
# reviewed — e.g. the guarded dev-only default itself, or a doc explaining
# a past incident. Add here explicitly rather than loosening the patterns
# above or excluding whole directories.
ALLOWLIST: set[tuple[str, str]] = {
    ("apps/api/app/core/config.py", "localhost:5432"),
    ("apps/api/app/tests/test_config.py", "localhost:5432"),
    ("apps/api/app/tests/test_config.py", "127.0.0.1:5432"),
    (".env.example", "localhost:5432"),  # template file, documents the same guarded dev default
}

# File extensions worth scanning as "source" — deliberately excludes
# .md/.txt so historical incident write-ups (docs/, SECURITY_REMEDIATION.md)
# don't trip this check; those are narrative record, not live config.
SOURCE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".json", ".yml", ".yaml", ".toml", ".sh", ".env", ".txt",
}
# .txt is included above only for requirements*.txt-style files; docs/*.txt
# would be an unusual choice for this repo and can be allowlisted if it ever appears.

EXCLUDE_DIR_PARTS = {
    "node_modules", ".git", ".next", "dist", "build", "__pycache__",
    ".venv", ".venv-phase3", "coverage", ".pytest_cache", ".claude-flow",
}


def _tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return [REPO_ROOT / line for line in out.stdout.splitlines() if line.strip()]


def _is_scannable(path: Path) -> bool:
    # This script's own source necessarily contains the literal patterns
    # it searches for (as list definitions) — scanning itself would always
    # self-flag, so it's excluded rather than allowlisted line-by-line.
    if path.resolve() == Path(__file__).resolve():
        return False
    # Path.suffix on ".env.production" is ".production", not ".env" — match
    # dotfile env variants (.env, .env.production, .env.local, ...) by name
    # prefix explicitly rather than relying on suffix parsing.
    is_env_file = path.name.startswith(".env")
    if not is_env_file and path.suffix not in SOURCE_EXTENSIONS:
        return False
    if any(part in EXCLUDE_DIR_PARTS for part in path.parts):
        return False
    return path.is_file()


def _scan(patterns: list[str], files: list[Path]) -> list[str]:
    violations: list[str] = []
    for path in files:
        if not _is_scannable(path):
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in patterns:
                if pattern in line and (rel, pattern) not in ALLOWLIST:
                    violations.append(f"{rel}:{lineno}: contains {pattern!r}")
    return violations


def _scan_frontend_build() -> list[str]:
    """Best-effort check of a built frontend bundle, if one exists locally.

    Not run in CI (no build artifact there unless the build step precedes
    this check in the same job) — this is a local/pre-deploy safety net.
    """
    build_dir = REPO_ROOT / "apps" / "web" / ".next"
    if not build_dir.exists():
        return []
    violations: list[str] = []
    for path in build_dir.rglob("*.js"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in STALE_HOSTS:
            if pattern in text:
                violations.append(
                    f"{path.relative_to(REPO_ROOT).as_posix()}: built bundle contains {pattern!r}"
                )
    return violations


def main() -> int:
    files = _tracked_files()
    violations = _scan(STALE_HOSTS, files)
    violations += _scan(DANGEROUS_DEFAULTS, files)
    violations += _scan_frontend_build()

    if violations:
        print("Config hygiene check FAILED:\n")
        for v in violations:
            print(f"  - {v}")
        print(
            "\nIf a match is a reviewed, intentional exception (e.g. a guarded "
            "dev-only default), add it to ALLOWLIST in this script with a comment "
            "explaining why — do not loosen the patterns or exclude whole directories."
        )
        return 1

    print("Config hygiene check passed — no stale hosts or dangerous defaults found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
