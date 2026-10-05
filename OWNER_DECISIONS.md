# Owner Decisions Required — Kymora Hardening

Actions in this file require the repository owner's explicit decision.
**Do NOT execute any of these automatically.**

---

## 1. Canonical Identity

### Findings (Task 7.1, 2026-10-06 full-tree grep)

Remote `origin` is `https://github.com/Aamodx6/Kymora.git` (rename done).
Live code (`src/`, `python/`, `landing/src/`, `tools/` minus the rename
script itself, `.github/`, `mkdocs.yml`, `pyproject.toml`) is clean: no
`tsxtract`/`tsxtractor`/`TsxSelector`/`TSXTRACT` outside intentional spots
(the rename tool `tools/rename_to_kymora.py`, the gone-names assertion
test, frozen benchmark evidence, refactor records).

| Location | Occurrence | Proposed replacement | Action |
|---|---|---|---|
| `CHANGELOG.md` link targets (10) | `Aamodx6/Tsxtract/compare/...` | `Aamodx6/Kymora/compare/...` | FIXED automatically (task 7.1) |
| `README.md:282` byline | `github.com/Aamod007` | owner to decide | NEEDS OWNER |
| `landing/.../Footer.tsx:165` byline | `github.com/Aamod007` | owner to decide | NEEDS OWNER |
| `paper/paper.md`, `paper/main.tex` | old name + `Aamodx6/Tsxtract` URLs + stale numbers | full rewrite | DEFERRED to task 8.2 (JOSS restructure) |
| `docs/refactor/**`, `benchmarks/results/**` | historical records | none (frozen evidence) | LEFT AS IS |
| `CHANGELOG.md` prose (§0.5.0–0.7.0) | rename history narrative | none (history) | LEFT AS IS |

### Decision needed
- Which GitHub account is canonical: `Aamodx6` or `Aamod007`?
  (`Aamodx6` owns the repo + all repo URLs; `Aamod007` appears only in two
  personal bylines. Proposed: keep `Aamodx6` for repo identity; owner
  confirms whether bylines move.)
- JOSS submission needs a valid ORCID for the author (the old paper draft
  carried placeholder `0009-0000-0000-0000`, removed in the 8.2 rewrite).
  Owner to provide or drop.
- Is `Kymora` the final product name? (Trademark check recommended before
  launch: USPTO/TMView search for "Kymora" in software classes + `kymora.dev`
  / `kymora.ai` domain availability. Do not print merch, file, or announce
  until cleared.)
- Domain: currently on default Vercel domain — acquire `kymora.dev` or similar?

---

## 2. Patent Folder

### Status (Task 7.6 — file names only, content untouched and unread)
The `patent/` directory exists in the public repository and contains one file:

- `patent/patent_disclosure.md`

No file in `patent/` was read, modified, moved, or deleted during this
hardening pass.

### Decision needed
- Keep patent/ in the public repo?
- Move to a private repo?
- Remove entirely?

> [!CAUTION]
> Public release of source code can affect patentability. Consult an IP
> attorney before the next public release.

---

## 3. PyPI Trusted Publisher Setup

### Required before release
- Configure PyPI Trusted Publishing (OIDC) for `kymora` package
- GitHub repository: `Aamodx6/Kymora` (or canonical once decided)
- Workflow file: `.github/workflows/release.yml`
- Environment: `pypi` (or `release`)

### Steps (owner-only)
1. Go to pypi.org/manage/project/kymora/settings/publishing/
2. Add GitHub as a trusted publisher
3. Set repository, workflow filename, environment name

---

## 4. Tag + Publish

### Pre-publish checklist
- [ ] All CI green on `hardening/kymora-v-next`
- [ ] Golden files unchanged
- [ ] CLAIMS.md reconciled
- [ ] CHANGELOG entry complete
- [ ] Version bumped in Cargo.toml
- [ ] Owner reviews OWNER_DECISIONS.md items 1-3

### Steps (owner-only)
1. Merge `hardening/kymora-v-next` → `main`
2. `git tag v0.8.0` (or next version per CHANGELOG convention)
3. `git push origin v0.8.0`
4. Monitor release workflow

### Cleanup note (2026-10-06, repo-cleanup branch)
A local `v0.8.0` tag already exists pointing at `9b9e104` (pre-cleanup tree).
It was NOT pushed and must NOT be pushed as-is: after the cleanup branch is
merged, delete it locally (`git tag -d v0.8.0`) and recreate it on the final
merged commit before publishing, otherwise the release would ship
pre-cleanup tree state.

---

## 5. Benchmark Hardware

### Current state
All benchmark numbers are from a single Windows laptop (i7-13620H), marked
"exploratory" per arch.md §11.7. Authoritative numbers require:
- Dedicated Linux machine with performance governor
- macOS arm64 (Apple Silicon) for aarch64 numbers

### Decision needed
- Run benchmarks on Linux CI (GitHub Actions ubuntu-latest) for non-exploratory numbers?
- Acquire/use a dedicated benchmark machine?
- Accept exploratory-only numbers for initial release?

---

## 6. Launch Timing

### Pre-launch checklist
- [ ] PyPI package published
- [ ] Documentation site deployed
- [ ] Landing page updated and deployed
- [ ] README badges working
- [ ] All CLAIMS.md items have artifacts or are marked PENDING

### Channels (drafts in docs/launch/)
- Show HN post
- r/Python post
- r/rust post
- Blog post
- sktime/aeon integration issues

### Decision needed
- When to launch?
- Stagger posts or simultaneous?
- Include paper submission timing?
