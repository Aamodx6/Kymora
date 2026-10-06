#!/usr/bin/env python3
"""Check that every numeric claim in README, landing, and docs is present in CLAIMS.md.

Exit code 0 if all figures are traceable, 1 otherwise.
Usage: python tools/check_claims.py [--fix]
"""

import json
import re
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
CLAIMS_FILE = REPO_ROOT / "CLAIMS.md"

# Files to check for claims consistency
CHECK_FILES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "benchmarks.md",
    REPO_ROOT / "docs" / "index.md",
    # Landing page source files
    *(REPO_ROOT / "landing" / "src").glob("**/*.tsx"),
    *(REPO_ROOT / "landing" / "src").glob("**/*.ts"),
]

# Patterns that look like benchmark claims (numbers with units or ratios)
CLAIM_PATTERNS = [
    # Throughput: e.g. "314,450 series/s" or "314450 series/sec"
    re.compile(r"([\d,]+)\s*series/s(?:ec(?:ond)?)?", re.IGNORECASE),
    # Latency: e.g. "3.18 ms"
    re.compile(r"(\d+\.?\d*)\s*ms\b"),
    # Speedup ratios: e.g. "262×" or "262x faster"
    re.compile(r"(\d+(?:,\d+)?)\s*[×x]\s*(?:faster|slower)?", re.IGNORECASE),
    # Per-feature cost: e.g. "0.0964 µs"
    re.compile(r"(\d+\.?\d*)\s*µs"),
    # Memory: e.g. "25.18 MiB"
    re.compile(r"(\d+\.?\d*)\s*MiB"),
]

# Numbers that are NOT benchmark claims (skip these)
SKIP_PATTERNS = [
    re.compile(r"^\s*#"),  # Markdown headings
    re.compile(r"^\s*//"),  # TS/JS comment lines (e.g. animation timings)
    re.compile(r"```"),     # Code blocks
    re.compile(r"pip install"),
    re.compile(r"Python \d"),
    re.compile(r"version"),
    re.compile(r"numpy>="),
    re.compile(r"\d+\.\d+\.\d+"),  # Version numbers like 0.7.0
]

# Claims that exist in sources but are ALREADY tracked as pending in
# CLAIMS.md ("Pending re-baseline" section). Reported, but do not fail the
# gate — the tracking entry is the fix commitment, not silent acceptance.
# (Empty since 8.4 removed the last stale landing demo figures; kept as a
# hook for future pending items.)
KNOWN_PENDING: dict[tuple[str, str], str] = {}


def load_claims():
    """Load CLAIMS.md content."""
    if not CLAIMS_FILE.exists():
        print(f"ERROR: {CLAIMS_FILE} not found")
        sys.exit(1)
    return CLAIMS_FILE.read_text(encoding="utf-8")


def extract_numbers_from_claims(claims_text):
    """Extract all numeric values mentioned in CLAIMS.md."""
    numbers = set()
    for pattern in CLAIM_PATTERNS:
        for match in pattern.finditer(claims_text):
            num_str = match.group(1).replace(",", "")
            try:
                numbers.add(float(num_str))
            except ValueError:
                pass
    return numbers


def check_file(filepath, claims_text, claims_numbers):
    """Check a single file for claims not present in CLAIMS.md."""
    if not filepath.exists():
        return [], []

    issues = []
    pending = []
    in_code_block = False
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    for line_num, line in enumerate(lines, 1):
        # Track code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Skip non-claim lines
        if any(p.search(line) for p in SKIP_PATTERNS):
            continue

        for pattern in CLAIM_PATTERNS:
            for match in pattern.finditer(line):
                num_str = match.group(1).replace(",", "")
                try:
                    num_val = float(num_str)
                except ValueError:
                    continue

                # Check if this number appears in CLAIMS.md
                # Allow some tolerance for rounding
                found = False
                for claims_num in claims_numbers:
                    if claims_num == 0:
                        continue
                    ratio = abs(num_val - claims_num) / max(abs(claims_num), 1e-10)
                    if ratio < 0.01:  # Within 1%
                        found = True
                        break

                if not found:
                    # Check if the exact string appears in claims text
                    if match.group(0) in claims_text or num_str in claims_text:
                        found = True

                if not found:
                    rel_path = filepath.relative_to(REPO_ROOT)
                    rel_posix = rel_path.as_posix()
                    entry = {
                        "file": str(rel_path),
                        "line": line_num,
                        "claim": match.group(0),
                        "value": num_str,
                        "context": line.strip()[:120],
                    }
                    key = (rel_posix, match.group(0))
                    if key in KNOWN_PENDING:
                        entry["reason"] = KNOWN_PENDING[key]
                        pending.append(entry)
                    else:
                        issues.append(entry)

    return issues, pending


