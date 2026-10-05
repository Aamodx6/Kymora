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
        'Inner computational loops are compiled with full optimizations and run across worker threads. Computes 33 features at 3.18 ms median per 1,000 series x 500 steps on an i7-13620H laptop (10 cores / 16 threads, exploratory).',
      codeSnippet: '// Rayon parallel chunk iterator\nseries.par_chunks(chunk_size)\n  .map(|chunk| compute_features(chunk))',
      badge: '3.18 ms median (1k x 500)',
    },
    {
      number: '02',
      title: 'Parallel Extraction',
      tag: 'Series-dimension scaling',
      description:
        'The GIL is released immediately upon entering Rust. Extraction parallelises across the series dimension using Rayon, scaling up to the physical core count (plateaus near it on hybrid laptops — see Benchmarks).',
      codeSnippet: '# GIL released, 16 cores fully saturated\nX = np.random.randn(100_000, 500)\nfeats = kymora.extract_features(X)',
      badge: 'GIL-free Rayon scaling',
    },
    {
      number: '03',
      title: '33 Curated Features',
      tag: 'Statistical & Spectral',
      description:
        'Carefully selected feature set covering statistical moments (mean, variance, skewness, kurtosis), temporal dynamics (autocorrelation, zero-crossings), and FFT spectral energy.',
      codeSnippet: 'features = [\n  "mean", "var", "skewness",\n  "permutation_entropy", "spectral_centroid"\n]',
      badge: 'Documented NaN contract',
    },
    {
      number: '04',
      title: 'Pandas & Polars Friendly',
      tag: 'DataFrame interop',
      description:
        'Return results directly as typed Polars or Pandas DataFrames with human-readable column headers via extract_features_df(X). Keeps index and metadata intact.',
      codeSnippet: 'df = kymora.extract_features_df(X)\nprint(df.columns)  # [mean, std, var, ...]',
      badge: 'Zero serialization overhead',
    },
    {
      number: '05',
      title: 'Zero-Copy NumPy Interop',
      tag: 'PyO3 memory buffers',
      description:
        'Binds directly to contiguous C-order float64 numpy arrays without copying memory into Rust. Input validation enforces contiguous layouts at zero runtime penalty.',
      codeSnippet: '# Direct memory pointer borrowed by Rust\nassert X.flags["C_CONTIGUOUS"]\nfeats = kymora.extract_features(X)',
      badge: '0 intermediate copies',
    },
    {
      number: '06',
      title: 'Sklearn-Ready Pipelines',
      tag: 'Drop-in Transformer',
      description:
        'Includes a standard Scikit-learn transformer class. Plug time-series feature extraction directly into Pipeline, GridSearchCV, and ColumnTransformer workflows.',
      codeSnippet: 'from kymora.sklearn import KymoraTransformer\npipe = Pipeline([\n  ("extract", KymoraTransformer()),\n  ("clf", HistGradientBoostingClassifier())\n])',
      badge: 'Estimator compliant',
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

        {/* 6 Cards Grid with hover lift */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((card) => (
            <div
              key={card.number}
              className="group relative flex flex-col justify-between rounded-xl border border-borderLine bg-card p-6 sm:p-7 shadow-card transition-all duration-200 hover:-translate-y-1 hover:border-ink/40 hover:shadow-card-hover"
            >
              <div>
                {/* Header row: Number and Tag */}
                <div className="flex items-center justify-between border-b border-borderDim pb-4 mb-5">
                  <span className="font-mono text-xs font-bold text-ink bg-canvas px-2 py-0.5 rounded">
                    {card.number}
                  </span>
                  <span className="font-mono text-[11px] text-muted tracking-tight">
                    {card.tag}
                  </span>
                </div>

                {/* Card Title */}
                <h3 className="font-sans text-xl font-bold text-ink mb-2.5 tracking-tight group-hover:text-black">
                  {card.title}
                </h3>

                {/* Card Description */}
                <p className="font-sans text-sm text-body leading-relaxed mb-6">
                  {card.description}
                </p>
              </div>

              <div>
                {/* Code Mini block */}
                {card.codeSnippet && (
                  <div className="rounded-md border border-borderDim bg-canvas/70 p-3 font-mono text-[11px] text-ink overflow-x-auto leading-relaxed mb-4">
                    <pre className="text-body whitespace-pre">{card.codeSnippet}</pre>
                  </div>
                )}

                {/* Badge indicator */}
                {card.badge && (
                  <div className="flex items-center gap-1.5 text-xs font-mono font-medium text-ink">
                    <span className="h-1.5 w-1.5 rounded-full bg-highlight" />
                    <span>{card.badge}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
