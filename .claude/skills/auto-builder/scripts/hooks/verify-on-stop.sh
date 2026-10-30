#!/usr/bin/env bash
# Opt-in Stop hook: run the project's check command before Claude finishes.
#
#   AUTO_BUILDER_CHECK_CMD      shell command to run (required; hook is a no-op if unset)
#   AUTO_BUILDER_CHECK_TIMEOUT  seconds before the check is killed (default 300)
#   AUTO_BUILDER_MAX_RETRIES    consecutive blocks allowed per session (default 5)
#
# Failing check -> exit 2 (Claude is told to keep working). After MAX_RETRIES
# consecutive failures the hook lets Claude stop and says so, so it cannot loop
# forever (Claude Code also caps consecutive Stop-hook continuations). That means
# this is a strong nudge, NOT an absolute gate: always read the final report.
#
# SECURITY: AUTO_BUILDER_CHECK_CMD runs as shell. Only set it yourself, in your own
# settings; never accept it from an untrusted repository's checked-in settings.
set -u

cmd="${AUTO_BUILDER_CHECK_CMD:-}"
[ -n "$cmd" ] || exit 0

if ! command -v jq >/dev/null 2>&1; then
  echo "verify-on-stop: jq not found; hook is NOT enforcing." >&2
  exit 0
fi

input="$(cat)"
sid="$(printf '%s' "$input" | jq -r '.session_id // "nosession"' 2>/dev/null || echo nosession)"
sid="${sid//[^A-Za-z0-9_-]/_}"
counter="${TMPDIR:-/tmp}/auto-builder-stop-$sid.count"
max="${AUTO_BUILDER_MAX_RETRIES:-5}"
tmo="${AUTO_BUILDER_CHECK_TIMEOUT:-300}"

if ! cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null; then
  echo "verify-on-stop: cannot cd to '${CLAUDE_PROJECT_DIR:-.}'; checks were NOT run." >&2
  exit 2
fi

if command -v timeout >/dev/null 2>&1; then
  out="$(timeout "$tmo" bash -c "$cmd" 2>&1)"; rc=$?
else
  out="$(bash -c "$cmd" 2>&1)"; rc=$?
fi

if [ $rc -eq 0 ]; then
  rm -f -- "$counter"
  exit 0
fi

n=$(( $(cat "$counter" 2>/dev/null || echo 0) + 1 ))
if [ "$n" -gt "$max" ]; then
  rm -f -- "$counter"
  echo "verify-on-stop: checks still failing after $max attempts; allowing stop. Report the failure honestly." >&2
  exit 0
fi
echo "$n" > "$counter"

{
  [ $rc -eq 124 ] && echo "Check timed out after ${tmo}s."
  echo "Checks failed (exit $rc, attempt $n/$max). Fix before finishing:"
  printf '%s\n' "$out" | tail -n 60 | cut -c1-400
} >&2
exit 2
