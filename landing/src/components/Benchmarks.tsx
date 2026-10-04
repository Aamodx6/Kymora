import React, { useState } from 'react';
import { BENCHMARK_DATA, BENCHMARK_CONFIG, BenchmarkItem } from '../benchmarks';
import { RandomHighlight } from './RandomHighlight';

export const Benchmarks: React.FC = () => {
  const [metric, setMetric] = useState<'throughput' | 'latency'>('throughput');
  const [selectedItem, setSelectedItem] = useState<BenchmarkItem>(BENCHMARK_DATA[0]);
  const [copiedBenchCmd, setCopiedBenchCmd] = useState(false);

  const benchCommand = 'python benchmarks/bench_libraries.py --n-series 1000 --n-steps 500';

  const copyBenchCommand = async () => {
    try {
      await navigator.clipboard.writeText(benchCommand);
      setCopiedBenchCmd(true);
      setTimeout(() => setCopiedBenchCmd(false), 2000);
    } catch {
      // fallback
    }
  };

  // Find max values for percentage calculations
  const maxThroughput = Math.max(...BENCHMARK_DATA.map((d) => d.seriesPerSec));
  const maxLatency = Math.max(...BENCHMARK_DATA.map((d) => d.totalTimeMs));

  return (
    <section id="benchmarks" className="py-20 md:py-28 border-b border-borderDim bg-canvas/30">
      <div className="mx-auto max-w-container px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="mb-12 max-w-3xl">
          <div className="mb-3 font-mono text-xs uppercase tracking-wider text-muted">
            Empirical Performance
          </div>
          <h2 className="font-sans text-3xl font-extrabold tracking-tight text-ink sm:text-4xl md:text-5xl leading-tight">
            <RandomHighlight
              text="Measurably faster than Python alternatives."
              intervalRange={[2200, 3200]}
              maxSpan={2}
              color="#FFE53B"
              staticWordIndex={1}
              dotHandle={false}
            />
          </h2>
          <p className="mt-4 font-sans text-base sm:text-lg text-body leading-relaxed">
            Standard Python time-series packages compute features using sequential loops or Python-level
            multiprocessing. Kymora uses Rust zero-copy buffers and multi-threaded Rayon work-stealing.
          </p>
        </div>

        {/* Visible Placeholder Disclaimer Callout */}
        <div className="mb-8 rounded-lg border border-borderLine bg-card p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs font-mono">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-highlight text-[10px] font-bold text-ink">
              !
            </span>
            <div className="text-body">
              <span className="font-semibold text-ink">EXPLORATORY LAPTOP BENCHMARK</span>
              <p className="mt-0.5 text-muted">
                /* Numbers below are single-machine measurements (i7-13620H, 10 cores/16 threads — see CLAIMS.md), not fleet evidence. Run the script below on your machine to verify. */
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={copyBenchCommand}
            className="group flex shrink-0 items-center gap-2 rounded border border-borderDim bg-canvas px-3 py-1.5 text-ink hover:border-ink"
            aria-label="Copy benchmark reproduction command"
          >
            <span>{copiedBenchCmd ? 'Copied script command!' : benchCommand}</span>
            <svg className="h-3.5 w-3.5 text-muted group-hover:text-ink" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" strokeWidth={1.5} />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" strokeWidth={1.5} />
            </svg>
          </button>
        </div>

        {/* Interactive Chart Container */}
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
              // Calculate bar width percentage
              let percent = 0;
              if (metric === 'throughput') {
                // Logarithmic-scaled bar for wide dynamic range
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
                        <span className="truncate">Kymora (314k series/s, exploratory)</span>
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
        </div>
      </div>
    </section>
  );
};
