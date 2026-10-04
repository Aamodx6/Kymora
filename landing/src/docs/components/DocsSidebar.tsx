import React, { useState, useEffect } from 'react';
import { NavLink, useLocation, Link } from 'react-router-dom';
import { NAV_SECTIONS, getSectionForSlug } from '../nav';

interface DocsSidebarProps {
  onLinkClick?: () => void;
}

const STORAGE_KEY = 'tsxtract_docs_sidebar_collapsed';

export const DocsSidebar: React.FC<DocsSidebarProps> = ({ onLinkClick }) => {
  const location = useLocation();
  const currentSlug = location.pathname.replace(/^\/docs\/?/, '').split('#')[0] || 'introduction';

  // Read saved collapsed state from sessionStorage (try/catch)
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>(() => {
    let saved: Record<string, boolean> = {};
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      if (stored) {
        saved = JSON.parse(stored);
      }
    } catch {
      // ignore sessionStorage access errors
    }

    // The section containing the active page is always open on load
    const activeSection = getSectionForSlug(currentSlug);
    if (activeSection) {
      saved[activeSection] = false;
    }
    return saved;
  });

  // Ensure active section is open whenever slug changes
  useEffect(() => {
    const activeSection = getSectionForSlug(currentSlug);
    if (activeSection && collapsed[activeSection]) {
      setCollapsed((prev) => {
        const next = { ...prev, [activeSection]: false };
        try {
          sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        } catch {
          // ignore
        }
        return next;
      });
    }
  }, [currentSlug]);

  const toggleSection = (sectionTitle: string) => {
    setCollapsed((prev) => {
      const next = {
        ...prev,
        [sectionTitle]: !prev[sectionTitle],
      };
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        // ignore
      }
      return next;
    });
  };

  const handleItemClick = () => {
    window.scrollTo({ top: 0, behavior: 'instant' });
    if (onLinkClick) {
      onLinkClick();
    }
  };

  return (
    <aside
      className="flex h-full flex-col justify-between px-4 py-6 text-sm"
      aria-label="Documentation navigation"
    >
      <div className="space-y-6">
        {/* Nav Sections from nav.ts */}
        <nav className="space-y-4" aria-label="Documentation sections">
          {NAV_SECTIONS.map((section) => {
            const isSectionCollapsed = Boolean(collapsed[section.title]);
            const isOpen = !isSectionCollapsed;

            return (
              <div key={section.title} className="space-y-1.5">
                {/* Section Header Button with aria-expanded and chevron transition */}
                <button
                  type="button"
                  onClick={() => toggleSection(section.title)}
                  className="flex w-full items-center justify-between py-1 text-xs font-semibold uppercase tracking-wider text-muted hover:text-ink transition cursor-pointer"
                  aria-expanded={isOpen}
                  aria-controls={`section-${section.title.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  <span className="font-mono text-[11px]">{section.title}</span>
                  <svg
                    className={`h-3.5 w-3.5 text-muted transition-transform duration-200 ${
                      isOpen ? 'rotate-0' : '-rotate-90'
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Collapsible section with short height transition */}
                <div
                  id={`section-${section.title.toLowerCase().replace(/\s+/g, '-')}`}
                  className={`grid transition-[grid-template-rows,opacity] duration-200 ease-in-out ${
                    isOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0 pointer-events-none'
                  }`}
                >
                  <div className="overflow-hidden">
                    <ul className="space-y-1 pl-1 border-l border-borderDim pt-1">
                      {section.items.map((item) => {
                        const targetPath = `/docs/${item.slug}`;

                        return (
                          <li key={item.slug}>
                            <NavLink
                              to={targetPath}
                              onClick={handleItemClick}
                              className={({ isActive }) =>
                                `block rounded-md px-2.5 py-1.5 text-xs font-medium transition ${
                                  isActive
                                    ? 'bg-ink text-canvas dark:bg-[#202521] dark:text-[#f2f3ef] dark:border dark:border-[#303631] font-semibold shadow-sm'
                                    : 'text-body hover:bg-canvas hover:text-ink'
                                }`
                              }
                            >
                              {item.title}
                            </NavLink>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                </div>
              </div>
            );
          })}
        </nav>
      </div>

      {/* Sidebar Footer Navigation */}
      <div className="pt-6 border-t border-borderDim flex flex-col gap-2 text-xs text-muted">
        <Link to="/" className="hover:text-ink transition flex items-center gap-1.5 font-medium">
          <span>← Back to Landing Site</span>
        </Link>
        <a
          href="https://github.com/Aamodx6/Kymora"
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-ink transition flex items-center gap-1.5"
        >
          <span>GitHub Repository ↗</span>
        </a>
      </div>
    </aside>
  );
};
