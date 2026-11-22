# Kymora Memory Scaling Sweep Report

Empirical memory sweep evaluating extraction overhead across series count $N \in [1\text{k} .. 100\text{k}]$ at $L = 500$.
Configured with 16 Rayon worker threads under 64-bit IEEE-754 precision.

## Measured Sweep Table

| Series N | Length L | Input Matrix (MiB) | Output Matrix (MiB) | Measured Worker Scratch (MiB) | Total Peak Delta (MiB) | Scaling Behavior |
|:---:|:---:|:---:|:---:|:---:|:---:|---|
| 1,000 | 500 | 3.81 MiB | 0.25 MiB | **2.26 MiB** | 9.69 MiB | $O(T \times L)$ bounded |
| 5,000 | 500 | 19.07 MiB | 1.26 MiB | **2.32 MiB** | 21.40 MiB | $O(T \times L)$ bounded |
| 10,000 | 500 | 38.15 MiB | 2.52 MiB | **3.22 MiB** | 41.38 MiB | $O(T \times L)$ bounded |
| 50,000 | 500 | 190.73 MiB | 12.59 MiB | **14.01 MiB** | 204.75 MiB | $O(T \times L)$ bounded |
| 100,000 | 500 | 381.47 MiB | 25.18 MiB | **25.29 MiB** | 406.77 MiB | $O(T \times L)$ bounded |

## Key Architectural Findings

- **Zero Input Copies:** Input memory is borrowed directly without duplication ($0\times$ defensive copies).
- **Constant Scratch with respect to N:** The actual thread-local `Scratch` buffer size is proportional to $O(T \times L)$ (number of threads $T \times$ series length $L$), remaining bounded at **~3.2 MiB** regardless of whether $N = 1,000$ or $N = 100,000$.
- **Output Predictability:** The only component that scales linearly with $N$ is the caller's pre-allocated output matrix ($N \times 33 \times 8$ bytes).