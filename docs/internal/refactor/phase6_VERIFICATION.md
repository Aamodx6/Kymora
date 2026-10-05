# Phase 6 verification — website (2026-10-04)

## Inventory

- Landing (`landing/`, Vercel SPA via `vercel.json` rewrites; `tsc` + vite)
  already carried the Phase 1 rename: Nav/Hero/CTA clipboard commands
  (`pip install tsxtract-rs`), GitHub repo URLs (`Aamodx6`), benchmark
  path comments, and the docs content extras lines.
- Route integrity: `docRegistry.ts` auto-registers slugs from
  `content/*.md`; `nav.ts` ↔ 16 content files match 16/16 both
  directions; every internal `/docs/*` link in the markdown resolves to
  a registered slug; all `/figures/*.png` referenced by docs exist in
  `public/figures/` (5/5).
- No SIMD/spin-pool false claims in landing (Phase 5 cleanup had no
  landing counterparts); `O(1)` mentions are push-level/amortized or
  mathematically true (`mean_change` telescoping) — consistent with
  Phase 5 wording.

## Defects found & fixed

1. **False conda instructions (critical)** — `installation.md` had four
   `conda install/update/remove -c conda-forge tsxtract` blocks.
   Verified 404 on Anaconda API for BOTH `tsxtract` and `tsxtractor` →
   package does not exist. Removed all four blocks; the install NOTE now
   records the negative check; the TODO(verify) note drops conda (already
   checked) and keeps only OS/glibc floors as unverified.
2. **Wrong pip/uv dist names (critical)** — same file: upgrade,
   uninstall, troubleshooting, proxy, and success-output lines used bare
   `tsxtract`, which on PyPI resolves to an **unrelated JAX project**
   (rule D8 in `naming.md`). Fixed 9 occurrences to `tsxtract-rs`;
   extras mentions `"tsxtract[...]"` → `"tsxtract-rs[...]"`; sample
   output version `0.3.0` → `0.5.0`.
3. **`docs/api.md:75`** — same D8 violation (`"tsxtract[pandas]"`) →
   `"tsxtract-rs[pandas]"`.
4. **Dead export** — `landing/src/docs/constants.ts` `TSXTRACT_VERSION`
   was `0.3.0` and imported nowhere (Cargo is 0.5.0); removed rather
   than bumped (dead code).

## Deliberately not changed

- **F1 throughput exposure on the site**: `index.html` meta
  ("800k+ series/s"), docs benchmark tables (800,256 / 555,016 / other
  figures), `benchmarks.ts` (labeled `PLACEHOLDER DATA`). F1 stays
  with the B-track rerun/owner decision (arch.md §2.2).
- **Footer.tsx:165** profile link `github.com/Aamod007` — personal
  identity, NEEDS-OWNER #1 (repo links already point at `Aamodx6`).
- Historical `changelog.md` release-note copy ("persistent
  low-latency worker pools" etc.) — mirrors CHANGELOG.md as a record.

## Open facts recorded this phase

- **NEEDS-OWNER #2 RESOLVED**: PyPI API shows `tsxtract-rs` releases
  0.3.0–0.5.0 (0.5.0 published 2026-10-04T04:08Z) owned by user
  `aamoddev11`, metadata identical to this repo (extras, project URLs →
  `Aamodx6/Tsxtract`, MIT, description). The dist name is ours.
- **PyPI long_description is stale** (0.5.0 was built from a
  pre-refactor README): still shows `import tsxtractor`, Aamod007
  clone URLs, SIMD/quickselect claims, and tables contradicting the
  headline number. No action needed — `pyproject.toml` derives it from
  repo `README.md`, so the next release self-corrects.

## Verification output

- `landing npm run build`: ✓ built in 38.33s (tsc clean)
- `mkdocs build --strict`: exit 0
- `cargo test`: 16/16 · `clippy -D warnings`: exit 0 · `fmt`: exit 0
  (no Rust/Python source touched this phase)
- `pytest tests -q`: 138 passed
- `feature_names()` sha256: MATCH
- Residual scan: no bare `tsxtract` pip/uv/conda commands left in
  `landing/` or `docs/`; conda only in the two explanatory notes above

## Commits

- (this phase) fix(docs/landing): drop nonexistent conda channel, correct
  dist names, remove dead constant
