# Phase 0 inventory — rename to Kymora (2026-10-04)

Branch: `refactor/rename-kymora` on top of `main` (6a9f308), tag `pre-rename`.
Note: `main` already contains the merged `refactor/tsxtract` work (merge-base == refactor tip), so no earlier refactor is redone.

## Tracked files

- Total tracked: **312** (see `file_classification.txt`).
- benchmarks: 118
- ci: 11
- config-root: 18
- docs: 40
- paper-patent(DO-NOT-TOUCH): 17
- scripts: 3
- site-landing: 60
- source-python: 6
- source-rust: 23
- tests: 15
- unknown: 1

## Sizes

```
count: 1992
size: 26.62 MiB
in-pack: 159
packs: 1
size-pack: 606.68 KiB
prune-packable: 0
garbage: 0
size-garbage: 0 bytes
```
- Files >1MB tracked: 0
  (none)

## Secrets scan (basic patterns, NOT a full gitleaks run)

- gitleaks/trufflehog: **not installed** in this environment (Get-Command found neither); used stdlib regex scan instead. Recommend owner run gitleaks in CI.
- Working tree: **no hits** for AWS/GH/PyPI/private-key/generic-secret patterns in tracked files.
- History (last 200 commits, pattern scan): 0 raw matches (often false positives in docs, e.g. env var names).

## Name occurrences (word-boundary, case-sensitive)

- `tsxtract-rs`: **116** hits in 52 files (detail: `name_occurrences.txt`)
- `tsxtractor`: **123** hits in 42 files (detail: `name_occurrences.txt`)
- `tsxtract`: **963** hits in 167 files (detail: `name_occurrences.txt`)
- `Tsxtract`: **302** hits in 86 files (detail: `name_occurrences.txt`)
- `TSXTRACT`: **36** hits in 18 files (detail: `name_occurrences.txt`)
- Note: counts overlap by construction (`tsxtract-rs` and `tsxtractor` both
  contain the substring `tsxtract` with a non-word boundary at `-`/end).
  The authoritative pre-rename file list is `name_occurrences.txt`.
- Note: `CLAUDE.md` (root agent instructions) was classed `unknown` by the
  script; it belongs to `config-root` (total config-root is 18 + CLAUDE.md).

## Canonical remote (record, do NOT decide)

```
origin	https://github.com/Aamodx6/Tsxtract.git (fetch)
origin	https://github.com/Aamodx6/Tsxtract.git (push)
```
- `origin` = `https://github.com/Aamodx6/Tsxtract.git` (only remote configured).
- README mixes accounts (counts across tree):
  - `Aamod007`: 12
  - `Aamodx6`: 71
  - `aamod007`: 4
  - `aamodx6`: 5
  - `aamoddev11`: 6
  - Decision stays NEEDS-OWNER (canonical account + fate of `Aamod007` byline/footer links).

## patent/ + paper/ (DO NOT TOUCH)

- `patent/` and `paper/` left exactly as-is; listed in NEEDS-OWNER (IP/publication decision belongs to owner).

## Pre-existing dirty state at branch time

```
 M .github/workflows/ci.yml
 M .github/workflows/release.yml
 M benchmarks/STATE.md
 M benchmarks/bench_matrix.py
 M benchmarks/results/LOSS_LEDGER.md
 M tests/test_invariants.py
?? benchmarks/results/2026-10-04_gate_audit/
?? benchmarks/results/B3_REPORT.md
?? benchmarks/results/COMPETITOR_REPORT.md
?? benchmarks/results/L1_ROOT_CAUSE.md
?? benchmarks/results/env.json
?? benchmarks/results/l1_root_cause.json
?? benchmarks/results/latency.jsonl
?? benchmarks/results/memory.jsonl
?? benchmarks/results/scaling.jsonl
?? benchmarks/results/sliding.jsonl
?? benchmarks/results/startup.jsonl
?? benchmarks/results/streaming.jsonl
?? benchmarks/results/throughput.jsonl
?? benchmarks/results/throughput_competitors.jsonl
?? docs/refactor/rename-kymora/
```
- `M` files are uncommitted B-track/doc-link work (arch_max→arch.md refs, CI python matrix, LOSS_LEDGER append); untracked `benchmarks/results/*` are run outputs that must stay untracked. Left untouched by Phase 0.
