---
title: "feat: Implement energy_ratio_by_chunks feature"
labels: ["enhancement", "good first issue", "features"]
---

## Context
`energy_ratio_by_chunks` calculates the ratio of energy (sum of squares) contained within a specific segment/chunk of the time series relative to the total series energy. It helps detect bursty signals or non-stationary transient events.

## Acceptance Criteria
1. Split the series into $C$ uniform segments (e.g. $C=10$).
2. Calculate chunk energy $E_k = \sum_{t \in \text{chunk}_k} x_t^2$ and total energy $E_{\text{total}} = \sum_{t=1}^N x_t^2$.
3. Return ratio $E_k / E_{\text{total}}$.
4. If $E_{\text{total}} == 0.0$ (all zeros), return $0.0$.

## Files to Touch
- `src/features/energy.rs`: Chunk energy computation.
- `src/plan.rs`: Parameterized feature registration.

## Tests to Add
- `tests/unit/test_energy_chunks.py`: Assert that sum across all chunks $k=1..C$ equals $1.0$ (within numerical tolerance).
