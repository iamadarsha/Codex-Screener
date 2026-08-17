#!/usr/bin/env bash
# BreakoutScan — Fly.io deploy script
# Run this AFTER: flyctl auth login
# Usage: bash deploy_fly.sh

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

# ── Collect missing secrets ───────────────────────────────────────────────────
echo "You need 4 values that aren't stored locally."
echo ""

read -rsp "1. REDIS_URL (from Redis Cloud — e.g. redis://default:PASS@HOST:PORT): " REDIS_URL
echo ""

read -rsp "2. GEMINI_API_KEY (from aistudio.google.com): " GEMINI_API_KEY
echo ""

read -rsp "3. INDIAN_API_KEY (from indianapi.in dashboard): " INDIAN_API_KEY
echo ""

read -rsp "4. SUPABASE DB PASSWORD (from supabase.com → Settings → Database): " SUPABASE_DB_PASS
echo ""
echo ""

DATABASE_URL="postgresql+asyncpg://postgres:${SUPABASE_DB_PASS}@db.gruaokvbcnvgvklhqimw.supabase.co:5432/postgres"

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
  SUPABASE_URL="https://gruaokvbcnvgvklhqimw.supabase.co" \
  SUPABASE_ANON_KEY="***REMOVED-SUPABASE-ANON-KEY***" \
  SUPABASE_SERVICE_KEY="***REMOVED-SUPABASE-SERVICE-KEY***" \
  UPSTOX_API_KEY="***REMOVED-UPSTOX-KEY***" \
  UPSTOX_API_SECRET="***REMOVED-UPSTOX-SECRET***" \
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
