# Influences, interpretation, and sources

AUTO-BUILDER is an original workflow synthesis.

## Boris Cherny — Claude Code workflows (inspiration)

Practices drawn from public discussion of Claude Code workflows: plan before implementing; give the agent a way to verify its work; keep a concise shared `CLAUDE.md`; delegate bounded tasks; use parallel sessions/worktrees when work is independent; use Git checkpoints; simplify after building.

## Andrej Karpathy — agentic coding (inspiration)

Public commentary on agentic coding motivates: express intent at a high level, delegate meaningful tasks, state success criteria, iterate quickly, keep the human responsible for direction and review, and avoid unnecessary complexity.

## Anthropic — Claude Code engineering

Explore → plan → implement → verify; skills for reusable workflows; subagents for isolated specialist work; hooks for deterministic checks; `CLAUDE.md` for persistent instructions; worktrees for isolation; independent review; least-privilege permissions and sandboxing.

## Authoritative references (checked when this package was prepared)

- Skills: https://code.claude.com/docs/en/skills
- Subagents: https://code.claude.com/docs/en/sub-agents
- Hooks: https://code.claude.com/docs/en/hooks
- Settings: https://code.claude.com/docs/en/settings

## Attribution discipline

These are engineering inspirations, not claims of endorsement. AUTO-BUILDER is an independent community project and is not affiliated with or endorsed by Anthropic, Boris Cherny or Andrej Karpathy. The interpretation of their public guidance here is ours and may be imperfect. Always check current Claude Code documentation before relying on a specific frontmatter field, hook event or tool name.

## How the principles map to this skill

| Principle | Where it shows up |
|---|---|
| Plan before implementing (Claude Code workflows) | Phases 1–4, Checkpoint A, plan mode |
| Verify rather than trust | Phase 6, `workflows/verification.md`, independent reviewers |
| Parallel sessions / worktrees, only when independent | `references/parallel-work.md` |
| Persistent project knowledge | `docs/auto-builder/` state files, concise `CLAUDE.md` additions |
| Git checkpoints and review | Work branch + local checkpoint commits, never pushed |
| Simplify after implementation | Phase 8 pre-delivery simplification |
| High-level goals, delegate meaningful tasks (agentic coding) | `$ARGUMENTS` goal intake, subagent briefs |
| Human oversight of product decisions | Checkpoint A and the approval policy |
| Avoid premature complexity | Principle 3; "spawn only what's needed" |
| Skills, subagents, hooks, CLAUDE.md, permissions | Repo layout; opt-in hooks; no permission bypass |
