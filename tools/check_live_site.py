#!/usr/bin/env python3
"""Post-deploy live site auditor.

Fetches the live documentation site and production landing page, auditing
the rendered content against denylisted stale numbers and banned phrases
defined in tools/check_repo_hygiene.py.

Usage:
    python tools/check_live_site.py [--docs-url URL] [--landing-url URL]
Exit 1 on any violation.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Import DENYLIST_TERMS directly from tools.check_repo_hygiene for consistency
sys.path.insert(0, str(REPO / "tools"))
try:
    from check_repo_hygiene import DENYLIST_TERMS
except ImportError:
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

DEFAULT_DOCS_URL = "https://aamodx6.github.io/Kymora/"
DEFAULT_LANDING_URL = "https://landing-drab-six-14.vercel.app/"


def fetch_url(url: str, timeout: int = 20) -> str:
    """Fetch URL contents with browser-like user agent."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "KymoraPostDeployAuditor/1.0 (CI audit)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} fetching {url}")
        return resp.read().decode("utf-8", errors="replace")


def check_html(url: str, content: str) -> list[str]:
    """Check HTML content against all denylisted terms."""
    violations: list[str] = []
    # Test both raw content and HTML-unescaped text
    unescaped = html.unescape(content)
    lower_raw = content.lower()
    lower_unescaped = unescaped.lower()

    for term in DENYLIST_TERMS:
        term_lower = term.lower()
        if term_lower in lower_raw or term_lower in lower_unescaped:
            # Locate snippet for reporting
            target = unescaped if term_lower in lower_unescaped else content
            idx = target.lower().find(term_lower)
            start = max(0, idx - 40)
            end = min(len(target), idx + len(term) + 40)
            snippet = target[start:end].replace("\n", " ").strip()
            violations.append(f"[{url}] Banned term '{term}' found: '...{snippet}...'")

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit live docs and landing site for denylisted terms")
    parser.add_argument("--docs-url", default=DEFAULT_DOCS_URL, help=f"Live docs URL (default: {DEFAULT_DOCS_URL})")
    parser.add_argument("--landing-url", default=DEFAULT_LANDING_URL, help=f"Live landing URL (default: {DEFAULT_LANDING_URL})")
    args = parser.parse_args()

    targets = [("Live Documentation", args.docs_url), ("Landing Page", args.landing_url)]
    all_violations: list[str] = []

    print("=" * 65)
    print("  Kymora Post-Deploy Live Site Hygiene Verification")
    print("=" * 65)

    for label, url in targets:
        print(f"Fetching {label}: {url} ...")
        try:
            body = fetch_url(url)
            print(f"  -> Successfully retrieved {len(body):,} bytes")
            v = check_html(url, body)
            if v:
                all_violations.extend(v)
                print(f"  -> [FAIL] Found {len(v)} violation(s)")
            else:
                print(f"  -> [OK] No denylisted terms detected")
        except Exception as exc:
            err = f"[{url}] Failed to fetch live site: {exc}"
            print(f"  -> [ERROR] {err}")
            all_violations.append(err)

    print("=" * 65)
    if all_violations:
        print(f"FAILED: Found {len(all_violations)} live site hygiene violation(s):")
        for v in all_violations:
            print(f"  - {v}")
        return 1

    print("PASSED: All live sites verified clean against denylist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
