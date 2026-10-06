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
| root files (docs/internal/arch.md, CHANGELOG.md, README.md, Cargo.lock, …) | FILEs | <0.1 MB total |

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
are tracked build outputs of the legacy draft (now `paper/legacy/main.tex`) — resolved
in Phase 4 task G (moved to `paper/legacy/` with its PDFs).

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
   new B3 suite, docstring cites `docs/internal/arch.md §11.5`). Keep-or-commit decision —
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
5. `paper/figures/*.pdf` (tracked, ~178 KB total, build outputs of the legacy
   draft). Resolved in Phase 4 task G: moved to `paper/legacy/` with
   `main.tex` + `generate_figures.py`; PNGs kept in place (duplicates in
   `landing/` kept per owner decision).
6. `landing/public/figures/*.png` duplicates of `paper/figures/*.png`
   (~1 MB). Proposed: keep both (different deploy targets) — owner confirms.
7. `Makefile` advertises `clean` in `.PHONY` but defines no `clean` target.
   Phase 5 will add real `clean`/`distclean`/`dev`.

## Phase 2 — DONE (2026-10-06, commit `87320ea` + purge below)

`make clean` / `distclean` / `dev` added to Makefile (bulk paths only;
`benchmarks/results/` deliberately excluded to protect frozen evidence).
`make` binary is absent on this Windows box, so every recipe was executed
by hand in order: distclean-equivalent → dev-equivalent → full gates.

Dry-run (all untracked/ignored, zero tracked — `git clean -ndx` preview +
per-path `git ls-files` check; `.benchmarks/` + `tools/__pycache__` absent):
site/ 4.7, dist/ 0.6, target/wheels/ 53.3, target/test_wheel/ 3.8,
.pytest_cache/ ~0, .hypothesis/ 1.2, .mypy_cache/ 99.0, 5×__pycache__ ~0.7,
target/ 4530.9, fuzz/target/ 542.9, benchmarks/.venvs/ 910.3,
landing/node_modules/ 74.4, landing/dist/ 1.3, 13 results strays ~49.2
(`equal_feature_run.log` 47.1 dominates; all archived per §A).
Executed via `git clean -fdx -- <explicit paths>` (≈6215 MB unique).

`make dev` equivalent: `setup_venvs.py --lib all` recreated antropy/sktime/
tsflex (uv), `npm ci` restored landing/node_modules, `maturin build
--release` + reinstall → `kymora 0.8.0, 33 features`. Full gates re-run
after dev: pytest 279 passed 1 skipped (one flaky warning on first
post-rebuild run, clean on the next two — timing artifact, not code),
cargo 30, clippy/fmt/mkdocs/claims/feature-docs/validation/snippets/mypy
green, golden sha `8a1e27…31af2e`, golden diff empty.

Working dir: ~6178 MB → ~10 MB excl. `.git` (tracked 5.7 MB + live
`.gstack/` + rebuilt `site/`? no — site/ only on mkdocs build; current
10 MB is tracked + `.gstack/` + fresh build outputs pending next build).
`.git`: 63.8 MB loose → plain `git gc --prune=now` → 6.0 MB packed
(no reflog expire, no --aggressive, per orders; before/after from
`git count-objects -vH`: 63.76 MiB/3298 loose → 5.85 MiB packed).

### Deferred (not on this branch)

- perf_gate: never green on this box (70–80% background CPU; ratios
  1.09–2.07, CV up to 0.33; `src/`+`python/` byte-identical to pre-cleanup).
  Deferred to quiet CI. The CI branch's nightly.yml runs the gate 3× with
  issue-filing — that is the authoritative check before merge.
- Task I (figure hash-equality assertion) + Phase 5.2 (check_repo_hygiene +
  CI job): `tools/check_repo_hygiene.py` lives on chore/ci-restructure.
  Both deferred to the CI branch after rebase (incl. root-file allowlist
  update for the Phase 4 moves).
- Phase 5.3 READMEs (tools/, docs/internal/) + CONTRIBUTING map: pending,
  post-Phase-4.

## Phase 4 — PROPOSED (moves NOT executed; owner review required)

