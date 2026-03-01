#!/bin/bash
# Lucy-C Master Verification Script

echo "Checking system health for Lucy-C..."
echo "-----------------------------------"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

run_test() {
    echo "Running $1..."
    ./.venv/bin/python3 "$1" > /tmp/lucy_test.log 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}PASS${NC}: $1"
    else
        echo -e "${RED}FAIL${NC}: $1 (Check /tmp/lucy_test.log)"
        # Print the last few lines of the error for context
        tail -n 5 /tmp/lucy_test.log
    fi
}

# 1. Core Phases
run_test "scripts/verify_phase1.py"
run_test "scripts/verify_phase2.py"
run_test "scripts/verify_phase4.py"

# 2. Body Components
run_test "scripts/verify_voice.py"
run_test "scripts/verify_automation.py"
run_test "scripts/verify_vision.py"

# 3. Persistence and Memory
run_test "scripts/verify_memory.py"
run_test "scripts/verify_persistence.py"

echo "-----------------------------------"
echo "Verification complete."
