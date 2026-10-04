"""JSONL schema definition and validation for Kymora benchmarks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

StatusType = Literal["ok", "error", "nan", "mismatch", "timeout"]


@dataclass
class BenchmarkRecord:
    suite: str
    case_id: str
    lib: str
    feature_set: str  # profile or feature subset name
    n_series: int
    length: int
    dtype: str
    layout: str  # "C", "F", "ragged", "strided", etc.
    threads: int
    dist: str  # distribution / data generator name
    runs: list[float]  # execution wall times in seconds
    stats: dict[str, Any]  # min, median, mean, iqr, p95, cv, etc.
    peak_rss_mb: float
    status: StatusType
    guarded: bool = True
    error_msg: str | None = None
    env_ref: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BenchmarkRecord:
        allowed = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**allowed)


REQUIRED_FIELDS = {
    "suite",
    "case_id",
    "lib",
    "feature_set",
    "n_series",
    "length",
    "dtype",
    "layout",
    "threads",
    "dist",
    "runs",
    "stats",
    "peak_rss_mb",
    "status",
    "guarded",
    "error_msg",
    "env_ref",
}

VALID_STATUSES = {"ok", "error", "nan", "mismatch", "timeout"}


def validate_record(record: dict[str, Any]) -> tuple[bool, str | None]:
    """Validate that a record matches the benchmark schema."""
    missing = REQUIRED_FIELDS - set(record.keys())
    if missing:
        return False, f"Missing required fields: {sorted(missing)}"

    if record["status"] not in VALID_STATUSES:
        return False, f"Invalid status: {record['status']}; must be one of {VALID_STATUSES}"

    if not isinstance(record["runs"], list):
        return False, "Field 'runs' must be a list of floats"

    if not isinstance(record["stats"], dict):
        return False, "Field 'stats' must be a dictionary"

    return True, None
