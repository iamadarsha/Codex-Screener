#!/usr/bin/env bash
# Build the BreakoutScan API image using Apple's `container` CLI.
# See docs/APPLE_CONTAINER.md for prerequisites.

set -euo pipefail

IMAGE_TAG="${IMAGE_TAG:-breakoutscan-api:local}"
CONTEXT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../apps/api" && pwd)"

echo "Building ${IMAGE_TAG} from ${CONTEXT_DIR} ..."
container build -t "${IMAGE_TAG}" "${CONTEXT_DIR}"

echo "Done. Run it with: scripts/container-run.sh"
