"""Feature extraction configuration and domain discovery settings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .features import ALL_DOMAINS

DEFAULT_JSON_PATH = Path(__file__).resolve().parent / "features.json"


def load_json(json_path: str | Path | None = None) -> Dict[str, Any]:
    """Load feature specification dictionary from JSON.

    Parameters
    ----------
    json_path : str, Path, or None, default=None
        Path to custom JSON file. If None, loads Kymora's default `features.json`.

    Returns
    -------
    dict
        Dictionary mapping domain names to feature configurations.
    """
    path = Path(json_path) if json_path is not None else DEFAULT_JSON_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Feature configuration JSON file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_features_by_domain(
    domain: Optional[str] = None,
    json_path: Optional[str | Path] = None,
) -> Dict[str, Dict[str, Any]]:
    """Return dictionary of features grouped by scientific domain.

    Matches TSFEL configuration signature while supporting Kymora's ultra-fast
    Rust-native extraction engine.

    Parameters
    ----------
    domain : str or None, default=None
        Scientific domain to retrieve:
        - None / 'all': All domains ('statistical', 'temporal', 'spectral', 'fractal').
        - 'statistical': Distributional moments, quantiles, order statistics.
        - 'temporal': Zero crossings, turn points, velocities, arc length.
        - 'spectral': FFT power descriptors, Cepstral (MFCC/LPCC), Continuous Wavelets (CWT).
        - 'fractal': Petrosian fractal dimension.
    json_path : str, Path, or None, default=None
        Optional path to custom feature specification file.

    Returns
    -------
    dict
        Feature configuration dictionary suitable for `time_series_features_extractor`.
    """
    if json_path is not None:
        full_cfg = load_json(json_path)
    else:
        try:
            base_json = load_json(DEFAULT_JSON_PATH)
        except Exception:
            base_json = {}

        full_cfg = {}
        for d, feat_list in ALL_DOMAINS.items():
            domain_dict = {}
            for f in feat_list:
                desc = base_json.get(d, {}).get(f, {}).get("description", f"Feature {f}")
                params = base_json.get(d, {}).get(f, {}).get("parameters", "")
                domain_dict[f] = {"description": desc, "parameters": params, "use": "yes"}
            full_cfg[d] = domain_dict

    if domain is None or domain.lower() in ("all", "*"):
        return full_cfg

    domain_clean = domain.lower()
    if domain_clean not in full_cfg:
        valid = list(full_cfg.keys()) + ["all"]
        raise ValueError(f"Unknown domain '{domain}'. Valid domains: {valid}")

    return {domain_clean: full_cfg[domain_clean]}

