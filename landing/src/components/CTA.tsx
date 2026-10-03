import React, { useState } from 'react';

export const CTA: React.FC = () => {
  const [copied, setCopied] = useState(false);

  const copyCommand = async () => {
    try {
      await navigator.clipboard.writeText('pip install tsxtract-rs');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  return (
    <section className="py-20 md:py-28 bg-canvas">
      <div className="mx-auto max-w-container px-4 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-2xl border border-black/10 bg-card p-8 sm:p-12 md:p-16 shadow-card text-center">
          {/* Subtle highlighter mark in background */}
          <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-highlight/30 blur-3xl" />
          <div className="pointer-events-none absolute -left-24 -bottom-24 h-64 w-64 rounded-full bg-borderDim/50 blur-3xl" />

          <div className="relative z-10 mx-auto max-w-2xl">
            {/* Tag */}
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-borderLine bg-canvas px-3 py-1 font-mono text-xs font-semibold text-ink">
              <span className="h-1.5 w-1.5 rounded-full bg-highlight" />
              <span>PRODUCTION-READY TIME SERIES</span>
            </div>

            {/* Title */}
            <h2 className="font-sans text-3xl font-extrabold tracking-tight text-ink sm:text-4xl md:text-5xl leading-tight mb-4">
              Stop waiting on Python loops. Extract at Rust speed.
            </h2>

            {/* Description */}
            <p className="font-sans text-base sm:text-lg text-body mb-8 leading-relaxed">
              Tsxtract is free, open source, and available immediately via PyPI for Linux,
              macOS, and Windows. No compiler or toolchain needed.
            </p>

            {/* Copyable Install Bar */}
            <div className="mx-auto mb-8 flex max-w-md items-center justify-between rounded-lg border border-borderLine bg-canvas px-4 py-3 font-mono text-sm text-ink shadow-inner">
              <div className="flex items-center gap-2">
                <span className="text-muted select-none">$</span>
                <span className="font-semibold">pip install tsxtract-rs</span>
              </div>
              <button
                type="button"
                onClick={copyCommand}
                className="flex items-center gap-1.5 rounded bg-card px-2.5 py-1 text-xs font-sans font-medium text-ink border border-borderDim shadow-btn hover:border-ink transition"
                aria-label="Copy install command"
              >
                {copied ? (
                  <span className="text-emerald-600 font-semibold">Copied!</span>
                ) : (
                  <>
                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" strokeWidth={1.5} />
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" strokeWidth={1.5} />
                    </svg>
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-4">
              <a
                href="https://github.com/Aamod007/Tsxtract"
                target="_blank"
                rel="noopener noreferrer"
                className="group relative inline-flex h-12 items-center justify-center overflow-hidden rounded-md bg-ink px-6 text-sm font-semibold text-white shadow-btn transition hover:bg-ink-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"
              >
                <span className="relative z-10 flex items-center gap-2">
                  <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24">
                    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                  </svg>
                  GitHub Repository
                </span>
                <span className="absolute bottom-0 left-0 h-[3px] w-full origin-left scale-x-0 bg-highlight transition-transform duration-300 group-hover:scale-x-100" />
              </a>

              <a
                href="https://github.com/Aamod007/Tsxtract#readme"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex h-12 items-center justify-center gap-2 rounded-md border border-borderLine bg-card px-6 text-sm font-semibold text-ink shadow-btn transition hover:border-ink hover:bg-white focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"
              >
                Read Documentation
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
