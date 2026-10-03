export interface DocFrontmatter {
  title: string;
  description: string;
  order: number;
  section: 'Start here' | 'Concepts' | 'Guides' | 'Reference' | 'Help';
}

export interface DocPageData extends DocFrontmatter {
  slug: string;
  rawContent: string;
  body: string;
}

export interface TocHeading {
  id: string;
  text: string;
  level: number;
}

export interface FeatureDefinition {
  index: number;
  name: string;
  group: 'Stats' | 'Change' | 'Counts' | 'Correlation' | 'Entropy' | 'Spectral';
  definition: string;
  complexity: 'O(1)' | 'O(n)' | 'O(n log n)';
  undefinedWhen: string;
  notes: string;
}

export interface SearchResult {
  slug: string;
  title: string;
  section: string;
  description: string;
  matchSnippet?: string;
  headingMatch?: string;
  headingId?: string;
  score: number;
}
