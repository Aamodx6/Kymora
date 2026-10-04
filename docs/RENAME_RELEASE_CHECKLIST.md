# Rename release checklist — Kymora (do NOT publish yet)

Owner-gated. Nothing in this file publishes anything; it is the runbook
for the 0.7.0 rename release and the `tsxtract-rs` deprecation tail.

## 1. GitHub repo rename (owner, ~5 min)

1. Repo Settings → General → Repository name: `Tsxtract` → `Kymora`.
   GitHub keeps redirects (`github.com/Aamodx6/Tsxtract/*` → `.../Kymora/*`),
   stars, watchers, and forks automatically.
2. Each clone updates its remote once:
   `git remote set-url origin https://github.com/Aamodx6/Kymora.git`
   (old URL keeps working via redirect, but update to avoid confusion).
3. GitHub Pages (mkdocs site): the site URL changes
   `aamodx6.github.io/Tsxtract/` → `aamodx6.github.io/Kymora/`
   (`mkdocs.yml` `site_url`/`repo_url` already point at `Kymora`).
   After the rename, re-run the docs workflow once to republish under the
   new path; the old path 404s (no redirect for project pages — note in
   Phase 5 site redirects if it matters).
4. Vercel (`landing/`): the project follows the GitHub rename via redirect,
   but confirm the linked repo + production domain in the Vercel dashboard.
5. Canonical account (`Aamodx6` vs `Aamod007` bylines/footers) is still
   NEEDS-OWNER — independent of the rename.

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

## 3. `tsxtract-rs` final deprecation release (0.6.1, owner)

One last release under the OLD dist name so existing users get a guided
path instead of a dead end. Layout (separate throwaway packaging dir,
not this repo tree):

```toml
# pyproject.toml (tsxtract-rs 0.6.1)
[project]
name = "tsxtract-rs"
version = "0.6.1"
dependencies = ["kymora>=0.7.0"]
```

```python
# tsxtract/__init__.py + tsxtractor/__init__.py (in the 0.6.1 sdist)
import warnings
warnings.warn(
    "tsxtract-rs is renamed to kymora; pip install kymora "
    "and use `import kymora`. This shim will not be updated further.",
    DeprecationWarning, stacklevel=2,
)
from kymora import *  # noqa
```

Publish with the EXISTING `tsxtract-rs` trusted publisher (unchanged).
No further `tsxtract-rs` releases after 0.6.1.

## 4. Removal schedule (already recorded in CHANGELOG)

- `import tsxtract` shim: removal >= **0.8.0** (`tsxtractor` already deleted).
- `TsxSelector` alias: removal >= **0.8.0**.
- `tsxtract-rs` 0.6.1 shim dist: no updates, ever.

## 5. Post-publish verification (paste output into the release notes PR)

- `pip download kymora==0.7.0 --no-deps` + clean-venv
  `import kymora` / `import tsxtract` (warns).
- `feature_names()` sha256 still
  `8a1e27942b370ec886130db4f19ca973b2a1b36ea17823723c9d7afd1431af2e`.
- README quickstart blocks 1–4 verbatim in the clean venv.
