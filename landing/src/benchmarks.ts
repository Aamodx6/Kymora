/**
 * Benchmark Datasets for Kymora Landing Page
 *
 * Measured 2026-11-24 on Canonical Real-World UCR Archive Datasets
 * and exploratory high-throughput synthetic runs (Python 3.14.6, 16 threads).
 * Artifacts:
 *   - benchmarks/results/KYMORA_VS_TSFEL_BENCHMARK_REPORT.md
 *   - benchmarks/results/kymora_vs_tsfel_real_benchmark.json
 *   - benchmarks/results/HEADLINE_SAME_SESSION_REPORT.md
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
  multiplierVsKymora: number; // e.g. 1 for baseline, 95 for 95x slower
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
  runner: "i7-13620H laptop, 16 threads, Python 3.14.6",
};

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
    notes: "Direct buffer borrowing (no copy of the input), GIL-released Rayon parallel compute",
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

export interface RealWorldBenchmarkItem {
  id: string;
  dataset: string;
  domain: string;
  length: number;
  nSeries: number;
  kymoraLatencyMs: number;
  tsfelLatencyMs: number;
  speedup: number;
  parityError: string;
  mlAccuracy: string;
  description: string;
}

export const REAL_WORLD_BENCHMARKS: RealWorldBenchmarkItem[] = [
  {
    id: "gunpoint",
    dataset: "GunPoint",
    domain: "Video Motion Capture",
    length: 150,
    nSeries: 300,
    kymoraLatencyMs: 1.57,
    tsfelLatencyMs: 3065.13,
    speedup: 1946.2,
    parityError: "< 8.59e-13",
    mlAccuracy: "100.0%",
    description: "Motion tracking sensor telemetry distinguishing actors drawing a replica gun vs pointing a finger.",
  },
  {
    id: "coffee",
    dataset: "Coffee",
    domain: "Food Spectroscopy",
    length: 286,
    nSeries: 300,
    kymoraLatencyMs: 1.35,
    tsfelLatencyMs: 200.42,
    speedup: 147.9,
    parityError: "< 8.59e-13",
    mlAccuracy: "100.0%",
    description: "Near-infrared absorption spectra discriminating Arabica from Robusta coffee beans (full catalog speedup: 3,948x).",
  },
  {
    id: "ecg200",
    dataset: "ECG200",
    domain: "Cardiology / Medical",
    length: 96,
    nSeries: 300,
    kymoraLatencyMs: 0.64,
    tsfelLatencyMs: 197.23,
    speedup: 307.8,
    parityError: "< 8.59e-13",
    mlAccuracy: "100.0%",
    description: "Patient electrocardiogram heartbeats diagnosing normal rhythm vs myocardial infarction.",
  },
  {
    id: "wafer",
    dataset: "Wafer",
    domain: "Semiconductor Etching",
    length: 152,
    nSeries: 300,
    kymoraLatencyMs: 1.25,
    tsfelLatencyMs: 211.76,
    speedup: 169.2,
    parityError: "< 8.59e-13",
    mlAccuracy: "100.0%",
    description: "Real-time inline fabrication sensor telemetry during semiconductor wafer plasma etching.",
  },
  {
    id: "italypower",
    dataset: "ItalyPowerDemand",
    domain: "Power Grid Telemetry",
    length: 24,
    nSeries: 300,
    kymoraLatencyMs: 1.27,
    tsfelLatencyMs: 172.56,
    speedup: 135.9,
    parityError: "< 8.59e-13",
    mlAccuracy: "100.0%",
    description: "National electrical energy demand telemetry comparing seasonal cycles in Italy.",
  },
];