Full old→new map: `CLEANUP_MOVES.tsv` (43 MOVEs via `git mv`, ~30 REWRITEs,
KEEP list with rationale). Workflow-refs column: **zero** `.github/`
references to any moved path on this branch (verified by grep) — the CI
branch needs no workflow edits for these moves, only a post-rebase
re-verification. Notable corrections to the brief: `release.yml` does NOT
reference RELEASE_NOTES.md (nothing to update); `tools/name_check.py:137`
default out path and `tools/rename_to_kymora.py` skip-lists MUST move with
`docs/internal/refactor/` or they recreate/bypass it; `check_snippets.py` exclusion
logic must follow. `mkdir` for `docs/internal/hardening/` +
`docs/internal/refactor/{baseline,rename-kymora}/` precedes `git mv`.
STOPPED before any move, per orders.

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
listing; `docs/internal/arch.md` reference left for the Phase 4 move).

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

## Incident 2026-10-06 — shared-tree collision (REPAIRED, work PAUSED)

While committing adjustments A–E, the working tree was found checked out on
a new branch `chore/ci-restructure` (cut from this branch at `dd7129e` by a
concurrent process restructuring CI: unstaged edits to 7 workflow/README
files + new `nightly.yml`/`wheels.yml`/`deny.toml`/`docs/internal/hardening/`/
`tools/check_repo_hygiene.py`). One commit (`d2a84a5`) accidentally swept in
that process's staged deletion of `.github/workflows/benchmark.yml`.

Repair (no foreign work touched, nothing pushed):
- Switched back to `chore/repo-cleanup` (foreign unstaged/untracked work
  preserved in tree).
- Replayed docs commit as `c7c9774` (same 3 files, deletion excluded) and
  hygiene commit as `20ffdad` (clean cherry-pick of `b8c8537`).
- `git diff chore/repo-cleanup chore/ci-restructure` is now exactly the
  foreign `benchmark.yml` deletion — nothing else crossed branches.
- Contaminated commits `d2a84a5`/`b8c8537` remain on `chore/ci-restructure`
  only; do not merge that branch without dropping them.

WORK PAUSED by owner pending coordination. On resume: re-run full gates
(fast gates re-verified at pause; full pytest re-run pending), then continue
with F (gc), G (paper trace), I (hygiene hash check), Phase 2 purge,
Phase 4 moves.

## Phase 4 — DONE (2026-10-06; moves `278d4b9`, docs refs `e3a658f`, code refs `838e5b6` + stragglers)

Owner decisions applied: Dockerfile/reproduce.sh/CODE_OF_CONDUCT.md KEEP at
root; `vercel.json` KEEP (project config builds `landing/`, project root =
repo root — moving breaks deploys); `docs/REFACTOR_STATE.md` moved to
`docs/internal/refactor/` (map updated accordingly).

40 files moved with `git mv` (history preserved); ~35 mechanical rewrites
(`arch.md` → `docs/internal/arch.md`, `docs/refactor/` →
`docs/internal/refactor/`; §-numbers unchanged); zero `.github/` references
to any moved path on this branch (workflow-refs column all `(none)`), so no
workflow edits here — CI branch checklist is OWNER_DECISIONS.md §7.
Corrections found en route: `release.yml` never referenced RELEASE_NOTES.md;
`tools/name_check.py:137` default out path and `rename_to_kymora.py`
skip-lists moved with `docs/refactor/` (else they recreate/bypass it).

Root now holds exactly the allowlist (plus `vercel.json`, rationale above;
no `.gitattributes`/`deny.toml` exist): README, CHANGELOG, CLAIMS, CLAUDE,
OWNER_DECISIONS, CITATION.cff, LICENSE, SECURITY, CONTRIBUTING,
CODE_OF_CONDUCT, Cargo.toml, Cargo.lock, pyproject.toml, Makefile,
mkdocs.yml, Dockerfile, reproduce.sh, vercel.json, .gitignore.
`proptest-regressions/` stays at crate root (functional: proptest seed
replay path). `.freebuff/project-id` is external-tool state (ignored via
`.git/info/exclude`), left alone.

sdist (`maturin sdist` + `tar -tzf`): before (pre-cleanup tree)
2,927,130 bytes / 354 files incl. `.github/`, `benchmarks/results/`,
`landing/`, `paper/`, `patent/`; after (exclude list in pyproject.toml)
531,713 bytes with none of `landing/`, `benchmarks/results/`, `paper/`,
`patent/`, `fuzz/`, `site/`, `.git*`. Wheel: 712,561 → 712,704 bytes
(rebuild noise; wheels never contained the junk).

