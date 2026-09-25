#!/usr/bin/env bash
# RecoTrust V5.1 — Lancement production (écoute locale uniquement)
# À placer derrière un reverse-proxy HTTPS (nginx / Traefik / F5).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Chemins persistants (surchargeables)
export RECOTRUST_DATA_DIR="${RECOTRUST_DATA_DIR:-$ROOT/data}"
export RECOTRUST_LOG_DIR="${RECOTRUST_LOG_DIR:-$ROOT/logs}"

mkdir -p "$RECOTRUST_DATA_DIR" "$RECOTRUST_LOG_DIR"

HOST="${RECOTRUST_HOST:-127.0.0.1}"
PORT="${RECOTRUST_PORT:-8501}"

echo "RecoTrust V5.1 — production"
echo "  address : ${HOST}:${PORT}"
echo "  data    : ${RECOTRUST_DATA_DIR}"
echo "  logs    : ${RECOTRUST_LOG_DIR}"
echo "  (Ctrl+C pour arrêter)"

exec streamlit run main.py \
  --server.address "${HOST}" \
  --server.port "${PORT}" \
  --server.headless true \
  --browser.gatherUsageStats false
