import React, { useEffect, useRef, useState } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import mermaid from 'mermaid';
import { getDocBySlug, getAdjacentDocs } from '../docRegistry';
import { renderDocMarkdown } from '../markdown';
import { DocsLayout } from './DocsLayout';
import { DocsNotFound } from './DocsNotFound';
import { FeatureCatalogTable } from './FeatureCatalogTable';
import { GITHUB_DOCS_BASE } from '../constants';

mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'loose',
  fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
});

export const DocsPage: React.FC = () => {
  const { slug = 'introduction' } = useParams<{ slug: string }>();
  const location = useLocation();
  const doc = getDocBySlug(slug);

  const [helpfulState, setHelpfulState] = useState<'idle' | 'yes' | 'no'>('idle');
  const contentRef = useRef<HTMLDivElement | null>(null);

  // Scroll to hash on direct load, or reset to top when slug changes without a hash
  useEffect(() => {
    setHelpfulState('idle');
    const hash = location.hash.replace(/^#/, '');

    if (hash) {
      const timer = setTimeout(() => {
        const el = document.getElementById(hash);
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 80);
      return () => clearTimeout(timer);
    } else {
      window.scrollTo(0, 0);
    }
  }, [slug, location.hash]);

  // SEO: Update page title and meta description
  useEffect(() => {
    if (doc) {
      document.title = `${doc.title} · Tsxtract Documentation`;
      const metaDesc = document.querySelector('meta[name="description"]');
      if (metaDesc) {
        metaDesc.setAttribute(
          'content',
          doc.description || `${doc.title} - Tsxtract time-series feature extraction documentation.`
        );
      }
    } else {
      document.title = 'Page Not Found · Tsxtract Documentation';
    }
  }, [doc]);

  // Interactive event delegation for copy buttons and code tabs
  useEffect(() => {
    const el = contentRef.current;
    if (!el) return;

    // Handle code copying
    const handleCopyClick = (e: MouseEvent) => {
      const target = (e.target as HTMLElement).closest('.copy-code-btn') as HTMLElement | null;
      if (!target) return;

      const encodedCode = target.getAttribute('data-code');
      if (!encodedCode) return;

      const code = decodeURIComponent(encodedCode);
      navigator.clipboard.writeText(code).then(() => {
        const label = target.querySelector('.copy-label');
        if (label) label.textContent = 'Copied!';
        target.classList.add('text-emerald-400');

        setTimeout(() => {
          if (label) label.textContent = 'Copy';
          target.classList.remove('text-emerald-400');
        }, 2000);
      });
    };

    // Handle tab switching
    const handleTabClick = (e: MouseEvent) => {
      const target = (e.target as HTMLElement).closest('.docs-tab-btn') as HTMLElement | null;
      if (!target) return;

      const groupId = target.getAttribute('data-group');
      const tabIdx = target.getAttribute('data-tab-idx');
      if (!groupId || tabIdx === null) return;

      const container = document.getElementById(groupId);
      if (!container) return;

      // Update button states
      const buttons = container.querySelectorAll('.docs-tab-btn');
      buttons.forEach((btn) => btn.classList.remove('is-active'));
      target.classList.add('is-active');

      // Update pane states
      const panes = container.querySelectorAll('.docs-tab-pane');
      panes.forEach((pane) => {
        if (pane.getAttribute('data-tab-idx') === tabIdx) {
          pane.classList.remove('hidden');
          pane.classList.add('is-active');
        } else {
          pane.classList.add('hidden');
          pane.classList.remove('is-active');
        }
      });
    };

    el.addEventListener('click', handleCopyClick);
    el.addEventListener('click', handleTabClick);

    return () => {
      el.removeEventListener('click', handleCopyClick);
      el.removeEventListener('click', handleTabClick);
    };
  }, [doc, slug]);

  // Render Mermaid diagrams when doc content updates
  useEffect(() => {
    const el = contentRef.current;
    if (!el) return;
    const mermaidNodes = el.querySelectorAll<HTMLElement>('.mermaid');
    if (mermaidNodes.length > 0) {
      mermaid.run({ nodes: Array.from(mermaidNodes) }).catch((err) => {
        console.warn('Mermaid rendering error:', err);
      });
    }
  }, [doc?.body, slug]);

  if (!doc) {
    return (
      <DocsLayout headings={[]}>
        <DocsNotFound />
      </DocsLayout>
    );
  }

  const { html, headings } = renderDocMarkdown(doc.body);
  const { prev, next } = getAdjacentDocs(doc.slug);

  return (
    <DocsLayout headings={headings}>
      <article className="prose-docs max-w-none text-body">
        {/* Breadcrumb */}
        <div className="flex items-center gap-1.5 text-xs text-muted mb-4 font-mono">
          <Link to="/docs/introduction" className="hover:text-ink transition">
            docs
          </Link>
          <span>/</span>
          <span className="text-body font-medium">{doc.section.toLowerCase()}</span>
          <span>/</span>
          <span className="text-ink font-semibold">{doc.slug}</span>
        </div>

        {/* Page Title & Description */}
        <header className="mb-8 border-b border-borderDim pb-6">
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-ink mb-3">
            {doc.title}
          </h1>
          {doc.description && (
            <p className="text-base sm:text-lg text-body leading-relaxed mt-2">
              {doc.description}
            </p>
          )}
        </header>

        {/* Rendered Markdown Content with prose-docs styling */}
        <div
          ref={contentRef}
          className="docs-markdown-body prose-docs"
          dangerouslySetInnerHTML={{ __html: html }}
        />

        {/* Dynamic Feature Catalog Interactive Table if on feature-catalog page */}
        {doc.slug === 'feature-catalog' && <FeatureCatalogTable />}

        {/* Page Footer Utilities: Feedback & Edit on GitHub */}
        <div className="mt-12 pt-6 border-t border-borderDim flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
          {/* Was this helpful? */}
          <div className="flex items-center gap-3">
            <span className="font-medium text-body">Was this page helpful?</span>
            {helpfulState === 'idle' ? (
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setHelpfulState('yes')}
                  className="rounded border border-borderLine bg-card px-2.5 py-1 text-ink hover:border-ink transition font-medium cursor-pointer"
                >
                  👍 Yes
                </button>
                <button
                  type="button"
                  onClick={() => setHelpfulState('no')}
                  className="rounded border border-borderLine bg-card px-2.5 py-1 text-ink hover:border-ink transition font-medium cursor-pointer"
                >
                  👎 No
                </button>
              </div>
            ) : (
              <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                Thank you for your feedback!
              </span>
            )}
          </div>

          {/* Edit on GitHub Link */}
          <a
            href={`${GITHUB_DOCS_BASE}/${doc.slug}.md`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-muted hover:text-ink transition"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
            <span>Edit this page on GitHub</span>
          </a>
        </div>

        {/* Prev / Next Pagination Links */}
        <nav
          className="mt-8 pt-6 border-t border-borderDim grid grid-cols-1 sm:grid-cols-2 gap-4"
          aria-label="Pagination Navigation"
        >
          {prev ? (
            <Link
              to={`/docs/${prev.slug}`}
              className="group flex flex-col rounded-lg border border-borderLine bg-card p-4 transition hover:border-ink"
            >
              <span className="text-[11px] font-mono uppercase tracking-wider text-muted group-hover:text-ink">
                ← Previous
              </span>
              <span className="mt-1 text-sm font-semibold text-ink">
                {prev.title}
              </span>
            </Link>
          ) : <div />}

          {next ? (
            <Link
              to={`/docs/${next.slug}`}
              className="group flex flex-col rounded-lg border border-borderLine bg-card p-4 text-right transition hover:border-ink sm:col-start-2"
            >
              <span className="text-[11px] font-mono uppercase tracking-wider text-muted group-hover:text-ink">
                Next →
              </span>
              <span className="mt-1 text-sm font-semibold text-ink">
                {next.title}
              </span>
            </Link>
          ) : null}
        </nav>
      </article>
    </DocsLayout>
  );
};
