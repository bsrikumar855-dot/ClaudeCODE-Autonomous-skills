#!/usr/bin/env bash
# Installer tests in isolated temp dirs. Never touches the real ~/.claude.
set -uo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
fails=0; n=0

t() { # t "description" command...
  local d="$1"; shift; n=$((n+1))
  if "$@" >/dev/null 2>&1; then echo "ok   - $d"; else echo "FAIL - $d"; fails=$((fails+1)); fi
}
nt() { local d="$1"; shift; n=$((n+1))
  if "$@" >/dev/null 2>&1; then echo "FAIL - $d"; fails=$((fails+1)); else echo "ok   - $d"; fi; }

# --- personal install into a fake HOME
home="$tmp/home"; mkdir -p "$home"
HOME="$home" "$repo/install.sh" --personal >"$tmp/out1" 2>&1
t "personal: SKILL.md installed"         test -f "$home/.claude/skills/auto-builder/SKILL.md"
n_agents="$(ls "$repo/.claude/agents"/*.md | wc -l)"
t "repo ships exactly nine agents"        test "$n_agents" -eq 9
t "personal: all nine agents installed"  test "$(ls "$home/.claude/agents" | wc -l)" -eq "$n_agents"
t "personal: security-engineer installed" test -f "$home/.claude/agents/security-engineer.md"
t "personal: hook script stays executable" test -x "$home/.claude/skills/auto-builder/scripts/hooks/protect-secrets.sh"
t "personal: all playbooks installed"     test "$(ls "$home/.claude/skills/auto-builder/playbooks" | wc -l)" -eq "$(ls "$repo/.claude/skills/auto-builder/playbooks" | wc -l)"
t "personal: router + arena installed"   test -f "$home/.claude/skills/auto-builder/workflows/router.md" -a -f "$home/.claude/skills/auto-builder/workflows/arena.md"
t "personal: principles installed"       test -f "$home/.claude/skills/auto-builder/principles/engineering-principles.md"
t "personal: templates installed"        test -f "$home/.claude/skills/auto-builder/templates/TASKS.md"
t "personal: no settings/CLAUDE.md written" bash -c "! ls '$home/.claude/settings.json' '$home/.claude/CLAUDE.md' 2>/dev/null"

# --- idempotent re-run
HOME="$home" "$repo/install.sh" --personal >"$tmp/out2" 2>&1
t "rerun: reports nothing installed" grep -q "Installed: 0" "$tmp/out2"

# --- preservation of custom agent + modified skill file
echo "MY CUSTOM ARCHITECT" > "$home/.claude/agents/architect.md"
echo "# mine" >> "$home/.claude/skills/auto-builder/workflows/delivery.md"
HOME="$home" "$repo/install.sh" --personal >"$tmp/out3" 2>&1
t "preserve: custom agent untouched"  grep -q "MY CUSTOM ARCHITECT" "$home/.claude/agents/architect.md"
t "preserve: modified skill file untouched" grep -q "# mine" "$home/.claude/skills/auto-builder/workflows/delivery.md"
t "preserve: reported PRESERVE" grep -q "PRESERVE" "$tmp/out3"

# --- --update backs up and replaces
HOME="$home" "$repo/install.sh" --personal --update >"$tmp/out4" 2>&1
t "update: agent restored"   cmp -s "$repo/.claude/agents/architect.md" "$home/.claude/agents/architect.md"
t "update: backup kept"      grep -q "MY CUSTOM ARCHITECT" "$home/.claude/agents/architect.md.bak"

# --- project install from a different cwd, with a space in the path
proj="$tmp/my project"; mkdir -p "$proj"
( cd "$tmp" && "$repo/install.sh" --project "$proj" >"$tmp/out5" 2>&1 )
t "project: skill installed"  test -f "$proj/.claude/skills/auto-builder/SKILL.md"
t "project: all nine agents installed" test "$(ls "$proj/.claude/agents" | wc -l)" -eq "$n_agents"
t "project: security-engineer installed" test -f "$proj/.claude/agents/security-engineer.md"
t "project: installed agents identical to source" bash -c "for f in \"$repo\"/.claude/agents/*.md; do cmp -s \"\$f\" \"$proj/.claude/agents/\$(basename \"\$f\")\" || exit 1; done"

