# Kymora Hardening + Release + Launch-Readiness Plan

**Branch:** `hardening/kymora-v-next`
**Started:** 2026-10-05
**Tracking:** STATUS.md (per-task), OWNER_DECISIONS.md (owner-only actions)

## Codebase State Summary

- **Version:** 0.7.0 (Cargo.toml + pyproject.toml)
- **Rust core:** ~4,063 lines across 21 files in `src/`
- **Python package:** 4 files in `python/kymora/` (~639 lines)
- **Tests:** 19 test files + golden/fixture files (~138 tests reported passing)
- **Benchmarks:** Full harness with 9 adapters, F1_REPORT.md completed 2026-10-04
- **CI:** 4 workflows (ci, release, docs, benchmark)
- **Missing:** py.typed, SECURITY.md, CITATION.cff, STATUS.md, OWNER_DECISIONS.md
- **Key issue:** README still has †-marked stale rows for profiles/scaling/memory
- **Key issue:** Old URLs (Aamod007, Tsxtract) still in CHANGELOG links
- **Key issue:** Landing is a client-rendered SPA (F7)

## Environment Constraints

This is a **Windows development machine** (i7-13620H). Some tasks require:
- Building the Rust extension (`maturin develop --release`) — AVAILABLE
- Running Python tests — AVAILABLE
- Running `cargo test`, `cargo clippy`, `cargo fmt --check` — AVAILABLE
- Running benchmarks against competitor libraries — AVAILABLE but results are "exploratory"
- Linux/macOS CI — NOT AVAILABLE locally, workflows only
- `cargo-fuzz` — Linux-only, will prepare config but cannot run
- `perf`/`samply`/flamegraph profiling — Linux tools, not available here

## Phase Plan

### Phase 1: Benchmark Credibility
| Task | Description | Approach | Estimate |
|------|-------------|----------|----------|
| 1.1 | Equal-feature intersection mapping | Analyze catch22/TSFEL/tsfresh feature lists vs core33, create mapping table | Code + docs |
| 1.2 | Benchmark shared features at 4 shapes | Write benchmark script, run locally (exploratory), save artifacts | Code + run |
| 1.3 | Re-measure †-marked README rows | Run F1 harness for profiles/scaling/memory | Code + run |
| 1.4 | Add numba baseline + "Where Kymora is slower" section | Add to competitive table, document losses honestly | Code + docs |
| 1.5 | Rewrite README benchmark section | Median-first, three tables, honest framing | Docs |
| 1.6 | Add bench.yml CI workflow | Manual dispatch + weekly, ubuntu + macos-14 | Code |
| 1.7 | Propagate figures + add check_claims.py | Cross-reference all docs against CLAIMS.md | Code + docs |

### Phase 2: Streaming Correctness + Performance
| Task | Description | Approach |
|------|-------------|----------|
| 2.1 | Audit StreamingExtractor O(1) guarantees | Review Rust code, fix algorithms | Code |
| 2.2 | Document O(1) vs O(W) per feature | Update README/docs | Docs |
| 2.3 | Streaming vs batch parity tests | Add comprehensive test suite | Code |
| 2.4 | Per-push cost benchmark | Benchmark script + artifact | Code + run |

### Phase 3: Input Surface + Robustness
| Task | Description | Approach |
|------|-------------|----------|
| 3.1 | NaN/Inf/degenerate policy doc | docs/numerics.md + consistent implementation | Code + docs |
| 3.2 | float32 end-to-end support | Audit existing f32 path, add tests | Code |
| 3.3 | Multivariate (n,C,T) input | Audit existing mc path, add labeled output | Code |
| 3.4 | Non-contiguous input handling | Document behavior, add tests | Code + docs |
| 3.5 | Shape/dtype/edge case test matrix | Hypothesis + fuzz-style tests | Code |

### Phase 4: sklearn / Ecosystem
| Task | Description | Approach |
|------|-------------|----------|
| 4.1 | KymoraTransformer in-package | Ship sklearn transformer, estimator checks | Code |
| 4.2 | Optional extras in pyproject | [pandas], [polars], [sklearn], [all] | Config |
| 4.3 | sktime/aeon adapter example | Example + optional test | Code + docs |
| 4.4 | py.typed + type stubs + mypy CI | Complete _core.pyi, add py.typed marker | Code |

### Phase 5: Thread Scaling + Perf Regression
| Task | Description | Approach |
|------|-------------|----------|
| 5.1 | Investigate scaling plateau | Profile if possible, review code | Analysis |
| 5.2 | Data-driven thread default | Benchmark, document recommendation | Code + docs |
| 5.3 | Bisect 0.3.2→0.4.0 slowdown | TODO: requires git bisect + repeated runs | Analysis |
| 5.4 | Benchmark unwired experiments | Run pool.rs, soa_4x against HEAD | Code + run |

### Phase 6: Correctness Assurance
| Task | Description | Approach |
|------|-------------|----------|
| 6.1 | Parity test suite | Compare each feature against reference impls | Code |
| 6.2 | Feature catalog docs | Exact formulas, NaN behavior, equivalents | Code + docs |
| 6.3 | Fuzz/proptest + unsafe audit | cargo-fuzz config, unsafe documentation | Code + docs |
| 6.4 | Cross-platform CI | Expand CI matrix, test against wheels | Config |

### Phase 7: Identity, Packaging, Release
| Task | Description | Approach |
|------|-------------|----------|
| 7.1 | URL/name inconsistency grep | Find and catalog all old names | Analysis |
| 7.2 | CITATION.cff + metadata consistency | Create missing files, align metadata | Config + docs |
| 7.3 | Release prep | Version bump, CHANGELOG, release workflow | Config |
| 7.4 | README sync + badges | Single-source long_description, add badges | Config + docs |
| 7.5 | Security: audits, SECURITY.md, SBOM | Add security infrastructure | Config + docs |
| 7.6 | patent/ folder documentation | Document without touching content | Docs |

### Phase 8: Docs, Paper, Launch Assets
| Task | Description | Approach |
|------|-------------|----------|
| 8.1 | Refresh/add documentation pages | All 8 doc categories | Docs |
| 8.2 | JOSS paper restructure | paper.md + paper.bib with traceable numbers | Docs |
| 8.3 | Launch kit | HN, Reddit, blog drafts, integration issues | Docs |
| 8.4 | Landing page update | Match CLAIMS.md, add limitations section | Code |

## Execution Strategy

1. **Commit discipline:** One commit per task (N.M format), run gates before each
2. **Frozen numerics:** Never change core33 output — verify golden files after every change
3. **No fabrication:** All numbers from artifacts or marked TODO/PENDING
4. **Owner actions:** Logged in OWNER_DECISIONS.md, never executed
5. **Priority:** Phase 1 (credibility) and Phase 6 (correctness) are highest priority
   as they directly affect trustworthiness. Phase 7 (packaging) and Phase 8 (docs)
   are primarily documentation work.

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Cannot run benchmarks (competitor deps) | Install in venvs, run exploratory |
| cargo-fuzz unavailable on Windows | Prepare config, mark as CI-only |
| profiling tools unavailable | Code review + instrumented timers instead |
| Build failures in maturin | Already working per CLAUDE.md dev loop |
| Test failures from changes | Run full gate before each commit |
