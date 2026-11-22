#!/usr/bin/env bash
# reproduce.sh - One-command reproducible benchmark pipeline for Kymora
# Verifies numerical parity, runs definition-matched benchmarks, and prints
# the ratio comparison table in < 10 minutes.
set -euo pipefail

echo "================================================================="
echo "        Kymora Benchmark Reproduction Suite (0.8.2)              "
echo "================================================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR="${ROOT_DIR}/.reproduce_venv"

if command -v uv >/dev/null 2>&1; then
    echo ">> Using uv for fast environment management..."
    if [ ! -d "$VENV_DIR" ]; then
        uv venv "$VENV_DIR"
    fi
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate" 2>/dev/null || source "$VENV_DIR/Scripts/activate"
    uv pip install --upgrade pip
    uv pip install numpy scipy numba tabulate pandas tsfresh pycatch22 tsfel
    if [ -f "dist/kymora-0.8.2-cp38-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl" ]; then
        uv pip install dist/kymora-0.8.2-*.whl
    elif [ -f "dist/kymora-0.8.2-cp38-abi3-win_amd64.whl" ]; then
        uv pip install dist/kymora-0.8.2-*.whl
    else
        uv pip install -e ".[bench,test]" --no-build-isolation
    fi
else
    echo ">> Using standard python3 venv..."
    PYTHON="${PYTHON:-python3}"
    if [ ! -d "$VENV_DIR" ]; then
        "$PYTHON" -m venv "$VENV_DIR"
    fi
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate" 2>/dev/null || source "$VENV_DIR/Scripts/activate"
    pip install --upgrade pip
    pip install numpy scipy numba tabulate pandas tsfresh pycatch22 tsfel
    pip install -e ".[bench,test]"
fi

echo ""
echo ">> Environment Check:"
python -c "import kymora as km, numpy as np, numba; print(f'Kymora: {km.__version__} | NumPy: {np.__version__} | Numba: {numba.__version__}')"

ROUNDS="${1:-3}"

echo ""
echo ">> Step 1: Running Parity Gate (verifying numerical agreement: exact <= 1e-9, close <= 1e-5)..."
python benchmarks/suites/equal_feature.py parity

echo ""
echo ">> Step 2: Running Equal-Feature Benchmark (1,000 x 500, ${ROUNDS} rounds)..."
python benchmarks/suites/equal_feature.py bench --rounds "$ROUNDS" --shape 1000 500

echo ""
echo ">> Step 3: Formatting Summary Table..."
python - <<'EOF'
import json
import glob
import os

results = sorted(glob.glob("benchmarks/results/*_equal_feature/equal_feature.jsonl"))
if results:
    latest = results[-1]
    print(f"\nLatest benchmark run: {latest}\n")
    print("-" * 75)
    print(f"{'Competitor':<15} | {'Shape':<12} | {'Features':<10} | {'Ratio vs Kymora':<16} | {'95% CI':<15}")
    print("-" * 75)
    with open(latest, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            data = json.loads(line)
            comp = data.get("competitor", "unknown")
            shape = f"{data.get('n_series', 0)}x{data.get('length', 0)}"
            n_feats = data.get("n_features_kymora", data.get("n_features", 0))
            ratio = data.get("ratio_competitor_over_kymora", data.get("ratio_median", 0.0))
            if "ratio_ci95" in data and isinstance(data["ratio_ci95"], (list, tuple)):
                ci = f"[{data['ratio_ci95'][0]:.1f}, {data['ratio_ci95'][1]:.1f}]"
            else:
                ci = f"[{data.get('ratio_ci_low', 0.0):.1f}, {data.get('ratio_ci_high', 0.0):.1f}]"
            print(f"{comp:<15} | {shape:<12} | {n_feats:<10} | {ratio:>14.1f}x | {ci:<15}")
    print("-" * 75)
else:
    print("No equal_feature.jsonl found.")
EOF

echo ""
echo "================================================================="
echo "  Reproduction completed successfully. Details in CLAIMS.md.    "
echo "================================================================="
