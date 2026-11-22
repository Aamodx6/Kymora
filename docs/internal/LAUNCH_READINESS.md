# Kymora Launch Readiness & Final Audit Report

> **Document Version:** 1.0.0 (v0.8.2 Release Candidate)  
> **Date:** 2026-11-22  
> **Status:** READY FOR HUMAN MAINTAINER GATES (All automated technical gates GREEN)

---

## 1. Executive Summary

All 10 preparation phases have been completed and verified across clean CI environments on Linux, macOS, and Windows. Every numerical claim traces directly to committed frozen artifacts with hardware telemetry in `CLAIMS.md`. Ambiguous phrases ("zero-copy", unbacked superlatives) and stale benchmark numbers have been audited with zero hits remaining across the repository.

Technical readiness is **100% GREEN**. Automated operations must now **STOP** at the human gates detailed in Section 3.

---

## 2. Comprehensive Gate Verification Matrix

| Area | Check / Gate | Status | Evidence / Artifact Link | Notes |
|---|---|---|---|---|
| **Hygiene** | Root directory cleanliness | **GREEN** | `tools/check_repo_hygiene.py` | Root strictly restricted to standard distribution files. |
| **Hygiene** | Stale name & number denylist | **GREEN** | `tools/check_repo_hygiene.py` | 0 occurrences of deprecated names, unpooled throughputs, or banned phrases. |
| **Versions** | Cross-manifest version sync | **GREEN** | `tools/check_versions.py` | Exact `0.8.2` match across Cargo.toml, pyproject dynamic, CITATION, Zenodo, docs. |
| **Evidence** | Numeric claims traceability | **GREEN** | `tools/check_claims.py` | All 136 numbers in docs/README trace 100% to `CLAIMS.md`. |
| **Banned Phrases** | Terminology audit | **GREEN** | Local script audit (`re.search`) | 0 unpermitted hits for `zero-copy`, `beats`, `outperforms`. |
| **Docs** | Strict MkDocs build | **GREEN** | `mkdocs build --strict` | Site builds cleanly in < 1 second with zero markdown or link errors. |
| **Docs** | Documentation link integrity | **GREEN** | `tools/check_docs_links.py` | All internal relative links and anchor headers verified. |
| **Paper** | JOSS manuscript & claims sync | **GREEN** | `paper/gen_numbers.py --check` | `paper/paper.md` numbers match CLAIMS; citeproc compiles cleanly. |
| **Preprint** | LaTeX arXiv preprint | **GREEN** | `paper/arxiv/main.tex` | Formatted two-column preprint with BibTeX citations. |
| **Build** | Rust fmt, clippy, unit tests | **GREEN** | CI job `rust fmt, clippy, tests` | Zero clippy warnings under `-D warnings`. |
| **Build** | Multi-arch binary wheel matrix | **GREEN** | CI job `wheels` (`wheels.yml`) | Linux (`x86_64`, `aarch64`), macOS (`x86_64`, `arm64`), Windows (`x64`). |
| **Build** | Source distribution (`sdist`) | **GREEN** | CI job `sdist verify and install` | Source tarball builds and installs cleanly on fresh runners. |
| **Runtime** | Cross-platform Python test matrix | **GREEN** | CI matrix `test (py3.10..3.14)` | 44 matrix jobs across Linux, macOS, and Windows all PASS. |
| **Runtime** | Python 3.13 free-threaded (`cp313t`) | **DOCUMENTATION-ONLY** | CI job `test freethreaded` | Documented limitation: PyO3 0.23 requires CPython >= 3.14 for free-threaded builds (`PyO3 does not support the free-threaded build of CPython versions below 3.14`). PyO3 module has `#[pymodule(gil_used = false)]` configured for thread safety under 3.14t+. |
| **Correctness** | Parity gate (numerical agreement) | **GREEN** | CI job `parity external` | Relative errors $\le 10^{-11}$ across tsfresh, TSFEL, Numba, NumPy. |
| **Performance** | Automated regression gate | **GREEN** | CI job `benchmark regression gate` | 7% budget monitored with `github-action-benchmark`. |
| **Reproduction** | One-command reproduction suite | **GREEN** | `reproduce.sh` in `validation-report` | Runs parity gate, benchmarks, and outputs ratio table in CI. |
| **Release** | Release dry run & verification | **GREEN** | `scripts/verify_release.py` / `.sh` | Verified sdist inspection, checksums, and clean venv installation. |
| **Release** | Hardened release workflow | **GREEN** | `.github/workflows/release.yml` | Default `dry_run: true`; production publish restricted to tags + environment review. |
| **Archival** | Zenodo metadata readiness | **GREEN** | `.zenodo.json` | Valid metadata matching `CITATION.cff`. |
| **Community** | Good First Issue drafts | **GREEN** | `docs/internal/issues/` (12 issues) | Complete specifications with formulas, acceptance criteria, test cases. |
| **Launch** | Platform-specific launch drafts | **GREEN** | `docs/launch/` (8 documents) | Tailored posts with parity-gated tables, UCR tradeoffs, and FAQ. |
| **Operations** | Operational launch runbook | **GREEN** | `docs/launch/launch_runbook.md` | Staged roll-out schedule, maintainer SLA (<2h), dispute protocol. |

---

## 3. Honest Loss Ledger Summary

In compliance with Kymora evidence rules, all performance losses and scaling plateaus are published prominently in documentation and launch drafts:

