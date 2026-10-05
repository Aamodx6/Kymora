# Quarantined experiments (Phase 5.4)

Benchmarked once against HEAD per arch §15.1/P7 gating (revive only on
>10% core33 win **and** golden-test parity). Method: isolated worktrees of
the experiment branches, `--release` builds, same-session interleaved
probes (1k×500 core33, 31 runs, GC disabled), numeric parity as max abs
diff vs HEAD output.

Machine: i7-13620H laptop, Windows 11, Performance plan, AC online.
Exploratory numbers.

## spin-pool (`experiment/spin-pool`, custom spin-then-park pool)

| Variant | Median | Q1–Q3 | vs HEAD |
|---|---|---|---|
| HEAD (hardening branch, cached rayon pools) | 2.08 ms | 1.94–2.29 | — |
| spin-pool default (custom pool) | 2.09 ms | 1.97–2.23 | +0.5% (noise) |
| spin-pool `TSXTRACT_POOL=rayon` | 2.06 ms | — | −1% (noise) |

Numeric parity: max abs diff vs HEAD = 0.0 (bit-identical).

**Verdict: stays quarantined.** No win on this workload (pool wake/join
is not the bottleneck at 1k×500; the custom pool adds complexity for
±1%). Revisit only with flamegraph evidence of rayon overhead on a
target workload (arch Z6 gate: η < 0.85 at 1k×500).

## soa-4x (`experiment/soa-4x`, lane-batched SoA kernels)

| Variant | Median | Q1–Q3 | vs HEAD |
|---|---|---|---|
| HEAD | 2.08 ms | 1.94–2.29 | — |
| soa-4x branch default path | 2.36 ms | 2.23–2.49 | −13% (slower) |

Numeric parity: max abs diff vs HEAD = 0.0 (bit-identical).

**Verdict: stays quarantined.** Slower than HEAD on the gated workload;
the transposition overhead exceeds the lane-batched gains at n=500
(arch Z2 gate: fused+ACF+perm > 30% — not met). Do not wire in.

## Notes

- Both branches are 0.5.0-era (`tsxtract`/`tsxtractor` names, `TSXTRACT_*`
  env); the comparison used their default paths, which is what "wire it
  in" would promote.
- Worktrees used for the builds were removed after measurement; branches
  remain in git (`experiment/spin-pool`, `experiment/soa-4x`) for
  archaeology, not compilation.
