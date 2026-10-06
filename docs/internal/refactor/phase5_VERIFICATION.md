# Phase 5 verification — documentation architecture (2026-10-04)

## Claims cleanup (arch §14.1 / F1–F7)

User-facing docs claimed as shipped what is prototype or absent
(Phase 3 evidence: no SIMD intrinsics, `pool.rs` unwired). Fixed:

| Location | Was | Now |
|---|---|---|
| `docs/index.md:5` | "SIMD vectorization and persistent worker pools" | Rayon + fused passes + shared intermediates |
| `docs/index.md` bullets | AVX2/NEON SoA lanes; spin-then-park pool as shipped | Fused passes; Rayon + serial fallback (`SERIAL_THRESHOLD`); kept the *true* histogram-quantile bullet |
| `docs/index.md:30`, `README.md:25` | blanket "sub-microsecond O(1)" / "constant memory O(1)" | amortized-O(1) ingestion + fast 12-feature tier without sort/FFT |
| `README.md:31` | "native Rust SIMD" | "native-Rust" (auto-vectorization only) |
| `README.md:35` | "branchless quantile quickselects" (word absent from `src/`) | "histogram multi-select" (matches `sort.rs`) |
| `README.md:157` | "True O(1) online fast tier (sub-microsecond…)" | two linear passes; measured 1.8 µs/call at w=500 |
| `docs/api.md:317-320`, `docs/quickstart.md:98-110` | `TSXTRACT_POOL` spin/rayon as functional | documented as unwired; `tune()` recommendation provisional |
| `src/features/streaming.rs:233` | "O(1) subset" (`compute_fast` is 2 full passes) | O(window), O(1)-amortized `push` |

Left alone (historical record, not live claims): `timeline_progress.md`,
`benchmarks/zenith_baseline.md`, CHANGELOG, F1 throughput-number dispute
(B-track reruns needed — owner/B-phase).

## Link integrity

- `mkdocs build --strict`: exit 0, **zero anchor INFOs** (was 2).
  Fixed by adding the missing sections, not by retargeting:
  `index.md` gained "Where the speed comes from" (actual architecture,
  incl. an explicit what-does-*not*-contribute paragraph) and
  "When not to use this" (closed catalog, CPU-only, single-series
  overhead ~0.1 ms per arch F2, contiguous f64/f32 only).

## Site config

- `mkdocs.yml site_url`: `aamod007.github.io` → `aamodx6.github.io`
  (aligns with `repo_url` per D0; resolves NEEDS-OWNER #6; #1 stays open
  for the fate of anything under `Aamod007`).

## Roles decision (D13)

- Measured `docs/` ↔ landing-docs textual overlap: 0.02–0.29 (independently
  written, not mirrors). No merge attempted.
- Rule: `docs/` (mkdocs → GitHub Pages) is the versioned project reference;
  `landing/src/docs/` is product-site content. Same topics may be covered in
  different words; neither copies the other. New shared facts go in `docs/`
  first.
- Nav unchanged: historical reports (`parity_matrix`, `arch_audit`,
  `timeline_progress`, `redundancy_report`) stay out of nav (reachable via
  git/arch links); `REFACTOR_STATE.md` stays unlisted process state.
- `PRD.md` / `patent/`: untouched (owner calls #4/#5 stand).

## Verification output (final tree, wheel rebuilt+reinstalled)

- `mkdocs build --strict`: exit 0, no anchor diagnostics
- `cargo test`: 16/16 (comment-only Rust change)
- `cargo clippy --all-targets -- -D warnings`: exit 0
- `cargo fmt --check`: exit 0; `cargo doc --no-deps`: 0 warnings
- `pytest tests -q -W error`: 138 passed
- `feature_names()` sha256: MATCH
- `mypy python/tsxtract`: clean (unchanged)
- `landing npm run build`: ✓ built in 48.76s (pre-existing chunk-size
  warning only) — **was missed in the first Phase 5 pass, run during
  diff review**

## Post-completion diff review (2026-10-04)

Full `git diff --stat pre-refactor..HEAD` audit (214 files, +6862/−2280):
all regions accounted for — renames (benches→benchmarks, tests subdirs),
evidenced deletions (arch_max/zenith, insp/, py.typed, STATE.md), and
rename-driven edits in landing/paper/scripts/Makefile/CONTRIBUTING.

One defect found and fixed in this review: **Phase 1's rename broke
`paper/main.tex`** — the sed turned the `\tsxtractor` alias into a second
`\newcommand{\tsxtract}` (LaTeX "already defined" error) and left a
redundant `(\tsxtract{})` in the abstract. Removed the duplicate macro;
abstract now `(\texttt{tsxtract})`. Structural check: 7 unique macros,
0 `\tsxtractor` refs, balanced braces (no pdflatex on this machine, so
compile check deferred to CI/manual).

## Commits

- `afc9bf0` docs(refactor): Phase 5 claims cleanup, anchors, site_url, state
- (follow-up) fix(paper): undo duplicate \newcommand created by rename
