"""Real-world benchmark time-series dataset loaders and utilities."""

from __future__ import annotations

import os
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

# Canonical cache directory
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "kymora" / "datasets"

UCR_BASE_URL = "https://raw.githubusercontent.com/deric/time-series-machine-learning/master/datasets/UCRArchive_2018"

AVAILABLE_DATASETS: Dict[str, Dict[str, Union[int, str]]] = {
    "GunPoint": {
        "domain": "Video Motion Capture",
        "description": "Motion tracking of human actors drawing a replica gun vs pointing a finger.",
        "length": 150,
        "n_classes": 2,
    },
    "ECG200": {
        "domain": "Cardiology / Medical",
        "description": "Electrocardiogram heartbeats (normal cardiac cycles vs myocardial infarction).",
        "length": 96,
        "n_classes": 2,
    },
    "ItalyPowerDemand": {
        "domain": "Energy Telemetry",
        "description": "Italian electrical power consumption telemetry across seasonal cycles.",
        "length": 24,
        "n_classes": 2,
    },
    "Coffee": {
        "domain": "Food Chemistry",
        "description": "Near-infrared (NIR) absorption spectra discriminating Arabica from Robusta coffee.",
        "length": 286,
        "n_classes": 2,
    },
    "Wafer": {
        "domain": "Semiconductor Sensors",
        "description": "In-line sensor telemetry from semiconductor wafer fabrication tools.",
        "length": 152,
        "n_classes": 2,
    },
    "FordA": {
        "domain": "Automotive Telemetry",
        "description": "Engine noise and subsystem sensor diagnostics.",
        "length": 500,
        "n_classes": 2,
    },
    "TwoLeadECG": {
        "domain": "Biomedical ECG",
        "description": "Two-lead medical electrocardiogram recording.",
        "length": 82,
        "n_classes": 2,
    },
    "SyntheticControl": {
        "domain": "Process Control",
        "description": "Control chart telemetry patterns for statistical quality control.",
        "length": 60,
        "n_classes": 6,
    },
}


def get_cache_dir(cache_dir: Optional[Union[str, Path]] = None) -> Path:
    """Return cache path, creating parent directories if necessary."""
    path = Path(cache_dir) if cache_dir is not None else DEFAULT_CACHE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_datasets() -> Dict[str, Dict[str, Union[int, str]]]:
    """List all available canonical real-world benchmark datasets.

    Returns
    -------
    dict
        Dictionary mapping dataset names to metadata (domain, description, length, n_classes).
    """
    return dict(AVAILABLE_DATASETS)


def load_ucr_dataset(
    name: str,
    split: str = "TRAIN",
    cache_dir: Optional[Union[str, Path]] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Load a specific split of a UCR Time Series Archive dataset.

    Parameters
    ----------
    name : str
        Canonical name (e.g. 'ECG200', 'GunPoint', 'ItalyPowerDemand', 'Coffee', 'Wafer').
    split : {'TRAIN', 'TEST'}, default='TRAIN'
        Dataset partition.
    cache_dir : str, Path, or None, optional
        Custom directory for cached TSV files.

    Returns
    -------
    X : np.ndarray of shape (n_samples, n_timestamps)
        Signal array (float64).
    y : np.ndarray of shape (n_samples,)
        Class labels (int).
    """
    cache = get_cache_dir(cache_dir)
    file_name = f"{name}_{split.upper()}.tsv"
    file_path = cache / file_name

    # Check local repo cache first
    local_cache = Path(__file__).resolve().parent.parent.parent.parent / "benchmarks" / "datasets" / "cache" / file_name
    if local_cache.is_file():
        file_path = local_cache

    if not file_path.is_file():
        url = f"{UCR_BASE_URL}/{name}/{name}_{split.upper()}.tsv"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                file_path.write_bytes(data)
        except Exception as e:
            raise RuntimeError(f"Could not download dataset '{name}' ({split}): {e}") from e

    raw = np.loadtxt(file_path, delimiter="\t")
    y = raw[:, 0].astype(int)
    X = raw[:, 1:].astype(np.float64)
    return X, y


def load_dataset(
    name: str,
    split: Optional[str] = None,
    cache_dir: Optional[Union[str, Path]] = None,
) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
    """Load a canonical time-series benchmark dataset.

    Parameters
    ----------
    name : str
        Dataset identifier (e.g., 'ECG200', 'GunPoint', 'Coffee', 'ItalyPowerDemand', 'Wafer').
    split : {'train', 'test', None}, optional
        If 'train' or 'test', returns (X, y).
        If None, returns (X_train, y_train, X_test, y_test).
    cache_dir : str, Path, or None, optional
        Directory for caching downloaded datasets.

    Returns
    -------
    tuple
        Either (X, y) or (X_train, y_train, X_test, y_test).
    """
    if name not in AVAILABLE_DATASETS:
        known = list(AVAILABLE_DATASETS.keys())
        raise ValueError(f"Unknown dataset '{name}'. Available canonical datasets: {known}")

    if split is not None:
        split_clean = split.upper()
        if split_clean not in ("TRAIN", "TEST"):
            raise ValueError(f"split must be 'train', 'test', or None; got '{split}'")
        return load_ucr_dataset(name, split=split_clean, cache_dir=cache_dir)

    X_train, y_train = load_ucr_dataset(name, split="TRAIN", cache_dir=cache_dir)
    X_test, y_test = load_ucr_dataset(name, split="TEST", cache_dir=cache_dir)
    return X_train, y_train, X_test, y_test
