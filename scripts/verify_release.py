"""scripts/verify_release.py - Cross-platform post-release & asset verification.

Validates distribution artifacts in dist/, checksums in SHA256SUMS.txt,
and verifies an installed kymora distribution in an isolated environment.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_dist_artifacts(dist_dir: Path) -> bool:
    if not dist_dir.is_dir():
        print(f"Dist directory {dist_dir} does not exist.")
        return False

    artifacts = list(dist_dir.glob("*.whl")) + list(dist_dir.glob("*.tar.gz"))
    if not artifacts:
        print(f"No wheels or sdists found in {dist_dir}.")
        return False

    print(f"Found {len(artifacts)} release artifacts in {dist_dir}:")
    for a in sorted(artifacts):
        sha = compute_sha256(a)
        print(f"  {a.name} ({a.stat().st_size:,} bytes) - sha256: {sha[:16]}...")

    # Validate sdist contents if present
    sdists = list(dist_dir.glob("*.tar.gz"))
    for sdist in sdists:
        with tarfile.open(sdist, "r:gz") as tar:
            names = tar.getnames()
            required_entries = ["Cargo.toml", "pyproject.toml"]
            for req in required_entries:
                found = any(n.endswith(f"/{req}") or n == req for n in names)
                if not found:
                    print(f"ERROR: sdist {sdist.name} missing required entry: {req}")
                    return False
        print(f"sdist {sdist.name} structure OK.")

    # Validate checksum file if present
    sums_file = dist_dir / "SHA256SUMS.txt"
    if sums_file.exists():
        print(f"Verifying {sums_file.name}...")
        with open(sums_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    expected_sha, fname = parts[0], parts[1].lstrip("*")
                    target = dist_dir / fname
                    if target.exists():
                        actual_sha = compute_sha256(target)
                        if actual_sha.lower() != expected_sha.lower():
                            print(f"ERROR: Checksum mismatch for {fname}!")
                            return False
                        print(f"  OK: {fname}")
    return True


def run_smoke_tests(python_exe: str, expected_version: str) -> bool:
    code = f"""
import sys
import numpy as np
import kymora as km

print(f"Module file:    {{km.__file__}}")
print(f"Module version: {{km.__version__}}")

# 1. Version check
assert km.__version__ == "{expected_version}", f"Version mismatch: expected {expected_version}, got {{km.__version__}}"

# 2. Feature names check
features = km.feature_names()
assert len(features) == 33, f"Expected 33 features, got {{len(features)}}"

# 3. Batch extraction
np.random.seed(42)
x = np.random.randn(10, 100).astype(np.float64)
feats = km.extract_features(x)
assert feats.shape == (10, 33), f"Shape mismatch: {{feats.shape}}"
assert not np.isnan(feats).any(), "NaN in output"

# 4. Single-series fast path
x1 = np.random.randn(100).astype(np.float64)
f1 = km.extract_one(x1)
assert f1.shape == (33,), f"Shape mismatch: {{f1.shape}}"

# 5. Streaming extractor
stream = km.StreamingExtractor(64)
for val in np.random.randn(100):
    stream.push(float(val))
fast = stream.compute(kind="fast")
all_feats = stream.compute(kind="all")
assert len(fast) > 0, "Streaming fast compute returned empty"
assert len(all_feats) == 33, f"Streaming all compute expected 33 features, got {{len(all_feats)}}"

print("All smoke checks passed.")
"""
    cmd = [python_exe, "-c", code]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Smoke tests failed with code {res.returncode}:\n{res.stderr}\n{res.stdout}")
        return False
    print(res.stdout.strip())
    return True


def test_in_isolated_venv(wheel_or_source: str, expected_version: str) -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_dir = Path(tmpdir) / "test_venv"
        print(f"Creating isolated venv at {venv_dir}...")
        res = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], capture_output=True)
        if res.returncode != 0:
            print("Failed to create test venv.")
            return False

        if os.name == "nt":
            py_bin = str(venv_dir / "Scripts" / "python.exe")
        else:
            py_bin = str(venv_dir / "bin" / "python")

        print("Installing dependencies...")
        subprocess.run([py_bin, "-m", "pip", "install", "--upgrade", "pip"], capture_output=True)
        subprocess.run([py_bin, "-m", "pip", "install", "numpy"], capture_output=True)

        print(f"Installing {wheel_or_source}...")
        if wheel_or_source == "pypi":
            cmd = [py_bin, "-m", "pip", "install", f"kymora=={expected_version}"]
        elif wheel_or_source == "testpypi":
            cmd = [
                py_bin,
                "-m",
                "pip",
                "install",
                "--index-url",
                "https://test.pypi.org/simple/",
                "--extra-index-url",
                "https://pypi.org/simple/",
                f"kymora=={expected_version}",
            ]
        else:
            cmd = [py_bin, "-m", "pip", "install", wheel_or_source]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Pip install failed:\n{res.stderr}\n{res.stdout}")
            return False

        print("Running smoke tests in isolated venv...")
        return run_smoke_tests(py_bin, expected_version)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Kymora release artifacts and installation")
    parser.add_argument("--version", default="0.8.2", help="Expected release version (default: 0.8.2)")
    parser.add_argument("--dist-dir", type=Path, default=REPO_ROOT / "dist", help="Path to dist directory")
    parser.add_argument("--install", choices=["pypi", "testpypi", "wheel"], default=None, help="Test install in venv")
    parser.add_argument("--wheel-path", type=str, default=None, help="Explicit path to wheel for testing")
    parser.add_argument("--current-env", action="store_true", help="Run smoke test against current python environment")

    args = parser.parse_args()

    print(f"=== Kymora Release Verification (v{args.version}) ===")

    success = True
    if args.dist_dir.exists() and any(args.dist_dir.iterdir()):
        if not verify_dist_artifacts(args.dist_dir):
            success = False

    if args.current_env:
        print("Testing in current Python environment...")
        if not run_smoke_tests(sys.executable, args.version):
            success = False

    if args.install:
        source = args.wheel_path if args.install == "wheel" and args.wheel_path else args.install
        print(f"Testing installation from: {source}")
        if not test_in_isolated_venv(source, args.version):
            success = False

    if success:
        print(f"=== Verification completed SUCCESSFULLY for v{args.version} ===")
        return 0
    else:
        print(f"=== Verification FAILED for v{args.version} ===")
        return 1


if __name__ == "__main__":
    sys.exit(main())
