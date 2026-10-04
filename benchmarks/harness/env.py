"""Comprehensive machine and runtime environment capture for benchmarks."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any


def _get_cpu_info() -> dict[str, Any]:
    info: dict[str, Any] = {
        "model": platform.processor(),
        "architecture": platform.machine(),
        "logical_cores": os.cpu_count() or 1,
        "physical_cores": None,
        "p_cores": None,
        "e_cores": None,
        "flags": [],
    }
    try:
        import psutil
        log_cores = psutil.cpu_count(logical=True) or 1
        phys_cores = psutil.cpu_count(logical=False) or log_cores
        info["logical_cores"] = log_cores
        info["physical_cores"] = phys_cores

        # Hybrid Intel (Alder/Raptor/Meteor Lake): P-cores have SMT (2 threads), E-cores have 1 thread.
        # log = 2 * P + E, phys = P + E => P = log - phys, E = phys - P
        if log_cores > phys_cores:
            p = log_cores - phys_cores
            e = phys_cores - p
            if e >= 0 and p > 0:
                info["p_cores"] = p
                info["e_cores"] = e
            else:
                info["p_cores"] = phys_cores
                info["e_cores"] = 0
        else:
            info["p_cores"] = phys_cores
            info["e_cores"] = 0
    except Exception:
        pass

    system = platform.system()
    if system == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            info["model"] = name.strip()
        except Exception:
            pass
    elif system == "Linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                content = f.read()
            for line in content.splitlines():
                if "model name" in line:
                    info["model"] = line.split(":", 1)[1].strip()
                if "flags" in line and not info["flags"]:
                    info["flags"] = line.split(":", 1)[1].strip().split()
        except Exception:
            pass
    elif system == "Darwin":
        try:
            res = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, timeout=2)
            info["model"] = res.stdout.strip()
        except Exception:
            pass

    return info


def _get_ram_info() -> dict[str, Any]:
    try:
        import psutil
        vm = psutil.virtual_memory()
        return {
            "total_bytes": vm.total,
            "total_gb": round(vm.total / (1024**3), 2),
            "available_gb": round(vm.available / (1024**3), 2),
        }
    except Exception:
        return {"total_bytes": None, "total_gb": None, "available_gb": None}


def _get_os_info() -> dict[str, Any]:
    gov = "standard"
    system = platform.system()
    if system == "Linux":
        try:
            p = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
            if p.exists():
                gov = p.read_text().strip()
        except Exception:
            pass
    elif system == "Windows":
        gov = "windows_balanced_or_high_perf"

    return {
        "system": system,
        "release": platform.release(),
        "version": platform.version(),
        "platform_str": platform.platform(),
        "governor": gov,
    }


def _get_git_info() -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2]
    info = {"commit": "unknown", "branch": "unknown", "is_dirty": False}
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            info["commit"] = res.stdout.strip()
        res_b = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root, capture_output=True, text=True, timeout=2)
        if res_b.returncode == 0:
            info["branch"] = res_b.stdout.strip()
        res_d = subprocess.run(["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True, timeout=2)
        if res_d.returncode == 0:
            info["is_dirty"] = bool(res_d.stdout.strip())
    except Exception:
        pass
    return info


def _get_rust_info() -> dict[str, Any]:
    info = {"rustc": None, "cargo": None}
    rustc_candidates = ["rustc", str(Path.home() / ".cargo" / "bin" / "rustc.exe"), str(Path.home() / ".cargo" / "bin" / "rustc")]
    cargo_candidates = ["cargo", str(Path.home() / ".cargo" / "bin" / "cargo.exe"), str(Path.home() / ".cargo" / "bin" / "cargo")]

    for cand in rustc_candidates:
        try:
            res = subprocess.run([cand, "--version"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                info["rustc"] = res.stdout.strip()
                break
        except Exception:
            continue

    for cand in cargo_candidates:
        try:
            res = subprocess.run([cand, "--version"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                info["cargo"] = res.stdout.strip()
                break
        except Exception:
            continue

    return info


def _get_blas_threads() -> dict[str, Any]:
    return {
        "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS"),
        "MKL_NUM_THREADS": os.environ.get("MKL_NUM_THREADS"),
        "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
        "RAYON_NUM_THREADS": os.environ.get("RAYON_NUM_THREADS"),
    }


def _get_installed_packages() -> dict[str, str]:
    pkgs = {}
    try:
        for dist in metadata.distributions():
            pkgs[dist.metadata["Name"]] = dist.version
    except Exception:
        pass
    return dict(sorted(pkgs.items()))


def _get_power_info() -> dict[str, Any]:
    """Capture Windows power plan scheme and AC vs battery status."""
    info: dict[str, Any] = {
        "scheme": "unknown",
        "is_high_performance": True,
        "ac_plugged": True,
        "battery_percent": None,
        "on_battery": False,
    }
    if platform.system() == "Windows":
        try:
            res = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                raw_scheme = res.stdout.strip()
                info["scheme"] = raw_scheme
                lower = raw_scheme.lower()
                # Consider Performance, High Performance, or Ultimate as high-performance
                info["is_high_performance"] = ("performance" in lower) or ("ultimate" in lower)
        except Exception:
            pass

    try:
        import psutil
        bat = psutil.sensors_battery()
        if bat is not None:
            info["ac_plugged"] = bool(bat.power_plugged)
            info["battery_percent"] = float(bat.percent)
            info["on_battery"] = not bool(bat.power_plugged)
    except Exception:
        pass

    return info


def measure_cpu_freq() -> dict[str, Any]:
    """Sample current CPU frequency in MHz."""
    try:
        import psutil
        freq = psutil.cpu_freq()
        if freq is not None:
            return {
                "current_mhz": float(freq.current),
                "min_mhz": float(freq.min),
                "max_mhz": float(freq.max),
            }
    except Exception:
        pass
    return {"current_mhz": None, "min_mhz": None, "max_mhz": None}


def check_environment_warnings(env_data: dict[str, Any]) -> list[str]:
    """Return list of warnings if running under throttling or non-ideal benchmark conditions."""
    warnings = []
    power = env_data.get("power", {})
    if power.get("on_battery", False):
        warnings.append("System is running on BATTERY power. CPU frequency and throttling will affect results.")
    if not power.get("is_high_performance", True):
        warnings.append(
            f"Active Windows power plan is '{power.get('scheme')}'; recommend High Performance or Ultimate Performance."
        )
    return warnings


def capture_env() -> dict[str, Any]:
    """Capture full hardware, OS, Python, Rust, and library environment."""
    return {
        "cpu": _get_cpu_info(),
        "cpu_freq": measure_cpu_freq(),
        "power": _get_power_info(),
        "ram": _get_ram_info(),
        "os": _get_os_info(),
        "git": _get_git_info(),
        "rust": _get_rust_info(),
        "threading": _get_blas_threads(),
        "python": {
            "version": sys.version,
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "packages": _get_installed_packages(),
    }


def save_env(out_path: Path | str) -> dict[str, Any]:
    env_data = capture_env()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(env_data, f, indent=2)
    return env_data


if __name__ == "__main__":
    data = capture_env()
    print(json.dumps(data, indent=2))
    warns = check_environment_warnings(data)
    if warns:
        print("\nWarnings:")
        for w in warns:
            print(f"  [WARN] {w}")
