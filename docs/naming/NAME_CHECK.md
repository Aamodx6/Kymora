# Name check — Kymora / Tachyra / Aevra (2026-10-04)

Script: `tools/name_check.py` (stdlib only). Raw JSON:
`docs/refactor/rename-kymora/NAME_CHECK_RAW.json`.
Command: `python tools/name_check.py --out docs/refactor/rename-kymora/NAME_CHECK_RAW.json Kymora Tachyra Aevra`

Variants checked per candidate: `name`, `name-rs`, `py<name>`, `<name>-py`,
plus hyphen/underscore/PEP 503 normalizations (all normalize identically —
no hidden collisions).

## Registry results (live, 2026-10-04)

| Candidate | PyPI (`name`, `-rs`, `py-`, `--py`) | crates.io (same) | npm (same) | `import <name>` |
|---|---|---|---|---|
| **Kymora** | FREE (404 ×6) | FREE (404 ×6) | FREE (404 ×6) | FREE (fails as required) |
| Tachyra | FREE (404 ×6) | FREE (404 ×6) | FREE (404 ×6) | FREE (fails as required) |
| Aevra | FREE (404 ×6) | FREE (404 ×6) | FREE (404 ×6) | FREE (fails as required) |

## GitHub (api.github.com, unauthenticated)

| Candidate | Repo search (`<name> in:name`) | `users/<name>` | `orgs/<name>` |
|---|---|---|---|
| Kymora | 0 hits, no exact-name repos | TAKEN (existing user) | FREE (404) |
| Tachyra | 0 hits, no exact-name repos | TAKEN (existing user) | FREE (404) |
| Aevra | 0 hits, no exact-name repos | TAKEN (existing user) | FREE (404) |

`users/<name>` being taken only means that *username* is unavailable — it
does not block renaming the repo under the owner's account (`Aamodx6/...`;
GitHub keeps redirects and stars). No conflicting repo named Kymora exists.

## Domains (RDAP via rdap.org)

| Candidate | .com | .dev | .io | .org |
|---|---|---|---|---|
| Kymora | TAKEN | TAKEN | likely FREE | TAKEN |
| Tachyra | TAKEN | likely FREE | likely FREE | TAKEN |
| Aevra | TAKEN | TAKEN | likely FREE | TAKEN |

Domain ownership is informative only — the project ships on PyPI/crates.io
plus docs/landing hosting, not on a standalone domain.

## Manual items for the owner (not scriptable)

1. **Trademark search:** WIPO Global Brand Database, IP India, USPTO —
   classes 9 and 42 — for "Kymora".
2. **Web search:** "Kymora python / rust / library" (known non-software uses
   exist, e.g. game-modding names — confirm no conflicting software library).
3. **Meaning/pronunciation sanity check** in major languages.
4. PyPI search-result skim for near-neighbours of `kymora` (typosquat view).

## Ranking + recommendation

1. **Kymora (recommended)** — clean on all three registries in every
   variant, no repo conflicts, `.io` free. Owner-confirmed 2026-10-04.
2. Tachyra — equally clean, `.dev`+`.io` free; fallback.
3. Aevra — equally clean; fallback.

## Gate

**Phase 1 GATE: PASS** — owner confirmed the final name: **Kymora**.
Everything below uses `<newname> = kymora` (import/distinct forms:
`Kymora` display, `KYMORA` env prefix, `kymora` PyPI dist,
`kymora` crate, `pykymora` reserved, `kymora-py` reserved).
