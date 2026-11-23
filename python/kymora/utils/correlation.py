"""Unsupervised feature pruning and correlation filtering utilities."""

from __future__ import annotations

from typing import Union
import numpy as np
import pandas as pd


def correlated_features(
    features: Union[pd.DataFrame, np.ndarray],
    threshold: float = 0.95,
) -> Union[pd.DataFrame, np.ndarray]:
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
    is_df = isinstance(features, pd.DataFrame)
    if is_df:
        df = features
        cols = list(df.columns)
        mat = df.to_numpy()
    else:
        mat = np.asarray(features)
        cols = [f"feat_{i}" for i in range(mat.shape[1])]

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
        return df.iloc[:, kept_indices]
    return mat[:, kept_indices]
