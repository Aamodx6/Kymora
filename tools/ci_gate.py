#!/usr/bin/env python3
"""ci-gate evaluator (CI `ci gate` job in .github/workflows/ci.yml).

Reads the `needs` context as JSON from NEEDS_JSON and exits 1 when the gate
is red. Rules:
  - `changes` (paths-filter) must be `success` — a failed/cancelled filter
    means the path gates are untrustworthy, so skips below it prove nothing.
  - every other job must be `success` or `skipped` (path-gated skips allowed).
  - anything `failure`/`cancelled` fails the gate.

Usage:
    NEEDS_JSON='...' python tools/ci_gate.py
    python tools/ci_gate.py --self-test   # unit cases, also run in CI
"""

from __future__ import annotations

import json
import os
import sys

# Keep in sync with ci.yml `ci-gate` needs (used only for --self-test fixtures).
GATE_JOBS = (
    "changes",
    "rust",
    "test",
    "test-macos-intel",
    "validation-report",
    "typecheck",
    "docs",
    "hygiene",
    "audit-pr",
    "wheels",
)


def evaluate(needs: dict) -> list[str]:
    errors: list[str] = []
    if needs.get("changes", {}).get("result") != "success":
        errors.append(
            "BLOCKED: changes job result is "
            f"{needs.get('changes', {}).get('result')!r}, need 'success'"
        )
    for key, val in needs.items():
        if key == "changes":
            continue
        if val["result"] not in ("success", "skipped"):
            errors.append(f"BLOCKED by {key}: {val['result']}")
    return errors


def self_test() -> int:
    def fixture(results: dict) -> dict:
        needs = {job: {"result": "success"} for job in GATE_JOBS}
        needs.update(results)
        return needs

    all_skipped_except_changes = {"changes": {"result": "failure"}}
    all_skipped_except_changes.update(
        {job: {"result": "skipped"} for job in GATE_JOBS if job != "changes"}
    )
    cases = [
        ("all success", fixture({}), 0),
        ("success plus path-gated skips", fixture({"rust": {"result": "skipped"}}), 0),
        (
            "changes failure, all others skipped",
            all_skipped_except_changes,
            1,
        ),
        ("changes cancelled", fixture({"changes": {"result": "cancelled"}}), 1),
        ("one job failed", fixture({"test": {"result": "failure"}}), 1),
        ("one job cancelled", fixture({"docs": {"result": "cancelled"}}), 1),
        ("reusable wheels call failed", fixture({"wheels": {"result": "failure"}}), 1),
    ]
    failures = 0
    for name, needs, expected in cases:
        errors = evaluate(needs)
        code = 1 if errors else 0
        status = "ok" if code == expected else "MISMATCH"
        if code != expected:
            failures += 1
        print(f"{status}: {name} -> exit {code} (expected {expected})")
        for err in errors:
            print(f"    {err}")
    print(f"--- {len(cases) - failures}/{len(cases)} cases pass ---")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    try:
        needs = json.loads(os.environ["NEEDS_JSON"])
    except (KeyError, json.JSONDecodeError) as exc:
        print(f"NEEDS_JSON missing or invalid: {exc}")
        return 2
    errors = evaluate(needs)
    if errors:
        for err in errors:
            print(err)
        return 1
    print("all green (success or path-gated skip):")
    for key, val in needs.items():
        print(f"  {key}: {val['result']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
