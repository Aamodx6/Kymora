import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { DocsSearchModal } from './DocsSearchModal';

export const DocsNotFound: React.FC = () => {
  const [searchOpen, setSearchOpen] = useState(false);

  return (
    <div className="py-16 text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-borderDim text-2xl font-mono font-bold text-ink">
        404
      </div>
      <h1 className="mt-6 text-2xl font-bold tracking-tight text-ink sm:text-3xl">Page Not Found</h1>
      <p className="mt-3 text-sm text-body max-w-md mx-auto leading-relaxed">
        The documentation page you are looking for doesn't exist or may have moved. Use search or jump to one of our popular sections below.
      </p>

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <button
          type="button"
          onClick={() => setSearchOpen(true)}
          className="inline-flex items-center gap-2 rounded-md bg-ink px-4 py-2 text-xs font-semibold text-white shadow hover:bg-ink-soft transition"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          Search Documentation (⌘K)
        </button>
        <Link
          to="/docs/introduction"
          className="inline-flex items-center rounded-md border border-borderLine bg-card px-4 py-2 text-xs font-semibold text-ink hover:border-ink transition"
        >
          Go to Introduction
        </Link>
      </div>

      <div className="mt-12 border-t border-borderDim pt-8 text-left max-w-md mx-auto">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted mb-3">Popular Pages</h2>
        <ul className="space-y-2 text-xs">
          <li>
            <Link to="/docs/installation" className="text-ink font-medium hover:underline">
              → Installation (pip, wheels, source)
            </Link>
          </li>
          <li>
            <Link to="/docs/quickstart" className="text-ink font-medium hover:underline">
              → 5-minute Quickstart
            </Link>
          </li>
          <li>
            <Link to="/docs/api-reference" className="text-ink font-medium hover:underline">
              → Full API Reference
            </Link>
          </li>
          <li>
            <Link to="/docs/feature-catalog" className="text-ink font-medium hover:underline">
              → 33 Features Catalog & Explorer
            </Link>
          </li>
        </ul>
      </div>

      <DocsSearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
};
