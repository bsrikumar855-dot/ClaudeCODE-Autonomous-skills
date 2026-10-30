#!/usr/bin/env bash
# Opt-in PreToolUse hook: block Edit/Write/NotebookEdit on secret-bearing files.
# Exit 2 = block (stderr is shown to Claude). Requires jq.
#
# LIMITS (be honest about them): this inspects only the file path of file-editing
# tools. It does NOT stop Bash commands (echo > .env, sed -i, cp) or Read.
# Use Claude Code permission rules (permissions.deny) for those. Malformed input
# or a missing jq makes the hook fail OPEN with a warning on stderr.
set -u

if ! command -v jq >/dev/null 2>&1; then
  echo "protect-secrets: jq not found; hook is NOT enforcing." >&2
  exit 0
fi

input="$(cat)"
if ! file="$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.notebook_path // .tool_input.path // empty' 2>/dev/null)"; then
  echo "protect-secrets: could not parse hook input; hook is NOT enforcing." >&2
  exit 0
fi
[ -n "$file" ] || exit 0

# Normalise: Windows separators, trailing blanks, case (macOS/Windows are case-insensitive).
norm="$(printf '%s' "$file" | tr '\\' '/' | tr '[:upper:]' '[:lower:]' | sed -e 's/[[:space:]]*$//')"
base="${norm##*/}"

block() {
  echo "Blocked: '$file' looks like it contains secrets ($1). Use environment variables and a committed .env.example; ask the user to edit real secrets." >&2
  exit 2
}

# Directories that are secret stores.
case "/$norm/" in
  */.ssh/*|*/.gnupg/*|*/.aws/*|*/.env/*) block "secret directory" ;;
esac

# Template files are fine.
case "$base" in
  *.example|*.sample|*.template|*.dist|*.example.*|*.sample.*|*.template.*) exit 0 ;;
esac

case "$base" in
  .env|.env.*|*.env|.envrc|.netrc|.npmrc|.pypirc|.git-credentials|.pgpass) block "env/credential file" ;;
  *.pem|*.key|*.p12|*.pfx|*.jks|*.keystore|*.kdbx|*.tfvars) block "key/keystore" ;;
  id_rsa|id_dsa|id_ecdsa|id_ed25519) block "private SSH key" ;;
  credentials|credentials.json|credentials.yml|credentials.yaml) block "credentials file" ;;
  secret.json|secrets.json|secrets.yml|secrets.yaml|secrets.toml) block "secrets file" ;;
esac
exit 0
