# antropy Adapter Tuning Notes

## Library Overview
- **Name:** antropy
- **Version:** >=0.1.6
- **Purpose:** Fast calculation of time-series entropy and complexity metrics (permutation entropy, spectral entropy, sample entropy, svd entropy, hjorth parameters).

## Fast Configuration & Tuning
- **Permutation Entropy:** Uses order=3, delay=1, normalize=True to match Kymora's `permutation_entropy` definition for matched comparisons.
- **Spectral Entropy:** Uses FFT method with sampling frequency `sf=1.0`.
- **Parallelism:** Evaluated in serial per-series calls or multi-threaded batches.
