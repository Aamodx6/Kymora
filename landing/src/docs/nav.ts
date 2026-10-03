export interface NavItem {
  slug: string;
  title: string;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export const NAV_SECTIONS: NavSection[] = [
  {
    title: 'Start here',
    items: [
      { slug: 'introduction', title: 'Introduction' },
      { slug: 'installation', title: 'Installation' },
      { slug: 'quickstart', title: 'Quickstart' },
    ],
  },
  {
    title: 'Concepts',
    items: [
      { slug: 'core-concepts', title: 'Core Concepts' },
      { slug: 'performance', title: 'Performance & Architecture' },
      { slug: 'benchmarks', title: 'Benchmarks & Competitors' },
    ],
  },
  {
    title: 'Guides',
    items: [
      { slug: 'pandas-and-polars', title: 'Pandas and Polars Integration' },
      { slug: 'sklearn-pipelines', title: 'Scikit-Learn Pipelines & Transformers' },
      { slug: 'large-datasets', title: 'Large Datasets & Streaming' },
      { slug: 'selecting-features', title: 'Selecting Feature Subsets' },
    ],
  },
  {
    title: 'Reference',
    items: [
      { slug: 'api-reference', title: 'API Reference' },
      { slug: 'feature-catalog', title: 'Feature Catalog' },
      { slug: 'configuration', title: 'Configuration & Environment Variables' },
    ],
  },
  {
    title: 'Help',
    items: [
      { slug: 'faq', title: 'FAQ & Troubleshooting' },
      { slug: 'contributing', title: 'Contributing Guide' },
      { slug: 'changelog', title: 'Changelog' },
    ],
  },
];

// Flat list of all items with their parent section title
export interface FlatNavItem extends NavItem {
  section: string;
}

export function getAllNavItems(): FlatNavItem[] {
  const list: FlatNavItem[] = [];
  for (const section of NAV_SECTIONS) {
    for (const item of section.items) {
      list.push({
        ...item,
        section: section.title,
      });
    }
  }
  return list;
}

// Find section title for a given slug
export function getSectionForSlug(slug: string): string | undefined {
  for (const section of NAV_SECTIONS) {
    if (section.items.some((item) => item.slug === slug)) {
      return section.title;
    }
  }
  return undefined;
}

// Adjacent docs navigation (previous and next)
export function getAdjacentNav(slug: string): {
  prev: NavItem | null;
  next: NavItem | null;
} {
  const items = getAllNavItems();
  const index = items.findIndex((item) => item.slug === slug);
  if (index === -1) {
    return { prev: null, next: null };
  }
  return {
    prev: index > 0 ? items[index - 1] : null,
    next: index < items.length - 1 ? items[index + 1] : null,
  };
}
