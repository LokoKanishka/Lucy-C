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

# Mimic3 CLI (TTS)
if ! command -v mimic3 >/dev/null 2>&1; then
  echo "[install] mimic3 CLI not found. Installing into venv..." >&2
  "$VENV/bin/python" -m pip install mycroft-mimic3-tts
  echo "[install] NOTE: run Lucy-C using ./scripts/run_web_ui.sh (it uses the venv)," >&2
  echo "so mimic3 should be available without touching your system PATH." >&2
fi

# GPU hint
if command -v nvidia-smi >/dev/null 2>&1; then
  echo "[install] NVIDIA GPU detected. Recommended ASR settings:" >&2
  echo "  asr.device: cuda" >&2
  echo "  asr.compute_type: float16" >&2
fi

echo "[install] Done. Next: ./scripts/run_web_ui.sh"
