#!/usr/bin/env bash
# scripts/verify_release.sh - Post-release verification script
# Runs in a fresh temporary venv, installs Kymora (from PyPI, TestPyPI, or local wheel),
# and verifies version, symbols, quickstart, streaming, and feature count.
set -euo pipefail

EXPECTED_VERSION="${1:-0.8.2}"
SOURCE="${2:-pypi}"  # options: pypi, testpypi, or path to local wheel/sdist

echo "=== Kymora Release Verification ==="
echo "Target version: ${EXPECTED_VERSION}"
echo "Source:         ${SOURCE}"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

VENV_DIR="${TMPDIR}/kymora_verify_venv"
echo "Creating isolated test environment in ${VENV_DIR}..."
python3 -m venv "${VENV_DIR}"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

pip install --upgrade pip

if [ "${SOURCE}" = "pypi" ]; then
    echo "Installing kymora==${EXPECTED_VERSION} from PyPI..."
    pip install "kymora==${EXPECTED_VERSION}"
elif [ "${SOURCE}" = "testpypi" ]; then
    echo "Installing kymora==${EXPECTED_VERSION} from TestPyPI..."
    # TestPyPI may not host all wheels or dependencies (numpy); install numpy first from PyPI
    pip install numpy
    pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "kymora==${EXPECTED_VERSION}"
else
    echo "Installing from local path: ${SOURCE}..."
    pip install "${SOURCE}"
fi

echo "Running verification suite..."
python3 - <<EOF
import sys
import numpy as np
import kymora as km

print(f"Loaded kymora from: {km.__file__}")
print(f"Reported version:   {km.__version__}")

# 1. Version assertion
assert km.__version__ == "${EXPECTED_VERSION}", f"Version mismatch: expected ${EXPECTED_VERSION}, got {km.__version__}"

# 2. Feature names check
features = km.feature_names()
assert len(features) == 33, f"Expected 33 features, got {len(features)}"

# 3. Batch extraction
np.random.seed(42)
x = np.random.randn(10, 100).astype(np.float64)
feats = km.extract_features(x)
assert feats.shape == (10, 33), f"Shape mismatch: {feats.shape}"
assert not np.isnan(feats).any(), "NaN found in clean extraction"

# 4. Single-series fast path
x1 = np.random.randn(100).astype(np.float64)
f1 = km.extract_one(x1)
assert f1.shape == (33,), f"Shape mismatch: {f1.shape}"

# 5. Streaming extractor
stream = km.StreamingExtractor(64)
for val in np.random.randn(100):
    stream.push(float(val))
fast = stream.compute(kind="fast")
all_feats = stream.compute(kind="all")
assert len(fast) > 0, "Streaming fast compute returned empty"
assert len(all_feats) == 33, f"Streaming all compute expected 33 features, got {len(all_feats)}"

print("All smoke checks passed successfully!")
EOF

echo "=== Release verification PASSED for ${EXPECTED_VERSION} ==="
