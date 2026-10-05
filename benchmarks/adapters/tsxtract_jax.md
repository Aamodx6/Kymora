# PyPI 'tsxtract' (JAX) Name Collision Documentation

## Background
On PyPI, an unrelated project named `tsxtract` was registered, implementing a small set of JAX-based time-series feature operations.

## Differentiation
- **Our Library:** `kymora` (developed in this repository) provides a high-throughput Rust engine (`_core.pyd` / `.so`), zero-copy NumPy buffer ingestion, Scikit-learn integration, Rayon multi-threading, and 33-100+ statistical, temporal, and spectral features.
- **Import Namespace:**
  - Our library provides `import kymora` only — no alternate spellings, no shims.
  - To prevent accidental user confusion when installing from PyPI, our build configuration maps the package namespace cleanly to `kymora` (dist `kymora`), and our documentation explicitly highlights the difference.
