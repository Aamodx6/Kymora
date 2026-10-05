# Rename release checklist — Kymora (do NOT publish yet)

Owner-gated. Nothing in this file publishes anything; it is the runbook
for the 0.7.0 rename release.

## 1. GitHub repo rename — DONE (owner renamed `Tsxtract` → `Kymora`)

GitHub kept redirects; the local remote is updated. Remaining: re-run the
docs workflow once to republish the mkdocs site under
`aamodx6.github.io/Kymora/`; confirm the linked repo in the Vercel
dashboard. Canonical account (`Aamod007` bylines) still NEEDS-OWNER.

## 2. PyPI trusted publishing for `kymora` (owner, web UI)

`.github/workflows/release.yml` publishes via OIDC (`environment: pypi`,
no stored token). PyPI trusted publishers are per-project, so the NEW
project needs its own entry:

1. Ship 0.7.0 to `main` first (this branch), tag `v0.7.0` only when the
   release notes are ready.
2. On PyPI, create project `kymora` (first upload) OR pre-register a
   trusted publisher: owner/repo `Aamodx6/Kymora`, workflow
   `release.yml`, environment `pypi`.
3. Publish a GitHub Release `v0.7.0` → workflow builds the matrix and
   uploads `kymora 0.7.0` wheels. Verify:
   fresh venv → `pip install kymora` → `import kymora` works,
   `import tsxtract` warns and works.

## 3. `tsxtract-rs` finale — CANCELLED (owner deleted the PyPI project)

PyPI never allows re-registering a deleted project name, so no 0.6.1
deprecation release is possible. `pip install tsxtract-rs` now fails with
"not found". The migration path is docs-only: CHANGELOG 0.7.0, the
`import tsxtract` shim inside `kymora`, and `docs/migrating.md`.

## 4. Removal schedule (already recorded in CHANGELOG)

- Old import names (`tsxtract`, `tsxtractor`) and the `TsxSelector` alias:
  deleted outright, no removal window. `tsxtract-rs` the PyPI project was
  deleted by the owner (name can never be re-registered).

## 5. Post-publish verification (paste output into the release notes PR)

- `pip download kymora==0.7.0 --no-deps` + clean-venv `import kymora`.
- `feature_names()` sha256 still
  `8a1e27942b370ec886130db4f19ca973b2a1b36ea17823723c9d7afd1431af2e`.
- README quickstart blocks 1–4 verbatim in the clean venv.