### Scope note (latent numerical bug found by the purge, fixed `86cde1f`)

Purging `.hypothesis/` forced fresh property-test exploration, which found
a real bug: on numerically-degenerate windows (nonzero `var <=
(eps·mean)²`, e.g. 1-ulp pairs) batch skew/kurt emitted rounding garbage
(~√2) while streaming gave exact 0.0. Fix mirrors `scipy.stats.skew/
kurtosis` (`m2 <= (eps·mean)² → NaN`, gh-15905) in `stats.rs`, both
`reduce.rs` pass-2 variants, batch + streaming callers, with Rust
regression tests; `test_hypothesis_fast_matches_batch` now assumes away
degenerate windows (its premise is well-conditioned parity) and
`docs/numerics.md` documents the rule. `cid_ce` on such windows stays
defined-but-path-divergent (batch centers differently than the exact
streaming expansion); also documented. Goldens, validation, and all gates
unaffected (no degenerate inputs in fixtures).

### Final tree (depth 2; ignored build/cache dirs omitted)
- `.github/` actions/, CODEOWNERS, dependabot.yml, ISSUE_TEMPLATE/,
  PULL_REQUEST_TEMPLATE.md, workflows/
- `benchmarks/` adapters/, agreement/, baseline/, datasets/, harness/,
  report/, results/ (frozen), suites/, *.py suites, requirements-*.txt,
  README.md, STATE.md, LINUX_16VCPU_PLAN.md, zenith_baseline.md, smoke.py,
  reproduce.py, setup_venvs.py
- `docs/` user guides + `img/`, `benchmarks/`, `examples/`, `launch/`,
  `naming/` + `internal/` (arch.md, experiments.md, thread_scaling.md,
  unsafe_audit.md, hardening/, refactor/)
- `fuzz/` Cargo.toml, fuzz_targets/
- `landing/` src/, public/, config (own vercel.json for routing)
- `paper/` paper.md, paper.bib, figures/ (PNG), README.md, legacy/
- `patent/` patent_disclosure.md
- `proptest-regressions/` proptest_checks.txt
- `python/kymora/` package
- `src/` core rs files + features/, kernels/
- `tests/` test_*.py + fixtures/, golden/, parity/, property/, reference/
- `tools/` *.py scripts

Working dir: ~6178 MB → ~10 MB excl. `.git` (6.0 MB packed).
Tracked: 357 files / 5.7 MB → 364 files / 5.8 MB (net +7: +benchmarks/README,
+proptest seeds, +concurrency suite ×2, +paper/legacy/README, +CLEANUP_MOVES;
moves preserve history).
All gates green at every commit; golden files unchanged; nothing pushed,
merged, or tagged.

## Leftover phases — DONE

- L1 banner: 2 lines atop `benchmarks/results/L1_ROOT_CAUSE.md`, body
  untouched (`960adf0`).
- 5.1 `.gitignore`: sectioned rewrite, frozen evidence explicitly excluded
  (`*.svg` deliberately not ignored — `benchmarks/report/charts/*.svg` is
  tracked); `git ls-files | git check-ignore --stdin` empty
  (`23df316`, also adds `tools/README.md` + `docs/internal/README.md`).
  Backup sweep: no `*.bak/*~/*.orig/*.old` outside `target/` build noise.
- L1 rerun on HEAD (`9d6364c`): fresh `throughput.py --no-competitors`
  matrix (135 rows, kymora×numpy×numba all ok) → `2026-10-05_l1_rerun/
  l1_root_cause.json` (8 losses, was 17; only 1×100 gaussian 1.78×,
  heavy_tailed 1.75×, random_walk 1.43× robust). CLAIMS Where-slower row +
  README loss section rewritten from that artifact only (check_claims
  green). Scratch `throughput.jsonl` re-deleted after use.
- feature_map.json numba set 23→33 (`d90ee36`): missing 10 verified EXACT
  (worst 9.7e-14) on gaussian/random_walk/ar1/heavy_tailed/sinusoid ×
  1×100/10×500/100×500, strict fastmath=False; adversarial dists excluded
  (conservative). Rerun agreement relabeled deterministically (measured
  values proven identical; 33/33 EXACT, 0 WRONG).
- Deferred (unchanged): perf_gate → quiet CI; hygiene hash-check + 5.2 →
  CI branch post-rebase (OWNER_DECISIONS.md §7).
