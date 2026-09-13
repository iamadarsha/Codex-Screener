# Security Remediation — Credential Exposure Incident

## What happened

Real production credentials were committed to git in plaintext across two
separate incidents, in a repository (`github.com/iamadarsha/Codex-Screener`)
that has been **public** the whole time:

1. **`apps/api/deploy_fly.sh`** (added in a prior session, commit originally
   `c4c3a79`): hardcoded `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`,
   `UPSTOX_API_KEY`, `UPSTOX_API_SECRET`.
2. **`PROJECT_HANDOFF.md`** (tracked since an earlier commit, `3537d64`): the
   above four values plus the **full Supabase database password** (in a
   plaintext connection string) and **`INDIAN_API_KEY`** and
   **`GEMINI_API_KEY`** — six additional/overlapping secrets not caught by
   the first pass over `deploy_fly.sh` alone.

A sibling file, `PROJECT_HANDOFF_HIDDEN_KEYS.md`, existed with the same
content but real values replaced by `***HIDDEN***` placeholders — that file
was safe; the confusing part is that its name suggests the opposite of what
it actually is.

## What was done (this session)

- Installed `git-filter-repo` and rewrote **all local branches**
  (`main`, `claude/debug-production-website-GdI1R`,
  `docs/agent-handover-package`, `feature/full-build`) to replace every
  occurrence of the 7 exposed literal values across the **entire git
  history** (99 commits) with `***REMOVED-<NAME>***` placeholders.
- Force-pushed the rewritten history to `origin` for all branches that
  changed (`feature/full-build`'s content had no matches, so its hash was
  unchanged and nothing needed pushing).
- Verified with `git log --all -p | grep` that none of the 7 original values
  remain anywhere in the rewritten history.
- Deleted the plaintext `PROJECT_HANDOFF.md` and promoted the already-safe
  `PROJECT_HANDOFF_HIDDEN_KEYS.md` in its place (single doc going forward,
  no more confusing duplicate).
- Rewrote `apps/api/deploy_fly.sh` so it **never hardcodes any secret** —
  every value (including the four that were previously hardcoded) is now
  read via an interactive `read -rsp` prompt at runtime.

## What was explicitly NOT done

**None of the exposed credentials were rotated**, per an explicit decision
made when this remediation was scoped: "do not rotate existing keys, just
hide them from public." The repository also **remains public**.

## Why "hidden" is not the same as "safe" — read this before assuming the incident is closed

Scrubbing git history only controls what a *future* visitor to the repo can
see. It does **not** undo exposure that already happened. Specifically:

- The repository has been public with these values live in it across
  multiple commits, for an unknown but non-trivial period of time.
- Automated secret scanners (GitHub's own, and many third-party ones like
  GitGuardian/TruffleHog, plus opportunistic scrapers) actively and
  continuously crawl public GitHub repositories specifically for patterns
  like `AIzaSy...` (Google API keys) and `eyJhbGci...` (JWTs) — these are
  some of the most commonly-targeted patterns in existence. There is no way
  to confirm or rule out that these specific values were already harvested.
- Anyone who already forked, cloned, or otherwise copied the repository
  before this session's history rewrite retains the original, unscrubbed
  history with all values intact — a history rewrite on `origin` does not
  reach those copies.
- The Supabase **service role key** bypasses Row Level Security entirely; if
  it was captured, RLS policies provide no protection against it.
- The **database password**, if captured, grants direct Postgres access
  independent of any application-level auth.

**The only way to be certain these six credentials cannot be misused is to
rotate them.** This remains true regardless of the history scrub above. This
document records that rotation was explicitly declined for now — if that
decision changes, rotate via:

| Credential | Where to rotate |
|---|---|
| `UPSTOX_API_KEY` / `UPSTOX_API_SECRET` | Upstox Developer App page |
| `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_KEY` | Supabase Dashboard → Settings → API |
| Supabase DB password | Supabase Dashboard → Settings → Database |
| `INDIAN_API_KEY` | stock.indianapi.in dashboard |
| `GEMINI_API_KEY` | Google AI Studio (delete + recreate) |

## Prevention going forward

Recommended, not yet implemented (Phase 1 follow-up):
- A `gitleaks` pre-commit hook and a CI check (`gitleaks detect`) so a real
  secret can't be committed again without an explicit override.
- Treat `PROJECT_HANDOFF*.md`-style "everything about the project" docs as
  inherently risky — prefer linking to where a credential lives (1Password,
  the provider's dashboard) over ever writing the literal value into a
  markdown file, redacted or not.
