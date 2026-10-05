"""Scikit-learn compatible transformer for time-series feature extraction.

`KymoraTransformer` turns a panel of time series ``X`` of shape
``(n_series, length)`` into a feature matrix of shape
``(n_series, n_features)`` inside `sklearn.pipeline.Pipeline` and friends.
All numerics stay in the Rust core; this class only validates, delegates,
and names columns.

Requires the optional dependency: ``pip install kymora[sklearn]``.
Core ``import kymora`` keeps working with numpy alone, so this module is
*not* imported by ``kymora/__init__.py`` — import it explicitly::

    from kymora.sklearn import KymoraTransformer
"""

from __future__ import annotations

from typing import Any, Sequence

try:
    from sklearn.base import BaseEstimator, TransformerMixin  # type: ignore[import-untyped]
    from sklearn.utils.validation import (  # type: ignore[import-untyped]
        check_array,
        check_is_fitted,
    )
except ImportError as exc:  # pragma: no cover - exercised without sklearn
    raise ImportError(
        "KymoraTransformer requires scikit-learn, which kymora does not "
        'install by default. Install it with: pip install "kymora[sklearn]"'
    ) from exc

from kymora._core import extract_features, feature_names


class KymoraTransformer(TransformerMixin, BaseEstimator):
    """Extract kymora features from a panel of time series.

    Args:
        profile: Feature profile name ("core33" default, "minimal",
            "extended", "full"). Ignored when `features` is given.
        features: Optional explicit feature/alias list (core33 subset for
            float32 input; anything for float64).
        views: Optional view list (requires float64 input).
        n_jobs: Optional worker-thread count (None = automatic).
        nan_policy: "propagate" (default) or "raise"; see docs/numerics.md.
        output_dtype: "float64" (default) or "float32".
    """

    def __init__(
        self,
        profile: str = "core33",
        features: Sequence[str] | None = None,
        views: Sequence[str] | None = None,
        n_jobs: int | None = None,
        nan_policy: str | None = None,
        output_dtype: str | None = None,
    ) -> None:
        self.profile = profile
        self.features = features
        self.views = views
        self.n_jobs = n_jobs
        self.nan_policy = nan_policy
        self.output_dtype = output_dtype

    # -- sklearn API --------------------------------------------------------

    def fit(self, X: Any, y: Any = None) -> "KymoraTransformer":
        """Record input dimensionality and output column names (stateless)."""
        X = self._validate(X)
        self.n_features_in_ = X.shape[1]
        self.feature_names_in_ = [f"series_{i}" for i in range(X.shape[1])]
        self.feature_names_out_ = feature_names(
            profile=None if self.features is not None else self.profile,
            features=list(self.features) if self.features is not None else None,
            views=list(self.views) if self.views is not None else None,
        )
        self.n_output_features_ = len(self.feature_names_out_)
        return self

    def transform(self, X: Any) -> Any:
        """Extract features; honors ``set_output(transform=...)``."""
        check_is_fitted(self, "feature_names_out_")
        X = self._validate(X)
        if X.shape[1] != self.n_features_in_:
            raise ValueError(
                f"X has {X.shape[1]} features, but {self.__class__.__name__} "
                f"is expecting {self.n_features_in_} features as input."
            )
        out = extract_features(
            X,
            profile=None if self.features is not None else self.profile,
            features=list(self.features) if self.features is not None else None,
            n_jobs=self.n_jobs,
            views=list(self.views) if self.views is not None else None,
            nan_policy=self.nan_policy,
            out_dtype=self.output_dtype,
        )
        return self._wrap(out)

    def get_feature_names_out(self, input_features: Any = None) -> Any:
        """Output column names in extraction order."""
        check_is_fitted(self, "feature_names_out_")
        import numpy as np

        return np.asarray(self.feature_names_out_, dtype=object)

    def __sklearn_tags__(self) -> Any:
        tags = super().__sklearn_tags__()
        tags.input_tags.allow_nan = True
        tags.transformer_tags.preserves_dtype = []
        return tags

    # -- internals ----------------------------------------------------------

    def _validate(self, X: Any) -> Any:
        # order="C": sklearn's own validator converts Fortran-order panels
        # (a documented sklearn-level copy); kymora itself still receives
        # only C-order buffers and never copies silently.
        return check_array(
            X,
            accept_sparse=False,
            ensure_2d=True,
            allow_nd=False,
            dtype="float64",
            order="C",
            ensure_all_finite="allow-nan",
        )

    def _wrap(self, out: Any) -> Any:
        config = getattr(self, "_sklearn_output_config", {}).get("transform", None)
        if config == "pandas":
            try:
                import pandas as pd
            except ImportError as exc:
                raise ImportError(
                    'set_output(transform="pandas") requires pandas: '
                    'pip install "kymora[pandas]"'
                ) from exc
            return pd.DataFrame(out, columns=self.feature_names_out_)
        if config == "polars":
            try:
                import polars as pl
            except ImportError as exc:
                raise ImportError(
                    'set_output(transform="polars") requires polars: '
                    'pip install "kymora[polars]"'
                ) from exc
            return pl.DataFrame(
                {name: out[:, j] for j, name in enumerate(self.feature_names_out_)}
            )
        return out
