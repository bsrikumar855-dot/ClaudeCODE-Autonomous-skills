# Implementation playbook

- Work in small, reviewable slices.
- Read neighboring code and tests before editing.
- Reuse existing libraries and patterns; add dependencies only with justification.
- Keep each subagent's ownership bounded and avoid overlapping edits.
- Use worktrees only when independent parallel work justifies the integration cost.
- Keep interfaces and docs synchronized with implementation.
- Preserve user changes and inspect diffs frequently.
- Only the lead makes local checkpoint commits on the `auto-builder/<slug>` branch after each verified milestone: stage by explicit path, skip files that already had user changes (ask first), never `git add -A`, never commit secrets.
- Do not push, open PRs, publish, or deploy without explicit user authorization.
- After the feature works, simplify: remove dead code, needless abstraction and unused dependencies, then re-run the checks.
