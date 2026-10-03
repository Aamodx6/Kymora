import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { getAllDocs } from '../docRegistry';
import { searchDocs, highlightMatch } from '../search';
import { SearchResult } from '../types';

interface DocsSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DocsSearchModal: React.FC<DocsSearchModalProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const modalBoxRef = useRef<HTMLDivElement | null>(null);
  const navigate = useNavigate();

  // 80ms Debounce on query
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(query);
    }, 80);
    return () => clearTimeout(handler);
  }, [query]);

  // Reset state on open and focus input
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setDebouncedQuery('');
      setSelectedIndex(0);
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 30);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  // Reset selected index when query results change
  useEffect(() => {
    setSelectedIndex(0);
  }, [debouncedQuery]);

  // Focus trap inside modal
  useEffect(() => {
    if (!isOpen) return;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      const modal = modalBoxRef.current;
      if (!modal) return;

      const focusableElements = modal.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    window.addEventListener('keydown', handleTabKey);
    return () => window.removeEventListener('keydown', handleTabKey);
  }, [isOpen]);

  const allDocs = getAllDocs();
  const results: SearchResult[] = debouncedQuery.trim() ? searchDocs(allDocs, debouncedQuery) : [];

  const handleSelectResult = (result: SearchResult) => {
    const targetUrl = result.headingId
      ? `/docs/${result.slug}#${result.headingId}`
      : `/docs/${result.slug}`;
    navigate(targetUrl);
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (results.length > 0 ? (prev + 1) % results.length : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (results.length > 0 ? (prev - 1 + results.length) % results.length : 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (results[selectedIndex]) {
        handleSelectResult(results[selectedIndex]);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  };

  if (!isOpen) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center pt-16 sm:pt-24 px-4 bg-black/60 backdrop-blur-sm transition-opacity"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Search documentation"
    >
      <div
        ref={modalBoxRef}
        className="w-full max-w-xl rounded-xl border border-borderLine bg-card shadow-2xl overflow-hidden flex flex-col max-h-[80vh] text-ink"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 border-b border-borderDim px-4 py-3 bg-canvas/30">
          <svg className="h-5 w-5 text-muted flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search documentation, guides, and API..."
            aria-label="Search query"
            className="flex-1 bg-transparent text-sm text-ink placeholder:text-muted focus:outline-none"
          />
          <button
            type="button"
            onClick={onClose}
            className="rounded border border-borderDim bg-canvas px-1.5 py-0.5 text-[11px] font-mono text-muted hover:text-ink transition"
            aria-label="Close search"
          >
            ESC
          </button>
        </div>

        {/* Results List */}
        <div className="flex-1 overflow-y-auto p-2">
          {query.trim() === '' ? (
            <div className="py-12 px-4 text-center">
              <p className="text-xs text-muted mb-3">
                Type to search 15 documentation guides, concepts, and reference pages.
              </p>
              <div className="flex items-center justify-center gap-2 text-xs">
                <span className="text-muted">Popular:</span>
                <button
                  type="button"
                  onClick={() => setQuery('quickstart')}
                  className="rounded bg-canvas border border-borderDim px-2 py-0.5 font-medium hover:border-ink transition text-ink"
                >
                  Quickstart
                </button>
                <button
                  type="button"
                  onClick={() => setQuery('api reference')}
                  className="rounded bg-canvas border border-borderDim px-2 py-0.5 font-medium hover:border-ink transition text-ink"
                >
                  API Reference
                </button>
                <button
                  type="button"
                  onClick={() => setQuery('rayon')}
                  className="rounded bg-canvas border border-borderDim px-2 py-0.5 font-medium hover:border-ink transition text-ink"
                >
                  Rayon
                </button>
              </div>
            </div>
          ) : results.length === 0 ? (
            <div className="py-12 px-4 text-center">
              <p className="text-sm text-muted mb-3">
                No results for <span className="font-semibold text-ink">"{query}"</span>
              </p>
              <div className="flex items-center justify-center gap-2 text-xs">
                <span className="text-muted">Try:</span>
                <button
                  type="button"
                  onClick={() => setQuery('quickstart')}
                  className="rounded bg-canvas border border-borderDim px-2 py-0.5 font-medium text-ink hover:border-ink transition"
                >
                  Quickstart
                </button>
                <button
                  type="button"
                  onClick={() => setQuery('api reference')}
                  className="rounded bg-canvas border border-borderDim px-2 py-0.5 font-medium text-ink hover:border-ink transition"
                >
                  API Reference
                </button>
              </div>
            </div>
          ) : (
            <ul className="space-y-1" role="listbox">
              {results.map((res, idx) => {
                const isSelected = idx === selectedIndex;
                const snippetHtml = res.matchSnippet
                  ? highlightMatch(res.matchSnippet, debouncedQuery)
                  : '';

                return (
                  <li key={`${res.slug}-${res.headingId || idx}`} role="option" aria-selected={isSelected}>
                    <button
                      type="button"
                      onClick={() => handleSelectResult(res)}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      className={`w-full text-left rounded-lg p-3 transition flex flex-col gap-1 ${
                        isSelected
                          ? 'bg-ink text-canvas dark:bg-[#202521] dark:text-[#f2f3ef] dark:border dark:border-[#303631]'
                          : 'hover:bg-canvas text-ink'
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className={`font-semibold text-[13px] ${isSelected ? 'text-canvas dark:text-[#f2f3ef]' : 'text-ink'}`}>
                          {res.title}
                        </span>
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-mono uppercase tracking-wider ${
                            isSelected ? 'bg-white/20 text-canvas dark:text-[#f2f3ef]' : 'bg-borderDim text-muted'
                          }`}
                        >
                          {res.section}
                        </span>
                      </div>

                      {res.headingMatch && (
                        <div
                          className={`text-xs flex items-center gap-1 font-medium ${
                            isSelected ? 'text-highlight' : 'text-blue-600 dark:text-blue-400'
                          }`}
                        >
                          <span>#</span>
                          <span>{res.headingMatch}</span>
                        </div>
                      )}

                      {snippetHtml && (
                        <p
                          className={`text-xs line-clamp-2 leading-relaxed ${
                            isSelected ? 'text-white/80' : 'text-muted'
                          }`}
                          dangerouslySetInnerHTML={{ __html: snippetHtml }}
                        />
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between border-t border-borderDim bg-canvas/50 px-4 py-2 text-[11px] text-muted">
          <div className="flex items-center gap-2">
            <span>Navigate <kbd className="font-mono font-semibold">↑</kbd> <kbd className="font-mono font-semibold">↓</kbd></span>
            <span>•</span>
            <span>Select <kbd className="font-mono font-semibold">↵</kbd></span>
          </div>
          <span>Client-side fuzzy index</span>
        </div>
      </div>
    </div>,
    document.body
  );
};
