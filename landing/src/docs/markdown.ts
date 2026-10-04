import { marked, Renderer } from 'marked';
import { DocFrontmatter, TocHeading } from './types';

// Hand-parse simple frontmatter: title, description, order, section
export function parseFrontmatter(raw: string): { frontmatter: DocFrontmatter; body: string } {
  const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  if (!match) {
    return {
      frontmatter: {
        title: 'Documentation',
        description: 'Tsxtract documentation',
        order: 999,
        section: 'Start here',
      },
      body: raw,
    };
  }

  const rawMeta = match[1];
  const body = match[2];

  const meta: Record<string, string> = {};
  for (const line of rawMeta.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const colonIdx = trimmed.indexOf(':');
    if (colonIdx > 0) {
      const key = trimmed.slice(0, colonIdx).trim();
      let value = trimmed.slice(colonIdx + 1).trim();
      if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      meta[key] = value;
    }
  }

  return {
    frontmatter: {
      title: meta.title || 'Documentation',
      description: meta.description || '',
      order: parseInt(meta.order || '999', 10),
      section: (meta.section as DocFrontmatter['section']) || 'Start here',
    },
    body,
  };
}

// Light syntax highlighting
export function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function highlightPython(code: string): string {
  const tokenRegex = /(#[^\r\n]*)|("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\r\n])*"|'(?:\\.|[^'\\\r\n])*')|(\b(?:def|class|return|import|from|as|if|elif|else|for|while|in|is|not|and|or|try|except|finally|with|raise|yield|async|await|None|True|False)\b)|(\b(?:tsxtract|extract_features|extract_features_df|sliding_features|feature_names|StreamingExtractor|np|pd|print|len|range|enumerate|zip|int|float|str|list|dict|tuple|bool)\b)|(\b\d+(?:\.\d+)?(?:e[+-]?\d+)?\b)/g;

  let lastIndex = 0;
  let out = '';
  let match: RegExpExecArray | null;

  while ((match = tokenRegex.exec(code)) !== null) {
    if (match.index > lastIndex) {
      out += escapeHtml(code.slice(lastIndex, match.index));
    }
    const [, comment, str, kw, fn, num] = match;
    if (comment) {
      out += `<span class="token-comment">${escapeHtml(comment)}</span>`;
    } else if (str) {
      out += `<span class="token-string">${escapeHtml(str)}</span>`;
    } else if (kw) {
      out += `<span class="token-keyword">${escapeHtml(kw)}</span>`;
    } else if (fn) {
      out += `<span class="token-function">${escapeHtml(fn)}</span>`;
    } else if (num) {
      out += `<span class="token-number">${escapeHtml(num)}</span>`;
    }
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < code.length) {
    out += escapeHtml(code.slice(lastIndex));
  }
  return out;
}

function highlightBash(code: string): string {
  const tokenRegex = /(#[^\r\n]*)|("(?:\\.|[^"\\\r\n])*"|'(?:\\.|[^'\\\r\n])*')|(\B--[a-z0-9-]+|\B-[a-z0-9])|(\b(?:pip|uv|conda|python|maturin|cargo|git|pytest|source|export|cd|echo|curl|tar|bash|sh)\b)|(\b\d+\b)/gi;

  let lastIndex = 0;
  let out = '';
  let match: RegExpExecArray | null;

  while ((match = tokenRegex.exec(code)) !== null) {
    if (match.index > lastIndex) {
      out += escapeHtml(code.slice(lastIndex, match.index));
    }
    const [, comment, str, flag, cmd, num] = match;
    if (comment) {
      out += `<span class="token-comment">${escapeHtml(comment)}</span>`;
    } else if (str) {
      out += `<span class="token-string">${escapeHtml(str)}</span>`;
    } else if (flag) {
      out += `<span class="token-keyword">${escapeHtml(flag)}</span>`;
    } else if (cmd) {
      out += `<span class="token-function">${escapeHtml(cmd)}</span>`;
    } else if (num) {
      out += `<span class="token-number">${escapeHtml(num)}</span>`;
    }
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < code.length) {
    out += escapeHtml(code.slice(lastIndex));
  }
  return out;
}

function highlightRust(code: string): string {
  const tokenRegex = /(\/\/[^\r\n]*)|("(?:\\.|[^"\\\r\n])*")|(\b(?:fn|pub|use|let|mut|struct|enum|impl|for|in|match|if|else|return|const|mod|crate|self|Self|where|as|trait|type)\b)|(\b(?:f64|usize|i64|u64|bool|str|String|Vec|Option|Result|Some|None|Ok|Err|StreamingExtractor)\b)|(\b\d+(?:\.\d+)?(?:f64)?\b)/g;

  let lastIndex = 0;
  let out = '';
  let match: RegExpExecArray | null;

  while ((match = tokenRegex.exec(code)) !== null) {
    if (match.index > lastIndex) {
      out += escapeHtml(code.slice(lastIndex, match.index));
    }
    const [, comment, str, kw, typ, num] = match;
    if (comment) {
      out += `<span class="token-comment">${escapeHtml(comment)}</span>`;
    } else if (str) {
      out += `<span class="token-string">${escapeHtml(str)}</span>`;
    } else if (kw) {
      out += `<span class="token-keyword">${escapeHtml(kw)}</span>`;
    } else if (typ) {
      out += `<span class="token-type">${escapeHtml(typ)}</span>`;
    } else if (num) {
      out += `<span class="token-number">${escapeHtml(num)}</span>`;
    }
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < code.length) {
    out += escapeHtml(code.slice(lastIndex));
  }
  return out;
}

function highlightToml(code: string): string {
  const tokenRegex = /(#[^\r\n]*)|(\[[^\]]+\])|("(?:\\.|[^"\\\r\n])*")|(^[a-zA-Z0-9_-]+(?=\s*=))/gm;

  let lastIndex = 0;
  let out = '';
  let match: RegExpExecArray | null;

  while ((match = tokenRegex.exec(code)) !== null) {
    if (match.index > lastIndex) {
      out += escapeHtml(code.slice(lastIndex, match.index));
    }
    const [, comment, section, str, key] = match;
    if (comment) {
      out += `<span class="token-comment">${escapeHtml(comment)}</span>`;
    } else if (section) {
      out += `<span class="token-section">${escapeHtml(section)}</span>`;
    } else if (str) {
      out += `<span class="token-string">${escapeHtml(str)}</span>`;
    } else if (key) {
      out += `<span class="token-key">${escapeHtml(key)}</span>`;
    }
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < code.length) {
    out += escapeHtml(code.slice(lastIndex));
  }
  return out;
}

function highlightCode(code: string, lang: string): string {
  const cleanLang = (lang || '').toLowerCase().trim();

  if (cleanLang === 'python' || cleanLang === 'py') {
    return highlightPython(code);
  }
  if (cleanLang === 'bash' || cleanLang === 'sh' || cleanLang === 'shell') {
    return highlightBash(code);
  }
  if (cleanLang === 'rust' || cleanLang === 'rs') {
    return highlightRust(code);
  }
  if (cleanLang === 'toml') {
    return highlightToml(code);
  }

  return escapeHtml(code);
}

// Convert heading text to clean URL slug
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/<[^>]*>/g, '') // remove HTML tags
    .replace(/[^\w\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-');
}

// Stateful slugger factory ensuring unique IDs (appends -2, -3 on duplicates)
export function createSlugger(): (text: string) => string {
  const occurrences = new Map<string, number>();

  return (text: string): string => {
    const raw = slugify(text) || 'heading';
    const count = occurrences.get(raw) || 0;
    occurrences.set(raw, count + 1);

    if (count === 0) {
      return raw;
    }
    return `${raw}-${count + 1}`;
  };
}

export interface RenderResult {
  html: string;
  headings: TocHeading[];
}

// Pre-process consecutive code blocks with tab="..." using placeholder tokens so marked never mangles the HTML
function extractTabs(markdown: string): { cleanMarkdown: string; tabMap: Map<string, string> } {
  const tabGroupRegex = /((?:```[^\n]*tab="[^"]+"[\s\S]*?```(?:\r?\n)*)+)/g;
  const tabMap = new Map<string, string>();
  let groupCounter = 0;

  const cleanMarkdown = markdown.replace(tabGroupRegex, (group) => {
    const singleBlockRegex = /```([a-zA-Z0-9_-]*)\s+tab="([^"]+)"\r?\n([\s\S]*?)```/g;
    const tabs: { lang: string; label: string; code: string }[] = [];
    let match: RegExpExecArray | null;

    while ((match = singleBlockRegex.exec(group)) !== null) {
      tabs.push({
        lang: match[1] || 'bash',
        label: match[2],
        code: match[3],
      });
    }

    if (tabs.length <= 1) {
      return group;
    }

    groupCounter++;
    const groupId = `tabgroup-${groupCounter}-${Math.random().toString(36).slice(2, 6)}`;
    const headersHtml = tabs
      .map(
        (t, idx) =>
          `<button type="button" class="docs-tab-btn ${idx === 0 ? 'is-active' : ''}" data-group="${groupId}" data-tab-idx="${idx}">${escapeHtml(t.label)}</button>`
      )
      .join('');

    const panesHtml = tabs
      .map((t, idx) => {
        const highlighted = highlightCode(t.code, t.lang);
        const encodedRaw = encodeURIComponent(t.code);
        return `<div class="docs-tab-pane ${idx === 0 ? 'is-active' : 'hidden'}" data-group="${groupId}" data-tab-idx="${idx}"><div class="code-block-wrapper group relative my-0 rounded-b-md rounded-tr-md border border-borderLine bg-[#0f1110] text-[#f2f3ef] shadow-sm overflow-hidden"><div class="flex items-center justify-between border-b border-[#232724] bg-[#141715] px-3.5 py-1.5 text-[11.5px] font-mono text-[#8a8f86]"><span class="uppercase tracking-wider font-semibold">${escapeHtml(t.lang)}</span><button type="button" class="copy-code-btn inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-xs text-[#a0a59c] hover:bg-[#1f2320] hover:text-white transition cursor-pointer" data-code="${encodedRaw}" aria-label="Copy code"><svg class="h-3.5 w-3.5 copy-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke-width="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke-width="2"/></svg><span class="copy-label">Copy</span></button></div><pre class="overflow-x-auto p-4 text-[13px] leading-relaxed font-mono"><code>${highlighted}</code></pre></div></div>`;
      })
      .join('');

    const containerHtml = `<div class="docs-tabs-container my-6" id="${groupId}"><div class="docs-tabs-header flex items-center gap-1 border-b border-borderLine">${headersHtml}</div><div class="docs-tabs-content">${panesHtml}</div></div>`;

    const placeholder = `%%DOCS_TAB_GROUP_PLACEHOLDER_${groupId}%%`;
    tabMap.set(placeholder, containerHtml);
    return `\n\n${placeholder}\n\n`;
  });

  return { cleanMarkdown, tabMap };
}

// Safety-net math preprocessor: convert $...$ complexity and math notation to readable inline code
function preprocessMath(markdown: string): string {
  return markdown.replace(/\$([^\$\n]+)\$/g, (_match, expr) => {
    const clean = expr
      .replace(/\\log/g, 'log')
      .replace(/\\times/g, '×')
      .replace(/\\dots/g, '...')
      .replace(/\\pm/g, '±')
      .replace(/\\in/g, '∈')
      .replace(/\\le/g, '≤')
      .replace(/\\ge/g, '≥')
      .replace(/\\neq/g, '≠')
      .replace(/\\approx/g, '≈')
      .replace(/\\mathbb\{I\}/g, 'I')
      .replace(/\\text\{([^}]+)\}/g, '$1')
      .replace(/\\operatorname\{([^}]+)\}/g, '$1')
      .replace(/\\mu/g, 'μ')
      .replace(/\\sigma/g, 'σ')
      .replace(/\\Delta/g, 'Δ')
      .replace(/\\beta_1/g, 'β₁')
      .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1 / $2)')
      .replace(/\\sum/g, 'Σ')
      .replace(/\\sqrt\{([^}]+)\}/g, '√($1)')
      .trim();
    return `<code class="docs-inline-code math-code font-mono">${escapeHtml(clean)}</code>`;
  });
}

