import React, { useEffect, useState, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { TocHeading } from '../types';

interface DocsTocProps {
  headings: TocHeading[];
}

export const DocsToc: React.FC<DocsTocProps> = ({ headings }) => {
  const [activeId, setActiveId] = useState<string>('');
  const location = useLocation();
  const isClickScrollingRef = useRef(false);

  // If fewer than 2 headings, hide the TOC per specification
  const hasEnoughHeadings = headings.length >= 2;

  // Scrollspy with IntersectionObserver + bottom-of-page detector
  useEffect(() => {
    if (!hasEnoughHeadings) return;

    // Check if URL has a hash initially
    const initialHash = window.location.hash.replace(/^#/, '');
    if (initialHash && headings.some((h) => h.id === initialHash)) {
      setActiveId(initialHash);
    } else if (headings.length > 0) {
      setActiveId(headings[0].id);
    }

    // IntersectionObserver with rootMargin "-80px 0px -70% 0px"
    const observer = new IntersectionObserver(
      (entries) => {
        if (isClickScrollingRef.current) return;

        // Check if user is scrolled to bottom of the page
        const isBottom =
          window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 30;
        if (isBottom && headings.length > 0) {
          setActiveId(headings[headings.length - 1].id);
          return;
        }

        // Find intersecting entries
        const visibleEntries = entries.filter((e) => e.isIntersecting);
        if (visibleEntries.length > 0) {
          // Sort by top offset
          visibleEntries.sort(
            (a, b) => a.boundingClientRect.top - b.boundingClientRect.top
          );
          setActiveId(visibleEntries[0].target.id);
        }
      },
      {
        root: null, // window/viewport
        rootMargin: '-80px 0px -70% 0px',
        threshold: [0, 1.0],
      }
    );

    // Observe each heading element
    const observedElements: HTMLElement[] = [];
    headings.forEach((h) => {
      const el = document.getElementById(h.id);
      if (el) {
        observer.observe(el);
        observedElements.push(el);
      }
    });

    // Also listen to window scroll to detect bottom of page immediately
    const handleScroll = () => {
      if (isClickScrollingRef.current) return;
      const isBottom =
        window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 30;
      if (isBottom && headings.length > 0) {
        setActiveId(headings[headings.length - 1].id);
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      observer.disconnect();
      window.removeEventListener('scroll', handleScroll);
    };
  }, [headings, location.pathname, hasEnoughHeadings]);

  if (!hasEnoughHeadings) {
    return null;
  }

  const handleHeadingClick = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault();
    const el = document.getElementById(id);
    if (!el) return;

    setActiveId(id);
    isClickScrollingRef.current = true;

    // Update URL hash without re-rendering or full navigation
    window.history.pushState(null, '', `#${id}`);

    // Smooth scroll into view
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });

    setTimeout(() => {
      isClickScrollingRef.current = false;
    }, 700);
  };

  return (
    <nav className="space-y-3" aria-label="Table of contents">
      <p className="text-xs font-semibold uppercase tracking-wider text-muted font-mono">
        On this page
      </p>
      <ul className="space-y-2 border-l border-borderLine pl-3 text-xs">
        {headings.map((h) => {
          const isActive = activeId === h.id;
          return (
            <li
              key={h.id}
              className={`${h.level === 3 ? 'ml-3' : ''}`}
            >
              <a
                href={`#${h.id}`}
                onClick={(e) => handleHeadingClick(e, h.id)}
                className={`block transition-all py-0.5 leading-snug ${
                  isActive
                    ? 'font-semibold text-ink border-l-2 -ml-[13px] pl-[11px] border-highlight'
                    : 'text-body hover:text-ink'
                }`}
              >
                {h.text}
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};
