# Parallel work and isolation

Parallelism costs integration effort. Use it only when tasks are independent.

## When to parallelise
- Research questions that don't depend on each other.
- Modules with disjoint file ownership and a fixed interface (agree the API contract first, then fan out frontend and backend).
- Independent review passes on a finished diff.

## When not to
- Tasks touching the same files, schema or lockfile; designs still undecided; tasks where briefing costs more than doing.

## Coordination rules
1. Fix shared interfaces (API schema, types, DB schema) **before** fanning out.
2. Every implementer brief lists the exact files/directories it owns and says: touch nothing else; do not run git add/commit/checkout/stash; do not install dependencies or edit lockfiles/shared config; do not edit `docs/auto-builder/`.
3. Only the lead commits, installs dependencies, and edits shared files and state docs. This also avoids `.git/index.lock` races.
4. These agents are safe to run concurrently on file edits because they have no edit tools: researcher, architect, product-manager, critical-reviewer, qa-engineer. Caveat: running tests and builds can write caches, build output, databases or ports; do not run two test/build runs that share those at once.
5. After integrating, run `git diff --stat` and confirm each changed file belongs to its owner; investigate anything else.

## Worktree isolation (exception, not default)
`isolation: worktree` is a documented subagent frontmatter field. Caveats: it needs a git repository (no fallback for non-git projects); a fresh worktree lacks untracked files such as `node_modules` and `.env`; the docs describe it as branching from the default branch, so it may **not** contain your earlier unmerged slices on `auto-builder/<slug>` (not verified here); results must be merged back by the lead, then the full checks re-run on the merged result. No agent here sets `isolation`; use it only after confirming what the worktree contains.

## Parallel human-driven sessions
For large efforts the user can run several Claude Code sessions in separate git worktrees and branches, with one lead session owning `TASKS.md`. AUTO-BUILDER does not start these itself.
