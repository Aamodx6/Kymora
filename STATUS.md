# Kymora Hardening — Status Tracker

**Branch:** `hardening/kymora-v-next`
**Last updated:** 2026-10-05T10:24Z

## Legend
- ✅ Done
- 🔄 In progress
- ⬜ Not started
- ⏭️ Skipped (with reason)
- 🚫 Blocked (with reason)

## Phase 0: Setup
| Task | Status | Notes |
|------|--------|-------|
| Read all ground-rule files | ✅ | CLAUDE.md, arch.md, CLAIMS.md, CHANGELOG.md, Cargo.toml, pyproject.toml, Makefile, workflows, F1_REPORT.md |
| Create branch | ✅ | `hardening/kymora-v-next` |
| Write PLAN.md | ✅ | |
| Write STATUS.md | ✅ | This file |
| Create OWNER_DECISIONS.md | ✅ | |

## Phase 1: Benchmark Credibility
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 1.1 Equal-feature mapping | ⬜ | | |
| 1.2 Benchmark shared features | ⬜ | | |
| 1.3 Re-measure † rows | ⬜ | | |
| 1.4 Numba baseline + losses | ⬜ | | |
| 1.5 Rewrite README bench section | ⬜ | | |
| 1.6 bench.yml CI workflow | ⬜ | | |
| 1.7 Propagate figures + check_claims.py | ⬜ | | |

## Phase 2: Streaming Correctness + Performance
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 2.1 Audit StreamingExtractor O(1) | ⬜ | | |
| 2.2 Document O(1) vs O(W) | ⬜ | | |
| 2.3 Streaming vs batch tests | ⬜ | | |
| 2.4 Per-push cost benchmark | ⬜ | | |

## Phase 3: Input Surface + Robustness
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 3.1 NaN/Inf policy doc | ⬜ | | |
| 3.2 float32 support | ⬜ | | |
| 3.3 Multivariate input | ⬜ | | |
| 3.4 Non-contiguous handling | ⬜ | | |
| 3.5 Shape/dtype test matrix | ⬜ | | |

## Phase 4: sklearn / Ecosystem
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 4.1 KymoraTransformer | ⬜ | | |
| 4.2 Optional extras | ⬜ | | |
| 4.3 sktime/aeon adapter | ⬜ | | |
| 4.4 py.typed + stubs + mypy | ⬜ | | |

## Phase 5: Thread Scaling + Perf Regression
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 5.1 Scaling plateau investigation | ⬜ | | |
| 5.2 Thread default | ⬜ | | |
| 5.3 Bisect 0.3.2→0.4.0 | ⬜ | | |
| 5.4 Benchmark experiments | ⬜ | | |

## Phase 6: Correctness Assurance
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 6.1 Parity test suite | ⬜ | | |
| 6.2 Feature catalog docs | ⬜ | | |
| 6.3 Fuzz/proptest + unsafe audit | ⬜ | | |
| 6.4 Cross-platform CI | ⬜ | | |

## Phase 7: Identity, Packaging, Release
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 7.1 URL/name grep | ⬜ | | |
| 7.2 CITATION.cff + metadata | ⬜ | | |
| 7.3 Release prep | ⬜ | | |
| 7.4 README sync + badges | ⬜ | | |
| 7.5 Security infrastructure | ⬜ | | |
| 7.6 patent/ documentation | ⬜ | | |

## Phase 8: Docs, Paper, Launch Assets
| Task | Status | Commit | Notes |
|------|--------|--------|-------|
| 8.1 Documentation refresh | ⬜ | | |
| 8.2 JOSS paper | ⬜ | | |
| 8.3 Launch kit | ⬜ | | |
| 8.4 Landing page | ⬜ | | |
