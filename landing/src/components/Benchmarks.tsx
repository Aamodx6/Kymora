import React, { useState } from 'react';
import {
  BENCHMARK_DATA,
  BENCHMARK_CONFIG,
  BenchmarkItem,
  REAL_WORLD_BENCHMARKS,
  RealWorldBenchmarkItem,
} from '../benchmarks';
import { RandomHighlight } from './RandomHighlight';

export const Benchmarks: React.FC = () => {
  const [viewMode, setViewMode] = useState<'real-world' | 'libraries'>('real-world');
  const [metric, setMetric] = useState<'throughput' | 'latency'>('throughput');
  const [selectedItem, setSelectedItem] = useState<BenchmarkItem>(BENCHMARK_DATA[0]);
  const [selectedRealWorld, setSelectedRealWorld] = useState<RealWorldBenchmarkItem>(REAL_WORLD_BENCHMARKS[0]);
  const [copiedBenchCmd, setCopiedBenchCmd] = useState(false);

  const realBenchCommand = 'python benchmarks/benchmark_real_world.py';
  const libBenchCommand = 'python benchmarks/bench_libraries.py --n-series 1000 --n-steps 500';
  const activeCommand = viewMode === 'real-world' ? realBenchCommand : libBenchCommand;

  const copyBenchCommand = async () => {
    try {
      await navigator.clipboard.writeText(activeCommand);
      setCopiedBenchCmd(true);
      setTimeout(() => setCopiedBenchCmd(false), 2000);
    } catch {
      // fallback
    }
  };

  // Find max values for percentage calculations
  const maxThroughput = Math.max(...BENCHMARK_DATA.map((d) => d.seriesPerSec));
  const maxLatency = Math.max(...BENCHMARK_DATA.map((d) => d.totalTimeMs));
  const maxRealSpeedup = Math.max(...REAL_WORLD_BENCHMARKS.map((d) => d.speedup));

  return (
    <section id="benchmarks" className="py-20 md:py-28 border-b border-borderDim bg-canvas/30">
      <div className="mx-auto max-w-container px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="mb-8 max-w-3xl">
          <div className="mb-3 font-mono text-xs uppercase tracking-wider text-muted">
            Empirical Performance &amp; Real-World Parity
          </div>
          <h2 className="font-sans text-3xl font-extrabold tracking-tight text-ink sm:text-4xl md:text-5xl leading-tight">
            <RandomHighlight
              text="Measurably faster on real-world datasets."
              intervalRange={[2200, 3200]}
              maxSpan={2}
              color="#FFE53B"
              staticWordIndex={1}
              dotHandle={false}
            />
          </h2>
          <p className="mt-4 font-sans text-base sm:text-lg text-body leading-relaxed">
            Benchmarked exclusively on canonical empirical datasets from the UCR Time Series Archive (cardiology ECG, video motion tracking, semiconductor etching, and spectroscopy). Kymora extracts equal features <strong>135.9× to 1,946.2× faster</strong> with zero numerical drift.
          </p>
        </div>

        {/* View Mode Switcher Pills */}
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => setViewMode('real-world')}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 font-sans text-sm font-semibold transition ${
              viewMode === 'real-world'
                ? 'bg-ink text-white shadow-sm'
                : 'border border-borderLine bg-card text-body hover:border-ink/50 hover:text-ink'
            }`}
          >
            <span>⚡ Canonical Real-World Datasets (UCR)</span>
            <span className={`rounded px-1.5 py-0.5 text-[11px] font-mono ${
              viewMode === 'real-world' ? 'bg-white/20 text-white' : 'bg-highlight text-ink'
            }`}>
              135×–1,946×
            </span>
          </button>
          <button
            type="button"
            onClick={() => setViewMode('libraries')}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 font-sans text-sm font-semibold transition ${
              viewMode === 'libraries'
                ? 'bg-ink text-white shadow-sm'
                : 'border border-borderLine bg-card text-body hover:border-ink/50 hover:text-ink'
            }`}
          >
            <span>📊 Multi-Library Scalability (1k × 500)</span>
          </button>
        </div>

        {/* Reproduction Command Callout */}
        <div className="mb-8 rounded-lg border border-borderLine bg-card p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs font-mono">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-highlight text-[10px] font-bold text-ink">
              ✓
            </span>
            <div className="text-body">
              <span className="font-semibold text-ink">
                {viewMode === 'real-world' ? '100% REAL-WORLD DATASETS' : 'EXPLORATORY LAPTOP BENCHMARK'}
              </span>
              <p className="mt-0.5 text-muted">
                {viewMode === 'real-world'
                  ? '/* Evaluated on canonical UCR real-world splits (16 threads, Python 3.14.6) with bitwise parity verification and downstream ML evaluation. */'
                  : '/* Numbers below are single-machine measurements (i7-13620H, 10 cores/16 threads — see CLAIMS.md). Run the script below to verify. */'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={copyBenchCommand}
            className="group flex shrink-0 items-center gap-2 rounded border border-borderDim bg-canvas px-3 py-1.5 text-ink hover:border-ink"
            aria-label="Copy benchmark reproduction command"
          >
            <span>{copiedBenchCmd ? 'Copied script command!' : activeCommand}</span>
            <svg className="h-3.5 w-3.5 text-muted group-hover:text-ink" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" strokeWidth={1.5} />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" strokeWidth={1.5} />
            </svg>
          </button>
        </div>

        {/* View 1: Real-World Empirical Datasets */}
        {viewMode === 'real-world' && (
          <div className="rounded-xl border border-black/10 bg-card shadow-card overflow-hidden">
            {/* Header */}
            <div className="border-b border-borderDim px-5 py-4 sm:px-7 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="font-sans text-base font-bold text-ink">
                  Head-to-Head Real-World Extraction: Kymora vs TSFEL
                </h3>
                <p className="font-mono text-xs text-muted">
                  Canonical UCR Archive train/test partitions · 16 threads · Equal 13 definition-identical features
                </p>
              </div>
              <div className="flex items-center gap-2 font-mono text-xs text-muted">
                <span className="inline-block h-2 w-2 rounded-full bg-emerald-500"></span>
                <span>Bitwise Parity Verified (&lt; 1e-12)</span>
              </div>
            </div>

            {/* Real-World Items List */}
            <div className="p-5 sm:p-7 space-y-4">
              {REAL_WORLD_BENCHMARKS.map((item) => {
                const isSelected = selectedRealWorld.id === item.id;
                const barWidth = Math.max(12, Math.round((item.speedup / maxRealSpeedup) * 100));

                return (
                  <div
                    key={item.id}
                    onClick={() => setSelectedRealWorld(item)}
                    className={`group cursor-pointer rounded-lg p-4 transition border ${
                      isSelected
                        ? 'border-ink bg-canvas/50 shadow-sm'
                        : 'border-transparent bg-canvas/20 hover:border-borderLine hover:bg-canvas/30'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-3">
                        <span className="font-sans text-base font-bold text-ink">
                          {item.dataset}
                        </span>
                        <span className="font-mono text-[11px] text-muted rounded bg-card px-2 py-0.5 border border-borderDim">
                          {item.domain}
                        </span>
                        <span className="font-mono text-[11px] text-muted">
                          L={item.length} · N={item.nSeries}
                        </span>
                      </div>

                      <div className="flex items-center gap-3 font-mono text-xs">
                        <span className="font-bold text-ink">
                          Kymora: <strong className="text-emerald-600">{item.kymoraLatencyMs} ms</strong>
                        </span>
                        <span className="text-muted">
                          TSFEL: {item.tsfelLatencyMs.toLocaleString()} ms
                        </span>
                        <span className="rounded bg-highlight px-2 py-0.5 font-bold text-ink">
                          {item.speedup.toLocaleString()}× FASTER
                        </span>
                      </div>
                    </div>

                    {/* Progress visual */}
                    <div className="relative h-6 w-full rounded bg-borderDim/50 overflow-hidden mt-3">
                      <div
                        className="h-full rounded bg-ink text-white font-mono text-[11px] font-semibold flex items-center px-3 transition-all duration-500"
                        style={{ width: `${barWidth}%` }}
                      >
                        <span className="truncate">{item.speedup}× faster ({item.kymoraLatencyMs} ms vs {item.tsfelLatencyMs} ms)</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Selected Dataset Detail Drawer */}
            <div className="border-t border-borderDim bg-canvas/60 px-5 py-4 sm:px-7 text-xs font-mono">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-ink">{selectedRealWorld.dataset}:</span>
                  <span className="text-body">{selectedRealWorld.description}</span>
                </div>
                <div className="flex items-center gap-5 text-muted shrink-0">
                  <span>Relative Parity: <strong className="text-emerald-700 font-medium">{selectedRealWorld.parityError}</strong></span>
                  <span>ML Test Accuracy: <strong className="text-ink font-medium">{selectedRealWorld.mlAccuracy}</strong></span>
                </div>
              </div>
            </div>

            {/* Real World Footnote */}
            <div className="border-t border-borderDim px-5 py-4 sm:px-7 font-sans text-xs text-body leading-relaxed">
              <p>
                <strong>Full domain extraction comparison:</strong> On food spectroscopy (<em>Coffee</em>), full catalog extraction took <strong>1.54 ms</strong> with Kymora vs <strong>6,080.09 ms</strong> with TSFEL (<strong>3,948× faster</strong>).
                Evaluated on Random Forest and Ridge classifiers with 100% test accuracy retention.
              </p>
            </div>
          </div>
        )}

        {/* View 2: Multi-Library Synthetic Scalability Chart */}
        {viewMode === 'libraries' && (
          <div className="rounded-xl border border-black/10 bg-card shadow-card overflow-hidden">
            {/* Chart Header Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-borderDim px-5 py-4 sm:px-7">
              <div>
                <h3 className="font-sans text-base font-bold text-ink">
                  1,000 Series × 500 Steps (10 cores / 16 threads, exploratory)
                </h3>
                <p className="font-mono text-xs text-muted">
                  {BENCHMARK_CONFIG.seriesCount} series · {BENCHMARK_CONFIG.stepsCount} timesteps · {BENCHMARK_CONFIG.dtype} · {BENCHMARK_CONFIG.cpuCores} cores / {BENCHMARK_CONFIG.threadsCount} threads
                </p>
              </div>

              {/* Metric Toggle */}
              <div className="inline-flex rounded-lg border border-borderLine bg-canvas p-1 text-xs font-sans font-medium">
                <button
                  type="button"
                  onClick={() => setMetric('throughput')}
                  className={`rounded-md px-3 py-1.5 transition ${
                    metric === 'throughput'
                      ? 'bg-card text-ink font-semibold shadow-sm'
                      : 'text-body hover:text-ink'
                  }`}
                >
                  Throughput (series/s) ↑
                </button>
                <button
                  type="button"
                  onClick={() => setMetric('latency')}
                  className={`rounded-md px-3 py-1.5 transition ${
                    metric === 'latency'
                      ? 'bg-card text-ink font-semibold shadow-sm'
                      : 'text-body hover:text-ink'
                  }`}
                >
                  Total Latency (ms) ↓
                </button>
              </div>
            </div>

            {/* Chart Content Area */}
            <div className="p-5 sm:p-7 space-y-6">
              {BENCHMARK_DATA.map((item) => {
                let percent = 0;
                if (metric === 'throughput') {
                  percent = item.isKymora ? 100 : Math.max(2, Math.round(Math.log10(item.seriesPerSec + 1) / Math.log10(maxThroughput + 1) * 90));
                } else {
                  const ratio = item.totalTimeMs / maxLatency;
                  percent = item.isKymora ? 2 : Math.max(3, Math.round(ratio * 100));
                }

                const isSelected = selectedItem.id === item.id;

                return (
                  <div
                    key={item.id}
                    onClick={() => setSelectedItem(item)}
                    className={`group cursor-pointer rounded-lg p-3 transition border ${
                      isSelected
                        ? 'border-ink bg-canvas/40'
                        : 'border-transparent hover:border-borderLine hover:bg-canvas/20'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                      <div className="flex items-center gap-2.5">
                        <span className="font-sans text-sm font-bold text-ink">
                          {item.name}
                        </span>
                        <span className="font-mono text-[11px] text-muted rounded bg-canvas px-1.5 py-0.5">
                          {item.language}
                        </span>
                        {item.isKymora && (
                          <span className="rounded bg-highlight px-2 py-0.5 font-mono text-[10px] font-bold text-ink">
                            BASELINE
                          </span>
                        )}
                      </div>

                      <div className="font-mono text-xs font-semibold text-ink flex items-center gap-3">
                        {metric === 'throughput' ? (
                          <>
                            <span>{item.seriesPerSec.toLocaleString()} series/s</span>
                            {!item.isKymora && (
                              <span className="text-muted font-normal text-[11px]">
                                ({item.multiplierVsKymora}x slower)
                              </span>
                            )}
                          </>
                        ) : (
                          <>
                            <span>{item.totalTimeMs.toLocaleString()} ms</span>
                            {!item.isKymora && (
                              <span className="text-muted font-normal text-[11px]">
                                ({item.multiplierVsKymora}x slower)
                              </span>
                            )}
                          </>
                        )}
                      </div>
                    </div>

                    {/* Horizontal Bar */}
                    <div className="relative h-6 w-full rounded bg-borderDim/50 overflow-hidden">
                      <div
                        className={`h-full rounded transition-all duration-700 ease-out flex items-center px-2.5 ${
                          item.isKymora
                            ? 'bg-ink text-white font-mono text-[10px] font-semibold'
                            : 'bg-muted/30 text-ink font-mono text-[10px]'
                        }`}
                        style={{ width: `${percent}%` }}
                      >
                        {item.isKymora && (
                          <span className="truncate">Kymora (514k series/s)</span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Selected Library Detail Footer Drawer */}
            <div className="border-t border-borderDim bg-canvas/50 px-5 py-4 sm:px-7 text-xs font-mono">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-ink">{selectedItem.name} Details:</span>
                  <span className="text-body">{selectedItem.notes}</span>
                </div>
                <div className="flex items-center gap-4 text-muted">
                  <span>Features: <strong className="text-ink font-medium">{selectedItem.featuresCount}</strong></span>
                  <span>Time/feat: <strong className="text-ink font-medium">{selectedItem.msPerFeature} µs</strong></span>
                </div>
              </div>
            </div>

            {/* Benchmarks and limitations */}
            <div className="border-t border-borderDim px-5 py-5 sm:px-7 font-sans text-sm text-body leading-relaxed">
              <p className="font-semibold text-ink">Benchmarks and limitations</p>
              <p className="mt-1.5">
                Raw totals compare 33 features against up to 777 — read the
                per-feature column, and the like-for-like equal-feature table in
                the README (TSFEL 13: 1,089.1×, tsfresh 13: 2,812.4×, numba 33:
                6.0×, all parity-gated). Kymora loses small-batch cases to numba
                (1.4×–1.8× at 1×100: fixed dispatch overhead), scaling stops near
                physical cores, and these are single-machine exploratory numbers.
                Full claim→artifact map: CLAIMS.md in the repo.
              </p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
