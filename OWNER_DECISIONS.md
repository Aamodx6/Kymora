# Owner Decisions Required — Kymora Hardening

Actions in this file require the repository owner's explicit decision.
**Do NOT execute any of these automatically.**

---

## 1. Canonical Identity

### Findings (Task 7.1)
*(To be populated during Phase 7)*

### Decision needed
- Which GitHub account is canonical: `Aamodx6` or `Aamod007`?
- Is `Kymora` the final product name? (Trademark/domain check recommended)
- Domain: currently on default Vercel domain — acquire `kymora.dev` or similar?

---

## 2. Patent Folder

### Status
The `patent/` directory exists in the public repository.
*(File listing to be added in Task 7.6 — file names only, no content)*

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