# --- project install defaulting to cwd
proj2="$tmp/proj2"; mkdir -p "$proj2"
( cd "$proj2" && "$repo/install.sh" --project >"$tmp/out6" 2>&1 )
t "project(cwd): skill installed" test -f "$proj2/.claude/skills/auto-builder/SKILL.md"

# --- dry run writes nothing
proj3="$tmp/proj3"; mkdir -p "$proj3"
"$repo/install.sh" --project "$proj3" --dry-run >"$tmp/out7" 2>&1
t "dry-run: reports INSTALL"   grep -q "INSTALL" "$tmp/out7"
nt "dry-run: no .claude created" test -e "$proj3/.claude"

# --- error handling
nt "error: no mode given"        "$repo/install.sh"
nt "error: bad option"           "$repo/install.sh" --bogus
nt "error: missing project dir"  "$repo/install.sh" --project "$tmp/nope"
nt "error: refuses own repo"     "$repo/install.sh" --project "$repo"

# --- installed init-artifacts script works and never overwrites
art="$tmp/art"; mkdir -p "$art"
t "init-artifacts: creates templates" "$proj/.claude/skills/auto-builder/scripts/init-artifacts.sh" "$art/docs"
t "init-artifacts: PROGRESS.md copied" test -f "$art/docs/PROGRESS.md"
t "init-artifacts: SECURITY-REVIEW.md copied" test -f "$art/docs/SECURITY-REVIEW.md"
t "init-artifacts: all templates copied" test "$(ls "$art/docs" | wc -l)" -eq "$(ls "$repo/.claude/skills/auto-builder/templates" | wc -l)"
echo keep > "$art/docs/TASKS.md"
"$proj/.claude/skills/auto-builder/scripts/init-artifacts.sh" "$art/docs" >/dev/null 2>&1
t "init-artifacts: kept existing file" grep -q keep "$art/docs/TASKS.md"

# --- hooks behave
hook="$proj/.claude/skills/auto-builder/scripts/hooks/protect-secrets.sh"
echo '{"tool_input":{"file_path":"/x/.env"}}' | "$hook" >/dev/null 2>&1; rc=$?
n=$((n+1)); if [ $rc -eq 2 ]; then echo "ok   - hook blocks .env (exit 2)"; else echo "FAIL - hook .env rc=$rc"; fails=$((fails+1)); fi
echo '{"tool_input":{"file_path":"/x/.env.example"}}' | "$hook" >/dev/null 2>&1; rc=$?
n=$((n+1)); if [ $rc -eq 0 ]; then echo "ok   - hook allows .env.example"; else echo "FAIL - hook .env.example rc=$rc"; fails=$((fails+1)); fi
echo '{"tool_input":{"file_path":"/x/app.py"}}' | "$hook" >/dev/null 2>&1; rc=$?
n=$((n+1)); if [ $rc -eq 0 ]; then echo "ok   - hook allows normal file"; else echo "FAIL - hook app.py rc=$rc"; fails=$((fails+1)); fi
stop="$proj/.claude/skills/auto-builder/scripts/hooks/verify-on-stop.sh"
echo '{}' | TMPDIR="$tmp" AUTO_BUILDER_CHECK_CMD="exit 1" "$stop" >/dev/null 2>&1; rc=$?
n=$((n+1)); if [ $rc -eq 2 ]; then echo "ok   - stop hook blocks on failing check"; else echo "FAIL - stop hook rc=$rc"; fails=$((fails+1)); fi
echo '{"stop_hook_active":true,"session_id":"old"}' | TMPDIR="$tmp" AUTO_BUILDER_CHECK_CMD="exit 1" "$stop" >/dev/null 2>&1; rc=$?
n=$((n+1)); if [ $rc -eq 2 ]; then echo "ok   - stop hook still blocks a failing check when stop_hook_active"; else echo "FAIL - stop hook active rc=$rc"; fails=$((fails+1)); fi
echo '{}' | TMPDIR="$tmp" AUTO_BUILDER_CHECK_CMD="true" "$stop" >/dev/null 2>&1; rc=$?
n=$((n+1)); if [ $rc -eq 0 ]; then echo "ok   - stop hook passes on green"; else echo "FAIL - stop hook green rc=$rc"; fails=$((fails+1)); fi


