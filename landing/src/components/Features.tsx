import React from 'react';
import { RandomHighlight } from './RandomHighlight';

interface FeatureCard {
  number: string;
  title: string;
  tag: string;
  description: string;
  codeSnippet?: string;
  badge?: string;
}

export const Features: React.FC = () => {
  const features: FeatureCard[] = [
    {
      number: '01',
      title: 'Rust-Core Speed',
      tag: 'Rust + Rayon',
      description:
        'Inner computational loops are compiled with native SIMD and multi-core work-stealing. Extracts features up to 3,948× faster than Python libraries on real-world datasets.',
      codeSnippet: '// Rayon parallel chunk iterator\nseries.par_chunks(chunk_size)\n  .map(|chunk| compute_features(chunk))',
      badge: '0.64 ms on real ECG200',
    },
    {
      number: '02',
      title: 'Parallel Extraction',
      tag: 'Series-dimension scaling',
      description:
        'The GIL is released immediately upon entering Rust. Extraction parallelises across the series dimension using Rayon, scaling linearly up to physical core count.',
      codeSnippet: '# GIL released, 16 cores fully saturated\nX = np.random.randn(100_000, 500)\nfeats = kymora.extract_features(X)',
      badge: 'GIL-free Rayon scaling',
    },
    {
      number: '03',
      title: '100% TSFEL Drop-In Migration',
      tag: 'Zero-code replacement',
      description:
        'Switch from TSFEL with a single import change. Run existing configurations, feature extraction pipelines, and collinearity filters with zero code rewrites.',
      codeSnippet: 'from kymora.compat import tsfel\ncfg = tsfel.get_features_by_domain()\ndf = tsfel.time_series_features_extractor(cfg, X)',
      badge: 'Up to 1,000× faster',
    },
    {
      number: '04',
      title: 'Acoustic & Dyadic CWT Wavelets',
      tag: 'Cepstral & Continuous Wavelets',
      description:
        'SIMD-accelerated Mel filterbank cepstrals (MFCC 0–11), LPCC autoregressive coefficients, and dyadic Ricker continuous wavelet transforms (37 wavelet features).',
      codeSnippet: 'feats = ["mfcc_0", "lpcc_0", "wavelet_energy_scale_1"]\ndf = kymora.extract_features_df(X, features=feats)',
      badge: '0.00 bitwise parity',
    },
    {
      number: '05',
      title: 'Scientific Domain Ergonomics',
      tag: 'Domain-driven filtering',
      description:
        'Extract features by scientific domain: statistical (36 features), temporal (23 features), spectral (75 features), or fractal. Mix and match with native profiles.',
      codeSnippet: '# Extract all statistical features\ndf = kymora.extract_features_df(X, domain="statistical")',
      badge: 'Domain-targeted',
    },
    {
      number: '06',
      title: 'Direct NumPy Buffer Borrowing',
      tag: 'PyO3 memory buffers',
      description:
        'Binds directly to contiguous C-order float64 and float32 NumPy arrays without copying memory into Rust. Input validation enforces contiguous layouts at zero penalty.',
      codeSnippet: '# Direct memory pointer borrowed by Rust\nassert X.flags["C_CONTIGUOUS"]\nfeats = kymora.extract_features(X)',
      badge: '0 intermediate copies',
    },
    {
      number: '07',
      title: 'Pandas & Polars Friendly',
      tag: 'DataFrame interop',
      description:
        'Return results directly as typed Polars or Pandas DataFrames with human-readable column headers via extract_features_df(X) or extract_features_polars(X).',
      codeSnippet: 'df = kymora.extract_features_df(X)\nprint(df.columns)  # [mean, std, var, ...]',
      badge: 'Zero serialization overhead',
    },
    {
      number: '08',
      title: 'Sklearn-Ready Pipelines',
      tag: 'Drop-in Transformer',
      description:
        'Includes standard Scikit-learn transformer and selector classes. Plug time-series extraction and FDR feature selection directly into Pipeline workflows.',
      codeSnippet: 'from kymora.sklearn import KymoraTransformer\npipe = Pipeline([\n  ("extract", KymoraTransformer()),\n  ("clf", HistGradientBoostingClassifier())\n])',
      badge: 'Estimator compliant',
    },
    {
      number: '09',
      title: 'Fleet Real-Time Streaming',
      tag: 'Rolling telemetry',
      description:
        'Stream thousands of live signals concurrently with amortized O(1) rolling-window updates. Bounded memory and sub-microsecond event loops.',
      codeSnippet: 'stream = kymora.StreamingExtractor(window=256)\nfor sample in sensor_feed:\n  features = stream.update(sample)',
      badge: 'Amortized O(1) sliding',
    },
  ];

  return (
    <section id="features" className="py-20 md:py-28 border-b border-borderDim bg-canvas">
      <div className="mx-auto max-w-container px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="mb-16 max-w-3xl">
          <div className="mb-3 font-mono text-xs uppercase tracking-wider text-muted">
            Architecture &amp; Capabilities
          </div>
          <h2 className="font-sans text-3xl font-extrabold tracking-tight text-ink sm:text-4xl md:text-5xl leading-tight">
            <RandomHighlight
              text="Engineered for high-throughput machine learning."
              intervalRange={[2400, 3400]}
              maxSpan={2}
              color="#FFE53B"
              staticWordIndex={3}
              dotHandle={false}
            />
          </h2>
          <p className="mt-4 font-sans text-base sm:text-lg text-body leading-relaxed">
            Every layer from NumPy buffer inspection to multi-core Rayon reduction is designed
            to eliminate memory copies, prevent GIL contention, and maximize hardware efficiency.
          </p>
        </div>

        {/* 9 Cards Grid (3x3) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((card) => (
            <div
              key={card.number}
              className="group relative flex flex-col justify-between rounded-xl border border-borderLine bg-card p-6 sm:p-7 shadow-card transition-all duration-200 hover:-translate-y-1 hover:border-ink/40 hover:shadow-card-hover"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="font-mono text-xs font-bold text-muted group-hover:text-ink transition-colors">
                    {card.number}
                  </span>
                  <span className="rounded bg-canvas px-2.5 py-1 font-mono text-[11px] text-body border border-borderDim">
                    {card.tag}
                  </span>
                </div>

                <h3 className="font-sans text-lg font-bold text-ink mb-2">
                  {card.title}
                </h3>

                <p className="font-sans text-sm text-body leading-relaxed mb-4">
                  {card.description}
                </p>
              </div>

              <div>
                {card.codeSnippet && (
                  <pre className="rounded-lg bg-canvas p-3 font-mono text-[11px] text-ink border border-borderDim overflow-x-auto mb-3">
                    <code>{card.codeSnippet}</code>
                  </pre>
                )}

                {card.badge && (
                  <span className="inline-block rounded bg-highlight/30 px-2 py-0.5 font-mono text-[10px] font-bold text-ink">
                    {card.badge}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
