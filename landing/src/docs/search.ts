import { DocPageData, SearchResult, TocHeading } from './types';
import { createSlugger } from './markdown';

export interface IndexedDoc {
  slug: string;
  title: string;
  section: string;
  description: string;
  headings: TocHeading[];
  plainBody: string;
}

// Strip markdown formatting to obtain plain text for search indexing
function cleanMarkdownText(md: string): string {
  return md
    .replace(/^---[\s\S]*?---/, '') // remove frontmatter
    .replace(/```[\s\S]*?```/g, '') // remove code blocks
    .replace(/`([^`]+)`/g, '$1') // inline code
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // links
    .replace(/[*_~#>-]/g, ' ') // symbols
    .replace(/\$([^$]+)\$/g, '$1') // math expressions
    .replace(/\s+/g, ' ')
    .trim();
}

// Extract headings with exact stable slugs
function extractDocumentHeadings(md: string): TocHeading[] {
  const headings: TocHeading[] = [];
  const slugger = createSlugger();
  const headingRegex = /^(#{2,3})\s+(.+)$/gm;
  let match: RegExpExecArray | null;

  while ((match = headingRegex.exec(md)) !== null) {
    const level = match[1].length;
    const rawText = match[2].replace(/<[^>]*>/g, '').trim();
    const id = slugger(rawText);
    headings.push({ id, text: rawText, level });
  }

  return headings;
}

let searchIndexCache: IndexedDoc[] | null = null;

export function getSearchIndex(docs: DocPageData[]): IndexedDoc[] {
  if (searchIndexCache && searchIndexCache.length === docs.length) {
    return searchIndexCache;
  }

  searchIndexCache = docs.map((doc) => ({
    slug: doc.slug,
    title: doc.title,
    section: doc.section,
    description: doc.description,
    headings: extractDocumentHeadings(doc.body),
    plainBody: cleanMarkdownText(doc.body),
  }));

  return searchIndexCache;
}

// Simple subsequence matching helper
function isSubsequence(pattern: string, text: string): boolean {
  let pIdx = 0;
  let tIdx = 0;
  while (pIdx < pattern.length && tIdx < text.length) {
    if (pattern[pIdx] === text[tIdx]) {
      pIdx++;
    }
    tIdx++;
  }
  return pIdx === pattern.length;
}

// Highlight matched query tokens in snippet
export function highlightMatch(text: string, query: string): string {
  if (!query.trim() || !text) return text;
  const tokens = query.trim().split(/\s+/).filter(Boolean);
  if (tokens.length === 0) return text;

  // Escape regex special chars in tokens
  const escaped = tokens
    .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .join('|');

  const regex = new RegExp(`(${escaped})`, 'gi');
  return text.replace(regex, '<mark class="bg-highlight/40 text-ink font-semibold rounded px-0.5">$1</mark>');
}

export function searchDocs(docs: DocPageData[], rawQuery: string): SearchResult[] {
  const query = rawQuery.trim().toLowerCase();
  if (!query) return [];

  const index = getSearchIndex(docs);
  const tokens = query.split(/\s+/).filter(Boolean);
  const results: SearchResult[] = [];

  for (const doc of index) {
    const titleLower = doc.title.toLowerCase();
    const descLower = doc.description.toLowerCase();
    const bodyLower = doc.plainBody.toLowerCase();

    let score = 0;
    let headingMatch: string | undefined;
    let headingId: string | undefined;
    let matchSnippet: string | undefined;

    // 1. Title match (highest weight)
    if (titleLower === query) {
      score += 250;
    } else if (titleLower.startsWith(query)) {
      score += 180;
    } else if (titleLower.includes(query)) {
      score += 120;
    } else if (isSubsequence(query, titleLower)) {
      score += 70;
    } else {
      let matchedTokens = 0;
      for (const t of tokens) {
        if (titleLower.includes(t)) matchedTokens++;
      }
      if (matchedTokens > 0) {
        score += matchedTokens * 40;
      }
    }

    // 2. Headings match (second weight)
    for (const h of doc.headings) {
      const hLower = h.text.toLowerCase();
      if (hLower === query) {
        score += 140;
        headingMatch = h.text;
        headingId = h.id;
        break;
      } else if (hLower.startsWith(query)) {
        score += 100;
        if (!headingMatch) {
          headingMatch = h.text;
          headingId = h.id;
        }
      } else if (hLower.includes(query)) {
        score += 75;
        if (!headingMatch) {
          headingMatch = h.text;
          headingId = h.id;
        }
      } else if (isSubsequence(query, hLower)) {
        score += 45;
        if (!headingMatch) {
          headingMatch = h.text;
          headingId = h.id;
        }
      }
    }

    // 3. Description match
    if (descLower.includes(query)) {
      score += 50;
      if (!matchSnippet) matchSnippet = doc.description;
    }

    // 4. Plain body match (lowest weight)
    const exactBodyIdx = bodyLower.indexOf(query);
    if (exactBodyIdx !== -1) {
      score += 30;
      const start = Math.max(0, exactBodyIdx - 40);
      const end = Math.min(doc.plainBody.length, exactBodyIdx + query.length + 60);
      let snippet = doc.plainBody.slice(start, end).trim();
      if (start > 0) snippet = '…' + snippet;
      if (end < doc.plainBody.length) snippet = snippet + '…';
      matchSnippet = snippet;
    } else {
      // Token matches in body
      for (const t of tokens) {
        const tIdx = bodyLower.indexOf(t);
        if (tIdx !== -1) {
          score += 10;
          if (!matchSnippet) {
            const start = Math.max(0, tIdx - 40);
            const end = Math.min(doc.plainBody.length, tIdx + t.length + 60);
            let snippet = doc.plainBody.slice(start, end).trim();
            if (start > 0) snippet = '…' + snippet;
            if (end < doc.plainBody.length) snippet = snippet + '…';
            matchSnippet = snippet;
          }
        }
      }
    }

    if (score > 0) {
      results.push({
        slug: doc.slug,
        title: doc.title,
        section: doc.section,
        description: doc.description,
        headingMatch,
        headingId,
        matchSnippet: matchSnippet || doc.description,
        score,
      });
    }
  }

  // Sort descending by score
  results.sort((a, b) => b.score - a.score);
  return results.slice(0, 10);
}
