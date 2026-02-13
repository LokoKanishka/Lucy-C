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
# Ensure venv executables (e.g., mimic3) and npm globals (e.g., clawdbot) are on PATH
export PATH="$VENV/bin:$HOME/.npm-global/bin:$PATH"

# CUDA runtime fallback: Ollama ships CUDA 12 libs here.
# If system CUDA runtime isn't installed, this makes libcublas.so.12 visible.
if [[ -d "/usr/local/lib/ollama/cuda_v12" ]]; then
  export LD_LIBRARY_PATH="/usr/local/lib/ollama/cuda_v12${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

# If Clawdbot Gateway token isn't set, try to read it locally.
# This enables switching LLM provider to "lucy (Clawdbot)" without manual env setup.
if [[ -z "${CLAWDBOT_GATEWAY_TOKEN:-}" && -f "$HOME/.clawdbot/clawdbot.json" ]]; then
  CLAWDBOT_GATEWAY_TOKEN="$($PY - <<'PY'
import json, os
p=os.path.expanduser('~/.clawdbot/clawdbot.json')
try:
  data=json.load(open(p,'r',encoding='utf-8'))
  print((data.get('gateway',{}) or {}).get('auth',{}).get('token','') or '')
except Exception:
  print('')
PY
)"
  export CLAWDBOT_GATEWAY_TOKEN
fi

# Port selection
BASE_PORT="${PORT:-5050}"
PORT_CHOSEN="$BASE_PORT"

is_port_free() {
  local port="$1"
  # If something is listening, this returns success => NOT free.
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$port" -sTCP:LISTEN -nP >/dev/null 2>&1 && return 1 || return 0
  fi
  # Fallback using bash /dev/tcp (best effort)
  (echo >"/dev/tcp/127.0.0.1/$port") >/dev/null 2>&1 && return 1 || return 0
}

for i in $(seq 0 20); do
  try_port=$((BASE_PORT + i))
  if is_port_free "$try_port"; then
    PORT_CHOSEN="$try_port"
    break
  fi
done

export PORT="$PORT_CHOSEN"

if [[ "$PORT_CHOSEN" != "$BASE_PORT" ]]; then
  echo "[run_web_ui] Port $BASE_PORT is busy. Using $PORT_CHOSEN instead." >&2
fi

echo "[run_web_ui] Starting Lucy-C Web UI: http://127.0.0.1:${PORT_CHOSEN}"
exec "$PY" -m lucy_c.web.app
