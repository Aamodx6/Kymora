# Kymora Naming Audit

**Audit Date:** 2026-11-22  
**Purpose:** Verify namespace status and collisions across PyPI, crates.io, and GitHub prior to v0.8.2 release.  
**Policy:** Read-only inspection via official package index APIs and GitHub CLI. No packages published, reserved, or modified.

---

## 1. PyPI (Python Package Index)

Audited via `python -m pip index versions <package>`:

| Package Name | Status on PyPI | Available Versions | Notes |
| :--- | :--- | :--- | :--- |
| **`kymora`** | **Active (Canonical)** | `0.7.0`, `0.8.0`, `0.8.1` | Owned by maintainer (`Aamodx6`). Sole supported distribution name. |
| `tsxtract` | Collision / External | `0.1.0` | Belongs to an unrelated JAX project by a third party. |
| `tsxtractor` | Abandoned / Old | `0.1.0`, `0.1.1` | Pre-0.5.0 abandoned release. Not used. |
| `tsxtract-rs` | Deleted | None (404) | Deleted namespace on PyPI. Cannot be resolved. |

**Conclusion:** `pip install kymora` is the sole canonical distribution name. No aliases or shims exist or will be published on PyPI.

---

## 2. crates.io (Rust Package Registry)

Audited via crates.io API (`https://crates.io/api/v1/crates/<name>`):

| Crate Name | Status on crates.io | Notes |
| :--- | :--- | :--- |
| **`kymora`** | **Available (404 Not Found)** | Unclaimed. Ready for pure Rust crate workspace split. |
| **`kymora-core`** | **Available (404 Not Found)** | Unclaimed. Candidate name for standalone computation core. |
| `tsxtract` | Available (404 Not Found) | Unclaimed. Do not publish. |
| `tsxtractor` | Available (404 Not Found) | Unclaimed. Do not publish. |
| `tsxtract-rs` | Available (404 Not Found) | Unclaimed. Do not publish. |

**Conclusion:** Both `kymora` and `kymora-core` are completely available on crates.io. Crate publishing decision will be prepared in Phase 6.

---

## 3. GitHub

Audited via GitHub CLI (`gh repo view`):

| Repository | Status | Notes |
| :--- | :--- | :--- |
| **`Aamodx6/Kymora`** | **Active (Canonical)** | Main repository. |
| `Aamodx6/Tsxtract` | Redirect Alias | GitHub automatically redirects `Aamodx6/Tsxtract` to `Aamodx6/Kymora`. |

**Conclusion:** Repository namespace is clean and consolidated under `Aamodx6/Kymora`.
