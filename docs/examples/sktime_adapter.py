"""Thin sktime adapter for kymora (no hard dependency).

`sktime` and `aeon` are never imported by the kymora package itself. This
example shows how to wrap `extract_features` in an sktime panel
transformer (Panel in, Primitives out) with five lines of glue. Verified
against sktime 1.2.0 (see tests/test_sktime_adapter.py); aeon compatibility
is untested and left as an exercise (aeon forked this interface, so the same
shape usually works — verify before relying on it).
"""

from __future__ import annotations

try:
    import pandas as pd
    from sktime.transformations.base import BaseTransformer

    _AVAILABLE = True
except ImportError:  # pragma: no cover - importorskip in tests
    pd = None
    BaseTransformer = object
    _AVAILABLE = False

import numpy as np


def require_adapter():
    """Raise a helpful error when the optional deps are missing."""
    if not _AVAILABLE:
        raise ImportError(
            "The sktime adapter needs sktime and pandas installed, e.g. "
            "pip install sktime pandas. kymora itself stays dependency-free."
        )


class KymoraFeatures(BaseTransformer):
    """sktime panel transformer backed by kymora's Rust core.

    Input: univariate panel (`numpy3D` mtype, shape `(n_instances, 1, length)`).
    Output: `pd.DataFrame` with one row per instance and one column per
    feature (`kymora.feature_names()` order).
    """

    _tags = {
        "scitype:transform-input": "Panel",
        "scitype:transform-output": "Primitives",
        "scitype:instancewise": False,
        "X_inner_mtype": "numpy3D",
        "capability:missing_values": False,
        "capability:multivariate": True,
        "capability:unequal_length": False,
        "fit_is_empty": True,
    }

    def __init__(self, profile="core33", features=None):
        require_adapter()
        self.profile = profile
        self.features = features
        super().__init__()

    def _fit(self, X, y=None):
        # NOTE: `fit_is_empty=True`, so sktime skips this method. Feature
        # names are resolved in `_transform`, which always runs.
        return self

    def _transform(self, X, y=None):
        import kymora

        arr = np.asarray(X)
        if arr.ndim != 3:
            raise ValueError(
                "KymoraFeatures expects a panel of shape "
                f"(n_instances, n_channels, length), got {arr.shape}"
            )
        profile = None if self.features is not None else self.profile
        if arr.shape[1] == 1:
            names = kymora.feature_names(profile=profile, features=self.features)
            panel = np.ascontiguousarray(arr[:, 0, :])
            Xt = kymora.extract_features(
                panel, profile=profile, features=self.features
            )
        else:
            # Multivariate: per-channel blocks, no cross terms (one row per
            # instance, stable `ch{c}__{feature}` columns).
            names = kymora.feature_names_mc(
                arr.shape[1], profile=profile, features=self.features, cross=False
            )
            Xt = kymora.extract_features_mc(
                np.ascontiguousarray(arr),
                profile=profile,
                features=self.features,
                cross=False,
            )
        self._feature_names = names
        return pd.DataFrame(Xt, columns=names)

    @classmethod
    def get_test_params(cls, parameter_set="default"):
        return {"profile": "minimal"}
