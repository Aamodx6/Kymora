#!/usr/bin/env python3
"""Check that version strings agree across Cargo.toml, pyproject.toml, CITATION.cff, and docs.

Exits with code 0 if all version declarations match, 1 otherwise.
Usage:
    python tools/check_versions.py [--expected 0.8.2]
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CARGO_TOML = REPO_ROOT / "Cargo.toml"
PYPROJECT_TOML = REPO_ROOT / "pyproject.toml"
CITATION_CFF = REPO_ROOT / "CITATION.cff"
ZENODO_JSON = REPO_ROOT / ".zenodo.json"
DOCS_API_MD = REPO_ROOT / "docs" / "api.md"


def get_cargo_version() -> str:
    content = CARGO_TOML.read_text(encoding="utf-8")
    match = re.search(r'^\[package\][\s\S]*?^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find [package] version in {CARGO_TOML}")
    return match.group(1).strip()


def verify_pyproject() -> list[str]:
    errors = []
    content = PYPROJECT_TOML.read_text(encoding="utf-8")
    if 'dynamic = ["version"]' not in content and 'dynamic = [ "version" ]' not in content:
        errors.append(f"{PYPROJECT_TOML} should specify dynamic = ['version'] (single-sourced from Cargo.toml)")
    return errors


def get_citation_version() -> str:
    content = CITATION_CFF.read_text(encoding="utf-8")
    match = re.search(r"^version:\s*([0-9a-zA-Z\.\-]+)", content, re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find version in {CITATION_CFF}")
    return match.group(1).strip()


def verify_zenodo() -> list[str]:
    errors = []
    if not ZENODO_JSON.exists():
        errors.append(f"Missing {ZENODO_JSON}")
        return errors
    try:
        data = json.loads(ZENODO_JSON.read_text(encoding="utf-8"))
        if not data.get("title"):
            errors.append(f"{ZENODO_JSON} missing 'title'")
        if not data.get("creators"):
            errors.append(f"{ZENODO_JSON} missing 'creators'")
    except Exception as exc:
        errors.append(f"Invalid JSON in {ZENODO_JSON}: {exc}")
    return errors


def verify_docs_version(expected: str) -> list[str]:
    errors = []
    if not DOCS_API_MD.exists():
        errors.append(f"Missing {DOCS_API_MD}")
        return errors
    text = DOCS_API_MD.read_text(encoding="utf-8")
    if expected not in text:
        errors.append(f"Expected version {expected} not found in {DOCS_API_MD.relative_to(REPO_ROOT)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check version consistency across Kymora metadata.")
    parser.add_argument("--expected", help="Expected version (default: read from Cargo.toml)")
    args = parser.parse_args()

    cargo_ver = get_cargo_version()
    citation_ver = get_citation_version()

    canonical = args.expected or cargo_ver

    errors = []
    if cargo_ver != canonical:
        errors.append(f"Cargo.toml version '{cargo_ver}' != expected '{canonical}'")
    if citation_ver != canonical:
        errors.append(f"CITATION.cff version '{citation_ver}' != expected '{canonical}'")

    errors.extend(verify_pyproject())
    errors.extend(verify_zenodo())
    errors.extend(verify_docs_version(canonical))

    if errors:
        print("FAIL: Version/metadata mismatch detected:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"OK: All version strings match canonical '{canonical}' across Cargo.toml, pyproject.toml, CITATION.cff, docs, and .zenodo.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
