# Authoritative Linux 16-vCPU benchmark run — PLAN (not yet executed)

Purpose: replace the exploratory i7-13620H laptop numbers (`CLAIMS.md`,
`F1_REPORT.md`) with authoritative figures from a 16-vCPU Linux runner
(arch.md §14.1: cloud runs are worded "16 vCPU"). Re-runs the exact F1 +
3b protocol. DO NOT improvise — follow the steps verbatim and commit the
artifacts.

## Machine

- Any 16-vCPU x86_64 Linux box (cloud VM or larger CI runner), Ubuntu
  22.04+, Python 3.12, Rust stable, ~30 GB free (target/ + venvs).
- Record: `nproc`, `lscpu`, kernel, governor
  (`cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor` — want
  `performance`), cloud instance type / runner label.

## Setup (exact commands)

```bash
git clone https://github.com/Aamodx6/Kymora.git && cd Kymora
git checkout <main-tip-at-run-time>   # record the SHA in the report
python3.12 -m venv .venv && . .venv/bin/activate
python -m pip install --upgrade pip maturin
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
export PATH="$HOME/.cargo/bin:$PATH"
python -m pip install -e ".[bench]"   # numpy/pandas/tsfresh/pycatch22/tsfel/…
maturin develop --release             # HEAD wheel, editable
python -m pytest tests/ -q            # sanity: 138 passed before timing
# Isolated version venvs (mirror of the laptop bisect):
for v in v032 v040 vPRE vHEAD; do python3.12 -m venv --system-site-packages "/tmp/venvs/$v"; done
/tmp/venvs/v032/bin/python -m pip install --no-deps tsxtract-rs==0.3.2
/tmp/venvs/v040/bin/python -m pip install --no-deps tsxtract-rs==0.4.0
/tmp/venvs/vPRE/bin/python -m pip install --no-deps <pre-refactor-wheel>  # build via: git worktree + maturin build --release
/tmp/venvs/vHEAD/bin/python -m pip install --no-deps <head-wheel>        # target/wheels/kymora-*.whl
```

Notes: 0.3.2 ships no manylinux wheel → its sdist builds against the
Rust toolchain installed above (takes ~2 min). Verify each venv before
measuring: `<venv>/bin/python -c "import tsxtract,tsxtractor"` must
resolve inside the venv (0.3.2 has NO `tsxtract` name — use the
`tsxtractor` fallback path; see F1_REPORT.md §3b for the franken-import
trap and the direct-probe workaround).

## Measurement protocol (in this order, no deviations)

1. `python benchmarks/suites/scaling.py` threads=1 cell only
   (single-thread cost — compare against the laptop's 12.163 µs/series).
2. F1 interleave with the stock suite (full, incl. slow competitors):
   PRE → HEAD → PRE → HEAD, results dirs `L16_F1_{P1,H1,P2,H2}/`.
3. Bisect, rotated: R1 `032probe,040,PRE,HEAD` → R2 `PRE,HEAD,040,032probe`;
   0.3.2 via the direct probe (5 warmup + 100 timed, same 1k×500 f64
   seed-42 input), others via the stock suite.
4. Direct-probe methodology-control set on all four venvs, rotated twice.
5. Pool runs per version (concatenate `runs` arrays), report median /
   best / 95% bootstrap CI of the median (20k resamples), per-feature
   µs, raw + per-feature ratios — same arithmetic as `F1_REPORT.md` §3c.

Driver pattern per suite round (from the repo root, so the harness
resolves while `sys.executable` stays the venv python):

```bash
<venv>/bin/python -c "
from pathlib import Path
from benchmarks.suites.reproduce_readme import run_readme_reproduce
run_readme_reproduce(results_dir=Path('benchmarks/results/L16_<VER>_R<n>'))"
```

## Estimated runtime (from laptop timings)

| Step | Laptop-measured basis | Linux est. |
|---|---|---|
| Setup (clone, toolchain, venvs, 2 local wheel builds, installs, pytest) | ~15 min on laptop | ~15 min |
| 4× F1 suite rounds (kymora 100 runs + catch22 + tsfel + tsfresh) | ~3 min/round | ~12 min |
| 6× bisect suite rounds | ~3 min/round | ~18 min |
| Probes (100 timed runs each, ~10 total incl. control sets) | ~40 s each | ~7 min |
| Scaling threads=1 cell + analysis + report | — | ~10 min |
| **Total** | | **~60–75 min wall** |

## Outputs (commit all of these, then update README/CLAIMS.md from them only)

- `benchmarks/results/L16_*/` (jsonl + env.json per round), probe JSONs,
  `L16_REPORT.md` (same sections as `F1_REPORT.md` + single-thread cell),
  `L16_SUMMARY.json`.
- Regenerate `landing/public/figures/throughput.png` (+ scaling/memory
  figures) from the new numbers; drop the "exploratory" labels the new
  numbers replace; keep per-round env.json as the hardware caption source.
- Promote `CLAIMS.md` rows from exploratory → authoritative; retire the
  laptop rows to the superseded list (do not delete — stale copies
  circulate).
