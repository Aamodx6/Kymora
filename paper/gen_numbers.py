#!/usr/bin/env python3
"""Verify or regenerate benchmark numbers in paper/paper.md from CLAIMS.md.

Exits with code 0 if all figures in paper.md trace to CLAIMS.md, 1 otherwise.
Usage:
    python paper/gen_numbers.py [--check]
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAIMS_FILE = REPO_ROOT / "CLAIMS.md"
PAPER_FILE = REPO_ROOT / "paper" / "paper.md"

CLAIM_PATTERNS = [
    re.compile(r"([\d,]+)\s*series/s(?:ec(?:ond)?)?", re.IGNORECASE),
    re.compile(r"(\d+\.?\d*)\s*ms\b"),
    re.compile(r"(\d+(?:\.\d+)?)\s*[×x]\s*(?:faster|slower|speedup)?", re.IGNORECASE),
    re.compile(r"(\d+\.?\d*)\s*µs"),
    re.compile(r"(\d+\.?\d*)\s*MiB"),
    re.compile(r"(\d+\.\d+)%"),
]

BANNED_PHRASES = [
    "zero-copy",
    "beats",
    "outperforms",
    "statistically significant",
]

SKIP_LINE_PATTERNS = [
    re.compile(r"^#"),
    re.compile(r"^---"),
    re.compile(r"date:"),
    re.compile(r"affiliation"),
    re.compile(r"```"),
    re.compile(r"\[@"),
]


def load_claims_numbers() -> tuple[str, set[float]]:
    if not CLAIMS_FILE.exists():
        print(f"ERROR: {CLAIMS_FILE} not found", file=sys.stderr)
        sys.exit(1)
    text = CLAIMS_FILE.read_text(encoding="utf-8")
    numbers = set()
    for pattern in CLAIM_PATTERNS:
        for match in pattern.finditer(text):
            num_str = match.group(1).replace(",", "")
            try:
                numbers.add(float(num_str))
            except ValueError:
                pass
    return text, numbers


def verify_paper() -> int:
    if not PAPER_FILE.exists():
        print(f"ERROR: {PAPER_FILE} not found", file=sys.stderr)
        return 1

    claims_text, claims_numbers = load_claims_numbers()
    paper_text = PAPER_FILE.read_text(encoding="utf-8")

    errors = []

    # Check banned phrases
    lower_text = paper_text.lower()
    for phrase in BANNED_PHRASES:
        if phrase in lower_text:
            errors.append(f"BANNED PHRASE found in paper.md: '{phrase}'")

    # Check numeric claims
    in_code_block = False
    for line_idx, line in enumerate(paper_text.splitlines(), start=1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if any(p.search(line) for p in SKIP_LINE_PATTERNS):
            continue

        for pattern in CLAIM_PATTERNS:
            for match in pattern.finditer(line):
                raw_claim = match.group(0)
                num_str = match.group(1).replace(",", "")
                try:
                    num_val = float(num_str)
                except ValueError:
                    continue

                # Ignore trivial constants: 1, 2, 4 (moments/dimensions)
                if num_val in {1.0, 2.0, 3.0, 4.0}:
                    continue

                found = False
                for c_num in claims_numbers:
                    if c_num == 0:
                        continue
                    if abs(num_val - c_num) / max(abs(c_num), 1e-10) < 0.01:
                        found = True
                        break

                if not found:
                    if num_str in claims_text or raw_claim in claims_text:
                        found = True

                if not found:
                    errors.append(
                        f"Line {line_idx}: Claim '{raw_claim}' ({num_val}) not found in CLAIMS.md. Context: {line.strip()[:100]}"
                    )

    if errors:
        print("FAIL: Verification failed in paper/paper.md:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"SUCCESS: All claims in {PAPER_FILE.relative_to(REPO_ROOT)} trace cleanly to CLAIMS.md.")
    return 0


if __name__ == "__main__":
    sys.exit(verify_paper())