# ===================== audit-driven additions =====================
rc_is() { # rc_is "desc" expected_rc cmd...   (stdin passes through)
  local d="$1" want="$2"; shift 2; n=$((n+1)); local out; out="$("$@" 2>&1)"; local rc=$?
  if [ $rc -eq "$want" ]; then echo "ok   - $d"; else echo "FAIL - $d (rc=$rc, want $want): $out" | head -3; fails=$((fails+1)); fi
}
hook_in() { printf '%s' "$1" | "$hook"; }

# --- protect-secrets: bypasses found in the audit
for p in '.ENV' '.Env.Local' 'prod.env' '.envrc' '.netrc' 'secrets.yaml' 'terraform.tfvars' 'id_ecdsa' '.git-credentials' 'server.pem' 'x/.aws/config' 'C:\\proj\\.env' 'sub/.env.production'; do
  rc_is "hook blocks $p" 2 hook_in "{\"tool_input\":{\"file_path\":\"$p\"}}"
done
for p in 'app.py' 'secrets.py' '.env.example' '.env.production.sample' 'id_rsa.pub' 'README.md' 'credentials_helper.py'; do
  rc_is "hook allows $p" 0 hook_in "{\"tool_input\":{\"file_path\":\"$p\"}}"
done
rc_is "hook blocks notebook_path"  2 hook_in '{"tool_input":{"notebook_path":"/x/.env"}}'
rc_is "hook: malformed JSON fails open (rc 0)" 0 hook_in 'not json'
rc_is "hook: empty input rc 0"  0 hook_in ''
rc_is "hook: no path rc 0"      0 hook_in '{"tool_input":{"command":"ls"}}'

# --- verify-on-stop: bounded retries, timeout, loud failure
st() { printf '%s' "$1" | env TMPDIR="$tmp" "${@:2}" "$stop"; }
export_sid='{"session_id":"s1"}'
rc_is "stop: fail #1 blocks" 2 st "$export_sid" AUTO_BUILDER_CHECK_CMD=false AUTO_BUILDER_MAX_RETRIES=2
rc_is "stop: fail #2 blocks" 2 st "$export_sid" AUTO_BUILDER_CHECK_CMD=false AUTO_BUILDER_MAX_RETRIES=2
rc_is "stop: fail #3 allowed after max retries" 0 st "$export_sid" AUTO_BUILDER_CHECK_CMD=false AUTO_BUILDER_MAX_RETRIES=2
rc_is "stop: stop_hook_active does NOT bypass a failing check" 2 st '{"session_id":"s2","stop_hook_active":true}' AUTO_BUILDER_CHECK_CMD=false
rc_is "stop: success resets and passes" 0 st '{"session_id":"s2"}' AUTO_BUILDER_CHECK_CMD=true
rc_is "stop: bad CLAUDE_PROJECT_DIR is loud (rc 2)" 2 st '{"session_id":"s3"}' AUTO_BUILDER_CHECK_CMD=true CLAUDE_PROJECT_DIR=/nonexistent-dir-xyz
rc_is "stop: quotes in command ok" 0 st '{"session_id":"s4"}' "AUTO_BUILDER_CHECK_CMD=echo \"it's ok\""
if command -v timeout >/dev/null 2>&1; then
  rc_is "stop: hung check is killed by timeout (rc 2)" 2 st '{"session_id":"s5"}' AUTO_BUILDER_CHECK_CMD="sleep 5" AUTO_BUILDER_CHECK_TIMEOUT=1
fi
big="$(printf '%s' '{"session_id":"s6"}' | env TMPDIR="$tmp" AUTO_BUILDER_CHECK_CMD="head -c 2000000 /dev/zero | tr '\\0' x; exit 1" "$stop" 2>&1 >/dev/null | wc -c)"
n=$((n+1)); if [ "$big" -lt 5000 ]; then echo "ok   - stop: huge single-line output is capped ($big bytes)"; else echo "FAIL - stop: output not capped ($big bytes)"; fails=$((fails+1)); fi

