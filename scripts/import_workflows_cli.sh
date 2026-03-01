#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SRC_DIR="$ROOT/integration/workflows_fusion"
TMP_DIR="$ROOT/integration/workflows_fusion/.import"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "ERROR: no existe $SRC_DIR" >&2
  exit 1
fi

rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

find "$SRC_DIR" -maxdepth 1 -type f -name '*.json' ! -name 'manifest.json' -print0 | while IFS= read -r -d '' file; do
  cp "$file" "$TMP_DIR/"
done

COUNT="$(find "$TMP_DIR" -maxdepth 1 -type f -name '*.json' | wc -l | tr -d ' ')"
if [[ "$COUNT" == "0" ]]; then
  echo "ERROR: no hay workflows para importar en $TMP_DIR" >&2
  exit 1
fi

echo "Importando $COUNT workflows via CLI en lucy_fusion_n8n..."
docker exec lucy_fusion_n8n n8n import:workflow --separate --input=/data/fusion/workflows/.import

echo "OK: importacion finalizada."
