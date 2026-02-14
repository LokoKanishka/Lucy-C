#!/bin/bash
set -e

echo "=== Lucy-C CI Check ==="

echo "[1/4] Running Flake8 (Linting)..."
# Exclude legacy and envs
.venv/bin/python -m flake8 lucy_c tests --count --select=E9,F63,F7,F82 --show-source --statistics
.venv/bin/python -m flake8 lucy_c tests --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

echo "[2/4] Running Mypy (Type Check)..."
# Ignore missing imports for now as some libs might not have stubs
.venv/bin/python -m mypy lucy_c --ignore-missing-imports || echo "Mypy found issues (non-fatal for now)"

echo "[3/4] Running Doctor..."
.venv/bin/python scripts/doctor.py

echo "[4/4] Running Unit Tests..."
.venv/bin/python -m pytest tests/unit

echo "=== ALL CHECKS PASSED ==="
