#!/usr/bin/env bash
# Tsxtract Benchmark Suite Reproduction Script
set -euo pipefail

echo "=========================================="
echo " Tsxtract Benchmark Reproduction Pipeline "
echo "=========================================="

PYTHON="${PYTHON:-python}"

echo "1. Checking environment..."
$PYTHON -c "import sys; print(f'Python: {sys.version}')"

echo "2. Setting up competitor environments..."
$PYTHON benches/setup_venvs.py --lib all

echo "3. Running Phase B0 Smoke Test..."
$PYTHON benches/smoke.py

echo "4. Running Phase B1 Correctness & Agreement Suite..."
$PYTHON benches/suites/agreement.py || true

echo "5. Generating Report..."
$PYTHON benches/report/make_report.py || true

echo "Benchmark reproduction completed."
