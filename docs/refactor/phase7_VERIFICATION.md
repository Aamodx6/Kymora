# Phase 7 verification — CI/CD, tooling, contributor experience (2026-10-04)

## Workflow audit

All four workflows re-read against the post-rename tree:

- `release.yml`: **no changes needed** — trusted publishing (OIDC), wheel
  matrix, sdist, smoke test installs `tsxtract-rs` from the built wheel
  with `--no-index --no-deps`, asserts shim identity under a warnings
  filter, publish gated on `release: published`.
- `ci.yml`: had the 19-line venv-creation block inlined **three times**
  (test / validation-report / typecheck) while
  `.github/actions/setup-venv/action.yml` (identical content, incl. the
  Windows `pwd -W` handling and the active-interpreter assertion) sat
  **untracked** in the tree. Wired it: 3 steps → `uses:
  ./.github/actions/setup-venv`, action file now tracked. Net −36 lines;
  behaviour identical (validation-report/typecheck gain the interpreter
  assertion step — strictly stricter).
- `benchmark.yml`: same consolidation (its simpler ubuntu-only venv block
  was compatible — the composite takes the `.venv/bin` branch).
- `docs.yml`: the primary install
  `pip install ".[docs]" --no-build-isolation --no-deps` could never
  succeed on a Rust-less runner *and* `--no-deps` would have skipped the
  extras anyway; only the `||` fallback ever ran. Replaced with the exact
  pyproject floors (`mkdocs>=1.6`, `mkdocs-material>=9.5`).

## Contributor files created (recorded as Phase 7 backlog in
`docs/refactor/deleted_files.md`; none existed before)

| File | Notes |
|---|---|
| `.github/CODEOWNERS` | `* @Aamodx6` (from remote/owner handle) |
| `CODE_OF_CONDUCT.md` | Contributor Covenant 2.1; **CONTRIBUTING.md's CoC link was dead until now**; enforcement contact = GitHub DM to @Aamodx6 (no public email known) |
| `SECURITY.md` | private reporting via GitHub advisories; calls out unsafe buffer handling as prime target; no backport policy (latest release only) |
| `CITATION.cff` | author from paper byline (Aamod Kumar); v0.5.0, date = PyPI release date |
| `.github/ISSUE_TEMPLATE/{bug_report,feature_request}.yml` + `config.yml` | bug form mirrors CONTRIBUTING's reporting checklist; proposal form encodes the closed-33-feature policy; config links private security reporting |
| `.github/PULL_REQUEST_TEMPLATE.md` | checklist mirrors CONTRIBUTING's PR rules + gates |
| `.github/dependabot.yml` | weekly groups for github-actions + cargo; pip deliberately omitted (maturin-backed pyproject, numpy-only runtime) |
| `CLAUDE.md` | agent guardrails: rebuild-before-pytest hazard, gate list, feature-hash invariant, D8 naming, `git add -A` prohibition |

## CONTRIBUTING additions (contributor experience)

1. **Dev-loop hazard** (Phase 4 finding): after editing `python/` or
   `src/`, pytest still runs the installed wheel — explicit
   `maturin develop --release` step added after the Checks section.
2. **Benchmarks section (runner consolidation, D14)**: the five raw
   `python benchmarks/...` commands documented as the canonical,
   cross-platform path; `Makefile` (make unavailable on the owner's
   Windows box) and `reproduce.sh` (bash-only, Dockerfile CMD) explicitly
   scoped as optional wrappers — **both kept** because `arch.md` gates
   and `Dockerfile CMD` reference them. Raw commands > wrappers is now
   written down instead of implied.

## Verification output

- All 9 workflow/template YAML files parse (`yaml.safe_load`)
- Wiring check: 3 local-action refs in ci.yml, 0 leftover inline venv
  blocks anywhere; benchmark.yml uses the action; `.[docs]` gone from
  docs.yml; `CITATION.cff` parses
- `cargo test` 16/16 · `clippy -D warnings` exit 0 · `fmt` exit 0
- `pytest tests -q -W error` 138 passed · hash MATCH
- `mkdocs build --strict` exit 0 · `mypy` clean ·
  `scripts/validation_report.py` exit 0
- Not run locally: actual GitHub Actions execution (first push to main
  exercises ci/docs/release; dispatch benchmark.yml if wanted)

## Commits

- (this phase) ci(tooling): composite venv action, docs install fix,
  community files, dev-loop + benchmark docs
