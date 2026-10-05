import React, { useState, useEffect, useRef, useCallback } from 'react';
import { RowType } from './RowType';

interface FeatureFamilyData {
  name: string;
  now: number;
  prev: number;
  subtitle: string;
  filter: string;
  headers: [string, string, string];
  rows: [string, string, string][];
}

export const Hero: React.FC = () => {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'chart' | 'query'>('chart');
  const [isRunning, setIsRunning] = useState(false);
  const [pickedRegion, setPickedRegion] = useState<string | null>('Statistical');
  const [shownRegion, setShownRegion] = useState<string>('Statistical');
  const [stepStates, setStepStates] = useState<number[]>([2, 2, 2, 2]); // 0=wait, 1=on, 2=done
  const [ansIn, setAnsIn] = useState(true);
  const [chartIn, setChartIn] = useState(true);

  const heroGridRef = useRef<HTMLDivElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const pathRef = useRef<SVGPathElement>(null);
  const circleRef = useRef<SVGCircleElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const timersRef = useRef<number[]>([]);

  // Real core33 feature groups (frozen column order) with measured sample
  // values (3 gaussian series x 500, seed 7). `now`/`prev` are both the
  // group size: the catalog is frozen, so there is no fake delta.
  const featureFamilies: FeatureFamilyData[] = [
    {
      name: 'Statistical',
      now: 14,
      prev: 14,
      subtitle: 'Moments, quantiles, energy — population ddof=0',
      filter: 'kymora.extract_features(X, features=["mean", "std"])',
      headers: ['Series', 'Feature', 'Value'],
      rows: [
        ['TS-01', 'mean', '-0.1283'],
        ['TS-02', 'mean', '1.9838'],
        ['TS-03', 'mean', '-1.5228'],
      ],
    },
    {
      name: 'Change',
      now: 4,
      prev: 4,
      subtitle: 'Successive differences and complexity estimate',
      filter: 'kymora.extract_features(X, features=["mean_abs_change"])',
      headers: ['Series', 'Feature', 'Value'],
      rows: [
        ['TS-01', 'mean_abs_change', '1.0812'],
        ['TS-02', 'mean_abs_change', '1.0326'],
        ['TS-03', 'mean_abs_change', '1.1482'],
      ],
    },
    {
      name: 'Counts',
      now: 5,
      prev: 5,
      subtitle: 'Zero/mean crossings, peaks, strikes',
      filter: 'kymora.extract_features(X, features=["zero_crossings"])',
      headers: ['Series', 'Feature', 'Value'],
      rows: [
        ['TS-01', 'zero_crossings', '263.0'],
        ['TS-02', 'zero_crossings', '22.0'],
        ['TS-03', 'zero_crossings', '74.0'],
      ],
    },
    {
      name: 'Correlation',
      now: 6,
      prev: 6,
      subtitle: 'Autocorrelation lags 1/2/5/10, trend slope and r2',
      filter: 'kymora.extract_features(X, features=["autocorr_lag_1"])',
      headers: ['Series', 'Feature', 'Value'],
      rows: [
        ['TS-01', 'autocorr_lag_1', '-0.0282'],
        ['TS-02', 'autocorr_lag_1', '0.0852'],
        ['TS-03', 'autocorr_lag_1', '0.0637'],
      ],
    },
    {
      name: 'Entropy',
      now: 1,
      prev: 1,
      subtitle: 'Order-3 permutation entropy, normalized to [0, 1]',
      filter: 'kymora.extract_features(X, features=["permutation_entropy"])',
      headers: ['Series', 'Feature', 'Value'],
      rows: [
        ['TS-01', 'permutation_entropy', '0.9983'],
        ['TS-02', 'permutation_entropy', '0.9996'],
        ['TS-03', 'permutation_entropy', '0.9986'],
      ],
    },
    {
      name: 'Spectral',
      now: 3,
      prev: 3,
      subtitle: 'Exact-spectrum dominant frequency, centroid, entropy',
      filter: 'kymora.extract_features(X, features=["dominant_frequency"])',
      headers: ['Series', 'Feature', 'Value'],
      rows: [
        ['TS-01', 'dominant_frequency', '0.146'],
        ['TS-02', 'dominant_frequency', '0.468'],
        ['TS-03', 'dominant_frequency', '0.128'],
      ],
    },
  ];

  const steps = [
    'Mapping NumPy buffer',
    'Releasing Python GIL',
    'Dispatching Rayon worker threads',
    'Validating feature matrix',
  ];

  const copyCommand = async () => {
    try {
      await navigator.clipboard.writeText('pip install kymora');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  const handleRun = () => {
    setIsRunning(true);
    setTimeout(() => setIsRunning(false), 700);
  };

  const handlePickRow = (name: string) => {
    // Clear running auto-sequence timers so manual user interaction takes immediate priority
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
    setShownRegion(name);
    setPickedRegion(name);
  };

    // Authentic Framer entrance sequence + 1-time sequence across the 6 core33 groups
  useEffect(() => {
    const el = heroGridRef.current;
    if (!el) return;

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) return;

    let started = false;

    const playEntrance = () => {
      started = true;
      setStepStates([0, 0, 0, 0]);
      setAnsIn(false);
      setChartIn(false);
      setPickedRegion(null);
        setShownRegion('Statistical');

      // Steps sequence matching framer.md
      const stepTimes = [350, 1000, 1700, 2450, 3150];
      steps.forEach((_, idx) => {
        timersRef.current.push(
          window.setTimeout(() => {
            setStepStates((prev) => prev.map((s, i) => (i === idx ? 1 : s)));
          }, stepTimes[idx])
        );
        timersRef.current.push(
          window.setTimeout(() => {
            setStepStates((prev) => prev.map((s, i) => (i === idx ? 2 : s)));
          }, stepTimes[Math.min(idx + 1, stepTimes.length - 1)])
        );
      });

      // Answer reveal at 3250ms
      timersRef.current.push(window.setTimeout(() => setAnsIn(true), 3250));

      // Chart bars reveal at 3450ms
      timersRef.current.push(window.setTimeout(() => setChartIn(true), 3450));

      // 1-time sequential sweep through all 6 core33 feature groups.
      // Deltas read "frozen": the catalog is frozen, both bars are the
      // group size by design — no fabricated change.
      const sequence = ['Statistical', 'Change', 'Counts', 'Correlation', 'Entropy', 'Spectral'];
      let baseTime = 4100;

      sequence.forEach((familyName, idx) => {
        // Highlight current feature family & draw leader line
        timersRef.current.push(
          window.setTimeout(() => {
            setShownRegion(familyName);
            setPickedRegion(familyName);
          }, baseTime)
        );

        // If not the final family, briefly retract leader line before jumping to next family
        if (idx < sequence.length - 1) {
          timersRef.current.push(
            window.setTimeout(() => {
              setPickedRegion(null);
            }, baseTime + 1350)
          );
          baseTime += 1650;
        }
      });
    };

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !started) {
            playEntrance();
          }
        });
      },
      { threshold: 0.2 }
    );

    observer.observe(el);

    return () => {
      timersRef.current.forEach(clearTimeout);
      timersRef.current = [];
      observer.disconnect();
    };
  }, []);

  // Compute and update the dynamic SVG leader line between Left Popover and Right Chart Row
  const updateLeaderLine = useCallback(() => {
    const grid = heroGridRef.current;
    const popover = popoverRef.current;
    const chart = chartRef.current;
    const path = pathRef.current;
    const circle = circleRef.current;
    const svg = svgRef.current;
    if (!grid || !popover || !chart || !path || !circle || !svg) return;

    if (window.innerWidth < 1024 || !pickedRegion) {
      path.setAttribute('d', '');
      circle.style.opacity = '0';
      return;
    }

    const targetRow = chart.querySelector(`[data-region="${pickedRegion}"] .lgad-lab span`);
    if (!targetRow) return;

    const gridRect = grid.getBoundingClientRect();
    const popoverRect = popover.getBoundingClientRect();
    const targetRect = targetRow.getBoundingClientRect();

    // Start point: right edge of the popover card (near vertical center)
    const startX = popoverRect.right - gridRect.left;
    const startY = popoverRect.top + popoverRect.height / 2 - gridRect.top;

    // End point: immediately to the left of the row's label
    const endX = targetRect.left - gridRect.left - 6;
    const endY = targetRect.top + targetRect.height / 2 - gridRect.top;

    // Midpoint horizontal turning channel in the gap between the two columns
    const midX = Math.round((startX + endX) / 2);

    const d = `M ${startX} ${startY} H ${midX} V ${endY} H ${endX}`;
    path.setAttribute('d', d);

    const length = Math.ceil(
      Math.abs(midX - startX) + Math.abs(endY - startY) + Math.abs(endX - midX)
    );
    svg.style.setProperty('--len', String(length));

    circle.setAttribute('cx', String(endX));
    circle.setAttribute('cy', String(endY));
    circle.style.opacity = '1';
  }, [pickedRegion, ansIn, chartIn]);

  useEffect(() => {
    updateLeaderLine();
    window.addEventListener('resize', updateLeaderLine);
    const ro = new ResizeObserver(updateLeaderLine);
    if (heroGridRef.current) ro.observe(heroGridRef.current);

    return () => {
      window.removeEventListener('resize', updateLeaderLine);
      ro.disconnect();
    };
  }, [updateLeaderLine]);

  const maxVal = Math.max(...featureFamilies.map((r) => Math.max(r.now, r.prev)));
  const scaleMax = Math.ceil(maxVal / 100) * 100;
  const currentPopover = featureFamilies.find((r) => r.name === shownRegion) || featureFamilies[4];

  return (
    <section className="relative overflow-hidden pt-12 sm:pt-16 md:pt-20 lg:pt-24 pb-12 md:pb-16 lg:pb-20 font-sans">
      <div className="relative z-10 mx-auto max-w-[1248px] px-4 sm:px-6 lg:px-8">
        {/* 1. Large Two-Line Headline spanning full width across the top */}
        <div className="mb-6 lg:mb-8 w-full">
          <RowType
            text={'Ask your data.\nCheck every number.'}
            tag="h1"
            minSize={52}
            fluid={6.4}
            maxSize={104}
            weight={800}
            tracking={-0.035}
            lineHeight={0.93}
            color="#000000"
            marker="#FFE53B"
            paper="#F2F3EF"
            trigger="load"
            effect={true}
            walk={true}
          />
        </div>

        {/* 2. Two-Column Split Grid: Left Column (Copy + Buttons + Assurance + Popover) and Right Column (Product Window) */}
        <div
          ref={heroGridRef}
          className="relative grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start"
        >
          {/* Left Column (~42% / 5 cols) */}
          <div className="lg:col-span-5 flex flex-col gap-3.5 pt-0.5">
            {/* Copy Lead */}
            <p className="text-[15px] sm:text-[15.5px] text-[#50524B] leading-[1.48] max-w-md">
              <strong className="font-bold text-[#000000]">
                The time-series extractor that shows its work.
              </strong>{' '}
              Kymora maps zero-copy views into NumPy buffers, releases the GIL, and computes 33 features at 3.18 ms median per 1,000 series x 500 steps on an i7-13620H laptop (10 cores / 16 threads, exploratory — see Benchmarks). Every number links back to the rows it came from.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={copyCommand}
                className="inline-flex h-[36px] items-center justify-center gap-2 rounded-md bg-black px-3.5 text-xs font-semibold text-white shadow-btn transition hover:bg-neutral-800"
                aria-label="Copy pip install kymora"
              >
                <span className="text-neutral-400 select-none">$</span>
                <span>pip install kymora</span>
                {copied ? (
                  <span className="text-emerald-400 font-sans font-medium text-[11px] ml-1">Copied!</span>
                ) : (
                  <svg className="h-3.5 w-3.5 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" strokeWidth={1.5} />
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" strokeWidth={1.5} />
                  </svg>
                )}
              </button>

              <a
                href="https://github.com/Aamodx6/Kymora"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex h-[36px] items-center justify-center gap-2 rounded-md border border-[#D8D9D2] bg-white px-3.5 text-xs font-semibold text-black shadow-btn transition hover:border-black"
              >
                <svg className="h-3.5 w-3.5 fill-current" viewBox="0 0 24 24">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
                <span>GitHub</span>
              </a>
            </div>

            {/* Read-only Assurance lock note */}
            <div className="flex items-center gap-1.5 text-[11.5px] text-[#6B6D65]">
              <svg className="h-3.5 w-3.5 flex-none" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="3" y="7" width="10" height="7" rx="1.5" />
                <path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" />
              </svg>
              <span>Zero-copy memory safety. No data ever leaves your process.</span>
            </div>

            {/* Popover Card: Cleanly docked in Left Column with authentic Framer styling */}
            <div
              ref={popoverRef}
              className={`lgad-pop mt-0.5 ${pickedRegion ? 'is-in' : ''}`}
            >
              <p className="lgad-pt text-black tracking-tight flex items-center gap-1.5">
                <mark>
                  {currentPopover.now.toLocaleString()}
                </mark>
                <span>features in this frozen group</span>
              </p>
              <p className="lgad-ps">
                {currentPopover.subtitle}
              </p>

              <code className="lgad-pq">
                {currentPopover.filter}
              </code>

              <table className="lgad-tb">
                <thead>
                  <tr>
                    <th>{currentPopover.headers[0]}</th>
                    <th>{currentPopover.headers[1]}</th>
                    <th>{currentPopover.headers[2]}</th>
                  </tr>
                </thead>
                <tbody>
                  {currentPopover.rows.map((row, i) => (
                    <tr key={i}>
                      <td>{row[0]}</td>
                      <td>{row[1]}</td>
                      <td>{row[2]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="lgad-pf">
                <span>Open all rows</span>
                <em>Showing 3 of {currentPopover.now.toLocaleString()}</em>
              </div>
            </div>
          </div>

          {/* Right Column (~58% / 7 cols): Product Window */}
          <div className="lg:col-span-7">
            <div className="lgad" data-layout="wide" style={{ width: '100%' }}>
              <figure
                ref={chartRef}
                className="lgad-app"
                aria-label="Kymora Engine feature-group demo"
              >
                {/* Window Top Bar */}
                <div className="lgad-top">
                  <div className="lgad-ws">
                    {/* Stepped logo mark */}
                    <svg className="lgad-mark" width="15" height="15" viewBox="0 0 21 21" aria-hidden="true">
                      <g fill="currentColor">
                        <rect x="0" y="0" width="3" height="3" />
                        <rect x="0" y="4.5" width="5" height="3" />
                        <rect x="0" y="9" width="11" height="3" />
                        <rect x="0" y="13.5" width="17" height="3" />
                        <rect x="0" y="18" width="21" height="3" />
                      </g>
                    </svg>
                    <span>Kymora Engine</span>
                    <svg className="lgad-chev" width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M3 4.5 6 7.5 9 4.5" />
                    </svg>
                  </div>

                  <div className="lgad-ro">
                    <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <rect x="3" y="7" width="10" height="7" rx="1.5" />
                      <path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" />
                    </svg>
                    <span>Zero-copy FFI</span>
                  </div>
                </div>

                {/* Window Body */}
                <div className="lgad-body">
                  {/* Question */}
                  <p className="lgad-q text-black">
                    What does the core33 feature catalog contain?
                  </p>

                  {/* 4 Steps Checklist */}
                  <ol className="lgad-steps">
                    {steps.map((step, idx) => {
                      const state = stepStates[idx];
                      const isOn = state === 1;
                      const isDone = state === 2;

                      return (
                        <li
                          key={step}
                          className={`lgad-step ${isOn ? 'is-on' : isDone ? 'is-done' : ''}`}
                        >
                          <i className="lgad-box" />
                          <span>{step}</span>
                        </li>
                      );
                    })}
                  </ol>

                  {/* Answer with dotted underline */}
                  <p className={`lgad-a ${ansIn ? 'is-in' : ''} text-[#50524B]`}>
                    <span className="lgad-ref font-semibold text-black">
                      33 frozen features in 6 groups.
                    </span>{' '}
                    Every value above was computed by the calls shown — same
                    column order as `kymora.feature_names()`.
                  </p>

                  {/* Chart Section */}
                  <div className={`lgad-chart ${chartIn ? 'is-in' : ''}`}>
                    <div className="lgad-chead">
                      <span>Extracted features across categories, this run vs. baseline</span>
                      <span className="lgad-legend">
                        <i className="lgad-sw" style={{ background: '#000000' }} />
                        <span className="text-black font-medium">Kymora (Rust)</span>
                        <i className="lgad-sw" style={{ background: '#E2E3DC' }} />
                        <span>Python baseline</span>
                      </span>
                    </div>

                    {/* Chart Rows */}
                    <div className="lgad-crows">
                      {featureFamilies.map((region, idx) => {
                        const isDown = region.now < region.prev;
                        const pct = ((region.now - region.prev) / region.prev) * 100;
                        const isPicked = pickedRegion === region.name;
                        const nowWidth = (region.now / scaleMax) * 100;
                        const prevWidth = (region.prev / scaleMax) * 100;

                        return (
                          <div
                            key={region.name}
                            data-region={region.name}
                            onClick={() => handlePickRow(region.name)}
                            className={`lgad-crow ${isDown ? 'is-down' : ''} ${isPicked ? 'is-picked' : ''}`}
                          >
                            <span className="lgad-lab truncate">
                              <span>{region.name}</span>
                            </span>

                            <span className="lgad-bars">
                              <i
                                className="lgad-bi"
                                style={{
                                  background: '#000000',
                                  width: `${nowWidth}%`,
                                  transitionDelay: chartIn ? `${idx * 0.06}s` : '0s',
                                }}
                              />
                              <i
                                className="lgad-bi"
                                style={{
                                  background: '#E2E3DC',
                                  width: `${prevWidth}%`,
                                  transitionDelay: chartIn ? `${idx * 0.06}s` : '0s',
                                }}
                              />
                            </span>

                            <span className="lgad-val">
                              <b>{region.now.toLocaleString()}</b>
                              <i>
                                {pct === 0 ? (
                                  <>frozen</>
                                ) : (
                                  <>
                                    {pct > 0 ? '+' : '−'}
                                    {Math.abs(pct).toFixed(1)}%
                                  </>
                                )}
                              </i>
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Sources and Action Tabs */}
                  <div className="lgad-src">
                    <span className="lgad-srcl">Based on 3 buffers</span>
                    <span className="lgad-chip">numpy</span>
                    <span className="lgad-chip">polars</span>
                    <span className="lgad-chip">arrow</span>

                    <span className="lgad-gap" />

                    <span
                      onClick={() => setActiveTab(activeTab === 'query' ? 'chart' : 'query')}
                      className={`lgad-btn lgad-line lgad-sm ${activeTab === 'query' ? 'is-active' : ''}`}
                    >
                      View pipeline
                    </span>
                    <span
                      onClick={() => setActiveTab('chart')}
                      className={`lgad-btn lgad-line lgad-sm ${activeTab === 'chart' ? 'is-active' : ''}`}
                    >
                      View rows
                    </span>
                  </div>

                  {/* Pipeline snippet drawer */}
                  {activeTab === 'query' && (
                    <div className="mt-3 rounded-md border border-[#E2E3DC] bg-[#F2F3EF] p-3 font-mono text-[11.5px] text-black animate-in fade-in">
                      <pre>
                        <code>
                          <span className="py-kw">import</span> kymora <span className="py-kw">as</span> km{'\n'}
                          <span className="py-com"># One FFI crossing for the whole batch</span>{'\n'}
                          features = km.extract_features({'\n'}
                          {'    '}X, <span className="py-com"># (n_series, length), C-contiguous f64</span>{'\n'}
                          {'    '}features=[<span className="py-str">"mean"</span>, <span className="py-str">"std"</span>, <span className="py-str">"autocorr_lag_1"</span>],{'\n'}
                          {'    '}n_jobs=<span className="py-num">8</span>{'\n'}
                          )
                        </code>
                      </pre>
                    </div>
                  )}

                  {/* Follow-up Interactive input */}
                  <div className="lgad-follow">
                    <span className="lgad-field">
                      Extract another feature or slice (e.g. permutation_entropy, trend_slope)...
                    </span>
                    <span
                      onClick={handleRun}
                      className="lgad-btn lgad-line"
                    >
                      Benchmark
                    </span>
                    <span
                      onClick={handleRun}
                      className="lgad-btn lgad-ink"
                    >
                      {isRunning ? 'Running...' : 'Schedule pipeline'}
                    </span>
                  </div>
                </div>
              </figure>
            </div>
          </div>

          {/* 3. SVG Leader Line connecting Popover on Left to Row on Right */}
          <svg
            ref={svgRef}
            className={`lgad-leader hidden lg:block ${pickedRegion ? 'is-in' : ''}`}
            aria-hidden="true"
          >
            <path
              ref={pathRef}
              d=""
            />
            <circle
              ref={circleRef}
              r="3.5"
              cx="0"
              cy="0"
            />
          </svg>
        </div>
      </div>
    </section>
  );
};

export default Hero;
