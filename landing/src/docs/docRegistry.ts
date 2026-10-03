/// <reference types="vite/client" />
import { parseFrontmatter } from './markdown';
import { DocPageData } from './types';
import { NAV_SECTIONS, getAdjacentNav, NavItem } from './nav';

// Load markdown files eager as raw strings
const rawDocs = import.meta.glob('./content/*.md', { query: '?raw', eager: true }) as Record<
  string,
  { default: string } | string
>;

let docsCache: DocPageData[] | null = null;

export function getAllDocs(): DocPageData[] {
  if (docsCache) return docsCache;

  const docs: DocPageData[] = [];

  for (const [filepath, raw] of Object.entries(rawDocs)) {
    const rawContent = typeof raw === 'string' ? raw : raw.default;
    // Extract slug from filepath: ./content/introduction.md -> introduction (support / or \)
    const slugMatch = filepath.match(/[\\/]content[\\/]([^\\/]+)\.md$/) || filepath.match(/([^\\/]+)\.md$/);
    if (!slugMatch) continue;
    const slug = slugMatch[1];

    const { frontmatter, body } = parseFrontmatter(rawContent);
    docs.push({
      slug,
      title: frontmatter.title,
      description: frontmatter.description,
      order: frontmatter.order,
      section: frontmatter.section,
      rawContent,
      body,
    });
  }

  // Sort by order ascending
  docs.sort((a, b) => a.order - b.order);
  docsCache = docs;
  return docs;
}

export function getDocBySlug(slug: string): DocPageData | undefined {
  const docs = getAllDocs();
  return docs.find((d) => d.slug === slug);
}

export interface NavSectionGroup {
  title: string;
  items: Array<NavItem & { description?: string }>;
}

export function getGroupedNav(): NavSectionGroup[] {
  return NAV_SECTIONS.map((sec) => ({
    title: sec.title,
    items: sec.items,
  }));
}

export function getAdjacentDocs(currentSlug: string): {
  prev: NavItem | null;
  next: NavItem | null;
} {
  return getAdjacentNav(currentSlug);
}