// Custom marked rendering pipeline
export function renderDocMarkdown(rawMarkdown: string): RenderResult {
  const headings: TocHeading[] = [];
  const slugger = createSlugger();
  const renderer = new Renderer();

  // Headings with stable unique slug id, scroll-margin-top 72px, hover anchor link, and badge formatting
  renderer.heading = ({ text, depth }: { text: string; depth: number }) => {
    const richText = marked.parseInline(text, { renderer }) as string;
    const rawText = richText.replace(/<[^>]*>/g, '').trim();
    const cleanDisplay = rawText.replace(/^\[+|\]+$/g, '').trim();
    const id = slugger(cleanDisplay || rawText);

    // CHANGELOG CATEGORY BADGES: Added, Changed, Fixed, Removed, Deprecated, Security
    const lower = cleanDisplay.toLowerCase();
    if (depth === 3 && ['added', 'changed', 'fixed', 'removed', 'deprecated', 'security'].includes(lower)) {
      let badgeStyle = 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30';
      if (lower === 'added') badgeStyle = 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30';
      if (lower === 'fixed') badgeStyle = 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30';
      if (lower === 'removed') badgeStyle = 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30';
      if (lower === 'security') badgeStyle = 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30';

      return `
        <h3 id="${id}" class="group scroll-mt-[72px] mt-8 mb-3 flex items-center gap-2">
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide border uppercase ${badgeStyle}">
            ${cleanDisplay}
          </span>
          <a href="#${id}" class="opacity-0 group-hover:opacity-100 transition-opacity ml-1 text-muted hover:text-ink font-mono text-[0.8em]" aria-label="Permalink to ${cleanDisplay}">#</a>
        </h3>
      `;
    }

    if (depth === 2 || depth === 3) {
      headings.push({ id, text: cleanDisplay, level: depth });
    }

    const tag = `h${depth}`;
    const sizeClasses =
      depth === 1
        ? 'text-2xl sm:text-3xl font-extrabold tracking-tight text-ink mt-2 mb-6'
        : depth === 2
        ? 'text-xl sm:text-2xl font-bold tracking-tight text-ink mt-10 mb-4 pb-2 border-b border-borderDim'
        : depth === 3
        ? 'text-lg sm:text-xl font-semibold tracking-tight text-ink mt-8 mb-3'
        : 'text-base font-semibold text-ink mt-5 mb-2';

    return `
      <${tag} id="${id}" class="group scroll-mt-[72px] relative flex items-center justify-between ${sizeClasses}">
        <span>${richText}</span>
        <a href="#${id}" class="opacity-0 group-hover:opacity-100 transition-opacity ml-2 text-muted hover:text-ink font-mono text-[0.8em] font-normal" aria-label="Permalink to ${cleanDisplay}">#</a>
      </${tag}>
    `;
  };

  // Blockquotes for GitHub-style callouts: > [!NOTE], > [!TIP], > [!WARNING], > [!IMPORTANT]
  renderer.blockquote = (token: any) => {
    const rawText: string = token.text ?? '';
    const inner = (marked.parse(rawText, { gfm: true, breaks: false }) as string).trim();
    const trimmed = inner;
    const calloutMatch = trimmed.match(/^<p>\s*\[!(NOTE|TIP|WARNING|IMPORTANT|CAUTION)\](?:\s*<br\s*\/?>)?([\s\S]*)<\/p>$/i);

    if (calloutMatch) {
      const type = calloutMatch[1].toUpperCase();
      const content = calloutMatch[2].trim();

      let themeClass = 'border-blue-500 bg-blue-50/60 dark:bg-blue-950/25 text-blue-950 dark:text-blue-200 border-l-4';
      let title = 'Note';
      let icon = `<svg class="h-4 w-4 text-blue-600 dark:text-blue-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>`;

      if (type === 'TIP') {
        themeClass = 'border-emerald-500 bg-emerald-50/60 dark:bg-emerald-950/25 text-emerald-950 dark:text-emerald-200 border-l-4';
        title = 'Tip';
        icon = `<svg class="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>`;
      } else if (type === 'WARNING' || type === 'CAUTION') {
        themeClass = 'border-amber-500 bg-amber-50/60 dark:bg-amber-950/25 text-amber-950 dark:text-amber-200 border-l-4';
        title = 'Warning';
        icon = `<svg class="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
      } else if (type === 'IMPORTANT') {
        themeClass = 'border-purple-500 bg-purple-50/60 dark:bg-purple-950/25 text-purple-950 dark:text-purple-200 border-l-4';
        title = 'Important';
        icon = `<svg class="h-4 w-4 text-purple-600 dark:text-purple-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
      }

      return `
        <div class="my-5 rounded-r-lg p-4 shadow-sm border border-l-0 border-borderLine/40 ${themeClass}">
          <div class="flex items-center gap-2 font-semibold text-xs uppercase tracking-wider mb-1.5">
            ${icon}
            <span>${title}</span>
          </div>
          <div class="text-[13.5px] leading-relaxed text-inherit opacity-95 [&>p]:my-1.5 [&>p:first-child]:mt-0 [&>p:last-child]:mb-0">
            ${content}
          </div>
        </div>
      `;
    }

    return `<blockquote class="my-4 border-l-4 border-borderLine pl-4 italic text-muted">${inner}</blockquote>`;
  };

  // Code blocks: copy button, language header, syntax highlighting, or mermaid diagram
  renderer.code = ({ text, lang }: { text: string; lang?: string }) => {
    const rawLang = (lang || '').trim();
    const tabMatch = rawLang.match(/tab="([^"]+)"/);
    const displayLang = rawLang.split(/\s+/)[0] || 'text';

    if (displayLang.toLowerCase() === 'mermaid') {
      const id = `mermaid-${Math.random().toString(36).slice(2, 9)}`;
      return `
        <div class="mermaid-diagram-container my-8 overflow-x-auto rounded-xl border border-borderLine bg-card/60 p-5 shadow-sm text-center">
          <div class="mermaid-label mb-3 flex items-center justify-between text-[11px] font-mono uppercase tracking-wider text-muted border-b border-borderDim pb-2">
            <span class="flex items-center gap-1.5 font-semibold text-ink">
              <svg class="h-3.5 w-3.5 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
              </svg>
              Architecture & Flow Diagram
            </span>
            <span class="text-[10px] text-muted font-normal">Interactive Vector</span>
          </div>
          <div class="mermaid flex justify-center py-2" id="${id}">${escapeHtml(text)}</div>
        </div>
      `;
    }

    const highlighted = highlightCode(text, displayLang);
    const encodedRaw = encodeURIComponent(text);

    return `
      <div class="code-block-wrapper group relative my-5 rounded-lg border border-borderLine bg-[#0f1110] text-[#f2f3ef] shadow-sm overflow-hidden">
        <div class="flex items-center justify-between border-b border-[#232724] bg-[#141715] px-3.5 py-1.5 text-[11.5px] font-mono text-[#8a8f86]">
          <span class="uppercase tracking-wider font-semibold">${escapeHtml(tabMatch ? tabMatch[1] : displayLang)}</span>
          <button type="button" class="copy-code-btn inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-xs text-[#a0a59c] hover:bg-[#1f2320] hover:text-white transition cursor-pointer" data-code="${encodedRaw}" aria-label="Copy code">
            <svg class="h-3.5 w-3.5 copy-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke-width="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke-width="2"/></svg>
            <span class="copy-label">Copy</span>
          </button>
        </div>
        <pre class="overflow-x-auto p-4 text-[13px] leading-relaxed font-mono"><code>${highlighted}</code></pre>
      </div>
    `;
  };

  // Modern figure wrapper for images with clean border, caption, and shadow
  renderer.image = ({ href, title, text }: { href: string; title?: string | null; text: string }) => {
    const caption = title || text;
    return `
      <figure class="my-8 flex flex-col items-center">
        <div class="overflow-hidden rounded-xl border border-borderLine bg-card p-2 shadow-sm transition-all hover:shadow-md max-w-full">
          <img src="${href}" alt="${escapeHtml(text)}" class="max-w-full h-auto rounded-lg block mx-auto" />
        </div>
        ${caption ? `<figcaption class="mt-2.5 text-center text-xs font-mono text-muted max-w-xl leading-relaxed">${escapeHtml(caption)}</figcaption>` : ''}
      </figure>
    `;
  };

  // Inline code using dedicated docs-inline-code class
  renderer.codespan = ({ text }: { text: string }) => {
    return `<code class="docs-inline-code">${escapeHtml(text)}</code>`;
  };

  // Links with smooth hover styling
  renderer.link = ({ href, title, text }: { href: string; title?: string | null; text: string }) => {
    const isExternal = href.startsWith('http://') || href.startsWith('https://');
    const target = isExternal ? ' target="_blank" rel="noopener noreferrer"' : '';
    const titleAttr = title ? ` title="${title}"` : '';
    return `<a href="${href}" class="text-ink font-medium underline underline-offset-4 decoration-borderLine hover:decoration-ink transition-colors"${titleAttr}${target}>${text}</a>`;
  };

  // Tables with horizontal scroll wrapper and responsive column styling
  renderer.table = (token) => {
    const inline = (src: string) => marked.parseInline(src, { renderer }) as string;
    const headerRow = token.header
      .map((cell) => `<th class="border border-borderLine bg-canvas px-3.5 py-2.5 text-left font-semibold text-xs text-ink uppercase tracking-wider whitespace-nowrap">${inline(cell.text)}</th>`)
      .join('');
    const bodyRows = token.rows
      .map(
        (row, idx) =>
          `<tr class="${idx % 2 === 1 ? 'bg-canvas/40' : 'bg-card'} hover:bg-canvas/70 transition-colors">` +
          row.map((cell) => `<td class="border border-borderLine px-3.5 py-2.5 text-xs text-body align-top leading-relaxed">${inline(cell.text)}</td>`).join('') +
          `</tr>`
      )
      .join('');

    return `
      <div class="table-scroll-wrapper my-6 overflow-x-auto rounded-lg border border-borderLine shadow-sm">
        <table class="min-w-full divide-y divide-borderLine text-left text-xs border-collapse">
          <thead><tr>${headerRow}</tr></thead>
          <tbody class="divide-y divide-borderLine">${bodyRows}</tbody>
        </table>
      </div>
    `;
  };

  const processedMath = preprocessMath(rawMarkdown);
  const { cleanMarkdown, tabMap } = extractTabs(processedMath);
  let html = marked.parse(cleanMarkdown, {
    gfm: true,
    breaks: false,
    renderer,
  }) as string;

  // Restore tab groups into HTML without marked indentation mangling
  tabMap.forEach((tabHtml, placeholder) => {
    const pRegex = new RegExp(`<p>\\s*${placeholder}\\s*<\\/p>`, 'g');
    if (pRegex.test(html)) {
      html = html.replace(pRegex, tabHtml);
    } else {
      html = html.split(placeholder).join(tabHtml);
    }
  });

  return { html, headings };
}
