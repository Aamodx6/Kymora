"""Automation script to create and maintain isolated competitor virtualenvs via uv."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

VENVS_DIR = Path(__file__).resolve().parent / ".venvs"
BENCHES_DIR = Path(__file__).resolve().parent

COMPETITORS = {
    "antropy": BENCHES_DIR / "requirements-antropy.txt",
    "tsflex": BENCHES_DIR / "requirements-tsflex.txt",
    "sktime": BENCHES_DIR / "requirements-sktime.txt",
    "jax_collision": BENCHES_DIR / "requirements-jax-collision.txt",
}


def setup_venv(name: str, req_file: Path, python_ver: str = "3.12") -> None:
    venv_path = VENVS_DIR / name
    scripts_dir = venv_path / "Scripts" if sys.platform == "win32" else venv_path / "bin"
    python_bin = scripts_dir / ("python.exe" if sys.platform == "win32" else "python")

    print(f"\n==========================================")
    print(f"Setting up isolated venv: {name} ({python_ver})")
    print(f"Path: {venv_path}")
    print(f"==========================================")

    if not venv_path.exists():
        cmd = ["uv", "venv", str(venv_path), "--python", python_ver]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

    if req_file.exists():
        cmd = ["uv", "pip", "install", "-r", str(req_file), "--python", str(python_bin)]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    else:
        print(f"Warning: Requirements file {req_file} not found.")


def main():
    parser = argparse.ArgumentParser(description="Set up isolated competitor venvs using uv.")
    parser.add_argument("--lib", choices=list(COMPETITORS.keys()) + ["all"], default="all")
    parser.add_argument("--python", default="3.12", help="Python version for competitor venvs")
    args = parser.parse_args()

    VENVS_DIR.mkdir(parents=True, exist_ok=True)

    targets = list(COMPETITORS.keys()) if args.lib == "all" else [args.lib]
    for target in targets:
        setup_venv(target, COMPETITORS[target], python_ver=args.python)

    print("\nAll requested competitor venvs configured successfully.")


if __name__ == "__main__":
    main()
