#!/usr/bin/env bash
# Smoke-test a running BreakoutScan API container (start it first with
# scripts/container-run.sh in another terminal, or this script will start
# one itself in the background and tear it down after).

set -euo pipefail

IMAGE_TAG="${IMAGE_TAG:-breakoutscan-api:local}"
CONTAINER_NAME="${CONTAINER_NAME:-breakoutscan-api-test}"
PORT="${PORT:-8001}"
STARTED_HERE=0

cleanup() {
  if [[ "${STARTED_HERE}" -eq 1 ]]; then
    echo "Stopping ${CONTAINER_NAME} ..."
    container stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

if ! container ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; then
  echo "Starting ${CONTAINER_NAME} for the test run ..."
  container run --name "${CONTAINER_NAME}" -d -p "${PORT}:${PORT}" -e "PORT=${PORT}" "${IMAGE_TAG}"
  STARTED_HERE=1
  sleep 5
fi

echo "Checking /health ..."
curl -fsS "http://localhost:${PORT}/health" | tee /dev/stderr | grep -q '"status"'

echo ""
echo "OK: container responded on /health"
