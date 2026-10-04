# Refactor state (tsxtract standardization)

Branch: `refactor/tsxtract`. Tag: `pre-refactor`. Base: `4c268ca`.
arch.md is the architecture source of truth.

## Phase checklist

- [x] Phase 0: baseline & inventory (2026-10-04). Gate: baseline recorded;
      two known-red items documented (mypy 10 errors, mkdocs warnings).
- [x] Phase 1: naming decision & packaging (2026-10-04). Gate: wheel builds
      as `tsxtract-rs 0.5.0`, `import tsxtract` works, `import tsxtractor`
      warns + works, 138 tests pass, feature hash unchanged, clean-venv
      install verified. See `docs/refactor/naming.md`,
      `docs/refactor/phase1_VERIFICATION.md`.
- [x] Phase 2: repository structure & obsolete file removal (2026-10-04).
      Gate: `benchmarks/` move + path updates (53 files, zero residuals),
      `tests/{property,reference}/` subdirs, `insp/` deleted with evidence,
      `.gitignore` fixed, builds/tests green. See
      `docs/refactor/deleted_files.md`. Contributor files
      (CODE_OF_CONDUCT, SECURITY, CITATION.cff, templates, dependabot)
      deferred to Phase 7; docs-system dedup deferred to Phase 5.
- [x] Phase 3: Rust core cleanup (2026-10-04). Gate: legacy dead code
      removed with evidence (−133 net), unsafe centralized into 2 helpers
      with SAFETY contract, `deny(unsafe_code)` in 17 modules
      (negative-tested), rustdoc warning-free, arch.md I8 + §4.1 aligned,
      cargo/pytest green, feature hash unchanged, perf no-regression.
      Fresh Zenith experiments kept (pool.rs, soa_4x, out32) pending owner
      wire-or-delete. See `docs/refactor/phase3_VERIFICATION.md`.
- [x] Phase 4: Python package cleanup (2026-10-04). Gate: mypy clean
      (was 10 errors; stubs completed from `ffi.rs` signatures, select.py
      typing fixed, scipy import made hermetic), 138 tests pass, feature
      hash unchanged. Dev-loop hazard found: tests import site-packages,
      so the wheel must be rebuilt+reinstalled before pytest means
      anything (done this phase; Phase 7 tooling candidate). See
      `docs/refactor/phase4_VERIFICATION.md`.
