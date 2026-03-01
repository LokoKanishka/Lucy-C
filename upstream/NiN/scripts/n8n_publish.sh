#!/usr/bin/env bash
#
# n8n_publish.sh — Publica un workflow JSON en n8n via docker exec + Node.js
#
# Uso:  bash scripts/n8n_publish.sh workflows/mi_workflow.json
#
# Requiere:
#   - Docker corriendo con container "n8n-lucy"
#   - Archivo .env con N8N_API_KEY en la raíz del repo
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$REPO_DIR/.env"

# --- Validaciones ---
if [[ $# -ne 1 ]]; then
  echo "❌ Uso: $0 <ruta_al_workflow.json>"
  exit 1
fi

WF_FILE="$1"
if [[ ! -f "$WF_FILE" ]]; then
  echo "❌ No existe el archivo: $WF_FILE"
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ No existe .env en $REPO_DIR"
  exit 1
fi

# Leer API key del .env
API_KEY=$(grep -oP 'N8N_API_KEY=\K.*' "$ENV_FILE" | tr -d '[:space:]')
if [[ -z "$API_KEY" ]]; then
  echo "❌ N8N_API_KEY no encontrada en .env"
  exit 1
fi

# Verificar que el container existe
if ! docker ps --format '{{.Names}}' | grep -q '^n8n-lucy$'; then
  echo "❌ Container n8n-lucy no está corriendo"
  exit 1
fi

# --- Leer el JSON ---
WF_JSON=$(cat "$WF_FILE")
WF_NAME=$(echo "$WF_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('name','Sin nombre'))")

echo "🔧 Publicando workflow: $WF_NAME"
echo "📄 Desde: $WF_FILE"

# --- Escapar JSON para inline en node -e ---
ESCAPED_JSON=$(echo "$WF_JSON" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))")

# --- Publicar via docker exec + Node.js ---
RESULT=$(docker exec n8n-lucy node -e "
const http = require('http');
const data = $ESCAPED_JSON;
const opts = {
  hostname: 'localhost', port: 5678, path: '/api/v1/workflows', method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-N8N-API-KEY': '$API_KEY',
    'Content-Length': Buffer.byteLength(data)
  }
};
const req = http.request(opts, (res) => {
  let body = '';
  res.on('data', (c) => body += c);
  res.on('end', () => {
    if (res.statusCode >= 200 && res.statusCode < 300) {
      const parsed = JSON.parse(body);
      console.log(JSON.stringify({status: 'ok', id: parsed.id, name: parsed.name}));
    } else {
      console.log(JSON.stringify({status: 'error', code: res.statusCode, body: body.substring(0,200)}));
    }
  });
});
req.on('error', (e) => console.log(JSON.stringify({status: 'error', message: e.message})));
req.write(data);
req.end();
")

# --- Parsear resultado ---
STATUS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")

if [[ "$STATUS" == "ok" ]]; then
  WF_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id','?'))")
  echo "✅ Workflow publicado con éxito!"
  echo "   ID: $WF_ID"
  echo "   Nombre: $WF_NAME"
  echo "   URL: http://localhost:5678/workflow/$WF_ID"
else
  echo "❌ Error al publicar workflow:"
  echo "$RESULT"
  exit 1
fi
