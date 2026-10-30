#!/usr/bin/env bash
# AUTO-BUILDER installer (Linux, macOS, WSL, Git Bash).
# Installs the skill and subagents without overwriting existing files.
set -euo pipefail

usage() {
  cat <<USAGE
Usage: ./install.sh (--personal | --project [DIR]) [--dry-run] [--update]

  --personal      Install to ~/.claude/skills/auto-builder and ~/.claude/agents
  --project [DIR] Install to DIR/.claude/... (DIR defaults to the current directory;
                  may appear before or after the other flags; use ./-name for dirs starting with '-')
  --dry-run       Show what would happen; change nothing
  --update        Replace differing package files; the old file is kept as .bak (or .bak.N)
  -h, --help      Show this help

Existing files are never overwritten unless --update is given. Symlinks at install
locations are never replaced. No settings, permissions, hooks or CLAUDE.md are touched.
Files left over from older package versions are reported as STALE, never deleted.
USAGE
}

die() { echo "error: $*" >&2; exit 1; }

mode=""; project_dir=""; dry=0; update=0
set_mode() { [ -z "$mode" ] || [ "$mode" = "$1" ] || die "choose only one of --personal / --project"; mode="$1"; }
while [ $# -gt 0 ]; do
  case "$1" in
    --personal) set_mode personal ;;
    --project)  set_mode project ;;
    --dry-run)  dry=1 ;;
    --update)   update=1 ;;
    -h|--help)  usage; exit 0 ;;
    --)         shift; [ $# -le 1 ] || die "too many arguments"; [ $# -eq 0 ] || project_dir="$1"; break ;;
    -*)         usage >&2; die "unknown option: $1" ;;
    *)          [ -z "$project_dir" ] || die "unexpected extra argument: $1"; project_dir="$1" ;;
  esac
  shift
done
[ -n "$mode" ] || { usage >&2; die "choose --personal or --project"; }
if [ "$mode" = personal ] && [ -n "$project_dir" ]; then die "a directory argument only applies to --project"; fi

case "$(uname -s 2>/dev/null || echo unknown)" in
  Linux*)  os=Linux ;;
  Darwin*) os=macOS ;;
  MINGW*|MSYS*|CYGWIN*) os="Windows (Git Bash/MSYS)" ;;
  *) os=unknown ;;
esac

# Resolve this script's real location even when invoked through a symlink.
self="${BASH_SOURCE[0]}"
while [ -L "$self" ]; do
  link="$(readlink -- "$self")"
  case "$link" in /*) self="$link" ;; *) self="$(dirname -- "$self")/$link" ;; esac
done
src_root="$(cd -P -- "$(dirname -- "$self")" && pwd -P)"
src_skill="$src_root/.claude/skills/auto-builder"
src_agents="$src_root/.claude/agents"
[ -f "$src_skill/SKILL.md" ] || die "missing $src_skill/SKILL.md (run from a complete checkout)"
ls "$src_agents"/*.md >/dev/null 2>&1 || die "no agent files in $src_agents"

if [ "$mode" = personal ]; then
  [ -n "${HOME:-}" ] || die "HOME is not set"
  base_parent="$HOME"
else
  d="${project_dir:-$PWD}"
  [ -d "$d" ] || die "project directory does not exist: $d"
  base_parent="$(cd -P -- "$d" && pwd -P)"
fi
base="$base_parent/.claude"
# Compare physical paths so symlinks cannot alias the source onto the destination.
if [ -d "$base" ]; then base_phys="$(cd -P -- "$base" && pwd -P)"; else base_phys="$base"; fi
[ "$base_phys" != "$src_root/.claude" ] || die "target is this repository itself; pick another project or --personal"

dst_skill="$base/skills/auto-builder"
dst_agents="$base/agents"
installed=0; unchanged=0; preserved=0; updated=0; conflicts=0

if [ $dry -eq 0 ]; then
  mkdir -p -- "$dst_skill" "$dst_agents" 2>/dev/null \
    || die "cannot create $base (check permissions and that '.claude' is not a file)"
  [ -w "$dst_skill" ] && [ -w "$dst_agents" ] || die "no write permission in $base"
fi

next_backup() { # print first unused backup name for $1
  local b="$1.bak" i=1
  while [ -e "$b" ] || [ -L "$b" ]; do b="$1.bak.$i"; i=$((i+1)); done
  printf '%s' "$b"
}

# install_file SRC DST
install_file() {
  local s="$1" t="$2"
  if [ -L "$t" ]; then
    echo "CONFLICT  $t is a symlink; left untouched"; conflicts=$((conflicts+1))
  elif [ -d "$t" ]; then
    echo "CONFLICT  $t is a directory, expected a file; left untouched"; conflicts=$((conflicts+1))
  elif [ ! -e "$t" ]; then
    echo "INSTALL   $t"
    if [ $dry -eq 0 ]; then mkdir -p -- "$(dirname -- "$t")"; cp -p -- "$s" "$t"; fi
    installed=$((installed+1))
  elif cmp -s -- "$s" "$t"; then
    unchanged=$((unchanged+1))
  elif [ $update -eq 1 ]; then
    local bak; bak="$(next_backup "$t")"
    echo "UPDATE    $t (backup: $bak)"
    if [ $dry -eq 0 ]; then cp -p -- "$t" "$bak"; cp -p -- "$s" "$t"; fi
    updated=$((updated+1))
  else
    echo "PRESERVE  $t (differs; kept your version, use --update to replace)"
    preserved=$((preserved+1))
  fi
}

echo "OS: $os | mode: $mode | target: $base$([ $dry -eq 1 ] && echo ' | DRY RUN')"

srclist="$(mktemp)"; trap 'rm -f "$srclist"' EXIT
while IFS= read -r -d '' f; do
  r="${f#"$src_skill"/}"
  printf '%s\n' "$r" >> "$srclist"
  install_file "$f" "$dst_skill/$r"
done < <(find "$src_skill" -type f ! -name '.DS_Store' ! -name '*.bak' ! -name '*.bak.*' -print0 | sort -z)

for f in "$src_agents"/*.md; do
  install_file "$f" "$dst_agents/$(basename -- "$f")"
done

# Report (never delete) package-owned files that the current version no longer ships.
stale=0
if [ -d "$dst_skill" ]; then
  while IFS= read -r -d '' f; do
    r="${f#"$dst_skill"/}"
    case "$r" in *.bak|*.bak.*) continue ;; esac
    if ! grep -Fxq -- "$r" "$srclist"; then
      echo "STALE     $f (not part of this version; remove manually if unused)"; stale=$((stale+1))
    fi
  done < <(find "$dst_skill" -type f -print0 | sort -z)
fi

echo
echo "Installed: $installed | updated: $updated | unchanged: $unchanged | preserved: $preserved | conflicts: $conflicts | stale: $stale"
[ $dry -eq 1 ] && echo "Dry run: nothing was written."
[ $preserved -eq 0 ] || echo "Note: $preserved file(s) differ from this version, so your install may mix versions. Run with --update to sync."
echo "Skill:  $dst_skill"
echo "Agents: $dst_agents"
echo "Next: open Claude Code in your project and run /auto-builder <your goal>"
[ $conflicts -eq 0 ] || exit 1
