"""Kymora Datasets Subpackage.

Provides easy loaders for real-world benchmark time-series datasets
(ECG, video motion capture, power telemetry, spectroscopy, sensors).
"""

from .loaders import list_datasets, load_dataset, load_ucr_dataset

__all__ = [
    "load_dataset",
    "list_datasets",
    "load_ucr_dataset",
]
