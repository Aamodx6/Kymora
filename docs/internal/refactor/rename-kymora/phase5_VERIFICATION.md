# Phase 5 verification — docs + site (2026-10-04)

## Docs IA (mkdocs, deployed by docs.yml to GitHub Pages)

Nav reorganized into spec sections (Getting started / Reference /
Benchmarks / Project); `parity_matrix.md` + `ROADMAP.md` joined the nav;
Changelog/Architecture link out to the single-source root files
(`CHANGELOG.md`, `arch.md`) instead of duplicating them. New `docs/faq.md`
(canonical short answers; JAX note; stability + claims pointers).
Historical reports (`arch_audit`, `timeline_progress`, `redundancy_report`,
`REFACTOR_STATE`, refactor records) stay intentionally un-nav'd —
`mkdocs build --strict` exit **0**, INFO-only.

Reference pages are hand-maintained (no mkdocstrings plugin); the stub
surface is instead enforced by `test_core_stubs_ship_and_cover_every_exported_function`.
`docs/api.md` signature-only fences are marked `skip` so the snippet
runner only executes real programs.

## Snippets executed in CI (new)

`tools/check_snippets.py` (stdlib): README + top-level `docs/*.md`,
shared namespace per file in document order, doctest support, `skip` /
`timeout=` flags. Local: **20 executed, 15 skipped, 0 failed**.
Wired as a `snippets` job in `ci.yml` (test extras + scikit-learn).
Fixed real bugs it found:
- README streaming used `StreamingExtractor(capacity=…)` — real kwarg is
  `window_size` (also fixed the same mistake nowhere else; competitor-side
  `autocorrelation__lag_*` names verified correct in context).
- README `describe_feature("autocorrelation__lag_1")` → `autocorr_lag_1`.
- sklearn/streaming blocks made self-contained (synthetic data inline);
  `migrating.md` tsfresh block marked skip (needs tsfresh + user data),
  ragged block given its own data; `nan-policy.md` converted to proper
  doctest form; `quickstart.md` sklearn cell given labels.
- Removed "Seamless" from `docs/quickstart.md` (spec copy rule; the only
  occurrence outside the arch policy text itself).

## Claims audit

README numbers = F1 artifact (3.18 ms / 314,450 s/s / 262× / 6,570×, hardware
stated); 800k/14,000× figures survive only in `CLAIMS.md` "superseded" rows
and arch F1 (resolved). Landing figures current + labeled exploratory.
Fixed one stale README anchor (`#streaming--sliding-windows` →
`#streaming-real-time-telemetry`).

## Site (landing/, Vercel)

- **Retired the duplicate docs portal** (`landing/src/docs/**`, 33 files):
  it duplicated `docs/` while the mkdocs site deploys separately. `main.tsx`
  router removed; Nav Docs links → canonical docs site; `/docs/*` **redirects**
  (permanent, vercel.json) to it; `react-router-dom` + `marked` + `mermaid`
  uninstalled (bundle 1.4 MB → 324 KB JS).
- **SEO basics:** canonical, OG + Twitter tags, `SoftwareApplication`
  JSON-LD, `robots.txt`, `sitemap.xml` (all in `dist/` — verified).
  OG image reuses the throughput figure; a proper 1200×630 card + a real
  domain (still the default vercel.app URL) stay NEEDS-OWNER.
- **Slop removal** (arch §14.4): CTA glow blobs deleted, pill tag →
  `rounded-md`. Kept functional bits (sticky-nav blur, list dots).
- **Link check** (stdlib script): 16 internal links + nav files — clean
  after the README anchor fix above.

## Lighthouse (desktop preset, local `dist/` server, Chrome stable)

| Performance | Accessibility | Best practices | SEO |
|---|---|---|---|
| **94** | **100** | **100** | **100** |

Fixed from the first run (93/94): footer `h4`→`h3` heading order, copy-button
`aria-label`s now contain the visible text. Remaining perf drag is lab-local
(no-cache `http.server`, render-blocking Google Fonts, unused Tailwind/JS):
not chased — the rename changes no site assets' weight class beyond the
-1.1 MB router/docs removal. Full JSON kept out of the tree (750 KB);
scores + causes recorded here.

## Gate status

**Phase 5 GATE: PASS** — docs + site build with zero warnings
(`mkdocs --strict` 0, `tsc && vite build` 0), link check clean, Lighthouse
committed above (94/100/100/100; perf <95 documented, cause lab-local),
`pytest 139` still green.
