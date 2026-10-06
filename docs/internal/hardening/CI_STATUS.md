# CI_STATUS.md — CI/CD restructure tracking

Branch: `chore/ci-restructure` (do not push until the draft PR; do not tag, do not publish).
Base: `origin/main` @ `c830a69` (cleanup merged via PRs #2 + #3; branch rebased
cleanly, single commit `b95d53c` on top). Date: 2026-10-05/07. Constraint: no
behavior change in what is verified — every existing check still exists with
the same coverage, better structure. Release OIDC permission semantics
unchanged (only restructured) — and verified working: `kymora 0.8.0` published
to PyPI via Trusted Publishing (run 37306732236). The failed release run
37307597215 was a duplicate-publish `400 File already exists`, not an auth
failure; no pending publisher is needed. Do NOT move the `v0.8.0` tag
(next release is 0.8.1).

## 0. Base reality (read before reviewing)

- Cleanup IS merged (`origin/main` @ `c830a69`: PR #2 merge `3784f13` +
  PR #3 merge `c830a69`). This branch was rebased onto it with zero
  conflicts (`b95d53c`). The §0 incident narrative from round 2 (cleanup
  paused, contaminated commits, `git reset --hard`) is history — kept below
  the line for the record and no longer operative.
- Post-merge sweep (2026-10-07, on the rebased tree): every
  `CLEANUP_MOVES.tsv` path swept across `.github/**`, `Makefile`,
  `tools/**`, `mkdocs.yml`, `pyproject.toml`/`Cargo.toml`. Only stale hit:
  `tools/check_repo_hygiene.py` `ROOT_ALLOWED` still listed the moved root
  files (`arch.md`, `PLAN.md`, `STATUS.md`, `CLEANUP_STATUS.md`,
  `RELEASE_NOTES.md`) — fixed to the final 20-entry layout (§2.6).
  `rename_to_kymora.py` and `Makefile`/`mkdocs.yml` refs already point at
  the new `docs/internal/` paths. `release.yml` never referenced
  `RELEASE_NOTES.md`. **Zero stale hits after the fix.**
- Historical (round 2, superseded):
- The prior session's `chore/ci-restructure` tip (`b8c8537`) carried the
  incident's contaminated commits; per the incident note they were dropped
  by resetting the branch to `main`. The CI branch therefore contains NO
  cleanup commits — correct, since cleanup is unmerged.
- Session-1 untracked files (`wheels.yml`, `nightly.yml`, `deny.toml`,
  `tools/check_repo_hygiene.py`, this file) vanished from the shared tree
  between sessions (concurrent owner housekeeping; the archive
  `../kymora-archive-2026-10-06.zip` may hold copies). All were recreated
  from record, then upgraded with round-2 tasks (§2 deltas). Tracked edits
  survived via the owner's stash (`stash@{0}`, left intact, not dropped).
- `git diff` leaves `tests/` (incl. `golden/`) untouched (verified §6).

Verification: `actionlint` 1.7.12 clean (installed locally, run at repo root);
all workflow YAML parses; `act` not run (no runner images on this host).

## 1. Moved-path sweep (round 2, task 1)

- `git ls-files | Select-String CLEANUP_MOVES`: **zero hits** (file never
  created in tree or history — nothing moved, nothing to remap).
- Grepped `.github/**` for `benchmarks/|docs/|tools/|paper/|landing/|patent/`:
  29 matches, all resolve (`benchmarks/bench_libraries.py`,
  `benchmarks/suites/equal_feature.py`, `remeasure_readme.py`,
  `benchmarks/results/`, `tools/{validation_report,check_claims,
  gen_feature_docs,check_snippets,check_repo_hygiene}.py`, `docs/**`,
  `landing/**`, `mkdocs.yml` — all exist).
- `Makefile` refs (`benchmarks/{setup_venvs,smoke,suites/agreement,
  reproduce,report/make_report}.py`): all exist.
- `mkdocs.yml`: nav + `edit_uri: edit/main/docs/` — no moved paths.
- `pyproject.toml` / `Cargo.toml`: no `include`/`exclude` path lists to
  update (maturin `python-source = "python"`, both dirs in place).
- Result: **zero dangling references. Zero hits.**

## 2. Round-2 deltas (on top of the round-1 restructure)

1. `ci-gate` job in `ci.yml`: `needs` all 10 jobs, `if: always()`, fails on
   any failure/cancelled, allows skipped. **The ONLY required check.**
2. `release.yml` first job `version-check`: tag `vX.Y.Z` must equal
   `Cargo.toml [package] version` and `pyproject` must keep a dynamic
   version; branch dispatches pass trivially (dry run). All other jobs
   `need` it.
3. `audit-pr` job in `ci.yml`: cargo-audit + pip-audit, job-level gate on
   new `deps` filter (`Cargo.toml`, `Cargo.lock`, `pyproject.toml`,
   `deny.toml`). Nightly keeps the full audit/deny suite too.
4. `nightly.yml`: `workflow_dispatch` (+ `fuzz_seconds` input) AND
   `pull_request` on paths `[.github/workflows/nightly.yml, deny.toml]` so
   draft PRs exercise deny/audit/perf on real runners; schedule kept.
   Perf-regression issue fires on schedule/dispatch ONLY (event gate in the
   step `if:`), never on PR events. Spam guard: the issue files/updates only
   after **2 consecutive failures** — the step queries the latest COMPLETED
   run on the branch via `gh run list`; a single failure (previous run green
   or none) exits 0 without filing. Rationale: shared runners make one-off
   perf failures noise; two in a row is signal. Update 2026-10-07: a single
   repeat at ratio >= 1.15 now bypasses the spam guard and files immediately
   (see delta 8 above); the old "(>15% failure-rate) alternative considered"
   note is superseded by this magnitude rule.
   Perf job keeps `continue-on-error: true` (workflow stays green); the
   `perf-regression` issue (label auto-created) is the signal. Perf job
   carries `issues: write` (top-level stays `contents: read`).
5. `wheels.yml` `full` input (`workflow_call` default false, dispatch
   default true): lite = 5 builds + `wheel-test` (3 OSes × py3.13, always);
   full adds `wheel-test-extended` (py3.10/3.14 × linux/win). ci passes
   `full: event == push` (PRs lite, main full); release passes `full: true`.
6. Hygiene: `ROOT_ALLOWED` = final post-cleanup root layout (20 entries:
    dotfile + manifests + docs + scripts + `deny.toml`; the moved process
    files stay out — a reappearance at root fails the gate). Plus two new
    checks: paper/landing figure SHA256 equality (5 PNG pairs) and
    `mkdocs.yml` must carry `exclude_docs: internal/`. Verified `hygiene OK`.
7. Bench provenance (new): every suite writes `env.json` next to its jsonl
    (CPU model, core counts, OS, governor/power info where available, load
    average at start AND end via new `snapshot_load()`), and every timing row
    carries per-row CV (harness `stats.cv` was already in remeasure rows;
    added `kymora_cv`/`competitor_cv` to equal-feature rows and `km_cv`/
    `numba_cv` to L1 loss rows). `l1_root_cause.py`/`throughput.py` never
    called `save_env` before — that is why the 2026-10-05 rerun has no
    env.json. bench.yml upload globs already cover the dated result dirs
    (and results/ root for bench-libraries), so no workflow change needed.
8. Nightly perf-issue rule tightened: 2 consecutive failures files as
    before, but a single repeat with ratio >= 1.15 (>15% regression, grepped
    from `perf_gate.py` `ratio X.XXXX` output) files immediately — that
    magnitude is never scheduler noise. Repeats now run to completion even
    after a failure (log keeps all three ratios for the grep).
9. Release hardening (round 4): `release.yml` gains workflow-level
    `concurrency: {group: release-<ref>, cancel-in-progress: false}` — one
    tag queues behind another instead of racing it (the v0.8.0
    duplicate-publish 400 came from two runs on one tag). `pypi-publish`
    job, `pypi` environment, OIDC token permission, and tag-only `if:`
    byte-identical (verified by diff).
10. External parity with teeth (round 4): new `parity` job in `ci.yml`
    (ubuntu, py3.12, installs `.[dev-parity,sklearn]`, runs
    `pytest tests/parity -q -rs` with `KYMORA_REQUIRE_PARITY=1`, which
    `tests/parity/conftest.py` turns reference-library skips into failures;
    hook verified both ways locally). Path-gated like the test jobs, in
    `ci-gate` needs (self-test now 8/8, incl. the new failed-parity case).
    Same job on nightly schedule. No CI job previously installed
    dev-parity — parity skipped silently everywhere; that hole is closed.

## 3. Old -> new job map

BEFORE = pre-restructure (`main`): ci jobs `rust, test(20), validation-report,
typecheck, snippets, audit, perf-gate, feature-docs, fuzz-smoke, wheel-smoke(4)`;
release `linux(2), macos(2), windows, sdist, smoke-test(3), sbom, publish,
github-release`; docs `build, deploy`; benchmark `bench`; bench `bench(2)`.

| BEFORE | AFTER |
|---|---|
| ci `rust` | ci `rust` / **rust fmt, clippy, tests (ubuntu-latest)** |
| ci `test` (20) | ci `test` / **test (pyX.Y, os)** (same 20) |
| — (new) | ci `test-macos-intel` / **test (py3.12, macos-15-intel)** |
| ci `validation-report` | ci `validation-report` / **validation report (ubuntu-latest, py3.12)** |
| ci `typecheck` | ci `typecheck` / **mypy (ubuntu-latest, py3.12)** |
| ci `snippets` + `feature-docs` + docs build check | ci `docs` / **docs (ubuntu-latest, py3.12)** |
| — (new) | ci `hygiene` / **repo hygiene (ubuntu-latest)** |
| ci `audit` | ci `audit-pr` / **dependency audit PR (ubuntu-latest)** (deps-change only) + nightly keeps full audits |
| — (new router) | ci `changes` / **changes (paths-filter)** (code/docs/deps filters) |
| ci `wheel-smoke`(4) + release builds/smoke | `wheels.yml`: `build-linux/mac/windows`, `build-sdist`, `wheel-test` (3, always) + `wheel-test-extended` (4, full only) |
| — (new aggregator) | ci `ci-gate` / **ci gate (all green)** — the only required check; logic in `tools/ci_gate.py` (7 self-test cases): `changes` must be `success`, everything else `success`/`skipped`; `needs` includes the `wheels` reusable call |
| ci `fuzz-smoke` (3×30s) | nightly `fuzz-smoke` / **fuzz smoke (ubuntu-latest, 10min)** (+ dispatch `fuzz_seconds`) |
| ci `perf-gate` (1×30) | nightly `perf-gate` / **perf gate core33 (ubuntu-latest, x3)** + `perf-regression` issue on failure |
| release `sbom` | release `sbom` / **SBOM SPDX (ubuntu-latest)** (same perms) |
| — (new) | release `version-check` / **version check (tag matches Cargo.toml)** (first job, all others need it) |
| release `publish` (on release event) | release `pypi-publish` / **PyPI publish (ubuntu-latest)** (`if: tag`, same `pypi` env + `id-token: write`) |
| release `github-release` (on release event) | release `github-release` / **GitHub release attach (ubuntu-latest)** (`if: tag`, same `contents: write`) |
| benchmark `bench` + bench `bench(2)` | bench `bench-libraries` + `bench-equal-feature` (manual only, macos-14→15) |

Job counts: BEFORE 10 ci + 8 release + 2 docs + 1 + 1 = 22 ids (45 checks).
AFTER 12 ci ids (20 test + 11 singles + wheels call) + 6 wheels ids (14 checks
full / 10 lite) + 5 release + 5 nightly + 3 bench + 2 docs = 33 ids
(72 checks full, 68 lite).

## 4. CI minutes per push (raw job-minutes, cache-warm assumptions §5/round-1)

| Push type | BEFORE | AFTER | Note |
|---|---|---|---|
| Code PR (lite wheels, no manifest change) | ~253 (ci) | ~265 | +gate/intel(+1), −audit/fuzz/perf to nightly, wheels lite (5 builds ~50 + 3 tests ~18 vs old 4 smokes ~40) |
| Code PR touching Cargo/pyproject/deny | ~253 | ~280 | +`audit-pr` ~15 |
| Push to `main` (full wheels) | ~303 (ci + release builds) | ~290 | full wheels (+4 extended ~24) but no release.yml per-push builds anymore |
| Docs-only PR | ~253 | ~12 (changes+docs+hygiene+gate) | −95% |
| Landing-only | ~253 | ~4 (changes+hygiene+gate) | no landing CI; Vercel preview covers it |
| Nightly (off critical path) | 0 | ~95 | audits ~27 + fuzz ~15 + perf 3×~12 + gate overhead |

## 5. Required status checks (owner action)

Set branch protection to require exactly one check: **`ci gate (all green)`**.
Remove all old per-job requirements (old display names are gone). Never
require individual jobs — matrix names shift; the gate aggregates via
`toJson(needs)` over all 10 jobs **including the `wheels` reusable call**,
and fails when `changes` itself is not `success` or on any other
failure/cancelled, while allowing path-gated skips. Nightly/bench/release
stay non-required; perf regressions surface as `perf-regression` issues
(after 2 consecutive failures), not red checks.

## 6. Round-2 verification (round-3 deltas re-verified)

- `actionlint` 1.7.12 at repo root: clean (run after all edits).
- `python -c yaml.safe_load` on all 6 workflow files: OK.
- `python tools/check_repo_hygiene.py`: `hygiene OK`.
- `python tools/ci_gate.py --self-test`: 7/7 pass, incl. the required case
  `changes=failure + all others skipped => gate fails`.
- `git diff --stat HEAD -- tests/`: empty (golden untouched).
- Tag-gating by inspection: `pypi-publish`/`github-release`
  `if: startsWith(github.ref, 'refs/tags/v')`; `version-check` strict on
  tags, trivially green on branch dispatch (dry run builds wheels + SBOM).
- `mkdocs` 1.6.1 present locally — `mkdocs build --strict` runnable as an
  extra check (docs job covers it in CI).
- Follow-ups: first nightly run must confirm `deny.toml` allowlist +
  `gh` issue flow (needs `issues: write`, granted); owner sets the single
  required check + creates the `vX.Y.Z` tag process (`version-check`
  enforces tag == Cargo.toml).

## 7. Round-4 verification (release hardening + parity teeth)

- `actionlint` 1.7.12 at repo root: clean (two self-inflicted newline
  joins caught and fixed during editing; final run exit 0).
- `python -c yaml.safe_load` on all 6 workflow files: OK.
- `git diff` on `release.yml` `pypi-publish` job / `pypi` env / OIDC /
  tag-only `if:`: empty (byte-identical; only the `concurrency` hunk added).
- `python tools/ci_gate.py --self-test`: 8/8 pass, incl. new
  `failed parity job => gate fails`.
- `tests/parity/conftest.py` hook verified locally against the real suite:
  blocked-tsfresh import skips without the env, fails with
  `KYMORA_REQUIRE_PARITY=1`; unblocked suite passes 2/2 with the env set.
- `git diff --stat HEAD -- tests/`: conftest.py only (new file; golden untouched).
- First-run confirmation for the owner: after pushing, the CI run must show
  jobs `parity external (ubuntu-latest, py3.12)` and
  `ci gate (all green)` both green; the gate name is unchanged so the
  `main protection` ruleset keeps matching.
