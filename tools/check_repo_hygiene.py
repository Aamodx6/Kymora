#!/usr/bin/env python3
"""Repository hygiene gate (CI `repo hygiene` job).

Fast, deterministic, stdlib-only checks that the working tree stays
committable: build outputs and vendored environments must never be tracked,
no tracked file may be unexpectedly large, and no unexpected file may appear
in the repo root.

Usage:
    python tools/check_repo_hygiene.py
Exit 1 on any violation.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Tracked paths with any of these prefixes are build outputs / environments,
# never sources. (Mirrors .gitignore; this gate catches `git add -f` slips.)
FORBIDDEN_PREFIXES = (
    "dist/",
    "site/",
    "target/",
    "fuzz/target/",
    "node_modules/",
    "landing/node_modules/",
    "landing/dist/",
    ".venv/",
    "benchmarks/.venvs/",
    "__pycache__/",
)

FORBIDDEN_SUFFIXES = (".whl", ".pdb", ".venv")

# 1 MiB: the tracked tree is sources + small evidence files (nothing tracked
# exceeds 1 MB).
MAX_TRACKED_BYTES = 1 << 20

REQUIRED_GITIGNORE_ENTRIES = ("target/", "site/", "dist/", "node_modules/")

# Final root layout (post-cleanup): every tracked file in the repo root must
# be in this set. Adding a root file means updating this list deliberately.
ROOT_ALLOWED = frozenset(
    {
        ".gitignore",
        "arch.md",
        "Cargo.lock",
        "Cargo.toml",
        "CHANGELOG.md",
        "CITATION.cff",
        "CLAIMS.md",
        "CLAUDE.md",
        "CLEANUP_STATUS.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "deny.toml",
        "Dockerfile",
        "LICENSE",
        "Makefile",
        "mkdocs.yml",
        "OWNER_DECISIONS.md",
        "PLAN.md",
        "pyproject.toml",
        "README.md",
        "RELEASE_NOTES.md",
        "reproduce.sh",
        "SECURITY.md",
        "STATUS.md",
        "vercel.json",
    }
)


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    return [p for p in out.stdout.split("\0") if p]


def main() -> int:
    errors: list[str] = []

    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()
    normalized = {line.strip().lstrip("/").rstrip("/") for line in gitignore}
    for entry in REQUIRED_GITIGNORE_ENTRIES:
        if entry.rstrip("/") not in normalized:
            errors.append(f".gitignore missing required entry: {entry}")

    for path in tracked_files():
        if "/" not in path and path not in ROOT_ALLOWED:
            errors.append(f"unexpected root file (update ROOT_ALLOWED?): {path}")
        if path.startswith(FORBIDDEN_PREFIXES) or path.endswith(FORBIDDEN_SUFFIXES):
            errors.append(f"tracked build output/environment: {path}")
            continue
        full = REPO / path
        try:
            size = full.stat().st_size
        except OSError:
            errors.append(f"tracked but unreadable: {path}")
            continue
        if size > MAX_TRACKED_BYTES:
            errors.append(f"tracked file exceeds 1 MiB ({size} bytes): {path}")

    if errors:
        print(f"{len(errors)} hygiene violation(s):")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("hygiene OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