# Expected Where-slower figures from the HEAD L1 rerun artifact
# (benchmarks/results/2026-10-05_l1_rerun/l1_root_cause.json). Tolerances are
# display-rounding width: ratios/CIs to 0.01, medians to 0.005 ms.
L1_RERUN_FILE = (
    REPO_ROOT / "benchmarks" / "results" / "2026-10-05_l1_rerun" / "l1_root_cause.json"
)
L1_ROBUST_ROWS = {
    # (n_series, length, dist): (ratio, ci_lo, ci_hi, km_median_ms, numba_median_ms)
    (1, 100, "gaussian"): (1.78, 1.76, 1.80, 0.029, 0.016),
    (1, 100, "heavy_tailed"): (1.75, 1.74, 1.76, 0.029, 0.016),
    (1, 100, "random_walk"): (1.43, 1.42, 1.45, 0.029, 0.020),
}
L1_TEN_BY_500_RANGE = (0.85, 1.08)


def verify_l1_rerun(claims_text):
    """Check the CLAIMS.md Where-slower figures against the L1 rerun artifact.

    Returns a list of drift descriptions (empty when everything matches).
    """
    issues = []
    if not L1_RERUN_FILE.exists():
        return ["artifact missing: " + L1_RERUN_FILE.as_posix()]
    artifact = json.loads(L1_RERUN_FILE.read_text(encoding="utf-8"))
    rows = {(r["n_series"], r["length"], r["dist"]): r for r in artifact["loss_table"]}

    for key, (ratio, lo, hi, km_med, numba_med) in L1_ROBUST_ROWS.items():
        row = rows.get(key)
        if row is None:
            issues.append(f"loss-table row missing for {key}")
            continue
        a_lo, a_hi = row["ratio_ci95"]
        for label, got, want, tol in [
            ("ratio", row["ratio"], ratio, 0.01),
            ("ci_lo", a_lo, lo, 0.01),
            ("ci_hi", a_hi, hi, 0.01),
            ("km_median_ms", row["km_median_ms"], km_med, 0.005),
            ("numba_median_ms", row["numba_median_ms"], numba_med, 0.005),
        ]:
            if abs(got - want) > tol:
                issues.append(f"{key} {label}: artifact {got:.4f} vs CLAIMS {want}")
        for token in (f"{ratio:.2f}×", f"[{lo:.2f},{hi:.2f}]"):
            if token not in claims_text:
                issues.append(f"CLAIMS.md no longer states {token} for {key}")

    ratios_10x500 = [r["ratio"] for k, r in rows.items() if k[0] == 10 and k[1] == 500]
    if ratios_10x500:
        lo_want, hi_want = L1_TEN_BY_500_RANGE
        if abs(min(ratios_10x500) - lo_want) > 0.01 or abs(max(ratios_10x500) - hi_want) > 0.01:
            issues.append(
                "10×500 range drifted: artifact "
                f"{min(ratios_10x500):.2f}–{max(ratios_10x500):.2f} "
                f"vs CLAIMS {lo_want:.2f}–{hi_want:.2f}"
            )
    return issues


def main():
    claims_text = load_claims()
    claims_numbers = extract_numbers_from_claims(claims_text)

    l1_issues = verify_l1_rerun(claims_text)

    all_issues = []
    all_pending = []
    files_checked = 0

    for filepath in CHECK_FILES:
        filepath = Path(filepath)
        if filepath.exists():
            files_checked += 1
            issues, pending = check_file(filepath, claims_text, claims_numbers)
            all_issues.extend(issues)
            all_pending.extend(pending)

    print(f"Checked {files_checked} files against CLAIMS.md")
    print(f"Found {len(claims_numbers)} numeric values in CLAIMS.md")

    if all_pending:
        print(f"\n…  {len(all_pending)} claim(s) KNOWN-PENDING (tracked in CLAIMS.md):")
        for issue in all_pending:
            print(f"  {issue['file']}:{issue['line']}: {issue['claim']}")
            print(f"    → {issue.get('reason', 'tracked as pending')}")

    if all_issues:
        print(f"\n⚠  {len(all_issues)} claim(s) not traceable to CLAIMS.md:\n")
        for issue in all_issues:
            print(f"  {issue['file']}:{issue['line']}: {issue['claim']}")
            print(f"    → {issue['context']}")
            print()
        sys.exit(1)
    if l1_issues:
        print(f"\n⚠  {len(l1_issues)} Where-slower value(s) drifted from the L1 rerun artifact:\n")
        for issue in l1_issues:
            print(f"  {issue}")
            print()
        sys.exit(1)
    else:
        print("\n✓ All numeric claims are traceable to CLAIMS.md")
        sys.exit(0)


if __name__ == "__main__":
    main()
