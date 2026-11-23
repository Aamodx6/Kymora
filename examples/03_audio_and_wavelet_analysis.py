"""Cepstral and Continuous Wavelet Transform (CWT) Analysis with Kymora.

Demonstrates extraction of specialized audio, acoustic, and biomedical features:
1. Mel-Frequency Cepstral Coefficients (MFCC, 12 coefficients).
2. Linear Prediction Cepstral Coefficients (LPCC, 12 coefficients).
3. Continuous Wavelet Transform (CWT) energy, variance, and entropy across 9 dyadic scales.
"""

import kymora
from kymora.datasets import load_dataset


def main():
    print("=" * 75)
    print("CEPSTRAL & CONTINUOUS WAVELET TRANSFORM (CWT) EXTRACTION")
    print("=" * 75)

    # Load patient ECG heartbeats
    X_train, y_train = load_dataset("ECG200", split="train")
    patient_signal = X_train[:5]

    features_to_extract = [
        # Statistical baseline
        "mean", "std", "root_mean_square",
        # Mel-Frequency Cepstral Coefficients
        "mfcc_0", "mfcc_1", "mfcc_2", "mfcc_3",
        # Linear Prediction Cepstral Coefficients
        "lpcc_0", "lpcc_1", "lpcc_2",
        # Continuous Wavelet Transform (Ricker mexh wavelet)
        "wavelet_energy_scale_1", "wavelet_energy_scale_2", "wavelet_energy_scale_4",
        "wavelet_entropy",
    ]

    df = kymora.extract_features_df(patient_signal, features=features_to_extract, fs=100.0)
    print(f"\nExtracted {df.shape[1]} cepstral and wavelet features for 5 patient records:")
    print(df.round(4).to_string())


if __name__ == "__main__":
    main()
