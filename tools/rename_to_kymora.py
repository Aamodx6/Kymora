"""One-shot rename tsxtract -> Kymora (content only; file moves done via git mv).

Usage:
    python tools/rename_to_kymora.py --dry-run   # report only
    python tools/rename_to_kymora.py --apply      # rewrite files

Rules (ordered, specific-first, word-boundary, case-sensitive):
    tsxtract-rs -> kymora-rs
    TsxError    -> KymoraError
    TsxSelector -> KymoraSelector
    tsxtract    -> kymora
    Tsxtract    -> Kymora
    TSXTRACT    -> KYMORA

Skipped (frozen evidence / history / foreign IP / generated lock data):
    docs/internal/refactor/**, benchmarks/results/**, benchmarks/report/**,
    paper/**, patent/**, CHANGELOG.md, tests/golden/**, tests/fixtures/**,
    benchmarks/adapters/tsxtract_jax.py/.md (JAX-collision docs, hand-edited),
    Cargo.lock (cargo regenerates), landing/package-lock.json,
    target/**, dist/**, node_modules/**, site/**, __pycache__.

`tsxtract` (single deprecated shim; the older `tsxtractor` alias was deleted
outright per owner direction) and `tsxtract_jax` (JAX collision marker)
are intentionally NOT matched: `_`/letters after `tsxtract` block the
word-boundary rule, and no explicit rule targets them.
JAX-context sentences (bare-PyPI-name notes) are fixed by hand afterwards;
this script prints every touched file for that review.
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RULES = [
    ("tsxtract-rs", "kymora-rs"),
    ("TsxError", "KymoraError"),
    ("TsxSelector", "KymoraSelector"),
    ("tsxtract", "kymora"),
    ("Tsxtract", "Kymora"),
    ("TSXTRACT", "KYMORA"),
]
RXS = [(re.compile(r"(?<![A-Za-z0-9_])" + re.escape(a) + r"(?![A-Za-z0-9_])"), b) for a, b in RULES]

SKIP_PREFIXES = (
    "docs/internal/refactor/", "benchmarks/results/", "benchmarks/report/",
    "paper/", "patent/", "tests/golden/", "tests/fixtures/",
    "target/", "dist/", "node_modules/", "site/",
)
SKIP_FILES = {
    "CHANGELOG.md", "Cargo.lock", "landing/package-lock.json",
    "benchmarks/adapters/tsxtract_jax.py", "benchmarks/adapters/tsxtract_jax.md",
    # B-track evidence / audit trail: lib id `tsxtract` in these rows is data.
    "docs/internal/refactor/REFACTOR_STATE.md", "benchmarks/STATE.md",
    "benchmarks/agreement/AGREEMENT_REPORT.md", "benchmarks/zenith_baseline.md",
    "benchmarks/requirements-jax-collision.txt",
}

# Pass 2: identifiers the word-boundary pass could not cover. Each entry is
# (files, compiled-regex, replacement). The `tsx` pattern excludes a
# preceding dot so `Hero.tsx`-style filenames never match.
PASS2 = [
    (["python/kymora/tune.py", "docs/internal/arch.md", "docs/api.md", "docs/quickstart.md",
      "landing/src/docs/content/api-reference.md",
      "landing/src/docs/content/configuration.md"],
     r"(?<![A-Za-z0-9_])TSXTRACT_", "KYMORA_"),
    (["benchmarks/suites/make_b3_report.py"],
     r"(?<![A-Za-z0-9_])TSXTRACT_LIB(?![A-Za-z0-9_])", "KYMORA_LIB"),
    (["benchmarks/suites/agreement.py", "benchmarks/suites/latency.py",
      "benchmarks/suites/scaling.py", "benchmarks/suites/throughput.py"],
     r"(?<![A-Za-z0-9_])TsxtractAdapter(?![A-Za-z0-9_])", "KymoraAdapter"),
    (["benchmarks/bench_libraries.py"],
     r"(?<![A-Za-z0-9_])bench_tsxtractor(?![A-Za-z0-9_])", "bench_kymora"),
    (["benchmarks/bench_ucr_downstream.py"],
     r"(?<![A-Za-z0-9_])extract_tsxtractor(?![A-Za-z0-9_])", "extract_kymora"),
    (["README.md", "landing/src/docs/content/sklearn-pipelines.md"],
     r"(?<![A-Za-z0-9_])TsxtractTransformer(?![A-Za-z0-9_])", "KymoraTransformer"),
    # Conventional snippet alias tsx -> km (user-facing docs + site + arch API).
    (["README.md", "docs/internal/arch.md", "landing/src/components/Hero.tsx",
      "landing/src/components/HowItWorks.tsx"],
     r"(?<![A-Za-z0-9_.])tsx(?![A-Za-z0-9_])", "km"),
    # Benchmark-local tsx vars/params/labels -> km (internal only).
    (["benchmarks/suites/agreement.py", "benchmarks/suites/l1_root_cause.py",
      "benchmarks/suites/latency.py", "benchmarks/suites/scaling.py",
      "benchmarks/suites/throughput.py", "benchmarks/suites/memory.py",
      "benchmarks/suites/make_b3_report.py",
      "benchmarks/suites/make_competitor_report.py"],
     r"(?<![A-Za-z0-9_.])tsx(?![A-Za-z0-9_])", "km"),
]


# Pass 3 (owner-directed 2026-10-04): bare `kymora` everywhere, no `-rs`
# suffix. Bare `kymora` is FREE on PyPI/crates.io/npm per the Phase 1
# check, so the dist, import, and wheel all use the plain name.
PASS3 = [
    (r"(?<![A-Za-z0-9_])kymora-rs(?![A-Za-z0-9_])", "kymora"),
    (r"(?<![A-Za-z0-9_])kymora_rs(?![A-Za-z0-9_])", "kymora"),
    (r"(?<![A-Za-z0-9_])Kymora-rs(?![A-Za-z0-9_])", "Kymora"),
]


def run_pass3(apply):
    grand, files = 0, 0
    for f in tracked_files():
        if not eligible(f):
            continue
        p = os.path.join(ROOT, f)
        try:
            with io.open(p, "r", encoding="utf-8", newline="") as fh:
                text = fh.read()
        except (UnicodeDecodeError, OSError):
            continue
        total = 0
        for pat, repl in PASS3:
            rx = re.compile(pat)
            n = len(rx.findall(text))
            if n:
                text = rx.sub(repl, text)
                total += n
        if total:
            grand += total
            files += 1
            print(f"{total:5d}  {f}")
            if apply:
                with io.open(p, "w", encoding="utf-8", newline="") as fh:
                    fh.write(text)
    print(f"--- pass3: {grand} replacements in {files} files "
          f"({'APPLIED' if apply else 'DRY RUN'})")


def run_pass2(apply):
    grand = 0
    for files, pat, repl in PASS2:
        rx = re.compile(pat)
        for f in files:
            p = os.path.join(ROOT, f)
            try:
                with io.open(p, "r", encoding="utf-8", newline="") as fh:
                    text = fh.read()
            except OSError:
                print(f"  MISSING  {f}")
                continue
            n = len(rx.findall(text))
            if n:
                grand += n
                print(f"{n:5d}  {f}  [{pat} -> {repl}]")
                if apply:
                    with io.open(p, "w", encoding="utf-8", newline="") as fh:
                        fh.write(rx.sub(repl, text))
    print(f"--- pass2: {grand} replacements ({'APPLIED' if apply else 'DRY RUN'})")


def tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    return [f.replace("\\", "/") for f in out.stdout.splitlines() if f.strip()]


def eligible(f):
    if f in SKIP_FILES:
        return False
    if f.startswith(SKIP_PREFIXES):
        return False
    if "__pycache__" in f:
        return False
    return True


def process(apply):
    changed = {}
    for f in tracked_files():
        if not eligible(f):
            continue
        p = os.path.join(ROOT, f)
        try:
            with io.open(p, "r", encoding="utf-8", newline="") as fh:
                text = fh.read()
        except (UnicodeDecodeError, OSError):
            continue
        total = 0
        per_rule = {}
        for rx, b in RXS:
            n = len(rx.findall(text))
            if n:
                text = rx.sub(b, text)
                total += n
                per_rule[next(a for a, bb in RULES if bb == b)] = n
        if total:
            changed[f] = per_rule
            if apply:
                with io.open(p, "w", encoding="utf-8", newline="") as fh:
                    fh.write(text)
    return changed


def main():
    if "--apply-pass2" in sys.argv:
        run_pass2(apply=True)
        return
    if "--dry-run-pass2" in sys.argv:
        run_pass2(apply=False)
        return
    if "--apply-pass3" in sys.argv:
        run_pass3(apply=True)
        return
    if "--dry-run-pass3" in sys.argv:
        run_pass3(apply=False)
        return
    apply = "--apply" in sys.argv
    changed = process(apply)
    grand = 0
    for f in sorted(changed):
        n = sum(changed[f].values())
        grand += n
        detail = ", ".join(f"{k}:{v}" for k, v in changed[f].items())
        print(f"{n:5d}  {f}  [{detail}]")
    print(f"--- {len(changed)} files, {grand} replacements ({'APPLIED' if apply else 'DRY RUN'})")


if __name__ == "__main__":
    main()
