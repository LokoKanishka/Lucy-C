#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -V

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[install] Missing ffmpeg. Install: sudo apt-get update && sudo apt-get install -y ffmpeg" >&2
  exit 1
fi

if ! command -v ollama >/dev/null 2>&1; then
  echo "[install] Missing ollama. Install from https://ollama.com" >&2
  exit 1
fi

# venv
VENV="$ROOT/.venv"
if [[ ! -x "$VENV/bin/python" ]]; then
  echo "[install] Creating venv: $VENV"
  python3 -m venv "$VENV"
fi

"$VENV/bin/python" -m pip install --upgrade pip wheel
"$VENV/bin/python" -m pip install -r requirements.txt

if ! command -v mimic3 >/dev/null 2>&1; then
  echo "[install] WARNING: mimic3 CLI not found. Install (one option):" >&2
  echo "  $VENV/bin/python -m pip install mycroft-mimic3-tts" >&2
  echo "Then ensure 'mimic3' is on PATH (or activate venv)." >&2
fi

echo "[install] Done. Next: ./scripts/run_web_ui.sh"
