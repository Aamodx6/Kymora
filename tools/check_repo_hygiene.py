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

import hashlib
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
# (Process files PLAN/STATUS/CLEANUP_STATUS/RELEASE_NOTES and arch.md live in
# docs/internal/ since the cleanup; they must NOT reappear at root.)
ROOT_ALLOWED = frozenset(
    {
        ".gitignore",
        "Cargo.lock",
        "Cargo.toml",
        "CHANGELOG.md",
        "CITATION.cff",
        "CLAIMS.md",
        "CLAUDE.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "deny.toml",
        "Dockerfile",
        "LICENSE",
        "Makefile",
        "mkdocs.yml",
        "OWNER_DECISIONS.md",
        "pyproject.toml",
        "README.md",
        "reproduce.sh",
        "SECURITY.md",
        "vercel.json",
    }
)

# Paper/landing figure duplicates must stay byte-identical (different deploy
# targets, same bytes).
FIGURE_PAIRS = (
    ("paper/figures/architecture.png", "landing/public/figures/architecture.png"),
    ("paper/figures/scaling.png", "landing/public/figures/scaling.png"),
    ("paper/figures/speedup.png", "landing/public/figures/speedup.png"),
    ("paper/figures/memory.png", "landing/public/figures/memory.png"),
    ("paper/figures/throughput.png", "landing/public/figures/throughput.png"),
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

    # docs/internal/ must stay out of the published site (it holds patent
    # references and process history). mkdocs >= 1.5 supports exclude_docs.
    mkdocs = (REPO / "mkdocs.yml").read_text(encoding="utf-8")
    if "exclude_docs" not in mkdocs or "internal/" not in mkdocs:
        errors.append("mkdocs.yml must exclude docs/internal/ (exclude_docs: internal/)")

    # Paper/landing figure duplicates must stay byte-identical.
    for paper_fig, landing_fig in FIGURE_PAIRS:
        pf, lf = REPO / paper_fig, REPO / landing_fig
        if not pf.exists() or not lf.exists():
            errors.append(f"figure pair missing: {paper_fig} / {landing_fig}")
            continue
        hp = hashlib.sha256(pf.read_bytes()).hexdigest()
        hl = hashlib.sha256(lf.read_bytes()).hexdigest()
        if hp != hl:
            errors.append(
                f"figure drift: {paper_fig} ({hp[:12]}) != {landing_fig} ({hl[:12]})"
            )

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
