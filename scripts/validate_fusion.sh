#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[1/4] Validando docker-compose.fusion.yml"
ENV_FILE=".env.fusion"
if [[ ! -f "$ENV_FILE" ]]; then
  ENV_FILE=".env.fusion.example"
fi
docker compose --env-file "$ENV_FILE" -f docker-compose.fusion.yml config >/dev/null

echo "[2/4] Validando sintaxis Python"
python3 -m py_compile scripts/build_fusion_workflows.py scripts/upsert_workflows.py scripts/lucy_forge_fusion.py

echo "[3/4] Reconstruyendo workflows fusionados"
python3 scripts/build_fusion_workflows.py

echo "[4/4] Resumen del manifest"
python3 - <<'PY'
import json
from pathlib import Path
manifest = Path("integration/workflows_fusion/manifest.json")
data = json.loads(manifest.read_text(encoding="utf-8"))
print(f"written={data.get('written', 0)} skipped={data.get('skipped', 0)}")
PY

echo "OK: fusion validada."
