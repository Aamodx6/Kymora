## What & why

<!-- Explain *why*, not just what — the diff shows the what. -->

## Checklist

- [ ] One logical change per PR (a feature and a refactor is two PRs)
- [ ] New behaviour has a test that fails without the change
- [ ] `pytest tests/ -q` passes (after rebuilding: `maturin develop --release`)
- [ ] `cargo test --no-default-features`, `cargo fmt --all -- --check`,
      `cargo clippy --no-default-features --all-targets -- -D warnings` pass
- [ ] `python tools/validation_report.py` passes (feature behaviour unchanged)
- [ ] Version impact noted below per the CONTRIBUTING versioning table
      (feature order/length is public API)

## Version impact

<!-- patch / minor / major / none — see CONTRIBUTING.md → Versioning policy -->
