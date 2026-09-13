#!/usr/bin/env bash
# Compile the Upstox V3 MarketDataFeed protobuf schema into a Python module.
#
# Run this whenever apps/api/app/market/proto/MarketDataFeed.proto changes
# (e.g. Upstox revises the schema — re-download it from
# https://assets.upstox.com/feed/market-data-feed/v3/MarketDataFeed.proto
# first). Requires grpcio-tools (apps/api/requirements-dev.txt).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROTO_DIR="${REPO_ROOT}/apps/api/app/market/proto"
OUT_DIR="${REPO_ROOT}/apps/api/app/market"

python -m grpc_tools.protoc \
  -I "${PROTO_DIR}" \
  --python_out="${OUT_DIR}" \
  "${PROTO_DIR}/MarketDataFeed.proto"

echo "Generated ${OUT_DIR}/MarketDataFeed_pb2.py"
