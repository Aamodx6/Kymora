## What & why

<!-- Explain *why*, not just what — the diff shows the what. -->

## Checklist

- [ ] One logical change per PR (a feature and a refactor is two PRs)
- [ ] New behaviour has a test that fails without the change
- [ ] `pytest tests/ -q` passes (after rebuilding: `maturin develop --release`)
- [ ] `cargo test --no-default-features`, `cargo fmt --all -- --check`,
      `cargo clippy --no-default-features --all-targets -- -D warnings` pass
- [ ] `python tools/validation_report.py` passes (feature behaviour unchanged)
- [ ] `python tools/check_claims.py` and `python tools/check_repo_hygiene.py` pass
- [ ] Claims touched? (If any numeric claim, throughput, or ratio moved, updated CLAIMS.md with artifact path + env.json; never soften a loss)
- [ ] Version impact noted below per the CONTRIBUTING versioning table
      (feature order/length is public API)

## Version impact

<!-- patch / minor / major / none — see CONTRIBUTING.md → Versioning policy -->
