#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VENV="$ROOT/.venv"
PY="$VENV/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "[run_web_ui] venv missing. Run: ./scripts/install.sh" >&2
  exit 1
fi

export PYTHONPATH="$ROOT"
export LUCY_C_CONFIG="$ROOT/config/config.yaml"

echo "[run_web_ui] Starting Lucy-C Web UI: http://127.0.0.1:5000"
exec "$PY" -m lucy_c.web.app
