#!/usr/bin/env bash
# Copy missing AUTO-BUILDER state-file templates into a project. Never overwrites.
# Usage: init-artifacts.sh [target-dir] [NAME ...]
#   target-dir  default: ./docs/auto-builder
#   NAME        template names without .md (e.g. TASKS PROGRESS); default: all templates
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
src="$here/../templates"
dest="${1:-docs/auto-builder}"
[ $# -gt 0 ] && shift

[ -d "$src" ] || { echo "error: templates directory not found: $src" >&2; exit 1; }

if [ $# -gt 0 ]; then
  files=()
  for name in "$@"; do
    case "$name" in *[!A-Za-z0-9_-]*|"") echo "error: invalid template name: $name" >&2; exit 2 ;; esac
    [ -f "$src/$name.md" ] || { echo "error: no such template: $name (available: $(cd "$src" && ls *.md | sed 's/\.md$//' | tr '\n' ' '))" >&2; exit 2; }
    files+=("$src/$name.md")
  done
else
  files=("$src"/*.md)
fi

mkdir -p "$dest"
for f in "${files[@]}"; do
  t="$dest/$(basename -- "$f")"
  if [ -e "$t" ]; then
    echo "exists, kept: $t"
  else
    cp -- "$f" "$t"
    echo "created:      $t"
  fi
done
