"""End-to-End Time-Series Classification Pipeline on Real-World Datasets.

Workflow:
1. Load real-world time-series data from UCR archive (ECG200 cardiology records).
2. Extract high-discriminative feature representations with Kymora in milliseconds.
3. Prune collinear redundant features using unsupervised correlation clustering.
4. Train Random Forest and Ridge classifiers and evaluate test accuracy and Macro-F1.
"""

import time
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.preprocessing import StandardScaler

import kymora
from kymora.datasets import load_dataset
from kymora.utils import correlated_features


def main():
    print("=" * 75)
    print("REAL-WORLD CLASSIFICATION: CARDIOLOGY ECG ANALYSIS")
    print("=" * 75)

    # 1. Load Real ECG Data (Normal Heartbeats vs Myocardial Infarction)
    X_train, y_train, X_test, y_test = load_dataset("ECG200")
    print(f"Loaded ECG200 dataset: {len(X_train)} train, {len(X_test)} test heartbeats")

    # 2. Extract features with Kymora
    t0 = time.perf_counter()
    df_train = kymora.extract_features_df(X_train, profile="core33")
    df_test = kymora.extract_features_df(X_test, profile="core33")
    t_extract = (time.perf_counter() - t0) * 1000.0
    print(f"Extracted {df_train.shape[1]} features for {len(X_train) + len(X_test)} signals in {t_extract:.2f} ms")

    # 3. Correlation pruning
    df_train_clean = correlated_features(df_train, threshold=0.90)
    kept_features = list(df_train_clean.columns)
    df_test_clean = df_test[kept_features]
    print(f"Retained {len(kept_features)} non-collinear features after correlation pruning")

    # 4. Standardize
    scaler = StandardScaler()
    X_tr_scaled = scaler.fit_transform(df_train_clean.to_numpy())
    X_te_scaled = scaler.transform(df_test_clean.to_numpy())

    # 5. Train Random Forest
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_tr_scaled, y_train)
    y_pred_rf = rf.predict(X_te_scaled)
    acc_rf = accuracy_score(y_test, y_pred_rf)
    f1_rf = f1_score(y_test, y_pred_rf, average="macro")

    # 6. Train Ridge Classifier
    ridge = RidgeClassifier(random_state=42)
    ridge.fit(X_tr_scaled, y_train)
    y_pred_rg = ridge.predict(X_te_scaled)
    acc_rg = accuracy_score(y_test, y_pred_rg)

    print("\n" + "=" * 50)
    print("DOWNSTREAM CLASSIFICATION RESULTS")
    print("=" * 50)
    print(f"Random Forest Accuracy: {acc_rf * 100:.2f}% (Macro-F1: {f1_rf:.3f})")
    print(f"Ridge Classifier Accuracy: {acc_rg * 100:.2f}%")
    print("\nDetailed Classification Report (Random Forest):")
    print(classification_report(y_test, y_pred_rf, digits=3))


if __name__ == "__main__":
    main()
