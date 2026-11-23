# Kymora Production Examples

This directory contains standalone, end-to-end Python examples demonstrating how to use Kymora in real-world data science, machine learning, and time-series engineering workflows.

All examples use **real-world empirical datasets** (cardiology ECG, video motion capture, etc.) and require zero synthetic generation.

---

## Example Catalog

| Script | Title | Description | Key Modules |
| :--- | :--- | :--- | :--- |
| [`01_quickstart_feature_extraction.py`](01_quickstart_feature_extraction.py) | **Quickstart & Domain Extraction** | Extract statistical, temporal, and spectral features using both fast Rust profiles and scientific domains. | `kymora.extract_features_df`, `domain="statistical"` |
| [`02_tsfel_drop_in_migration.py`](02_tsfel_drop_in_migration.py) | **100% TSFEL Drop-In Migration** | Migrate existing TSFEL pipelines with a single import change (`from kymora.compat import tsfel`). | `kymora.compat.tsfel`, `get_features_by_domain` |
| [`03_audio_and_wavelet_analysis.py`](03_audio_and_wavelet_analysis.py) | **Cepstral (MFCC/LPCC) & Wavelet (CWT)** | Extract acoustic mel filterbank cepstral coefficients, LPCC autoregressive coefficients, and dyadic Ricker CWT wavelets. | `mfcc_*`, `lpcc_*`, `wavelet_*` |
| [`04_real_world_classification.py`](04_real_world_classification.py) | **End-to-End ML Pipeline** | Load canonical UCR datasets (`GunPoint`), extract features at SIMD speeds, prune collinear features, and train a Random Forest classifier. | `kymora.datasets.load_dataset`, `kymora.utils.correlated_features`, `scikit-learn` |

---

## Running the Examples

Run any example directly with standard Python:

```bash
# 1. Quickstart feature extraction
python examples/01_quickstart_feature_extraction.py

# 2. TSFEL drop-in replacement pipeline
python examples/02_tsfel_drop_in_migration.py

# 3. Audio & biomedical wavelets (MFCC, LPCC, CWT)
python examples/03_audio_and_wavelet_analysis.py

# 4. End-to-end classification on real UCR benchmarks
python examples/04_real_world_classification.py
```
