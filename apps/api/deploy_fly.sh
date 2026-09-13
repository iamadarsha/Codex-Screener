#!/usr/bin/env bash
# BreakoutScan — Fly.io deploy script
#
# DEPRECATED / REFERENCE ONLY: Fly.io removed its always-on free tier for new
# accounts in Oct 2024 (new orgs are pay-as-you-go, ~$2-5/mo minimum for an
# always-on machine). The project's target backend host is now Oracle Cloud
# Always Free ARM — see docs/APPLE_CONTAINER.md and docs/DATA_PROVIDER_MATRIX.md.
# This script is kept only in case Fly.io's small paid tier is ever used.
#
# Run this AFTER: flyctl auth login
# Usage: bash deploy_fly.sh
#
# No secret is ever hardcoded in this file — every value below is either
# prompted for interactively or read from your own shell environment.

set -euo pipefail

APP_NAME="breakoutscan-api"
REGION="sin"  # Singapore — closest free region to India

echo "=== BreakoutScan Fly.io Deploy ==="
echo ""

# ── Check login ──────────────────────────────────────────────────────────────
if ! flyctl auth whoami &>/dev/null; then
  echo "❌ Not logged in. Run: flyctl auth login"
  exit 1
fi
echo "✅ Logged in as: $(flyctl auth whoami)"
echo ""

# ── Collect all secrets interactively — none are ever hardcoded here ─────────
echo "Enter the following values (input is hidden):"
echo ""

read -rsp "1. REDIS_URL (from Redis Cloud — e.g. redis://default:PASS@HOST:PORT): " REDIS_URL
echo ""

read -rsp "2. GEMINI_API_KEY (from aistudio.google.com): " GEMINI_API_KEY
echo ""

read -rsp "3. INDIAN_API_KEY (from indianapi.in dashboard): " INDIAN_API_KEY
echo ""

read -rsp "4. SUPABASE DB PASSWORD (from supabase.com → Settings → Database): " SUPABASE_DB_PASS
echo ""

read -rsp "5. SUPABASE_ANON_KEY (from supabase.com → Settings → API): " SUPABASE_ANON_KEY
echo ""

read -rsp "6. SUPABASE_SERVICE_KEY (from supabase.com → Settings → API): " SUPABASE_SERVICE_KEY
echo ""

read -rsp "7. UPSTOX_API_KEY (from Upstox Developer App): " UPSTOX_API_KEY
echo ""

read -rsp "8. UPSTOX_API_SECRET (from Upstox Developer App): " UPSTOX_API_SECRET
echo ""

read -rp "9. SUPABASE_URL (e.g. https://xxxx.supabase.co): " SUPABASE_URL
echo ""

read -rp "10. Supabase project ref (the xxxx in the URL above, used for the DB host): " SUPABASE_PROJECT_REF
echo ""

DATABASE_URL="postgresql+asyncpg://postgres:${SUPABASE_DB_PASS}@db.${SUPABASE_PROJECT_REF}.supabase.co:5432/postgres"

# ── Create app if it doesn't exist ───────────────────────────────────────────
if ! flyctl apps list 2>/dev/null | grep -q "^${APP_NAME}"; then
  echo "Creating Fly app: ${APP_NAME}..."
  flyctl apps create "${APP_NAME}" --machines
fi

# ── Set all secrets ──────────────────────────────────────────────────────────
echo "Setting secrets..."
flyctl secrets set \
  REDIS_URL="${REDIS_URL}" \
  GEMINI_API_KEY="${GEMINI_API_KEY}" \
  INDIAN_API_KEY="${INDIAN_API_KEY}" \
  DATABASE_URL="${DATABASE_URL}" \
  SUPABASE_URL="${SUPABASE_URL}" \
  SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY}" \
  SUPABASE_SERVICE_KEY="${SUPABASE_SERVICE_KEY}" \
  UPSTOX_API_KEY="${UPSTOX_API_KEY}" \
  UPSTOX_API_SECRET="${UPSTOX_API_SECRET}" \
  UPSTOX_REDIRECT_URI="https://breakoutscan-api.fly.dev/auth/upstox/callback" \
  CORS_ALLOWED_ORIGINS="https://breakoutscan-web.vercel.app,https://breakoutscan.in,https://www.breakoutscan.in" \
  ENVIRONMENT="production" \
  DEBUG="false" \
  --app "${APP_NAME}"

echo "✅ Secrets set"
echo ""

# ── Deploy ────────────────────────────────────────────────────────────────────
echo "Deploying (this takes ~3-5 min on first run)..."
flyctl deploy --app "${APP_NAME}" --remote-only

echo ""
echo "=== Deploy complete! ==="
echo "Backend: https://${APP_NAME}.fly.dev"
echo "Health:  https://${APP_NAME}.fly.dev/health"
echo "Frontend: https://breakoutscan-web.vercel.app"
echo ""
echo "Run 'flyctl logs --app ${APP_NAME}' to watch live logs."
