#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

load_env_file() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  while IFS='=' read -r key value; do
    [[ -z "${key// }" ]] && continue
    [[ "${key:0:1}" == "#" ]] && continue
    key="$(echo "$key" | xargs)"
    value="${value:-}"
    value="${value%"${value##*[![:space:]]}"}"
    value="${value#"${value%%[![:space:]]*}"}"
    export "${key}=${value}"
  done < "$file"
}

load_env_file "$ROOT/.env.fusion"
load_env_file "$ROOT/.env.fusion.example"

PROFILE="${FUSION_DEP_PROFILE:-full}"
VENV_PATH="${FUSION_VENV_PATH:-$ROOT/.venv}"
INSTALL_MCP="${FUSION_INSTALL_MCP:-true}"
MCP_VENV_PATH="${FUSION_MCP_VENV_PATH:-$ROOT/.venv-mcp}"
INSTALL_NODE="${FUSION_INSTALL_NODE:-true}"
INSTALL_PLAYWRIGHT_BROWSERS="${FUSION_INSTALL_PLAYWRIGHT_BROWSERS:-false}"

echo "Perfil de dependencias: $PROFILE"
echo "Venv: $VENV_PATH"

python3 -m venv "$VENV_PATH"
PY="$VENV_PATH/bin/python"
PIP="$VENV_PATH/bin/pip"

"$PIP" install --upgrade pip setuptools wheel

install_req_file() {
  local req="$1"
  if [[ -f "$req" ]]; then
    echo "Instalando Python deps: $req"
    "$PIP" install -r "$req"
  fi
}

install_req_file "$ROOT/scripts/requirements.txt"
install_req_file "$ROOT/scripts/requirements.nin.txt"

if [[ "$PROFILE" == "full" ]]; then
  install_req_file "$ROOT/upstream/cunningham-Espejo/antigravity/requirements.txt"
  install_req_file "$ROOT/upstream/cunningham-Espejo/apps/lucy_panel/requirements.txt"
  install_req_file "$ROOT/upstream/cunningham-Espejo/scripts/requirements-direct-chat-stt.txt"
fi

if [[ "$INSTALL_MCP" == "true" ]]; then
  echo "Instalando MCP en venv separado: $MCP_VENV_PATH"
  python3 -m venv "$MCP_VENV_PATH"
  MCP_PIP="$MCP_VENV_PATH/bin/pip"
  "$MCP_PIP" install --upgrade pip setuptools wheel
  if ! "$MCP_PIP" install mcp; then
    echo "WARN: no se pudo instalar mcp en venv separado. Continúo sin bloquear." >&2
  fi
fi

if [[ "$INSTALL_NODE" == "true" ]]; then
  if command -v npm >/dev/null 2>&1; then
    echo "Instalando Node deps para upstream/cunningham-Espejo (npm ci)..."
    (cd "$ROOT/upstream/cunningham-Espejo" && npm ci --no-audit --no-fund)

    if [[ "$INSTALL_PLAYWRIGHT_BROWSERS" == "true" ]]; then
      echo "Instalando browsers de Playwright (chromium)..."
      (cd "$ROOT/upstream/cunningham-Espejo" && npx playwright install chromium)
    fi
  else
    echo "WARN: npm no esta disponible; omito deps Node." >&2
  fi
fi

echo "Verificando consistencia de dependencias en venv principal..."
"$PIP" check

echo
echo "OK: dependencias duplicadas en entorno fusionado."
echo "Activar entorno Python:"
echo "  source \"$VENV_PATH/bin/activate\""
if [[ "$INSTALL_MCP" == "true" ]]; then
  echo "Activar entorno MCP separado:"
  echo "  source \"$MCP_VENV_PATH/bin/activate\""
fi
