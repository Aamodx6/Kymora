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
# (Process files PLAN/STATUS/CLEANUP_STATUS/RELEASE_NOTES, CLAUDE.md, and
# OWNER_DECISIONS.md live in docs/internal/; they must NOT reappear at root.)
ROOT_ALLOWED = frozenset(
    {
        ".gitignore",
        "Cargo.lock",
        "Cargo.toml",
        "CHANGELOG.md",
        "CITATION.cff",
        "CLAIMS.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "deny.toml",
        "Dockerfile",
        "LICENSE",
        "Makefile",
        "mkdocs.yml",
        "pyproject.toml",
        "README.md",
        "reproduce.sh",
        "ROADMAP.md",
        "SECURITY.md",
        "vercel.json",
    }
)

# Denylist of obsolete project names and deprecated benchmark numbers
# that must never appear in active source code, documentation, manifests, or landing pages.
DENYLIST_TERMS = (
    "tsxtract",
    "tsxtractor",
    "800,256",
    "555,016",
    "314,450",
    "542,682",
    "575,391",
    "262x",
    "262×",
    "249x",
    "249×",
    "1,175x",
    "1,175×",
    "8,612x",
    "8,612×",
    "two linear passes",
    "+0.00 MiB",
    "zero defensive",
)


def should_check_denylist(path: str) -> bool:
    """Return True if path is in the active scope for obsolete names and figures."""
    if path.startswith(("src/", "python/", "tests/")):
        return True
    if path.startswith("landing/"):
        return True
    if path.startswith("notebooks/"):
        return True
    if path.startswith(".github/workflows/"):
        return True
    if path.startswith("docs/") and not path.startswith("docs/internal/"):
        return True
    if path in {
        "Cargo.toml",
        "pyproject.toml",
        "CITATION.cff",
        "README.md",
        "ROADMAP.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "CLAIMS.md",
    }:
        return True
    return False

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

    # docs/internal/ must stay out of the published site (it holds patent
    # references and process history). mkdocs >= 1.5 supports exclude_docs.
    mkdocs = (REPO / "mkdocs.yml").read_text(encoding="utf-8")
    if "exclude_docs" not in mkdocs or "internal/" not in mkdocs:
        errors.append("mkdocs.yml must exclude docs/internal/ (exclude_docs: internal/)")

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

        # Check for forbidden deprecated names and numbers in active files
        if should_check_denylist(path):
            try:
                content = full.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()
                in_superseded = False
                for idx, line in enumerate(lines, 1):
                    if path == "CLAIMS.md" and "superseded" in line.lower():
                        in_superseded = True
                    elif path == "CLAIMS.md" and line.startswith("## Measured"):
                        in_superseded = False
                    if in_superseded and path == "CLAIMS.md":
                        continue
                    line_lower = line.lower()
                    for term in DENYLIST_TERMS:
                        if term.lower() in line_lower:
                            errors.append(
                                f"denylist term '{term}' found in {path}:{idx}: '{line.strip()[:80]}'"
                            )
            except Exception as e:
                errors.append(f"could not scan {path} for denylist: {e}")

    if errors:
        print(f"{len(errors)} hygiene violation(s):")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("hygiene OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