- [x] Phase 5: documentation architecture (2026-10-04). Gate: false
      SIMD/spin-pool/O(1)/sub-microsecond claims corrected in `docs/` +
      README (measured 1.8 µs fast-tier), 2 anchors fixed by adding the
      missing sections, `site_url` aligned (closes #6), mkdocs strict
      INFO-free, roles decision (no landing merge). PRD/patent untouched
      (#4/#5). See `docs/refactor/phase5_VERIFICATION.md`.
- [x] Phase 6: website (2026-10-04). Gate: landing build clean; removed
      4 false conda-forge blocks (Anaconda API 404 on both names) and
      fixed 9 wrong `tsxtract` dist names in install commands (would hit
      the unrelated JAX PyPI project); docs/api.md D8 violation fixed;
      dead `TSXTRACT_VERSION` removed; nav/links/figures integrity
      16/16. **#2 RESOLVED** (PyPI `tsxtract-rs` owned by `aamoddev11`,
      0.5.0 live). F1 exposure + Footer profile deferred (#1/B-track).
      See `docs/refactor/phase6_VERIFICATION.md`.
- [x] Phase 7: CI/CD, tooling, contributor experience (2026-10-04). Gate:
      setup-venv composite action wired into ci.yml ×3 + benchmark.yml
      (was untracked dup); docs.yml never-succeeding install replaced with
      pyproject floors; contributor files created (CODEOWNERS, CoC — was a
      dead link in CONTRIBUTING — SECURITY, CITATION.cff, issue/PR
      templates, dependabot, CLAUDE.md); dev-loop hazard + cross-platform
      benchmark commands documented (D14: raw commands canonical, wrappers
      kept for arch/Dockerfile refs). All YAML parse; full gates green.
      See `docs/refactor/phase7_VERIFICATION.md`.
- [x] Phase 8: final verification & report (2026-10-04). All 11 gates
      green on the final tree (cargo 16/16, clippy/fmt/doc clean, pytest
      138 under `-W error`, hash MATCH, validation within tolerance,
      mkdocs strict, mypy clean, landing builds, residual scan clean,
      phase records complete). 17 commits from `pre-refactor`. Not
      pushed — owner's call. See `docs/refactor/phase8_VERIFICATION.md`.

## Decisions

- D0 (Phase 0): canonical repo = `origin` (`Aamodx6/Tsxtract`) until owner
  confirms otherwise.
- D0 (Phase 0): `feature_names()` sha256
  `8a1e2794…3e1431af` is the semantic invariance anchor for all phases.
- D9 (Phase 2): `benchmarks/` is the Python harness dir (arch.md §4.1
  updated); `mkdocs build --strict` passes (docs CI green); `make` is
  unavailable on the owner's Windows box — runner consolidation is Phase 7.
- D10 (Phase 3): unsafe lives only in `ffi.rs` (numpy boundary, centralized
  helpers + SAFETY) and `kernels/` (designated home, currently unsafe-free);
  compile-enforced elsewhere via `deny(unsafe_code)`.
- D11 (Phase 3): deleted only legacy-superseded dead code; kept fresh
  Zenith-session experiments (`pool.rs`, `soa_4x`, `run_core33_f32_out32`)
  for an owner wire-or-delete call.
- D12 (Phase 4): `_core.pyi` is complete and runtime-verified; mypy gate is
  hermetic (no new CI deps needed for scipy); `select_features` returns
  plain `int` indices.
- D13 (Phase 5): `docs/` is the versioned project reference, landing docs
  are product-site content — no mirroring either way (overlap 0.02–0.29);
  new shared facts go in `docs/` first; historical reports stay out of nav.
- D14 (Phase 7): benchmark runner entry points — the five raw
  `python benchmarks/...` commands are the canonical portable path
  (Windows-safe); `Makefile` and `reproduce.sh` remain optional wrappers
  (referenced by arch.md gates and Dockerfile CMD), not deleted.

## Follow-up — post-Phase-8 steps (owner-directed, in order, gate each)

- [x] Step 1: quarantine #7/#8 → `experiment/spin-pool` +
      `experiment/soa-4x` + `docs/ROADMAP.md` (revival gates Z6/Z2).
      Committed `9c1b3dd`; branches local until push.
- [x] Step 2: F1 interleaved benchmark pre-refactor vs HEAD (P1→H1→P2→H2,
      same machine/env/harness; only the wheel varied). Pooled: tsxtract
      P med 3.31 CI [3.26,3.36] vs H med 3.25 CI [3.21,3.32] — overlap,
      refactor perf-neutral. README headline/table/competitor rows
      rewritten from the artifact (307,366 s/s med; 261×/829×/7,038×);
      stale rows marked †; root CLAIMS.md created per arch §14.1.
      Artifact: `benchmarks/results/F1_REPORT.md` + `F1_{P1,H1,P2,H2}/`.
      LOSS_LEDGER.md restored byte-identical. Landing/docs figures stay
      stale (pending section in CLAIMS.md).
- [x] Step 3: verify-results checks — golden diff vs pre-refactor EMPTY,
      feature hash MATCH, API dump PRE-vs-HEAD diff empty (33 lines, only
      venv path differs), clean-venv (`vCLEAN`, numpy+pandas+wheel, no
      repo on sys.path) README quickstart blocks 1–4 verbatim: exit 0,
      (1000,33), DataFrame [5×33], ragged (3,33). sklearn/streaming
      blocks need user data (X_train/incoming_data_feed undefined) —
      not self-contained, reported not run.
- [x] Step 3b: version bisect, interleaved + rotated (suite R1:
      032pb/040/PRE/HEAD; R2 rotated PRE/HEAD/040/032pb; probe sets PA2 +
      PB rotated). Excluded: B_PRE_R1 (Silent plan + battery flap),
      B_PRE_R1b partial (aborted, superseded by R1c), PA-v032
      (franken-import: measured main-env code). Result: 0.3.2 probe med
      2.00 CI [1.97,2.02] vs 0.4.0 2.41 / pre 2.34 / HEAD 2.35 (overlap)
      → ~15% step 0.3.2→0.4.0 on the IDENTICAL 33-name catalog (hashes
      equal); 0.4.0≈pre≈HEAD flat. Old 1.25/1.80 ms figures
      irreproducible on this machine at EVERY version → different
      hardware, not a regression. Artifacts untracked (commit in step 4).
- [x] Step 4 (this commit): F1 artifacts committed — `F1_REPORT.md`
      (+3b bisect appendix), `F1_SUMMARY.json`, 10 suite dirs
      (`F1_*`, `B_040_R*`, `B_PRE_R1c/R2`, `B_HEAD_R*` with jsonl+env),
      8 probe JSONs. Excluded rounds deleted (R1 battery flap, R1b
      partial). Total ~250KB, no LFS. Step-3/3b tracker folded in.
- [x] Step 3c: per-feature table (µs/series-feature + ratios) in
      F1_REPORT.md; README competitive table + CLAIMS.md show raw AND
      per-feature (10-round pools: 0.0964 / 37.87 / 16.29 / 26.89 µs;
      393×/169×/279×).
- [x] Step 3d: single-thread core33 at 500 pts via scaling-suite protocol
      (threads=1, n=122): 12.163 µs/series — at the §9.3 estimate band
      top (6–11 µs, marked est.); headroom to Zenith floor (2.5–5 µs) is
      ~2.4–4.9×. No optimization. Recorded in F1_REPORT.md.
- [x] Step 5 (pending claims, in order): PyPI source-verified
      (`readme = "README.md"` — self-corrects on next release, no edit);
      landing data + 3 docs tables + meta + mermaid + captions rewritten
      from the 10-round artifact; `docs/benchmarks.md` measured-run
      refreshed; arch.md F1 closed + §9.1 rebaselined; stale single-series
      + scaling/memory rows marked †/pending. All laptop numbers labeled
      exploratory. Final sweep: only new values + intentional historical
      references remain.
- [x] Step 6: `benchmarks/LINUX_16VCPU_PLAN.md` — exact setup/measure/
      commit commands, ~60–75 min estimate, outputs list. NOT run.
- [ ] CI failure fixes, one root cause per commit (unblocks after push)
- Release 0.6.0 (2026-10-04): packaging release — dist `tsxtract-rs`,
  import `tsxtract`, ext `tsxtract._core`, single-sourced version,
  `tsxtractor` shim deprecated (removal >= 0.7.0). Website docs corrected
  from `CLAIMS.md` artifact (hero/features perf sentences, Benchmarks µs
  unit, Footer PyPI URL + MIT-only license, Hero repo URL typo).
  Personal-profile links (`Aamod007` byline/footer) untouched per
  NEEDS-OWNER #1. Measured benchmark tables stay pinned to the 0.5.0
  artifact by design.
- NO PR: owner directed commit + push directly, no pull request.
  Merged 2026-10-04: local `main` (was stale at `4c268ca`) fast-forwarded
  to `88298f5` via `refactor/tsxtract` (origin/main `f6b670c` proved to be
  a direct ancestor — no divergent owner commits, no conflicts);
  `experiment/*` merges were no-ops by design (pre-deletion snapshots,
  deletions stand). `main` pushed (fast-forward, no force). CI + docs +
  wheel-build workflows triggered by the push. Incidental find during
  merge: `benchmarks/results/LOSS_LEDGER.md` is TRACKED (committed long
  ago) — 3b suite appends reverted to keep others' evidence intact.

## NEEDS-OWNER

1. Confirm canonical repo (`Aamodx6/Tsxtract`) and fate of anything under
   handle `Aamod007` (no second remote is configured locally).
2. ~~PyPI `tsxtract-rs` ownership~~ — resolved Phase 6: PyPI API shows
   releases 0.3.0–0.5.0 under owner `aamoddev11`, metadata identical to
   this repo. JAX project keeps bare `tsxtract` (D8 still applies:
   never `pip install tsxtract`).
3. Stashed prior-session work: resolved (popped + committed in Phase 1).
4. `PRD.md`: archive or migrate-then-delete (sole product-requirements
   record; weak references only).
5. `patent/patent_disclosure.md`: 0 references, but IP content — confirm
   keep (do NOT delete on usage heuristic).
6. ~~`mkdocs.yml: site_url` still `aamod007.github.io`~~ — resolved Phase 5
   (`aamodx6.github.io`, per D0).
7. ~~`pool.rs` / `TSXTRACT_POOL`~~ — resolved: `src/pool.rs` moved to
   `experiment/spin-pool`, deleted from main (0 callers); revival gated on
   arch.md Z6, recorded in `docs/ROADMAP.md`. `tune.py` pool dimension
   stays void until then.
8. ~~`soa_4x` kernels + `run_core33_f32_out32`~~ — resolved: soa_4x
   quartet (`reduce.rs:821-1153`) + `run_core33_f32_out32`
   (`pipeline.rs:252-260`) moved to `experiment/soa-4x`, deleted from
   main (0 callers, 0 parity tests, no ≥10% benchmark — exception clause
   failed on evidence); revival gated on arch.md Z2 + ≥10% end-to-end,
   recorded in `docs/ROADMAP.md`.

## Stash register

- `wip-arch-consolidation`: pre-existing uncommitted changes found on
  2026-10-04 (arch.md rewrite, arch_max.md/arch_zenith.md deletions,
  benchmarks/STATE.md + adapters + harness edits, LOSS_LEDGER.md).
