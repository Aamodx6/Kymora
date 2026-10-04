"""Adapter for unrelated PyPI 'tsxtract' (JAX-based) to document the package name collision."""

from __future__ import annotations

from typing import Any
import numpy as np

from benchmarks.adapters.base import BaseAdapter


class Adapter(BaseAdapter):
    name = "tsxtract_jax"
    version = "pypi_collision"

    def feature_names(self, feature_set: str = "default") -> list[str]:
        return ["jax_collision_notice"]

    def extract(
        self,
        X: np.ndarray,
        feature_set: str = "default",
        threads: int = 1,
        **kwargs: Any,
    ) -> np.ndarray:
        raise NotImplementedError(
            "This adapter represents the unrelated PyPI package 'tsxtract' (JAX-based). "
            "It is maintained solely to document the name collision and ensure users "
            "import 'tsxtract' (our high-performance Rust core) rather than the JAX package."
        )

    def tune_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "nature": "Name collision documentation on PyPI",
            "recommended_resolution": "Install our package via `pip install tsxtract-rs` and use `import tsxtract`",
        }
