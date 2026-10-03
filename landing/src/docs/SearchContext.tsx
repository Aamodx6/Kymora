import React, { createContext, useContext, useState, useEffect, useRef } from 'react';

interface SearchContextType {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  openSearch: () => void;
  closeSearch: () => void;
}

const SearchContext = createContext<SearchContextType | undefined>(undefined);

export const SearchProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const triggerRef = useRef<HTMLElement | null>(null);

  const openSearch = () => {
    triggerRef.current = document.activeElement as HTMLElement | null;
    setIsOpen(true);
  };

  const closeSearch = () => {
    setIsOpen(false);
    // Restore focus to previously active element
    if (triggerRef.current && typeof triggerRef.current.focus === 'function') {
      setTimeout(() => {
        triggerRef.current?.focus();
      }, 10);
    }
  };

  // Global keydown listeners:
  // - Ctrl/Cmd+K toggles search
  // - "/" opens search if user is not in an input/textarea/editable
  // - Esc closes search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl+K toggle
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) {
          closeSearch();
        } else {
          openSearch();
        }
        return;
      }

      // Esc closes
      if (e.key === 'Escape' && isOpen) {
        e.preventDefault();
        closeSearch();
        return;
      }

      // "/" opens search when not in an editable field
      if (e.key === '/' && !isOpen && !e.metaKey && !e.ctrlKey && !e.altKey) {
        const target = e.target as HTMLElement | null;
        const isInput =
          target instanceof HTMLInputElement ||
          target instanceof HTMLTextAreaElement ||
          target instanceof HTMLSelectElement ||
          Boolean(target?.isContentEditable);

        if (!isInput) {
          e.preventDefault();
          openSearch();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  return (
    <SearchContext.Provider value={{ isOpen, setIsOpen, openSearch, closeSearch }}>
      {children}
    </SearchContext.Provider>
  );
};

export const useSearch = (): SearchContextType => {
  const context = useContext(SearchContext);
  if (!context) {
    throw new Error('useSearch must be used within a SearchProvider');
  }
  return context;
};
