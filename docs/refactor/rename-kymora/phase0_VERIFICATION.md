# Phase 0 verification — rename to Kymora: inventory + baseline (2026-10-04)

Branch: `refactor/rename-kymora` (from `main` @ `6a9f308`). Tag: `pre-rename`.
`main` already contains the merged `refactor/tsxtract` work (merge-base == refactor tip
`88298f5`), so no earlier refactor was redone.

## Inventory (saved in `docs/refactor/rename-kymora/`)

- `INVENTORY.md` — 312 tracked files classified (benchmarks 118, ci 11,
  config-root 18+CLAUDE.md, docs 40, paper-patent 17 DO-NOT-TOUCH, scripts 3,
  site-landing 60, source-python 6, source-rust 23, tests 15);
  `git count-objects -vH` = 26.62 MiB, 0 tracked files >1 MB (working-tree
  size check + `file_classification.txt` agree).
- Secrets: gitleaks/trufflehog not installed here; stdlib regex scan over
  tracked working tree = **no hits**; history scan (last 200 commits) = 0 raw
  matches. Owner should run gitleaks in CI before release.
- Name occurrences (word-boundary, overlapping by construction — `tsxtract-rs`
  and `tsxtractor` contain `tsxtract`): `tsxtract-rs` 116 / `tsxtractor` 123 /
  `tsxtract` 963 / `Tsxtract` 302 / `TSXTRACT` 36. Detail:
  `name_occurrences.txt`.
- Remote: only `origin` = `https://github.com/Aamodx6/Tsxtract.git`. Account
  mix across tree: `Aamod007` 12, `Aamodx6` 71, `aamod007` 4, `aamodx6` 5,
  `aamoddev11` 6 — canonical-account decision stays NEEDS-OWNER.
- `patent/` + `paper/` untouched (17 files), NEEDS-OWNER.
- Pre-existing dirty state at branch time left untouched: `M ci.yml,
  release.yml, STATE.md, bench_matrix.py, LOSS_LEDGER.md, test_invariants.py`
  (B-track/doc-link work) + untracked `benchmarks/results/*` run outputs
  (must stay untracked per repo rule).

## Baseline gates (real output, wheel rebuilt from source first)

The installed wheel was stale (`tsxtract-rs 0.5.0` vs repo `0.6.0`), so per
the CLAUDE.md dev loop the baseline was taken after
`python -m maturin build --release` +
`pip install --force-reinstall --no-deps target/wheels/tsxtract_rs-0.6.0-*.whl`.

| Gate | Result |
|---|---|
| `feature_names()` hash (`sha256(json.dumps(names))`) | **MATCH** `8a1e27942b370ec886130db4f19ca973b2a1b36ea17823723c9d7afd1431af2e` (33 names; first mean/std/var, last dominant_frequency/spectral_centroid/spectral_entropy) |
| `python -m pytest tests -q` | **138 passed** in 31.44s |
| `cargo test --no-default-features` | **16 passed**, 0 failed |
| `cargo fmt --all -- --check` | exit **0** |
| `cargo clippy --no-default-features --all-targets -- -D warnings` | exit **0** |
| `python scripts/validation_report.py` | **All 33 features within tolerance**, exit 0 |
| `python -m mypy python/tsxtract` | clean (4 files), exit 0 |
| `python -m mkdocs build --strict` | exit **0** (INFO-only: un-nav'd pages incl. new INVENTORY.md; pre-existing condition) |

False alarm noted: a first hash probe with `"\n".join` gave `26fc8b…` —
wrong method, not drift. The canonical method (`json.dumps`, as in the
0.5.0 baseline) matches.

## Gate status

**Phase 0 GATE: PASS** — inventory committed; baseline green (after the
documented wheel rebuild); no secret found (pending CI gitleaks);
`patent/`+`paper/` untouched.

## Risks / next

- Dirty B-track files + untracked results stay out of rename commits; final
  `git status` will need reconciling with the owner.
- Owner has confirmed the new name: **Kymora** (Phase 1 name-check still
  runs as evidence, then Phase 2 cleanup).
