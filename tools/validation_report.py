"""Generate the reference-validation report: max absolute error per feature.

Reuses the same numpy/scipy reference implementations the test suite asserts
against (`tests/test_features.py`), but reports the numbers instead of only
pass/fail -- so a reader can see *how* close the Rust core is, per feature,
rather than trusting a green checkmark.

Two things are checked per (feature, series) pair:
  * NaN agreement -- reference NaN must line up with library NaN. A mismatch is
    a contract violation (see the NaN policy in the README), not a tolerance
    question, so it is reported separately from numeric error.
  * Max absolute error over every series where both values are finite.

Usage:
    python tools/validation_report.py [--out validation-report.md]

Exits non-zero if any feature exceeds the tolerance or disagrees on NaN, so CI
fails loudly rather than publishing a report full of red rows.
"""

from __future__ import annotations

import argparse
import math
import os
import platform
import sys

import numpy as np

# The reference implementations live with the tests; importing them here keeps
# exactly one definition of ground truth in the repo.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))

import tsxtract  # noqa: E402
from test_features import SERIES, reference  # noqa: E402

ATOL = 1e-10
RTOL = 1e-9


def collect() -> dict[str, dict[str, object]]:
    """Per-feature max error and NaN-mismatch tally across every sample series."""
    names = tsxtract.feature_names()
    stats: dict[str, dict[str, object]] = {
        name: {
            "max_abs_err": 0.0,
            "worst_series": "-",
            "worst_scale": 0.0,
            "nan_mismatch": [],
            "compared": 0,
        }
        for name in names
    }

    for label, x in SERIES.items():
        got = dict(zip(names, tsxtract.extract_features([np.asarray(x, np.float64)])[0]))
        want = reference(x, level=got["mean"])
        for name in names:
            g, w = float(got[name]), float(want[name])
            entry = stats[name]
            if math.isnan(g) != math.isnan(w):
                entry["nan_mismatch"].append(label)  # type: ignore[union-attr]
                continue
            if math.isnan(g):
                continue
            entry["compared"] = int(entry["compared"]) + 1  # type: ignore[arg-type]
            err = abs(g - w)
            if err > float(entry["max_abs_err"]):
                entry["max_abs_err"] = err
                entry["worst_series"] = label
                entry["worst_scale"] = abs(w)
    return stats


def tolerance_ok(err: float, scale: float) -> bool:
    """Same test numpy.testing.assert_allclose applies: atol + rtol * |expected|."""
    return err <= ATOL + RTOL * scale


def render(stats: dict[str, dict[str, object]]) -> tuple[str, bool]:
    rows = []
    ok = True
    for name, entry in stats.items():
        err = float(entry["max_abs_err"])
        mismatch = entry["nan_mismatch"]
        if mismatch:
            verdict = f"NaN mismatch: {', '.join(mismatch)}"  # type: ignore[arg-type]
            ok = False
        elif not tolerance_ok(err, float(entry["worst_scale"])):
            verdict = "over tolerance"
            ok = False
        elif int(entry["compared"]) == 0:
            verdict = "NaN by contract on all sample series"
        elif err == 0.0:
            verdict = "bit-identical"
        else:
            verdict = "within tolerance"
        rows.append((name, entry, err, verdict))

    lines = [
        "# Reference-validation report",
        "",
        f"tsxtract {tsxtract.__version__} on {platform.platform()}, "
        f"Python {platform.python_version()}, numpy {np.__version__}.",
        "",
        f"Each of the {len(stats)} features is compared against a numpy/scipy "
        "reference implementation across "
        f"{len(SERIES)} sample series ({', '.join(SERIES)}), covering normal, "
        "trending, periodic, constant, two-element, single-element, and "
        "heavily-tied data.",
        "",
        f"Tolerance: atol={ATOL:g}, rtol={RTOL:g}. NaN must agree exactly -- the "
        "NaN policy is part of the API contract, so a NaN where a number was "
        "expected (or vice versa) fails regardless of tolerance.",
        "",
        "| feature | max abs error | worst-case series | series compared | verdict |",
        "|---|---:|---|---:|---|",
    ]
    for name, entry, err, verdict in rows:
        lines.append(
            f"| `{name}` | {err:.3e} | {entry['worst_series']} | "
            f"{entry['compared']}/{len(SERIES)} | {verdict} |"
        )
    lines += [
        "",
        "Rows reading *NaN by contract* are features that are undefined for "
        "every sample series in this matrix (none currently) -- they are still "
        "asserted to be NaN in both implementations.",
        "",
        ("**All features within tolerance.**" if ok else "**FAILURES above.**"),
        "",
    ]
    return "\n".join(lines), ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None, help="write the report here as Markdown")
    args = ap.parse_args()

    report, ok = render(collect())
    print(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"wrote {args.out}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
