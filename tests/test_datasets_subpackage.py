"""Tests for kymora.datasets subpackage."""

import numpy as np
import pytest
import kymora.datasets as kd


def test_list_datasets():
    datasets = kd.list_datasets()
    assert isinstance(datasets, dict)
    assert "ECG200" in datasets
    assert "GunPoint" in datasets
    assert "Coffee" in datasets
    assert "ItalyPowerDemand" in datasets
    assert "Wafer" in datasets


def test_load_dataset_train_test():
    X_tr, y_tr = kd.load_dataset("ECG200", split="train")
    assert isinstance(X_tr, np.ndarray)
    assert isinstance(y_tr, np.ndarray)
    assert X_tr.shape == (100, 96)
    assert len(y_tr) == 100

    X_te, y_te = kd.load_dataset("ECG200", split="test")
    assert X_te.shape == (100, 96)
    assert len(y_te) == 100


def test_load_dataset_all():
    X_tr, y_tr, X_te, y_te = kd.load_dataset("GunPoint")
    assert X_tr.shape == (50, 150)
    assert X_te.shape == (150, 150)
    assert len(y_tr) == 50
    assert len(y_te) == 150


def test_unknown_dataset_raises():
    with pytest.raises(ValueError, match="Unknown dataset"):
        kd.load_dataset("NonExistentDatasetXYZ")
