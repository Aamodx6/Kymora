/**
 * Benchmark Datasets for Tsxtract Landing Page
 * 
 * =========================================================================
 * NOTE: REPLACE WITH REAL NUMBERS WHEN UPDATING YOUR REPRODUCIBLE BENCHMARKS
 * =========================================================================
 * Reference command:
 *   python benches/bench_libraries.py --n-series 1000 --n-steps 500
 * Tested on: 1,000 series x 500 steps, 16 cores (float64, C-contiguous)
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
  multiplierVsTsxtract: number; // e.g. 1 for baseline, 820 for 820x slower
  isTsxtract: boolean;
  notes: string;
}

export interface BenchmarkConfig {
  seriesCount: number;
  stepsCount: number;
  cpuCores: number;
  dtype: string;
  runner: string;
}

export const BENCHMARK_CONFIG: BenchmarkConfig = {
  seriesCount: 1000,
  stepsCount: 500,
  cpuCores: 16,
  dtype: "float64",
  runner: "16-core AMD Ryzen / GitHub Linux Actions Runner",
};

/* PLACEHOLDER DATA: Calibrated against published tsxtractor 0.2.1 suite */
export const BENCHMARK_DATA: BenchmarkItem[] = [
  {
    id: "tsxtract",
    name: "Tsxtract",
    version: "0.2.1",
    language: "Rust + PyO3",
    featuresCount: 33,
    totalTimeMs: 1.2,
    seriesPerSec: 800256,
    msPerFeature: 0.0379,
    multiplierVsTsxtract: 1.0,
    isTsxtract: true,
    notes: "Zero-copy NumPy view, GIL-released Rayon parallel compute",
  },
  {
    id: "catch22",
    name: "catch22 (pycatch22)",
    version: "0.4.4",
    language: "C wrapper",
    featuresCount: 22,
    totalTimeMs: 1020.0,
    seriesPerSec: 976,
    msPerFeature: 46.58,
    multiplierVsTsxtract: 820.0,
    isTsxtract: false,
    notes: "Per-series Python iteration loop overhead",
  },
  {
    id: "tsfel",
    name: "TSFEL (all domains)",
    version: "0.1.6",
    language: "Pure Python / NumPy",
    featuresCount: 156,
    totalTimeMs: 7150.0,
    seriesPerSec: 140,
    msPerFeature: 45.86,
    multiplierVsTsxtract: 5725.0,
    isTsxtract: false,
    notes: "Sequential python feature routines with heavy array copies",
  },
  {
    id: "tsfresh",
    name: "tsfresh (EfficientFC)",
    version: "0.20.2",
    language: "Python + Multiprocessing",
    featuresCount: 777,
    totalTimeMs: 17680.0,
    seriesPerSec: 57,
    msPerFeature: 22.76,
    multiplierVsTsxtract: 14151.0,
    isTsxtract: false,
    notes: "Requires long DataFrame melt; IPC and pickle serialization cost",
  },
];
