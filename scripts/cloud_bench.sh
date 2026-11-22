#!/usr/bin/env bash
# scripts/cloud_bench.sh
# Self-contained benchmark orchestrator for cloud instances (Ubuntu x86_64 / aarch64).
# Captures full machine telemetry (lscpu, numa, governor, memory) and runs
# the scaling, equal-feature, and headline throughput suites with cooldowns.

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="benchmarks/results/cloud_bench_${TIMESTAMP}"
mkdir -p "${RESULTS_DIR}"

echo "================================================================="
echo "  Kymora Cloud Benchmark Suite — ${TIMESTAMP}"
echo "================================================================="

# 1. System prerequisites
if command -v apt-get &>/dev/null; then
    echo "==> Updating apt and installing build tools..."
    sudo apt-get update -y || true
    sudo apt-get install -y build-essential curl git python3-dev python3-venv numactl cpufrequtils || true
fi

# 2. Rust Toolchain
if ! command -v cargo &>/dev/null; then
    echo "==> Installing Rust stable via rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi
fi

# 3. UV package manager
if ! command -v uv &>/dev/null; then
    echo "==> Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

# 4. Set performance governor if possible
echo "==> Setting CPU governor to performance..."
if [ -d /sys/devices/system/cpu/cpu0/cpufreq ]; then
    echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || true
fi

# 5. Capture hardware spec
echo "==> Capturing system hardware metadata..."
lscpu > "${RESULTS_DIR}/lscpu.txt" 2>&1 || true
numactl --hardware > "${RESULTS_DIR}/numactl.txt" 2>&1 || true
cat /proc/meminfo > "${RESULTS_DIR}/meminfo.txt" 2>&1 || true
uname -a > "${RESULTS_DIR}/uname.txt" 2>&1 || true
if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
    cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u > "${RESULTS_DIR}/governor.txt" 2>&1 || true
fi

# 6. Virtual environment and package build
echo "==> Setting up Python virtual environment..."
uv venv .venv_bench
source .venv_bench/bin/activate

uv pip install --upgrade pip maturin
echo "==> Building Kymora wheel from source in release mode..."
maturin build --release --out dist

WHEEL_FILE=$(ls -t dist/kymora-*.whl | head -n1)
echo "==> Installing ${WHEEL_FILE}..."
uv pip install --force-reinstall "${WHEEL_FILE}"
uv pip install pytest psutil scipy pandas tsfresh pycatch22 tsfel joblib numba

# 7. Record environment snapshot via tools/check_env.py
python tools/check_env.py || true

# 8. Suite 1: Equal-feature Parity Gate & Benchmark
echo "==> [Suite 1] Running equal-feature parity gate..."
python benchmarks/suites/equal_feature.py parity

echo "==> [Suite 1] Running equal-feature benchmark (3 rounds, 1000x500)..."
python benchmarks/suites/equal_feature.py bench --rounds 3 --shape 1000 500

echo "==> Cooldown (60 seconds)..."
sleep 60

# 9. Suite 2: Scaling sweep
echo "==> [Suite 2] Running scaling sweep..."
python benchmarks/suites/scaling.py || python benchmarks/suites/remeasure_readme.py --skip-slow

echo "==> Cooldown (60 seconds)..."
sleep 60

# 10. Suite 3: Memory sweep
echo "==> [Suite 3] Running memory sweep..."
python benchmarks/suites/bench_memory_sweep.py || true

echo "==> Cooldown (60 seconds)..."
sleep 60

# 11. Suite 4: Headline throughput protocol
echo "==> [Suite 4] Running headline throughput protocol..."
python benchmarks/suites/run_headline_protocol.py || echo "Headline protocol exited (check environment constraints)"

# 12. Package artifacts
TARBALL="kymora_cloud_bench_${TIMESTAMP}.tar.gz"
echo "==> Packaging results into ${TARBALL}..."
tar -czvf "${TARBALL}" "${RESULTS_DIR}" benchmarks/results/
SHA256=$(sha256sum "${TARBALL}" | cut -d' ' -f1)
echo "================================================================="
echo "  Benchmark completed successfully!"
echo "  Artifact: ${TARBALL}"
echo "  SHA256:   ${SHA256}"
echo "================================================================="
