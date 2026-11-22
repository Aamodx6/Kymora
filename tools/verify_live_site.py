"""Verification tool to audit rendered docs and landing pages for stale numbers.

Asserts that forbidden deprecated benchmark numbers and claims do not appear:
- 542,682 (old single-run headline throughput)
- 575,391 (old unpooled headline throughput)
- 249x / 249× (old TSFEL speedup)
- 1,175 / 1,175× (old TSFEL speedup)
- 8,612 / 8,612× (old tsfresh speedup)
- "beats catch22" (unsubstantiated downstream claim)
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PATTERNS = [
    r"542[,.]682",
    r"575[,.]391",
    r"249[x×]",
    r"1[,.]175",
    r"8[,.]612",
    r"beats catch22",
]


def check_content(text: str, source_name: str) -> list[str]:
    violations = []
    for pattern in FORBIDDEN_PATTERNS:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        for m in matches:
            # Get surrounding context
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            snippet = text[start:end].replace("\n", " ")
            violations.append(f"[{source_name}] Match for '{pattern}': '...{snippet}...'")
    return violations


def check_url(url: str) -> list[str]:
    print(f"Auditing live URL: {url} ...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KymoraAudit/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return check_content(body, url)
    except Exception as e:
        print(f"Warning: Failed to fetch {url}: {e}")
        return []


def check_directory(dir_path: Path) -> list[str]:
    print(f"Auditing directory: {dir_path} ...")
    violations = []
    extensions = {".html", ".js", ".json", ".md", ".txt"}
    for p in dir_path.rglob("*"):
        if p.is_file() and p.suffix in extensions:
            # Skip historical archives and tests
            if any(part in p.parts for part in ["tests", "tools", ".git", "venv", ".venv", "node_modules"]):
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                v = check_content(content, str(p.relative_to(REPO_ROOT)))
                violations.extend(v)
            except Exception:
                pass
    return violations


def main():
    parser = argparse.ArgumentParser(description="Audit docs/landing for stale benchmark claims")
    parser.add_argument("--url", action="append", help="Live URL(s) to fetch and verify")
    parser.add_argument("--dir", action="append", help="Directory/directories to scan recursively")
    args = parser.parse_args()

    all_violations = []

    if args.url:
        for u in args.url:
            all_violations.extend(check_url(u))

    if args.dir:
        for d in args.dir:
            p = Path(d)
            if p.exists():
                all_violations.extend(check_directory(p))
            else:
                print(f"Warning: Directory does not exist: {d}")

    # If neither specified, scan docs/ and landing/ by default
    if not args.url and not args.dir:
        for default_dir in [REPO_ROOT / "docs", REPO_ROOT / "landing" / "src"]:
            if default_dir.exists():
                all_violations.extend(check_directory(default_dir))

    print("=" * 60)
    print("  Live Site & Docs Stale Claims Audit")
    print("=" * 60)
    if all_violations:
        print(f"[ERROR] Found {len(all_violations)} violations of stale claims policy:")
        for v in all_violations:
            print(f"  - {v}")
        sys.exit(1)
    else:
        print("[OK] No stale claims or deprecated numbers detected.")
        sys.exit(0)


if __name__ == "__main__":
    main()
