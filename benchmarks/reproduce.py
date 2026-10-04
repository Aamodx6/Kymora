"""Master reproduction runner for Tsxtract benchmarks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Bootstrap sys.path
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from benchmarks.smoke import run_smoke


def main():
    parser = argparse.ArgumentParser(description="Reproduce Tsxtract benchmarks.")
    parser.add_argument("command", nargs="?", default="smoke", choices=["smoke", "agreement", "all", "report"])
    parser.add_argument("--suite", default="all", help="Target suite name")
    args = parser.parse_args()

    if args.command == "smoke":
        run_smoke()
    elif args.command == "agreement":
        from benchmarks.suites.agreement import run_agreement
        run_agreement()
    elif args.command == "report":
        from benchmarks.report.make_report import generate_report
        generate_report()
    elif args.command == "all":
        run_smoke()
        from benchmarks.suites.agreement import run_agreement
        run_agreement()
        from benchmarks.report.make_report import generate_report
        generate_report()


if __name__ == "__main__":
    main()