1. **Small-Batch Single-Call Overhead ($1 \times 10$)**:
   - **Result:** Numba JIT is faster than Kymora (Numba 3.00 µs vs Kymora 5.90 µs).
   - **Cause:** Fixed Python/Rust FFI crossing latency dominates on tiny arrays ($N=1, L=10$).
   - **Remediation:** Dedicated `extract_one` was introduced for single series, achieving 3.90 µs at $1 \times 100$. For $N=1, L \le 10$, an inlined JIT loop remains faster.
2. **Hybrid P/E-Core Thread Scaling**:
   - **Result:** On hybrid Intel Core i7-13620H (6P+4E / 16 threads), 16 threads (2.30 ms) is slower than 8 threads (2.22 ms), running at 30.5% scaling efficiency.
   - **Cause:** Rayon chunks scheduled on low-frequency Efficient cores delay barrier synchronization across threads.
   - **Remediation:** Documented openly with recommendations to pin threads to physical Performance cores (`taskset` or `ProcessAffinityMask`) on hybrid chips.
3. **Accuracy vs Extraction Time Tradeoff (UCR-42)**:
   - **Result:** Kymora `core33` attains 0.771 accuracy (rank 2.76) vs `tsfresh` 0.824 (rank 1.48) and `TSFEL` 0.812 (rank 2.07).
   - **Tradeoff:** `tsfresh` extracts 777 features and `TSFEL` extracts 285 features (vs 33 in Kymora). Kymora extracts at ~100× lower runtime than `catch22` (0.767, rank 2.69) and $>1,000\times$ faster than `TSFEL`/`tsfresh`. For exploratory tasks where latency is unconstrained, larger banks hold higher raw accuracy; for production inference budgets, `core33` offers strong accuracy per millisecond.

---

## 4. Human-Only Action Checklist (STOP HERE)

The automated maintainer agents must **NOT** execute the following steps. Each requires an explicit human instruction or external authorization:

### 1. Patent Counsel Review
- [ ] Confirm with patent counsel whether untracked content in `patent/` or prior commit history has exposure risks before repository launch. (Repo root contains no patent materials; `patent/` remains untracked and excluded).

### 2. Independent Hardware Reproduction
- [ ] Have an independent outside collaborator clone the repository and run `./reproduce.sh` on distinct hardware (e.g., Linux bare-metal server, Apple Silicon M-series Mac).
- [ ] Run `scripts/cloud_bench.sh` on a 32-core or 64-core cloud instance (AWS `c6i.16xlarge` or GCP `c2-standard-60`) to obtain multi-socket thread scaling numbers.
- [ ] Commit hardware artifacts to `benchmarks/results/` and run `python tools/check_claims.py`.

### 3. GitHub "pypi" Environment Protection & Release Tag
- [ ] Go to **GitHub Settings → Environments → `pypi`**.
- [ ] Add required reviewers (maintainer GitHub username) so any deployment to PyPI requires explicit two-person approval.
- [ ] When ready to release, push the official git tag:
  ```bash
  git tag -a v0.8.2 -m "Kymora 0.8.2 release"
  git push origin v0.8.2
  ```
- [ ] Approve the `pypi` deployment in GitHub Actions.
- [ ] After publication, run the post-release verification script in fresh virtual environments:
  ```bash
  bash scripts/verify_release.sh 0.8.2 pypi
  python scripts/verify_release.py --version 0.8.2 --install pypi
  ```

### 4. Zenodo Archival DOI Integration
- [ ] Log in to [Zenodo](https://zenodo.org/) using your GitHub account.
- [ ] Go to **GitHub Settings → Applications → Authorized OAuth Apps → Zenodo** and enable archiving for `Aamodx6/Kymora`.
- [ ] Trigger archiving on the release tag `v0.8.2`.
- [ ] Copy the generated DOI (e.g., `10.5281/zenodo.XXXXXXX`) and paste it into:
  - `CITATION.cff` (replace `10.5281/zenodo.placeholder`)
  - `README.md` (replace DOI badge URL)
  - `paper/paper.md`
- [ ] Run repository settings configuration:
  ```bash
  bash scripts/gh_repo_settings.sh
  ```

### 5. arXiv and JOSS Submission
- [ ] Submit `paper/arxiv/main.tex` and accompanying figures to arXiv (under `cs.LG` or `stat.ML`). Request endorsement if required.
- [ ] Submit manuscript `paper/paper.md` to JOSS (Journal of Open Source Software) using the tagged release and Zenodo DOI.

### 6. crates.io Publish Decision
- [ ] Decide whether to publish the current `kymora` crate to crates.io now or wait for the planned pure-Rust `kymora-core` split in v0.9.0 (as recommended in `docs/internal/crate_decision.md`).

### 7. Seed Community Issues & Enable Discussions
- [ ] Run the issue creation script to seed the 12 drafted "good first issues":
  ```bash
  bash scripts/create_issues.sh
  ```
- [ ] Go to repository settings and ensure **Discussions** and **Issues** tabs are publicly visible.

### 8. Staged Launch Execution
- [ ] Follow the staged roll-out sequence in `docs/launch/launch_runbook.md`:
  - **Day 1:** Soft technical launch on `/r/rust` (`docs/launch/reddit_rust.md`) and PyData Discourse (`docs/launch/discourse_pydata.md`).
  - **Day 3 (Tuesday/Wednesday 13:00 UTC):** Submit Show HN (`docs/launch/show_hn.md`). Post initial context comment and actively monitor responses (<2h SLA).
  - **Day 4–5:** Broader community posts on `/r/Python`, `/r/MachineLearning`, LinkedIn, and X (`docs/launch/social_threads.md`).
- [ ] Use the Benchmark Dispute Protocol in `launch_runbook.md` to handle any technical inquiries or hardware variations.
