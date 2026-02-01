#!/usr/bin/env bash
# Reset Lucy-C: Wipes session history and user facts to ensure a fresh, local-only start.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "🧹 Cleaning Lucy's memory and history..."

# Remove history
if [[ -d "data/history" ]]; then
    echo "   - Deleting session history (data/history/)"
    rm -rf data/history/*
fi

# Remove facts (persisted brain choices, etc.)
if [[ -d "data/facts" ]]; then
    echo "   - Deleting persisted facts (data/facts/)"
    rm -rf data/facts/*
fi

# Remove any stray logs
rm -f server*.log

echo "✨ Lucy is now fresh and ready for v1.0 action."
