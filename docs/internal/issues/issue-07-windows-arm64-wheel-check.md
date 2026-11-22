---
title: "ci: Investigate Windows ARM64 wheel build"
labels: ["ci", "build", "good first issue", "arm64"]
---

## Context
Kymora currently builds pre-compiled binary wheels for Linux (`x86_64`, `aarch64`), macOS (`x86_64`, `arm64`), and Windows (`x64`). Windows on ARM64 (e.g. Snapdragon X Elite devices) is becoming increasingly common.

## Acceptance Criteria
1. Explore cross-compilation target `aarch64-pc-windows-msvc` in Maturin.
2. Verify if GitHub Actions hosted runners (`windows-11-arm64` or cross-compilation via `maturin build --target aarch64-pc-windows-msvc`) can produce valid wheels.
3. If cross-compilation is viable without host runner costs, add it as an experimental job to `.github/workflows/wheels.yml`.

## Files to Touch
- `.github/workflows/wheels.yml`
- `docs/internal/wheel_matrix.md`

## Tests to Add
- Wheel artifact verification in CI.
