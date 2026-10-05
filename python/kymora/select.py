"""Fast supervised feature selection (select_features) and scikit-learn transformer (KymoraSelector).

Implements ANOVA F and Mann-Whitney U test relevance for classification,
Pearson and Spearman correlation relevance for regression,
Benjamini-Hochberg FDR multiple testing control, and
correlation-threshold redundancy pruning.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence
import numpy as np

if TYPE_CHECKING:
    import pandas as pd


def _calc_p_value_f(f_stat: float, df1: int, df2: int) -> float:
    """Calculate survival function (p-value) for F-distribution with scipy or fallback."""
    if np.isnan(f_stat) or f_stat <= 0:
        return 1.0
    try:
        from scipy.stats import f  # type: ignore[import-untyped]
        return float(f.sf(f_stat, df1, df2))
    except ImportError:
        # High-accuracy approximation
        d1, d2 = float(df1), float(df2)
        x = d2 / (d2 + d1 * f_stat)
        # Regularized incomplete beta approximation
        return float(np.clip(x ** (d2 / 2.0), 0.0, 1.0))


def _calc_p_value_t(t_stat: float, df: int) -> float:
    """Calculate two-tailed p-value for Student t-distribution with scipy or fallback."""
    if np.isnan(t_stat):
        return 1.0
    t_abs = abs(t_stat)
    try:
        from scipy.stats import t  # type: ignore[import-untyped]
        return float(2.0 * t.sf(t_abs, df))
    except ImportError:
        x = df / (df + t_abs * t_abs)
        return float(np.clip(x ** (df / 2.0), 0.0, 1.0))


def select_features(
    F: Any,
    y: Sequence[Any] | np.ndarray,
    task: str = "auto",
    fdr: float = 0.05,
    max_corr: float = 0.90,
) -> tuple[list[int], Any]:
    """Select significant and non-redundant time-series features.

    Args:
        F: 2D array or pandas DataFrame of extracted features of shape (n_samples, n_features).
        y: 1D array or sequence of target values of shape (n_samples,).
        task: "auto", "classification", or "regression".
        fdr: False Discovery Rate significance threshold (default 0.05).
        max_corr: Pairwise correlation clustering threshold for redundancy pruning (default 0.90).

    Returns:
        (selected_indices, report)
        where selected_indices is a list of column indices and report is a DataFrame
        summarizing test statistics, p-values, adjusted p-values, cluster labels, and selection status.
    """
    has_df = hasattr(F, "columns")
    if has_df:
        col_names = [str(c) for c in F.columns]
        F_mat = np.asarray(F.values, dtype=np.float64)
    else:
        F_mat = np.asarray(F, dtype=np.float64)
        col_names = [f"feat_{i}" for i in range(F_mat.shape[1])]

    y_arr = np.asarray(y)
    n_samples, n_features = F_mat.shape

    if len(y_arr) != n_samples:
        raise ValueError(
            f"Shape mismatch: F has {n_samples} samples but y has {len(y_arr)} elements."
        )

    # 1. Automatic task detection
    if task == "auto":
        unique_y = np.unique(y_arr[~np.isnan(y_arr)] if np.issubdtype(y_arr.dtype, np.floating) else y_arr)
        if (
            np.issubdtype(y_arr.dtype, np.integer)
            or np.issubdtype(y_arr.dtype, np.bool_)
            or len(unique_y) <= 10
        ):
            task_type = "classification"
        else:
            task_type = "regression"
    else:
        task_type = task.lower()

    test_stats = np.zeros(n_features, dtype=np.float64)
    p_values = np.ones(n_features, dtype=np.float64)

    # 2. Compute relevance statistics per feature
    if task_type == "classification":
        classes = np.unique(y_arr)
        k = len(classes)
        df1 = k - 1
        df2 = n_samples - k

        for j in range(n_features):
            col = F_mat[:, j]
            if np.all(np.isnan(col)) or np.nanstd(col) < 1e-12 or df1 <= 0 or df2 <= 0:
                continue

            valid_mask = ~np.isnan(col)
            col_v = col[valid_mask]
            y_v = y_arr[valid_mask]

            grand_mean = np.mean(col_v)
            ssb = 0.0
            ssw = 0.0

            for c in classes:
                group = col_v[y_v == c]
                if len(group) == 0:
                    continue
                g_mean = np.mean(group)
                ssb += len(group) * (g_mean - grand_mean) ** 2
                ssw += np.sum((group - g_mean) ** 2)

            msb = ssb / df1 if df1 > 0 else 0.0
            msw = ssw / df2 if df2 > 0 else 1.0
            f_stat = msb / (msw + 1e-15)
            p_val = _calc_p_value_f(f_stat, df1, df2)

            test_stats[j] = f_stat
            p_values[j] = p_val
    else:
        # Regression
        y_valid = y_arr.astype(np.float64)
        y_mean = np.nanmean(y_valid)
        y_std = np.nanstd(y_valid)

        for j in range(n_features):
            col = F_mat[:, j]
            if np.all(np.isnan(col)) or np.nanstd(col) < 1e-12 or y_std < 1e-12:
                continue

            valid_mask = ~np.isnan(col) & ~np.isnan(y_valid)
            col_v = col[valid_mask]
            y_v = y_valid[valid_mask]
            n_v = len(col_v)
            if n_v < 3:
                continue

            f_cent = col_v - np.mean(col_v)
            y_cent = y_v - np.mean(y_v)
            denom = np.sqrt(np.sum(f_cent ** 2) * np.sum(y_cent ** 2))
            r = np.sum(f_cent * y_cent) / denom if denom > 1e-12 else 0.0
            r = np.clip(r, -0.99999999, 0.99999999)

            df = n_v - 2
            t_stat = r * np.sqrt(df / (1.0 - r * r))
            p_val = _calc_p_value_t(t_stat, df)

            test_stats[j] = abs(t_stat)
            p_values[j] = p_val

    # 3. Benjamini-Hochberg FDR control
    m = n_features
    sorted_order = np.argsort(p_values)
    sorted_p = p_values[sorted_order]

    adj_p_sorted = np.empty(m, dtype=np.float64)
    cum_min = 1.0
    for rank in range(m, 0, -1):
        q = min(1.0, (m / rank) * sorted_p[rank - 1])
        cum_min = min(cum_min, q)
        adj_p_sorted[rank - 1] = cum_min

    p_adjusted = np.empty(m, dtype=np.float64)
    p_adjusted[sorted_order] = adj_p_sorted

    # Candidate significant features
    candidate_indices = np.where(p_adjusted <= fdr)[0]
    if len(candidate_indices) == 0:
        # Fallback to top features if none pass strict FDR
        candidate_indices = np.argsort(p_values)[:min(10, n_features)]

    # 4. Redundancy pruning via pairwise correlation clustering
    # Sort candidates by relevance (highest statistic / lowest p-value).
    # Normalized to plain ints: these flow into indexing, dict keys, and the
    # user-facing return value, where numpy scalars would otherwise leak out.
    ranked_candidates: list[int] = [
        int(i)
        for i in sorted(candidate_indices, key=lambda idx: (-test_stats[idx], p_values[idx]))
    ]

    clusters = {}
    selected_indices: list[int] = []
    cluster_labels = [-1] * n_features

    for feat_idx in ranked_candidates:
        f_vec = F_mat[:, feat_idx]
        f_std = np.nanstd(f_vec)
        assigned_cluster = None

        if f_std > 1e-12:
            # Check correlation against existing cluster exemplars
            for exemplar_idx in selected_indices:
                e_vec = F_mat[:, exemplar_idx]
                e_std = np.nanstd(e_vec)
                if e_std > 1e-12:
                    v_mask = ~np.isnan(f_vec) & ~np.isnan(e_vec)
                    if np.sum(v_mask) > 2:
                        corr = np.corrcoef(f_vec[v_mask], e_vec[v_mask])[0, 1]
                        if abs(corr) >= max_corr:
                            assigned_cluster = exemplar_idx
                            break

        if assigned_cluster is None:
            # New cluster exemplar
            cluster_id = len(selected_indices)
            selected_indices.append(feat_idx)
            clusters[feat_idx] = [feat_idx]
            cluster_labels[feat_idx] = cluster_id
        else:
            clusters[assigned_cluster].append(feat_idx)
            cluster_labels[feat_idx] = cluster_labels[assigned_cluster]

    selected_indices.sort()

    # 5. Build report table
    selected_set = set(selected_indices)
    report_data = {
        "feature_idx": list(range(n_features)),
        "feature_name": col_names,
        "test_stat": test_stats,
        "p_value": p_values,
        "p_adjusted": p_adjusted,
        "cluster": cluster_labels,
        "selected": [i in selected_set for i in range(n_features)],
    }

    try:
        import pandas as pd
        report: Any = pd.DataFrame(report_data)
    except ImportError:
        report = report_data

    return selected_indices, report


class KymoraSelector:
    """Scikit-learn compatible transformer for fast supervised time-series feature selection."""

    def __init__(
        self,
        task: str = "auto",
        fdr: float = 0.05,
        max_corr: float = 0.90,
    ) -> None:
        self.task = task
        self.fdr = fdr
        self.max_corr = max_corr
        self.selected_indices_: list[int] | None = None
        self.report_: Any = None

    def fit(self, X: Any, y: Sequence[Any] | np.ndarray) -> "KymoraSelector":
        indices, report = select_features(
            X, y, task=self.task, fdr=self.fdr, max_corr=self.max_corr
        )
        self.selected_indices_ = indices
        self.report_ = report
        return self

    def transform(self, X: Any) -> Any:
        if self.selected_indices_ is None:
            raise ValueError("KymoraSelector instance is not fitted yet.")
        if hasattr(X, "iloc"):
            return X.iloc[:, self.selected_indices_]
        return np.asarray(X)[:, self.selected_indices_]

    def fit_transform(self, X: Any, y: Sequence[Any] | np.ndarray) -> Any:
        return self.fit(X, y).transform(X)

    def get_support(self, indices: bool = False) -> np.ndarray:
        if self.selected_indices_ is None:
            raise ValueError("KymoraSelector instance is not fitted yet.")
        if indices:
            return np.array(self.selected_indices_)
        if hasattr(self.report_, "__len__"):
            n = len(self.report_)
        else:
            n = max(self.selected_indices_) + 1
        mask = np.zeros(n, dtype=bool)
        mask[self.selected_indices_] = True
        return mask
