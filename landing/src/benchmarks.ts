/**
 * Benchmark Datasets for Kymora Landing Page
 *
 * Measured 2026-10-04 (EXPLORATORY single-machine numbers — see CLAIMS.md).
 * Artifact: benchmarks/results/F1_REPORT.md (10 interleaved rounds).
 * Reference command:
 *   python benchmarks/bench_libraries.py --n-series 1000 --n-steps 500
 * Tested on: 1,000 series x 500 steps, i7-13620H laptop, 10 cores (6P+4E) /
 * 16 threads, Windows 11, Performance plan, AC online, float64 C-contiguous.
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

/* Measured 2026-10-04, pooled medians; artifact benchmarks/results/F1_REPORT.md */
export const BENCHMARK_DATA: BenchmarkItem[] = [
  {
    id: "kymora",
    name: "Kymora",
    version: "0.5.0",
    language: "Rust + PyO3",
    featuresCount: 33,
    totalTimeMs: 3.18,
    seriesPerSec: 314450,
    msPerFeature: 0.0964,
    multiplierVsKymora: 1.0,
    isKymora: true,
    notes: "Zero-copy NumPy view, GIL-released Rayon parallel compute",
  },
  {
    id: "catch22",
    name: "catch22 (pycatch22)",
    version: "0.5.0",
    language: "C wrapper",
    featuresCount: 22,
    totalTimeMs: 833.1,
    seriesPerSec: 1200,
    msPerFeature: 37.87,
    multiplierVsKymora: 262.0,
    isKymora: false,
    notes: "Per-series Python iteration loop overhead",
  },
  {
    id: "tsfel",
    name: "TSFEL (all domains)",
    version: "0.2.0",
    language: "Pure Python / NumPy",
    featuresCount: 156,
    totalTimeMs: 2541.6,
    seriesPerSec: 393,
    msPerFeature: 16.29,
    multiplierVsKymora: 799.2,
    isKymora: false,
    notes: "Sequential python feature routines with heavy array copies",
  },
  {
    id: "tsfresh",
    name: "tsfresh (EfficientFC)",
    version: "0.21.2",
    language: "Python + Multiprocessing",
    featuresCount: 777,
    totalTimeMs: 20891.2,
    seriesPerSec: 48,
    msPerFeature: 26.89,
    multiplierVsKymora: 6570.0,
    isKymora: false,
    notes: "Requires long DataFrame melt; IPC and pickle serialization cost",
  },
];
