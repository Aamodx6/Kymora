# CLEANUP_STATUS.md — repo cleanup + folder reorganization

Branch: `chore/repo-cleanup` (do not push, do not merge).
Backup: tag `pre-cleanup` + branch `backup/pre-cleanup` (both created, verified).
Base note: brief said branch from `hardening/kymora-v-next`, but local `main`
is `hardening/kymora-v-next` + 3 CI fixes (`67fd6e8`, `5e9ffbb`, `9b9e104`,
tagged `v0.8.0`). Cleanup branches from `main` so those fixes are kept.
Tracked tree at start: clean (`git diff` / `git diff --cached` empty; only
18 untracked paths present, all regenerable scratch — none committed).

Golden guard: `git diff pre-cleanup -- tests/golden` must stay empty (checked
after every tracked-file commit).

Gate-expectation conflict (owner note): task brief says pytest `279 passed,
1 skipped`; `CLAUDE.md` says `138 passed, 0 warnings`. Baseline gate run in
Phase 2 will establish which is true on this tree.

## Phase 1 — MEASURE (2026-10-05, no deletions made)

### 1. Top-level sizes (working dir, recursive incl. ignored)

| Entry | Type | Size |
|---|---|---|
| target/ | DIR (ignored `/target`) | 4423.7 MB |
| benchmarks/ | DIR (mixed) | 961.9 MB |
| fuzz/ | DIR (mixed) | 542.9 MB |
| .mypy_cache/ | DIR (not in root .gitignore) | 99.0 MB |
| landing/ | DIR (mixed) | 77.0 MB |
| .git/ | DIR | 64.4 MB |
| site/ | DIR (ignored `site/`) | 4.7 MB |
| paper/ | DIR (tracked) | 1.3 MB |
| .hypothesis/ | DIR (ignored) | 1.2 MB |
| dist/ | DIR (ignored `dist/`) | 0.6 MB |
| tests/ | DIR (tracked) | 0.6 MB |
| docs/ | DIR (tracked) | 0.4 MB |
| src/ | DIR (tracked) | 0.3 MB |
| .gstack/ | DIR (ignored) | 0.1 MB |
| tools/ | DIR (tracked) | 0.1 MB |
| python/ | DIR (tracked) | 0.0 MB |
| .github/ | DIR (tracked) | 0.0 MB |
| patent/ | DIR (tracked, FROZEN) | 0.0 MB |
| .pytest_cache/ | DIR (ignored) | 0.0 MB |
| proptest-regressions/ | DIR (untracked) | 0.0 MB |
| root files (arch.md, CHANGELOG.md, README.md, Cargo.lock, …) | FILEs | <0.1 MB total |

Working-dir total ≈ **6178 MB (~6.0 GiB)**: untracked/ignored **6172.7 MB**
(42555 files, includes `.git/`) + tracked **5.7 MB** (357 files).

### 2. Top directories (recursive, MB)

| Size | Path |
|---|---|
| 4423.7 | target/ (debug 3751.4 — incremental 2412.6, deps 1147.6; release 611.0) |
| 910.3 | benchmarks/.venvs/ (sktime 429.9, antropy 300.7, tsflex 179.8) |
| 611.0 | target/release/ |
| 542.9 | fuzz/target/ (= fuzz/target/debug) |
| 429.9 | benchmarks/.venvs/sktime/ |
| 300.7 | benchmarks/.venvs/antropy/ |
| 179.8 | benchmarks/.venvs/tsflex/ |
| 143.6 | target/debug/build |
| 99.0 | .mypy_cache/ |
| 74.4 | landing/node_modules/ |
| 64.4 | .git/ |
| 53.3 | target/wheels/ (13 stale wheels + sdist tarballs, largest 40.2 MB) |
| 50.2 | benchmarks/results/ (of which `equal_feature_run.log` = 47.1 MB) |
| 4.7 | site/ (mkdocs output: assets 2.4, refactor 0.6, search 0.3, …) |
| 1.3 | landing/dist/ |
| 1.2 | .hypothesis/ |
| 1.2 | paper/figures/ |

