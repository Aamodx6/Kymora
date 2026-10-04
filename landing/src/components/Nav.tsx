import React, { useState } from 'react';
import { Link } from 'react-router-dom';

export const Nav: React.FC = () => {
  const [copied, setCopied] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const copyCommand = async () => {
    try {
      await navigator.clipboard.writeText('pip install kymora');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-borderDim bg-canvas/90 backdrop-blur-md transition-colors">
      <div className="mx-auto flex h-[60px] max-w-container items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Left: Brand Wordmark */}
        <div className="flex items-center gap-3">
          <a
            href="#"
            className="group flex items-center gap-2.5 text-ink transition-opacity hover:opacity-85 focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"
            aria-label="kymora home"
          >
            {/* Minimal geometric mark matching reference aesthetic */}
            <div className="flex h-5 w-5 flex-col justify-between py-0.5" aria-hidden="true">
              <span className="h-[2px] w-2 bg-ink transition-transform group-hover:scale-x-110" />
              <span className="h-[2px] w-3.5 bg-ink transition-transform group-hover:scale-x-110" />
              <span className="h-[2px] w-5 bg-ink transition-transform group-hover:scale-x-110" />
              <span className="h-[2px] w-3 bg-ink transition-transform group-hover:scale-x-110" />
            </div>
            <span className="font-sans text-xl font-bold tracking-tight text-ink">
              kymora
            </span>
          </a>
        </div>

        {/* Center: Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-7 text-[14.5px] font-medium text-body" aria-label="Main Navigation">
          <a
            href="#features"
            className="transition-colors hover:text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"
          >
            Features
          </a>
          <a
            href="#benchmarks"
            className="transition-colors hover:text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"
          >
            Benchmarks
          </a>
          <a
            href="#how-it-works"
            className="transition-colors hover:text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"
          >
            How it works
          </a>
          <Link
            to="/docs/introduction"
            className="transition-colors hover:text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"
          >
            Docs
          </Link>
          <a
            href="https://github.com/Aamodx6/Kymora"
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors hover:text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"
          >
            GitHub
          </a>
        </nav>

        {/* Right: Quick Install CTA & GitHub */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={copyCommand}
            className="group relative inline-flex h-9 items-center gap-2 rounded-md border border-borderLine bg-card px-3 text-xs font-mono text-ink shadow-btn transition hover:border-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"
            aria-label="Copy install command"
          >
            <span className="text-muted select-none">$</span>
            <span className="font-semibold">pip install kymora</span>
            <span className="ml-1 text-muted group-hover:text-ink" aria-hidden="true">
              {copied ? (
                <svg className="h-3.5 w-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
              )}
            </span>
            {copied && (
              <span className="absolute -bottom-8 right-0 rounded bg-ink px-2 py-0.5 font-sans text-[11px] text-white shadow-md animate-fade-in">
                Copied!
              </span>
            )}
          </button>

          <a
            href="https://github.com/Aamodx6/Kymora"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex h-9 items-center justify-center rounded-md bg-ink px-3.5 text-[13.5px] font-semibold text-white shadow-btn transition hover:bg-ink-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"
          >
            Star on GitHub
          </a>

          {/* Mobile Menu Hamburger */}
          <button
            type="button"
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden flex h-9 w-9 items-center justify-center rounded-md border border-borderLine bg-card text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"
            aria-expanded={mobileOpen}
            aria-label="Toggle navigation menu"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              {mobileOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="border-b border-borderDim bg-canvas px-4 py-4 md:hidden animate-in fade-in slide-in-from-top-2">
          <nav className="flex flex-col gap-3 font-sans text-sm font-medium text-body">
            <a
              href="#features"
              onClick={() => setMobileOpen(false)}
              className="py-1 hover:text-ink"
            >
              Features
            </a>
            <a
              href="#benchmarks"
              onClick={() => setMobileOpen(false)}
              className="py-1 hover:text-ink"
            >
              Benchmarks
            </a>
            <a
              href="#how-it-works"
              onClick={() => setMobileOpen(false)}
              className="py-1 hover:text-ink"
            >
              How it works
            </a>
            <Link
              to="/docs/introduction"
              onClick={() => setMobileOpen(false)}
              className="py-1 hover:text-ink"
            >
              Documentation
            </Link>
            <a
              href="https://github.com/Aamodx6/Kymora"
              target="_blank"
              rel="noopener noreferrer"
              className="py-1 hover:text-ink"
            >
              GitHub Repository
            </a>
          </nav>
        </div>
      )}
    </header>
  );
};
