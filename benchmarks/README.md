# Benchmarks

Suites live in `suites/` (one script per benchmark area), shared harness code
in `harness/`, competitor adapters in `adapters/`.

## Competitor virtualenvs (regenerable, git-ignored)

`sktime`, `antropy`, and `tsflex` each get an isolated venv under
`.venvs/` so competitor dependencies never pollute the main environment.
The directory is git-ignored and safe to delete at any time; recreate with:

```bash
python benchmarks/setup_venvs.py --lib all
# or a single competitor: python benchmarks/setup_venvs.py --lib sktime
```

This runs `uv venv .venvs/<lib> --python 3.12` then
`uv pip install -r benchmarks/requirements-<lib>.txt` for each of
`antropy`, `tsflex`, `sktime` (see `COMPETITORS` in `setup_venvs.py`).

## Running suites

```bash
make bench-smoke       # Phase B0 smoke test on all adapters
make bench-agreement   # Phase B1 feature agreement & parity matrix
make bench-all         # Full benchmark matrix (Phases B1-B5)
make report            # REPORT.md + results.json from latest run
```

## Results

`results/` contains **frozen evidence** (tracked in git — never delete or
regenerate in place): `L1_ROOT_CAUSE.md`, `l1_root_cause.json`,
`B3_REPORT.md`, `F1_REPORT.md`, `EQUAL_FEATURE_REPORT.md`,
`STREAMING_PUSH_REPORT.md`, plus the dated run directories cited by
`CLAIMS.md`. Stray `*.log` / root-level `*.jsonl` outputs are scratch:
re-runnable via the suites above.
