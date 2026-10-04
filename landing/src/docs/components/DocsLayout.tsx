import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { DocsSidebar } from './DocsSidebar';
import { DocsToc } from './DocsToc';
import { DocsSearchModal } from './DocsSearchModal';
import { TocHeading } from '../types';
import { SearchProvider, useSearch } from '../SearchContext';

interface DocsLayoutInnerProps {
  children: React.ReactNode;
  headings: TocHeading[];
}

const DocsLayoutInner: React.FC<DocsLayoutInnerProps> = ({ children, headings }) => {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [mobileTocOpen, setMobileTocOpen] = useState(false);
  const location = useLocation();
  const { isOpen: searchOpen, openSearch, closeSearch } = useSearch();

  // Close mobile navigation on route change
  useEffect(() => {
    setMobileSidebarOpen(false);
    setMobileTocOpen(false);
  }, [location.pathname]);

  // Ensure dark class is removed on mount
  useEffect(() => {
    try {
      localStorage.removeItem('tsxtract_docs_theme');
    } catch {
      // ignore
    }
    document.documentElement.classList.remove('dark');
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-canvas text-ink transition-colors duration-200 overflow-x-clip">
      {/* Accessibility Skip Link */}
      <a
        href="#doc-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-ink focus:px-4 focus:py-2 focus:text-white focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-highlight"
      >
        Skip to main content
      </a>

      {/* Global Docs Header Bar (The ONE Brand Block & The ONLY Search Box) */}
      <header className="sticky top-0 z-30 w-full border-b border-borderDim bg-canvas/95 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Left: Mobile hamburger & Single Brand Block */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
              className="lg:hidden flex h-9 w-9 items-center justify-center rounded-md border border-borderLine bg-card text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-ink cursor-pointer"
              aria-label="Toggle docs navigation"
              aria-expanded={mobileSidebarOpen}
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {mobileSidebarOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>

            <Link
              to="/"
              className="flex items-center gap-2 font-sans font-bold text-lg tracking-tight text-ink hover:opacity-85 transition"
            >
              <span>kymora</span>
              <span className="text-xs font-mono font-normal text-muted">/ docs</span>
            </Link>
          </div>

          {/* Center: The ONLY visible search bar trigger */}
          <div className="flex-1 max-w-md mx-4 hidden md:block">
            <button
              type="button"
              onClick={openSearch}
              className="w-full flex items-center justify-between rounded-md border border-borderLine bg-card px-3 py-1.5 text-xs text-muted hover:border-ink hover:text-ink transition shadow-sm cursor-pointer"
              aria-label="Search documentation"
            >
              <span className="flex items-center gap-2">
                <svg className="h-3.5 w-3.5 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span>Search docs (press <kbd className="font-mono text-[10px]">Ctrl+K</kbd> / <kbd className="font-mono text-[10px]">/</kbd>)</span>
              </span>
              <kbd className="rounded border border-borderDim bg-canvas px-1 py-0.5 font-mono text-[10px]">⌘K</kbd>
            </button>
          </div>

          {/* Right: Mobile search trigger & Links */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={openSearch}
              className="md:hidden flex h-8 w-8 items-center justify-center rounded-md border border-borderLine bg-card text-ink cursor-pointer"
              aria-label="Search documentation"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </button>

            <a
              href="https://github.com/Aamodx6/Kymora"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:inline-flex h-8 items-center gap-1.5 rounded-md border border-borderLine bg-card px-2.5 text-xs font-medium text-ink hover:border-ink transition"
            >
              <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
              </svg>
              <span>GitHub</span>
            </a>
          </div>
        </div>

        {/* Mobile TOC Dropdown Toggle */}
        {headings.length >= 2 && (
          <div className="lg:hidden border-t border-borderDim bg-canvas px-4 py-2">
            <button
              type="button"
              onClick={() => setMobileTocOpen(!mobileTocOpen)}
              className="flex w-full items-center justify-between text-xs font-medium text-body hover:text-ink cursor-pointer"
              aria-expanded={mobileTocOpen}
            >
              <span className="flex items-center gap-1.5 font-mono">
                <svg className="h-3.5 w-3.5 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h10M4 18h7" />
                </svg>
                On this page
              </span>
              <svg
                className={`h-3 w-3 text-muted transition-transform ${mobileTocOpen ? 'rotate-180' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {mobileTocOpen && (
              <div className="mt-2 pt-2 border-t border-borderDim max-h-56 overflow-y-auto">
                <DocsToc headings={headings} />
              </div>
            )}
          </div>
        )}
      </header>

      {/* 3-Column Main Area: Single window scroll model */}
      <div className="mx-auto flex w-full max-w-7xl flex-1 px-4 sm:px-6 lg:px-8">
        {/* Desktop Left Sidebar: sticky at top 3.5rem */}
        <div className="hidden lg:block w-64 flex-shrink-0 border-r border-borderDim">
          <div className="sticky top-14 max-h-[calc(100vh-3.5rem)] overflow-y-auto">
            <DocsSidebar />
          </div>
        </div>

        {/* Mobile Left Sidebar Drawer */}
        {mobileSidebarOpen && (
          <div
            className="fixed inset-0 z-50 flex lg:hidden bg-black/50 backdrop-blur-sm"
            onClick={() => setMobileSidebarOpen(false)}
          >
            <div
              className="w-72 bg-canvas h-full shadow-2xl overflow-y-auto border-r border-borderLine"
              onClick={(e) => e.stopPropagation()}
            >
              <DocsSidebar onLinkClick={() => setMobileSidebarOpen(false)} />
            </div>
          </div>
        )}

        {/* Center Content Column */}
        <main
          id="doc-content"
          className="flex-1 min-w-0 py-8 lg:px-10 xl:px-12 max-w-[760px] mx-auto w-full"
        >
          {children}
        </main>

        {/* Desktop Right TOC: sticky at top 3.5rem */}
        <div className="hidden xl:block w-60 flex-shrink-0">
          <div className="sticky top-14 max-h-[calc(100vh-3.5rem)] overflow-y-auto pl-6 py-8">
            <DocsToc headings={headings} />
          </div>
        </div>
      </div>

      {/* Global Cmd/Ctrl+K Search Modal (Portaled) */}
      <DocsSearchModal isOpen={searchOpen} onClose={closeSearch} />
    </div>
  );
};

export const DocsLayout: React.FC<DocsLayoutInnerProps> = (props) => {
  return (
    <SearchProvider>
      <DocsLayoutInner {...props} />
    </SearchProvider>
  );
};
