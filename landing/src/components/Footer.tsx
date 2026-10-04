import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-borderDim bg-canvas pt-16 pb-12 text-xs font-sans text-body">
      <div className="mx-auto max-w-container px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 pb-12 border-b border-borderDim">
          {/* Brand Column */}
          <div className="md:col-span-5 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="flex h-5 w-5 flex-col justify-between py-0.5" aria-hidden="true">
                <span className="h-[2px] w-2 bg-ink" />
                <span className="h-[2px] w-3.5 bg-ink" />
                <span className="h-[2px] w-5 bg-ink" />
                <span className="h-[2px] w-3 bg-ink" />
              </div>
              <span className="font-sans text-lg font-bold tracking-tight text-ink">
                kymora
              </span>
            </div>
            <p className="max-w-sm text-body leading-relaxed">
              High-throughput batch time-series feature extraction in Python with an LLVM-optimized Rust core.
              Engineered for data science teams and real-time inference pipelines.
            </p>
            <div className="pt-1 font-mono text-[11px] text-muted">
              Repository: <a href="https://github.com/Aamodx6/Kymora" className="text-ink hover:underline">github.com/Aamodx6/Kymora</a>
            </div>
          </div>

          {/* Links Column 1: Library */}
          <div className="md:col-span-2 space-y-3">
            <h4 className="font-mono text-xs font-semibold text-ink uppercase tracking-wider">
              Library
            </h4>
            <ul className="space-y-2">
              <li>
                <a href="#features" className="hover:text-ink transition-colors">
                  Features
                </a>
              </li>
              <li>
                <a href="#benchmarks" className="hover:text-ink transition-colors">
                  Benchmarks
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-ink transition-colors">
                  How It Works
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/Aamodx6/Kymora#features"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-ink transition-colors"
                >
                  Feature Catalog
                </a>
              </li>
            </ul>
          </div>

          {/* Links Column 2: Ecosystem */}
          <div className="md:col-span-2 space-y-3">
            <h4 className="font-mono text-xs font-semibold text-ink uppercase tracking-wider">
              Ecosystem
            </h4>
            <ul className="space-y-2">
              <li>
                <a href="https://pyo3.rs" target="_blank" rel="noopener noreferrer" className="hover:text-ink transition-colors">
                  PyO3
                </a>
              </li>
              <li>
                <a href="https://github.com/rayon-rs/rayon" target="_blank" rel="noopener noreferrer" className="hover:text-ink transition-colors">
                  Rayon
                </a>
              </li>
              <li>
                <a href="https://numpy.org" target="_blank" rel="noopener noreferrer" className="hover:text-ink transition-colors">
                  NumPy
                </a>
              </li>
              <li>
                <a href="https://pola.rs" target="_blank" rel="noopener noreferrer" className="hover:text-ink transition-colors">
                  Polars
                </a>
              </li>
            </ul>
          </div>

          {/* Links Column 3: Community */}
          <div className="md:col-span-3 space-y-3">
            <h4 className="font-mono text-xs font-semibold text-ink uppercase tracking-wider">
              Project
            </h4>
            <ul className="space-y-2">
              <li>
                <a
                  href="https://github.com/Aamodx6/Kymora"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-ink transition-colors"
                >
                  GitHub Source Code
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/Aamodx6/Kymora/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-ink transition-colors"
                >
                  Issue Tracker
                </a>
              </li>
              <li>
                <a
                  href="https://pypi.org/project/kymora"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-ink transition-colors"
                >
                  PyPI Package
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/Aamodx6/Kymora/blob/main/LICENSE"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-ink transition-colors"
                >
                  License Terms
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11.5px] text-muted">
          <div>
            <span>Licensed under </span>
            <a
              href="https://github.com/Aamodx6/Kymora/blob/main/LICENSE"
              target="_blank"
              rel="noopener noreferrer"
              className="text-ink hover:underline"
            >
              MIT
            </a>
            <span>. Copyright &copy; {new Date().getFullYear()} Kymora contributors.</span>
          </div>

          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              <span>C-contiguous float64 compliant</span>
            </span>
            <span>·</span>
            <span>
              Made by <a href="https://github.com/Aamod007" target="_blank" rel="noopener noreferrer" className="font-semibold text-ink hover:underline">Aamod</a>
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
