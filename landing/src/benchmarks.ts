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

/* Measured 2026-11-22, pooled medians under High Performance same-session protocol;
   artifacts benchmarks/results/HEADLINE_SAME_SESSION_REPORT.md and headline_same_session_ratios.json.
   Kymora version label matches HEAD / 0.8.2 release. */
export const BENCHMARK_DATA: BenchmarkItem[] = [
  {
    id: "kymora",
    name: "Kymora",
    version: "0.8.2",
    language: "Rust + PyO3",
    featuresCount: 33,
    totalTimeMs: 1.94,
    seriesPerSec: 514245,
    msPerFeature: 0.0589,
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
    totalTimeMs: 185.50,
    seriesPerSec: 5391,
    msPerFeature: 8.43,
    multiplierVsKymora: 95.4,
    isKymora: false,
    notes: "Per-series Python iteration loop overhead (16 threads)",
  },
  {
    id: "tsfel",
    name: "TSFEL (all domains)",
    version: "0.3.0",
    language: "Pure Python / NumPy",
    featuresCount: 156,
    totalTimeMs: 2509.53,
    seriesPerSec: 398,
    msPerFeature: 16.09,
    multiplierVsKymora: 1291.0,
    isKymora: false,
    notes: "Multi-core extraction with array copies (16 threads)",
  },
  {
    id: "tsfresh",
    name: "tsfresh (EfficientFC)",
    version: "0.21.2",
    language: "Python + Multiprocessing",
    featuresCount: 777,
    totalTimeMs: 23540.62,
    seriesPerSec: 42,
    msPerFeature: 30.30,
    multiplierVsKymora: 12106.0,
    isKymora: false,
    notes: "Requires long DataFrame melt; IPC and pickle serialization cost (16 threads)",
  },
];
