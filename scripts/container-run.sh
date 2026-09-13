#!/usr/bin/env bash
# Run the BreakoutScan API container locally via Apple's `container` CLI.
# Reads env vars from apps/api/.env if present (create it from .env.example).

set -euo pipefail

IMAGE_TAG="${IMAGE_TAG:-breakoutscan-api:local}"
CONTAINER_NAME="${CONTAINER_NAME:-breakoutscan-api}"
PORT="${PORT:-8001}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${REPO_ROOT}/apps/api/.env"

ENV_ARGS=()
if [[ -f "${ENV_FILE}" ]]; then
  echo "Loading env from ${ENV_FILE}"
  ENV_ARGS+=(--env-file "${ENV_FILE}")
else
  echo "No apps/api/.env found — running with image defaults only (Redis/DB features will degrade gracefully)."
fi

echo "Starting ${CONTAINER_NAME} from ${IMAGE_TAG} on port ${PORT} ..."
container run \
  --name "${CONTAINER_NAME}" \
  --rm \
  -p "${PORT}:${PORT}" \
  -e "PORT=${PORT}" \
  "${ENV_ARGS[@]}" \
  "${IMAGE_TAG}"
