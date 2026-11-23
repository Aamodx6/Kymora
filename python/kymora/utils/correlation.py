"""Unsupervised feature pruning and correlation filtering utilities."""

from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd


def correlated_features(
    features: Any,
    threshold: float = 0.95,
) -> Any:
    """Prune collinear features using greedy Pearson correlation clustering.

    Parameters
    ----------
    features : pd.DataFrame or np.ndarray
        Feature matrix of shape (n_samples, n_features).
    threshold : float, default=0.95
        Absolute Pearson correlation threshold above which redundant features are dropped.

    Returns
    -------
    pd.DataFrame or np.ndarray
        Cleaned feature matrix with redundant collinear features removed.
    """
    if isinstance(features, pd.DataFrame):
        mat = features.to_numpy()
        is_df = True
    else:
        mat = np.asarray(features)
        is_df = False

    if mat.shape[1] <= 1:
        return features

    # Handle NaNs and Infs safely
    mat_clean = np.nan_to_num(mat, nan=0.0, posinf=0.0, neginf=0.0)

    # Compute correlation matrix
    with np.errstate(divide="ignore", invalid="ignore"):
        corr_matrix = np.corrcoef(mat_clean, rowvar=False)

    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    np.fill_diagonal(corr_matrix, 0.0)

    dropped_indices = set()
    n_feats = corr_matrix.shape[0]

    for i in range(n_feats):
        if i in dropped_indices:
            continue
        collinear = np.where(np.abs(corr_matrix[i, i + 1 :]) >= threshold)[0] + (i + 1)
        for c in collinear:
            dropped_indices.add(c)

    kept_indices = [i for i in range(n_feats) if i not in dropped_indices]

    if is_df:
        return features.iloc[:, kept_indices]
    return mat[:, kept_indices]
