# Makefile for Kymora benchmark suite

PYTHON ?= python

.PHONY: help setup-venvs bench-smoke bench-agreement bench-all report clean distclean dev

help:
	@echo "Kymora Benchmark Suite Commands:"
	@echo "  make bench-smoke     Run Phase B0 smoke test on all adapters"
	@echo "  make setup-venvs     Create all isolated competitor virtual environments"
	@echo "  make bench-agreement Run Phase B1 feature agreement & parity matrix"
	@echo "  make bench-all       Run full benchmark matrix (Phases B1-B5)"
	@echo "  make report          Generate REPORT.md and results.json from latest run"
	@echo "  make clean           Remove build outputs + caches (keeps target/, venvs, node_modules)"
	@echo "  make distclean       Also remove target/, venvs, node_modules (full purge)"
	@echo "  make dev             Rebuild everything removed by distclean"

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

# Repo hygiene (see CLEANUP_STATUS.md Phase 2). Every path removed below is
# regenerable via `make dev`. Windows: run under Git Bash (rm is required).
clean:  ## build outputs + caches (keeps target/, venvs, node_modules)
	rm -rf site/ dist/ target/wheels/ target/test_wheel/
	rm -rf .pytest_cache/ .hypothesis/ .mypy_cache/ .benchmarks/
	rm -rf tests/__pycache__ benchmarks/suites/__pycache__ benchmarks/harness/__pycache__ benchmarks/adapters/__pycache__ tools/__pycache__ docs/examples/__pycache__

distclean: clean  ## + target/, venvs, node_modules (full purge)
	rm -rf target/ fuzz/target/ benchmarks/.venvs/ landing/node_modules/ landing/dist/

dev:  ## rebuild everything removed by distclean
	$(PYTHON) benchmarks/setup_venvs.py --lib all
	cd landing && npm ci
	$(PYTHON) -m maturin build --release
	pip install --force-reinstall --no-deps target/wheels/kymora-*.whl
