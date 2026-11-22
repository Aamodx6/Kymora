#!/usr/bin/env python3
"""Check internal links and anchors in Markdown files under docs/ and README.md.

Validates that:
1. Linked files exist on disk.
2. Linked anchors exist in the target file (heading slugs or HTML anchors).
"""

import os
import re
import sys
from pathlib import Path


def slugify(text: str) -> str:
    """Convert a markdown heading into a GitHub/MkDocs anchor slug."""
    # Strip markdown formatting like code ticks, links, bold
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"[*_~]", "", text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Lowercase, replace non-alphanumeric with hyphens
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def extract_anchors(file_path: Path) -> set[str]:
    """Extract all heading slugs and HTML anchor IDs from a markdown file."""
    anchors = set()
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return anchors

    for line in content.splitlines():
        # Check markdown headings (# Heading)
        heading_match = re.match(r"^#{1,6}\s+(.+)$", line.strip())
        if heading_match:
            heading_text = heading_match.group(1).strip()
            # Check for explicit anchor {#custom-id}
            custom_id = re.search(r"\{#([^}]+)\}", heading_text)
            if custom_id:
                anchors.add(custom_id.group(1))
                heading_text = re.sub(r"\{#[^}]+\}", "", heading_text).strip()
            slug = slugify(heading_text)
            if slug:
                anchors.add(slug)

        # Check for HTML anchors: <a id="foo"> or <a name="foo">
        for html_anchor in re.findall(r'<a\s+[^>]*(?:id|name)=["\']([^"\']+)["\']', line, re.IGNORECASE):
            anchors.add(html_anchor)

    return anchors


def check_links() -> list[str]:
    root_dir = Path(__file__).resolve().parent.parent
    docs_dir = root_dir / "docs"

    files_to_check: list[Path] = []
    if (root_dir / "README.md").exists():
        files_to_check.append(root_dir / "README.md")
    for p in docs_dir.rglob("*.md"):
        # Skip internal and launch drafts
        rel = p.relative_to(docs_dir).as_posix()
        if rel.startswith("internal/") or rel.startswith("launch/"):
            continue
        files_to_check.append(p)

    broken: list[str] = []
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    # Cache anchors per file
    file_anchors: dict[Path, set[str]] = {}

    for file_path in files_to_check:
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            broken.append(f"Could not read {file_path}: {e}")
            continue

        # Ignore code blocks
        lines = content.splitlines()
        in_code_block = False

        for line_no, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            for match in link_pattern.finditer(line):
                target = match.group(2).strip()

                # Ignore external links, mailto, etc.
                if re.match(r"^(https?://|mailto:|ftp:|#)", target):
                    if target.startswith("#"):
                        # In-page anchor
                        anchor = target[1:]
                        if file_path not in file_anchors:
                            file_anchors[file_path] = extract_anchors(file_path)
                        if anchor and anchor not in file_anchors[file_path]:
                            # Allow common dynamic anchors like top
                            if anchor not in ("top", ""):
                                broken.append(f"{file_path}:{line_no}: In-page anchor '#{anchor}' not found")
                    continue

                # Remove title if present: e.g. "path/to/file.md 'title'"
                target_parts = target.split()
                target_clean = target_parts[0] if target_parts else ""

                if "#" in target_clean:
                    target_file_str, target_anchor = target_clean.split("#", 1)
                else:
                    target_file_str, target_anchor = target_clean, None

                if not target_file_str:
                    continue

                # Resolve target file path relative to current file
                target_path = (file_path.parent / target_file_str).resolve()

                if not target_path.exists():
                    # Check if relative to root
                    root_relative_path = (root_dir / target_file_str).resolve()
                    if root_relative_path.exists():
                        target_path = root_relative_path
                    else:
                        broken.append(f"{file_path}:{line_no}: Target file '{target_file_str}' does not exist")
                        continue

                if target_anchor and target_path.suffix == ".md":
                    if target_path not in file_anchors:
                        file_anchors[target_path] = extract_anchors(target_path)
                    if target_anchor and target_anchor not in file_anchors[target_path]:
                        broken.append(f"{file_path}:{line_no}: Anchor '#{target_anchor}' not found in {target_path.name}")

    return broken


def main() -> int:
    print("Checking markdown internal links and anchors...")
    broken = check_links()
    if broken:
        print(f"FAILED: Found {len(broken)} broken link(s):")
        for err in broken:
            print(f"  - {err}")
        return 1
    print("All internal links and anchors are valid!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
