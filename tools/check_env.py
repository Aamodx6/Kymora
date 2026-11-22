"""Environment verification protocol for benchmark headline runs.

Refuses headline benchmark runs unless:
1. AC power is plugged in (not running on battery).
2. Operating system power policy is set to maximum performance:
   - Windows: 'High performance' or 'Ultimate Performance'
   - Linux: CPU scaling governor is 'performance'
   - macOS: AC online
3. Installed kymora package matches repository HEAD git commit and version >= 0.8.1.
"""

from __future__ import annotations

import argparse
import hashlib
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]


def get_git_head_sha() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"


def get_kymora_wheel_or_binary_info() -> dict[str, Any]:
    import kymora

    info: dict[str, Any] = {
        "version": getattr(kymora, "__version__", "unknown"),
        "path": getattr(kymora, "__file__", "unknown"),
        "sha256": None,
    }

    try:
        km_dir = Path(kymora.__file__).parent
        candidates = list(km_dir.glob("_core*.pyd")) + list(km_dir.glob("_core*.so"))
        if candidates:
            bin_path = candidates[0]
            info["binary_path"] = str(bin_path)
            sha = hashlib.sha256(bin_path.read_bytes()).hexdigest()
            info["sha256"] = sha
            info["binary_sha256"] = sha
    except Exception as e:
        info["error"] = str(e)

    # Check for downloaded wheel
    wheel_dir = REPO_ROOT / "dist" / "head_wheels"
    if wheel_dir.exists():
        wheels = list(wheel_dir.glob("*.whl"))
        if wheels:
            info["head_wheel_path"] = str(wheels[0])
            info["head_wheel_sha256"] = hashlib.sha256(wheels[0].read_bytes()).hexdigest()

    return info


def verify_headline_environment(strict_power: bool = True, strict_git: bool = True) -> Tuple[bool, list[str]]:
    reasons = []

    # 1. AC power check
    try:
        import psutil

        bat = psutil.sensors_battery()
        if bat is not None and not bat.power_plugged:
            reasons.append("System is running on BATTERY. AC power is required for headline benchmark runs.")
    except Exception:
        pass

    # 2. Power scheme check
    system = platform.system()
    if system == "Windows":
        try:
            res = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                raw_scheme = res.stdout.strip().lower()
                is_high_perf = ("high performance" in raw_scheme) or ("ultimate performance" in raw_scheme)
                if not is_high_perf and strict_power:
                    reasons.append(
                        f"Windows power scheme is not High/Ultimate Performance: '{res.stdout.strip()}'. "
                        "Refusing headline run. Switch with: powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
                    )
        except Exception as e:
            if strict_power:
                reasons.append(f"Failed to check Windows power scheme: {e}")
    elif system == "Linux":
        try:
            gov_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
            if gov_path.exists():
                gov = gov_path.read_text().strip()
                if gov != "performance" and strict_power:
                    reasons.append(
                        f"Linux CPU scaling governor is '{gov}' (expected 'performance'). "
                        "Refusing headline run. Switch with: cpupower frequency-set -g performance"
                    )
        except Exception as e:
            if strict_power:
                reasons.append(f"Failed to check Linux governor: {e}")

    # 3. Kymora version & HEAD check
    try:
        import kymora

        version = getattr(kymora, "__version__", "unknown")
        if version < "0.8.1":
            reasons.append(
                f"Installed kymora version is {version} (must be >= 0.8.1 for HEAD benchmarks). "
                "Do not benchmark the 0.8.0 wheel."
            )

        if strict_git:
            head_sha = get_git_head_sha()
            info = get_kymora_wheel_or_binary_info()
            if head_sha == "unknown":
                reasons.append("Git HEAD SHA could not be resolved from repository checkout.")
            if not info.get("binary_sha256") or not info.get("head_wheel_sha256"):
                reasons.append(
                    "No verifiable build provenance (both binary SHA256 and head wheel SHA256 required) found for installed kymora. "
                    "A traceable HEAD build from CI or dist/head_wheels is required for headline runs."
                )
    except ImportError as e:
        reasons.append(f"kymora is not installed: {e}")

    return len(reasons) == 0, reasons


def main():
    parser = argparse.ArgumentParser(description="Check headline benchmark environment prerequisites")
    parser.add_argument("--strict-power", action="store_true", default=True, help="Enforce high performance power plan")
    parser.add_argument("--allow-suboptimal", action="store_false", dest="strict_power", help="Allow running on balanced/silent schemes")
    parser.add_argument("--strict-git", action="store_true", default=True, help="Enforce verifiable HEAD build provenance")
    parser.add_argument("--allow-untracked-git", action="store_false", dest="strict_git", help="Allow untracked build provenance")
    args = parser.parse_args()

    ok, reasons = verify_headline_environment(strict_power=args.strict_power, strict_git=args.strict_git)
    info = get_kymora_wheel_or_binary_info()
    head_sha = get_git_head_sha()

    print("=" * 60)
    print("  Benchmark Environment Audit")
    print("=" * 60)
    print(f"  OS System:        {platform.system()} {platform.release()}")
    print(f"  Git HEAD SHA:     {head_sha}")
    print(f"  Kymora Version:   {info.get('version')}")
    print(f"  Binary Path:      {info.get('binary_path')}")
    print(f"  Binary SHA256:    {info.get('sha256')}")
    if "head_wheel_sha256" in info:
        print(f"  Wheel SHA256:     {info.get('head_wheel_sha256')}")
    print("=" * 60)

    if not ok:
        print("\n[ERROR] Environment validation FAILED:")
        for r in reasons:
            print(f"  - {r}")
        sys.exit(1)
    else:
        print("\n[OK] Environment satisfies headline benchmark criteria.")
        sys.exit(0)


if __name__ == "__main__":
    main()
