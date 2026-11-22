#!/usr/bin/env bash
# scripts/create_issues.sh - Batch creation of "Good First Issue" tasks
#
# DO NOT RUN AUTOMATICALLY: This script is prepared for human maintainers to seed
# initial community issues on GitHub when ready after release launch.
set -euo pipefail

REPO="Aamodx6/Kymora"
ISSUES_DIR="docs/internal/issues"

if [ ! -d "$ISSUES_DIR" ]; then
    echo "Error: Directory $ISSUES_DIR not found!" >&2
    exit 1
fi

echo "=== Kymora Community Issue Seeder ==="
echo "Target repo: $REPO"
echo "Issues directory: $ISSUES_DIR"
echo ""

for issue_file in "$ISSUES_DIR"/*.md; do
    echo "Processing $issue_file..."
    
    # Extract title from frontmatter
    TITLE=$(grep '^title:' "$issue_file" | head -n 1 | sed -e 's/^title:[[:space:]]*"\{0,1\}//' -e 's/"\{0,1\}[[:space:]]*$//')
    
    # Extract labels from frontmatter
    LABELS_ARGS=$(python3 -c "
import re, sys
with open(sys.argv[1], encoding='utf-8') as f:
    text = f.read()
m = re.search(r'^labels:\s*\[(.*?)\]', text, re.M)
if m:
    tags = [t.strip().strip('\"\'') for t in m.group(1).split(',') if t.strip()]
    if 'good first issue' not in tags:
        tags.append('good first issue')
    print(' '.join(f'--label \"{t}\"' for t in tags))
else:
    print('--label \"good first issue\"')
" "$issue_file")
    
    # Extract body without frontmatter
    BODY=$(awk '
        BEGIN { in_fm = 0; fm_done = 0 }
        /^---$/ {
            if (in_fm == 0 && fm_done == 0) { in_fm = 1; next }
            if (in_fm == 1) { in_fm = 0; fm_done = 1; next }
        }
        fm_done == 1 { print }
    ' "$issue_file")
    
    echo "Creating issue: '$TITLE' with labels $LABELS_ARGS..."
    # shellcheck disable=SC2086
    gh issue create \
        --repo "$REPO" \
        --title "$TITLE" \
        $LABELS_ARGS \
        --body "$BODY"
        
    echo "Created successfully."
    sleep 2
done

echo ""
echo "All issues have been successfully seeded!"