No other directory exceeds 1 MB. `docs/`, `src/`, `tests/`, `tools/`,
`python/`, `patent/` are all <1 MB.

### 3. Top files (all untracked/ignored, MB)

| Size | Path |
|---|---|
| 114.79 | benchmarks/.venvs/sktime/…/llvmlite/binding/llvmlite.dll |
| 114.79 | benchmarks/.venvs/antropy/…/llvmlite/binding/llvmlite.dll |
| 70.61 | fuzz/target/debug/deps/lib_core.rlib |
| 70.37 | target/debug/deps/lib_core.rlib |
| 50.79 | target/debug/deps/_core-9404ac6c556f017c.pdb |
| 50.28 | target/debug/deps/_core-7a4a744623f2dbc1.pdb |
| **47.13** | **benchmarks/results/equal_feature_run.log (UNTRACKED stray log)** |
| 45.33 | target/debug/deps/_core-271aa150dc37edbe.pdb |
| 40.75 | target/debug/deps/_core.pdb |
| 38.36 | target/wheels/tsxtract_rs-0.3.0.tar.gz |
| 36.40 | benchmarks/.venvs/sktime/…/numpy.libs/…openblas….dll |
| 36.28 | target/debug/deps/libproptest-*.rlib |
| 35.27 | fuzz/target/debug/deps/_core.pdb |
| 32.55 | target/debug/_core.pdb |
| 32.46…22.81 | ~15 more `_core-*.pdb` + `dep-graph.bin` files (22–32 MB each) |
| 1.68 | benchmarks/results/streaming.jsonl (UNTRACKED stray output) |
| 0.58 | benchmarks/results/throughput_competitors.jsonl (UNTRACKED) |
| 0.26 | benchmarks/results/env.json (UNTRACKED) |

### 4. Tracked tree (357 files, 5.7 MB total)

Largest tracked files — **none exceeds 1 MB, no tracked dir exceeds 5 MB**
(Phase 3.1 triage therefore trivially passes; full list below for the record):

| Size | Path |
|---|---|
| 0.56 | benchmarks/results/2026-10-05_streaming/streaming.jsonl |
| 0.52 | benchmarks/agreement/agreement_matrix.json |
| 0.36 | landing/public/figures/architecture.png (= paper/figures/architecture.png, same sha256) |
| 0.36 | paper/figures/architecture.png |
| 0.25 | paper/figures/scaling.png (= landing copy) |
| 0.25 | landing/public/figures/scaling.png |
| 0.15 | paper/figures/speedup.png (= landing copy) |
| 0.15 | landing/public/figures/speedup.png |
| 0.14 | landing/public/figures/memory.png (= paper copy) |
| 0.14 | paper/figures/memory.png |
| 0.13 | benchmarks/results/l1_root_cause.json (protected evidence) |
| 0.09 | landing/package-lock.json |
| 0.09 | docs/parity_matrix.md |
| 0.09 | landing/public/figures/throughput.png (= paper copy) |
| 0.09 | paper/figures/throughput.png |

Duplicate-image note: all 5 paper figures are byte-identical in
`landing/public/figures/` (verified `architecture.png` hash
`EE29385A…7383C2` both sides). Paper PDFs (`architecture.pdf` 72 KB etc.)
are tracked build outputs of `paper/main.tex` — owner decision needed
(Phase 3).

### 5. `.git` analysis (no history rewrite; gc only)

- `git count-objects -vH`: 3251 loose objects, **63.69 MiB**; pack: 159
  objects, 606.68 KiB.
- Top blobs by `git rev-list --objects --all | git cat-file --batch-check`
  are all <10 KB (`benches/bench_libraries.py`, `select.py`, docs). **No
  large historical blob** — the 64 MB is loose-object bloat (shallow/old
  garbage), not committed large files. `git gc --prune=now` after backup
  should reclaim most of it. No filter-repo needed; nothing to record in
  OWNER_DECISIONS.md on that front.

### 6. Classification + expected savings

