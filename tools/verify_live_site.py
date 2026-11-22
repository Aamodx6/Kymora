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
import html
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
    # Check both raw content and HTML-unescaped content
    texts_to_check = [("raw", text)]
    unescaped = html.unescape(text)
    if unescaped != text:
        texts_to_check.append(("unescaped", unescaped))

    seen_matches = set()
    for tag, content in texts_to_check:
        for pattern in FORBIDDEN_PATTERNS:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            for m in matches:
                # Get surrounding context
                start = max(0, m.start() - 30)
                end = min(len(content), m.end() + 30)
                snippet = content[start:end].replace("\n", " ")
                key = (pattern, m.group(0).lower(), snippet)
                if key not in seen_matches:
                    seen_matches.add(key)
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
        err_msg = f"[{url}] Failed to fetch live URL: {e}"
        print(f"Error: {err_msg}")
        return [err_msg]


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
                p_resolved = p.resolve()
                try:
                    src_name = str(p_resolved.relative_to(REPO_ROOT.resolve()))
                except ValueError:
                    src_name = str(p_resolved)
                content = p.read_text(encoding="utf-8", errors="replace")
                v = check_content(content, src_name)
                violations.extend(v)
            except Exception as e:
                violations.append(f"[{p}] Failed to read file: {e}")
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
                err = f"Directory explicitly requested does not exist: {d}"
                print(f"Error: {err}")
                all_violations.append(err)

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
