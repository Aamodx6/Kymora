/**
 * Benchmark Datasets for Kymora Landing Page
 *
 * Measured 2026-11-22 (EXPLORATORY single-machine numbers — see CLAIMS.md).
 * Artifact: benchmarks/results/2026-11-22_reproduce_readme/ (subprocess runs).
 * Reference command:
 *   python benchmarks/bench_libraries.py --n-series 1000 --n-steps 500
 * Tested on: 1,000 series x 500 steps, i7-13620H laptop, 10 cores (6P+4E) /
 * 16 threads, Windows 11, AC online, power scheme recorded in env.json, float64 C-contiguous.
 */

export interface BenchmarkItem {
  id: string;
  name: string;
  version: string;
  language: string;
  featuresCount: number;
  totalTimeMs: number; // in milliseconds
  seriesPerSec: number;
  msPerFeature: number;
  multiplierVsKymora: number; // e.g. 1 for baseline, 262 for 262x slower
  isKymora: boolean;
  notes: string;
}

export interface BenchmarkConfig {
  seriesCount: number;
  stepsCount: number;
  cpuCores: number;
  threadsCount: number;
  dtype: string;
  runner: string;
}

export const BENCHMARK_CONFIG: BenchmarkConfig = {
  seriesCount: 1000,
  stepsCount: 500,
  cpuCores: 10,
  threadsCount: 16,
  dtype: "float64",
  runner: "i7-13620H laptop, exploratory (see CLAIMS.md)",
};

/* Measured 2026-11-22, pooled medians; artifact benchmarks/results/2026-11-22_reproduce_readme/.
   Kymora version label matches the artifact-era code (0.8.0). */
export const BENCHMARK_DATA: BenchmarkItem[] = [
  {
    id: "kymora",
    name: "Kymora",
    version: "0.8.0",
    language: "Rust + PyO3",
    featuresCount: 33,
    totalTimeMs: 1.84,
    seriesPerSec: 542682,
    msPerFeature: 0.0558,
    multiplierVsKymora: 1.0,
    isKymora: true,
    notes: "Zero-copy NumPy view, GIL-released Rayon parallel compute",
  },
  {
    id: "catch22",
    name: "catch22 (pycatch22)",
    version: "1.0.2",
    language: "C wrapper",
    featuresCount: 22,
    totalTimeMs: 432.6,
    seriesPerSec: 2312,
    msPerFeature: 19.66,
    multiplierVsKymora: 235.0,
    isKymora: false,
    notes: "Per-series Python iteration loop overhead",
  },
  {
    id: "tsfel",
    name: "TSFEL (all domains)",
    version: "0.3.0",
    language: "Pure Python / NumPy",
    featuresCount: 156,
    totalTimeMs: 2041.5,
    seriesPerSec: 490,
    msPerFeature: 13.09,
    multiplierVsKymora: 1108.0,
    isKymora: false,
    notes: "Sequential python feature routines with heavy array copies",
  },
  {
    id: "tsfresh",
    name: "tsfresh (EfficientFC)",
    version: "0.21.2",
    language: "Python + Multiprocessing",
    featuresCount: 777,
    totalTimeMs: 14966.8,
    seriesPerSec: 67,
    msPerFeature: 19.26,
    multiplierVsKymora: 8122.0,
    isKymora: false,
    notes: "Requires long DataFrame melt; IPC and pickle serialization cost",
  },
];
