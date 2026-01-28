#!/usr/bin/env bash
set -euo pipefail

NAME="Lucy-C Voice"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

TARGET1="$HOME/Escritorio/Lucy-C-Voice.desktop"
TARGET2="$HOME/Desktop/Lucy-C-Voice.desktop"

CONTENT="[Desktop Entry]
Type=Application
Name=${NAME}
Comment=Interfaz local push-to-talk para hablar con Lucy-C
Terminal=true
Exec=bash -lc 'cd \"${ROOT}\" && ./scripts/run_web_ui.sh'
Icon=utilities-terminal
Categories=Utility;
"

echo "$CONTENT" > "$TARGET1"
chmod +x "$TARGET1"

# If Desktop exists, copy there too
if [[ -d "$HOME/Desktop" ]]; then
  echo "$CONTENT" > "$TARGET2"
  chmod +x "$TARGET2"
fi

echo "[shortcut] Created: $TARGET1"
[[ -f "$TARGET2" ]] && echo "[shortcut] Created: $TARGET2" || true
