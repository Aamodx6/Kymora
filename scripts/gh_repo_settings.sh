#!/usr/bin/env bash
# scripts/gh_repo_settings.sh
# Configure GitHub repository description, homepage, topics, and community features.
#
# NOTE: DO NOT RUN WITHOUT EXPLICIT HUMAN AUTHORIZATION.
#
# Usage:
#   bash scripts/gh_repo_settings.sh

set -euo pipefail

REPO="Aamodx6/Kymora"

if [ "${1:-}" != "--apply" ]; then
  echo "DRY RUN: Pass '--apply' to execute these repository settings on GitHub."
  echo "Target repository: ${REPO}"
  echo "Actions: update description, homepage, 11 topics, enable issues & discussions."
  exit 0
fi

echo "Setting repository metadata for ${REPO}..."

gh repo edit "${REPO}" \
  --description "Fast time-series feature extraction in Rust & Python" \
  --homepage "https://aamodx6.github.io/Kymora/" \
  --add-topic "time-series" \
  --add-topic "feature-extraction" \
  --add-topic "rust" \
  --add-topic "pyo3" \
  --add-topic "python" \
  --add-topic "scikit-learn" \
  --add-topic "numpy" \
  --add-topic "polars" \
  --add-topic "catch22" \
  --add-topic "tsfresh" \
  --add-topic "signal-processing" \
  --enable-issues \
  --enable-discussions

echo "Repository settings updated successfully."