# --- installer: audit findings
h2="$tmp/h2"; mkdir -p "$h2"; HOME="$h2" "$repo/install.sh" --personal >/dev/null 2>&1
echo v1 > "$h2/.claude/agents/architect.md"; HOME="$h2" "$repo/install.sh" --personal --update >/dev/null 2>&1
echo v2 > "$h2/.claude/agents/architect.md"; HOME="$h2" "$repo/install.sh" --personal --update >/dev/null 2>&1
t "update twice: first backup (v1) survives"  grep -q v1 "$h2/.claude/agents/architect.md.bak"
t "update twice: second backup (v2) kept"     grep -q v2 "$h2/.claude/agents/architect.md.bak.1"

mkdir -p "$h2/.claude/skills/auto-builder/workflows"; echo old > "$h2/.claude/skills/auto-builder/workflows/removed.md"
out="$(HOME="$h2" "$repo/install.sh" --personal 2>&1)"
n=$((n+1)); if printf '%s' "$out" | grep -q "STALE.*removed.md"; then echo "ok   - stale file reported"; else echo "FAIL - stale not reported"; fails=$((fails+1)); fi
t "stale file not deleted" test -f "$h2/.claude/skills/auto-builder/workflows/removed.md"

ln -s "$repo/install.sh" "$tmp/inst-link"; pl="$tmp/pl"; mkdir -p "$pl"
t "works when invoked through a symlink" "$tmp/inst-link" --project "$pl"
nt "conflicting modes rejected"          "$repo/install.sh" --personal --project "$pl"
nt "--personal with a dir argument rejected" "$repo/install.sh" --personal "$pl"
pa="$tmp/pa"; mkdir -p "$pa"; t "dir argument after flags accepted" "$repo/install.sh" --project --dry-run "$pa"
pu="$tmp/ünï cödé"; mkdir -p "$pu"; t "unicode project path" "$repo/install.sh" --project "$pu"
mkdir -p "$tmp/-dash"; ( cd "$tmp" && t "leading-dash dir via ./" "$repo/install.sh" --project ./-dash )
( cd "$tmp" && t "relative project path" "$repo/install.sh" --project pa )

pc="$tmp/pc"; mkdir -p "$pc/.claude/agents"; echo real > "$tmp/real-agent.md"; ln -s "$tmp/real-agent.md" "$pc/.claude/agents/architect.md"
"$repo/install.sh" --project "$pc" --update >/dev/null 2>&1; rc=$?
n=$((n+1)); if [ $rc -ne 0 ] && grep -q real "$tmp/real-agent.md"; then echo "ok   - symlinked agent: CONFLICT, target untouched, rc!=0"; else echo "FAIL - symlink handling rc=$rc"; fails=$((fails+1)); fi
pd="$tmp/pd"; mkdir -p "$pd/.claude/agents/architect.md"
nt "directory in place of file: CONFLICT rc!=0" "$repo/install.sh" --project "$pd"

ln -s "$repo" "$tmp/repolink"
nt "self-install guard sees through symlinked dir" "$repo/install.sh" --project "$tmp/repolink"
pr="$tmp/pr"; mkdir -p "$pr"; ln -s "$repo/.claude" "$pr/.claude"
nt "self-install guard sees through symlinked .claude" "$repo/install.sh" --project "$pr"

pro="$tmp/pro"; mkdir -p "$pro"; chmod a-w "$pro"
if [ "$(id -u)" -ne 0 ]; then nt "read-only target gives friendly failure" "$repo/install.sh" --project "$pro"; fi
chmod u+w "$pro"
mkdir -p "$tmp/pnull"; ( cd "$tmp/pnull" && env -u HOME "$repo/install.sh" --personal >/dev/null 2>&1 ); rc=$?
n=$((n+1)); if [ $rc -ne 0 ]; then echo "ok   - HOME unset rejected"; else echo "FAIL - HOME unset accepted"; fails=$((fails+1)); fi
dry="$tmp/dr"; mkdir -p "$dry"; "$repo/install.sh" --project "$dry" --dry-run --update >/dev/null 2>&1
nt "dry-run + update writes nothing" test -e "$dry/.claude"
t "update preserves hook exec bit" test -x "$h2/.claude/skills/auto-builder/scripts/hooks/protect-secrets.sh"

echo
echo "$((n - fails))/$n passed"
[ $fails -eq 0 ]
