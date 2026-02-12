#!/bin/bash
set -euo pipefail

echo "=== System Info ==="
uname -a
python3 --version

echo
echo "=== API Check: Models ==="
MODELS_JSON=$(curl -s http://127.0.0.1:5050/api/models)
echo "$MODELS_JSON" | python3 -m json.tool

# Verify current model is in the list
CURRENT=$(echo "$MODELS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('current', ''))")
IN_LIST=$(echo "$MODELS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); models=[m['name'] for m in data.get('models', [])]; print('YES' if '$CURRENT' in models else 'NO')")

if [ "$IN_LIST" = "YES" ]; then
    echo "SUCCESS: Current model '$CURRENT' is in the installed list."
else
    echo "WARNING: Current model '$CURRENT' NOT in list. Fallback should trigger in backend."
fi

echo
echo "=== API Check: Chat ==="
CHAT_JSON=$(curl -s -X POST http://127.0.0.1:5050/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hola, respondé solo una palabra", "session_user": "smoke-test"}')

echo "$CHAT_JSON" | python3 -m json.tool

REPLY=$(echo "$CHAT_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('reply', ''))")

if [[ "$REPLY" == *"Ups"* && "$REPLY" != *"ID:"* ]]; then
    echo "FAILED: Received legacy error fallback without ID."
    exit 1
fi

echo "=== VERIFICATION PASSED ==="
