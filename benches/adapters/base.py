"""Standard base class and interface for benchmark adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
import numpy as np


class BaseAdapter(ABC):
    """Abstract base class for all feature extraction adapters."""

    name: str = "base"
    version: str = "unknown"

    @abstractmethod
    def extract(
        self,
        X: np.ndarray,
        feature_set: str = "default",
        threads: int = 1,
        **kwargs: Any,
    ) -> np.ndarray:
        """Extract features from 2D array X of shape (n_series, length).
        
        Returns 2D NumPy array of shape (n_series, n_features).
        """
        pass

    @abstractmethod
    def feature_names(self, feature_set: str = "default") -> list[str]:
        """Return list of feature names for the given feature set."""
        pass

    def tune_info(self) -> dict[str, Any]:
        """Return hardware and software tuning parameters used for this adapter."""
        return {
            "name": self.name,
            "version": self.version,
            "recommended_fast_config": True,
        }
