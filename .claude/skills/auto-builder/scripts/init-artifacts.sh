#!/usr/bin/env bash
# Copy missing AUTO-BUILDER state-file templates into a project. Never overwrites.
# Usage: init-artifacts.sh [target-dir]   (default: ./docs/auto-builder)
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
src="$here/../templates"
dest="${1:-docs/auto-builder}"

[ -d "$src" ] || { echo "error: templates directory not found: $src" >&2; exit 1; }
mkdir -p "$dest"

for f in "$src"/*.md; do
  t="$dest/$(basename -- "$f")"
  if [ -e "$t" ]; then
    echo "exists, kept: $t"
  else
    cp -- "$f" "$t"
    echo "created:      $t"
  fi
done
