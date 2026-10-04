# Security Policy

## Supported Versions

Security fixes are applied to the latest release on PyPI
([`kymora`](https://pypi.org/project/kymora/)). Older releases are
not backported; upgrading is the recommended mitigation.

| Version | Supported |
| ------- | --------- |
| latest release (0.5.x) | yes |
| older | no |

## Reporting a Vulnerability

Please do **not** open a public issue for security reports.

Use GitHub's private reporting for this repository:
https://github.com/Aamodx6/Kymora/security/advisories/new

Include, when possible:

- the affected version / platform
- a minimal reproduction or the input that triggers the issue
- the impact (memory unsafety, incorrect results, denial of service, supply
  chain, etc.)

The Rust core performs unsafe memory operations at the NumPy boundary
(`src/ffi.rs`, `src/kernels/`); reports touching buffer handling, bounds, or
dtype/contiguity checks are especially welcome. Expect an acknowledgement when
the report is received and a fix or published advisory before any public
disclosure.
