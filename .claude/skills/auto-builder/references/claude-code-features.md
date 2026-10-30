# Claude Code features this skill relies on

Frontmatter fields, hook input fields and exit codes were checked against the official docs on 2026-10-30 (skills, sub-agents, hooks pages; the settings page was not read in full). Products change: re-check before depending on details.

| Feature | Used for | Notes |
|---|---|---|
| **Skills** (`.claude/skills/<name>/SKILL.md`) | This workflow | `disable-model-invocation: true` makes it explicit-invoke only |
| **Subagents** (`.claude/agents/*.md`) | Specialist roles | Frontmatter: `name`, `description`, `tools`, `disallowedTools`, `model`, `maxTurns`, `color`, `isolation`, ... Subagents can't ask the user |
| **CLAUDE.md** | Persistent project conventions | Keep short and factual |
| **Plan mode** | User-driven main-session mode | The skill does not enter it; it just doesn't edit code before `TASKS.md` exists |
| **Hooks** (`settings.json`) | Deterministic checks | Exit code 2 blocks / feeds back stderr; exit 1 does not block. See `scripts/hooks/` |
| **Permissions / sandboxing** | Safety | The skill never asks to bypass them |
| **Git worktrees / `isolation: worktree`** | Parallel isolation | See [parallel-work.md](parallel-work.md) |

## Opt-in hooks shipped here (not auto-installed)

`scripts/hooks/protect-secrets.sh` — PreToolUse hook that blocks Edit/Write/NotebookEdit on secret-bearing file paths (`.env`, keys, credentials, …). It does **not** cover Bash commands or Read; use `permissions.deny` for those.
`scripts/hooks/verify-on-stop.sh` — Stop hook that runs the project's check command (`AUTO_BUILDER_CHECK_CMD`) and sends failures back to Claude. It retries a bounded number of times, then lets Claude stop; it is a strong nudge, not an absolute gate. `stop_hook_active` is a documented Stop-input field.

Enabling them is a deliberate settings change; see the README ("Hooks") for the JSON.

## Consequences of `disable-model-invocation: true`
Claude will not load the skill on its own, it is not preloaded into subagents, and a scheduled/`/loop` re-entry will not trigger it automatically. Only a user typing `/auto-builder` starts it. Do not rely on automatic re-entry; the Resume protocol re-reads state from files instead.

## Recommended permission setup (user-side)
Foreground prompts from subagents pass through to you, so a fully hands-off run needs your tools pre-allowed. Prefer narrow allow rules for your test/lint/build commands. Consider `permissions.deny` rules for `Bash(git push *)` and reads of `.env` files. Do not use bypass modes for this skill.
