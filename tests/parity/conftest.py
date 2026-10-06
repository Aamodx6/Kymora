"""Fail parity skips when KYMORA_REQUIRE_PARITY=1 (CI parity job).

Each test in this directory skips independently when its reference library
is missing (`pytest.importorskip`), so plain CI without the dev-parity
extras stays green. The CI `parity` job installs `.[dev-parity,sklearn]`
and sets KYMORA_REQUIRE_PARITY=1: any skip there means a reference library
failed to install and the parity claim went untested — fail loudly instead
of silently covering less.
"""

from __future__ import annotations

import os

import pytest


def _require_parity() -> bool:
    return os.environ.get("KYMORA_REQUIRE_PARITY") == "1"


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    if _require_parity() and report.when == "call" and report.skipped:
        report.outcome = "failed"
        report.longrepr = (
            "KYMORA_REQUIRE_PARITY=1: parity test skipped "
            f"(reference library missing?): {report.longrepr}"
        )
    return report
