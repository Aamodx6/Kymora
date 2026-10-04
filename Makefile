# Makefile for Tsxtract benchmark suite

PYTHON ?= python

.PHONY: help setup-venvs bench-smoke bench-agreement bench-all report clean

help:
	@echo "Tsxtract Benchmark Suite Commands:"
	@echo "  make bench-smoke     Run Phase B0 smoke test on all adapters"
	@echo "  make setup-venvs     Create all isolated competitor virtual environments"
	@echo "  make bench-agreement Run Phase B1 feature agreement & parity matrix"
	@echo "  make bench-all       Run full benchmark matrix (Phases B1-B5)"
	@echo "  make report          Generate REPORT.md and results.json from latest run"

setup-venvs:
	$(PYTHON) benchmarks/setup_venvs.py --lib all

bench-smoke:
	$(PYTHON) benchmarks/smoke.py

bench-agreement:
	$(PYTHON) benchmarks/suites/agreement.py

bench-all:
	$(PYTHON) benchmarks/reproduce.py --suite all

report:
	$(PYTHON) benchmarks/report/make_report.py
