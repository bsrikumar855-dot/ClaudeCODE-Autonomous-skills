# AUTO-BUILDER repository

This repo *is* a Claude Code skill package. Source of truth: `.claude/skills/auto-builder/` (skill) and `.claude/agents/` (subagents). Installers (`install.sh`, `install.ps1`) copy those into a user's `~/.claude` or a project's `.claude`.

## Checks (run before finishing any change)
- `bash tests/run-all.sh` — runs everything below (use it as the commit gate)
- `python3 -I tests/validate.py` — frontmatter, links, script syntax, hygiene
- `bash tests/test-install.sh` — installer behaviour in temp dirs (never touches real `~/.claude`)

## Conventions
- Only use Claude Code frontmatter fields documented at code.claude.com/docs (skills, sub-agents). Unknown keys are silently ignored, so typos fail silently — the validator checks them.
- Keep `SKILL.md` under 500 lines; put detail in `workflows/` or `references/` and link it.
- Installers must never overwrite existing user files without `--update`/`-Update`.
- Keep `install.sh` and `install.ps1` behaviourally equivalent.
- No secrets, local paths, or endorsement/benchmark claims in any file.