| Bucket | Entries | Size | Action | Expected saving |
|---|---|---|---|---|
| REGENERABLE | target/ (debug+release+doc) | 4423.7 MB | delete, rebuild via cargo/maturin `--release` | ~4424 MB |
| REGENERABLE | target/wheels/ (13 stale wheels/sdists) | 53.3 MB | delete (release rebuilds) | ~53 MB |
| REGENERABLE | fuzz/target/ | 542.9 MB | delete, rebuild via cargo | ~543 MB |
| REGENERABLE | benchmarks/.venvs/ (sktime/antropy/tsflex) | 910.3 MB | delete AFTER documenting recreate cmd (`python benchmarks/setup_venvs.py --lib all`; already exists — verify in Phase 2) | ~910 MB |
| REGENERABLE | landing/node_modules/ | 74.4 MB | delete, `npm ci` rebuilds | ~74 MB |
| REGENERABLE | landing/dist/ + landing/.vercel/ | 1.3 MB | delete, `npm run build` rebuilds | ~1 MB |
| REGENERABLE | site/ (mkdocs output) | 4.7 MB | delete, `python -m mkdocs build` rebuilds | ~5 MB |
| REGENERABLE | .mypy_cache/ | 99.0 MB | delete, mypy rebuilds | ~99 MB |
| REGENERABLE | .hypothesis/, .pytest_cache/, __pycache__/ | ~1.7 MB | delete | ~2 MB |
| REGENERABLE | dist/ (*.whl) | 0.6 MB | delete, maturin rebuilds | ~1 MB |
| REGENERABLE (stray) | benchmarks/results/*.log + root-level *.jsonl (untracked, NOT frozen evidence) | ~51 MB (`equal_feature_run.log` 47.1 alone) | delete after confirming untracked + unreferenced | ~51 MB |
| FROZEN EVIDENCE | benchmarks/results/ tracked (64 files, incl. L1_ROOT_CAUSE.md, l1_root_cause.json, B3_REPORT.md, F1_REPORT.md, EQUAL_FEATURE_REPORT.md, STREAMING_PUSH_REPORT.md) | ~1 MB | NEVER touch | 0 |
| SOURCE/DOCS | src/, python/, tests/, docs/, tools/, paper/*.tex, landing/src+public, .github/, root docs | ~5 MB | keep, reorganize only (Phase 4) | 0 |
| PROTECTED | tests/golden/, patent/, LICENSE, CITATION.cff, SECURITY.md, Cargo.lock, perf_gate baselines | — | NEVER touch | 0 |
| GC-ABLE | .git loose objects | ~63 MB | `git gc --prune=now` (backup exists) | ~50–60 MB |
| UNSURE (owner) | see list below | <0.1 MB | do not touch in cleanup | 0 |

**Expected working-dir saving: ~6100 MB (~99%) → final ≈ 70–80 MB**
(.git after gc + tracked 5.7 MB + site/ only when built).

### 7. UNSURE (owner decides) — nothing deleted, sizes recorded

1. `benchmarks/suites/concurrency.py` + `_conc_spawn_child.py` (untracked,
   new B3 suite, docstring cites `arch.md §11.5`). Keep-or-commit decision —
   looks like in-progress work, not scratch. Not deleted.
2. `benchmarks/results/` root-level untracked `env.json`, `latency.jsonl`,
   `memory.jsonl`, `scaling.jsonl`, `sliding.jsonl`, `startup.jsonl`,
   `streaming.jsonl` (1.68 MB), `throughput.jsonl`,
   `throughput_competitors.jsonl`, `remeasure_run.log`, `startup_run.log`,
   `2026-10-04_gate_audit/` — stray suite outputs vs intentional evidence?
   Proposed: delete (regenerable), but owner confirms none is cited.
3. `fuzz/Cargo.lock` (untracked, cargo-generated; root Cargo.lock is the
   protected one). Proposed: leave untracked + gitignore it.
4. `proptest-regressions/proptest_checks.txt` (387 B, untracked). Proposed:
   commit or ignore — defers to owner.
5. `paper/figures/*.pdf` (tracked, ~178 KB total, build outputs of
   `main.tex` via `generate_figures.py`). Proposed: keep (paper builds need
   them) — owner confirms.
6. `landing/public/figures/*.png` duplicates of `paper/figures/*.png`
   (~1 MB). Proposed: keep both (different deploy targets) — owner confirms.
7. `Makefile` advertises `clean` in `.PHONY` but defines no `clean` target.
   Phase 5 will add real `clean`/`distclean`/`dev`.

## Phase 2 — PENDING (no deletions yet)

Dry-run + execute per §2, then `make clean`/`distclean`/`dev`, then full
gate set. Baseline gate results to be recorded here before purging.

### Archive (adjustment A, 2026-10-06)

Before any untracked deletion, all untracked NON-regenerable items were
zipped (regenerable bulk — target/, fuzz/target/, .venvs/, node_modules/,
caches — deliberately excluded):

- Path: `F:\Active Repo\kymora-archive-2026-10-06.zip` (outside the repo)
- Size: 581213 bytes (0.55 MB)
- SHA256: `FFD1CD664BB35A5F2BCC6E71FE85D0CBF1DCA2C014A03741EE499DA4867F336D`
- Contents: `benchmarks/results/` untracked items only
  (`2026-10-04_gate_audit/`, `env.json`, `equal_feature_run.log`,
  `latency.jsonl`, `memory.jsonl`, `remeasure_run.log`, `scaling.jsonl`,
  `sliding.jsonl`, `startup.jsonl`, `startup_run.log`, `streaming.jsonl`,
  `throughput.jsonl`, `throughput_competitors.jsonl`) + `fuzz/Cargo.lock`
  + `proptest-regressions/proptest_checks.txt`.

### Gate baseline (adjustment D, 2026-10-06, commits through `dd7129e`)

Gate-expectation conflict resolved: brief was right, CLAUDE.md was stale
(fixed to `279 passed, 1 skipped` + cargo `30 passed` + `sklearn.py`
listing; `arch.md` reference left for the Phase 4 move).

| Gate | Result |
|---|---|
| pytest tests -q | 279 passed, 1 skipped (140 s) ✅ |
| cargo test --no-default-features | 30 passed ✅ |
| cargo clippy -D warnings | clean ✅ |
| cargo fmt --check | clean ✅ |
| mkdocs build --strict | built in 2.83 s ✅ |
| tools/check_claims.py | 16 files, 70 values, all traceable ✅ |
| tools/gen_feature_docs.py --check | current ✅ |
| tools/validation_report.py | all features within tolerance ✅ |
| tools/check_snippets.py | 22 executed, 16 skipped, 0 failed ✅ |
| mypy python/kymora | no issues, 5 files ✅ |
| feature_names() sha256 | `8a1e27…31af2e` match ✅ |
| git diff pre-cleanup -- tests/golden | empty ✅ |
| tools/perf_gate.py | ⚠️ AMBER (environmental): 3 runs failed at ratio 1.09/1.44/2.07 with CV 0.08–0.33; box under 70–80% background CPU (IDEs/browsers) and `src/`+`python/`+manifests are byte-identical to pre-cleanup, so a genuine hot-path regression is impossible. Re-run on quiet CI before merge. |

Wheel rebuilt from current tree (`maturin build --release`, reinstalled
`kymora-0.8.0-cp310-abi3-win_amd64.whl`) before the pytest run.

### .gitignore note (adjustment E)

`.gstack/` was already ignored (line 13) — no change needed. Added
`.mypy_cache/` and `fuzz/Cargo.lock`. Full rewrite deferred to Phase 5.

## Phase 3 — PENDING

Tracked-file triage: vacuously clean (>1 MB: none; >5 MB dirs: none).
Remaining work: paper-PDF decision, root-file moves (Phase 4), `git gc`.

## Phase 4 — PENDING (path map CLEANUP_MOVES.tsv to be written first)

## Phase 5 — PENDING

---
*Phase 1 complete. No file deleted, no tracked file modified. Next: commit
this report, then Phase 2 dry-run.*
