# Verification playbook

For each meaningful slice, select checks proportionate to the risk:

- Unit tests for local logic.
- Integration tests for service and data boundaries.
- Contract tests for APIs and schemas.
- End-to-end/browser tests for critical user journeys.
- Type checks, lint, formatting, and production build.
- Security checks for auth, input handling, secrets, dependencies, and data exposure.
- Accessibility and responsive checks for UI.
- Evaluation datasets and explicit metrics for AI behavior.

Run commands from the repository's documented scripts. Capture exact pass/fail output. Fix failures, rerun, and record skipped checks with reasons. A passing build alone does not prove the feature works.

## Milestone gate checklist

Copy into the milestone's row in `TASKS.md` and tick only what actually happened. Do not start the next milestone until every applicable box is ticked and no blocker/major finding is open.

- [ ] Expected outcome and acceptance criteria were written *before* implementing
- [ ] Relevant tests run (command + result recorded)
- [ ] Lint / type check / build run where the project has them
- [ ] Regression checks re-run (earlier tests still pass); changed files reviewed via `git diff --stat` and the diff
- [ ] Independent review done if required (or "not independent" disclosed)
- [ ] Security gate run if this milestone is in scope (see security.md): no open Critical; every High fixed or user-accepted; Medium/Low tracked
- [ ] Each acceptance criterion marked Verified / Partially verified / Untested with evidence
- [ ] `TASKS.md`, `PROGRESS.md`, `DECISIONS.md`, `TESTING.md` updated
- [ ] No open blocker or major finding

## Evidence vocabulary

| State | Meaning | Required to claim it |
|---|---|---|
| **Verified** | A check you ran passed | The command and the observed result |
| **Partially verified** | Some paths or cases checked | Which were checked and which were not |
| **Untested** | No check was run | Say so; list it as a risk or limitation |

Never upgrade a state without running a new check. "The code looks right" and "the build succeeded" are not evidence for behaviour.

## Reviewer brief (template for `critical-reviewer` / `qa-engineer`)

> You are read-only: do not modify files, install packages, start long-lived servers or write outside a temp directory (your Bash access is not technically restricted, so this is an instruction). `qa-engineer`: return proposed test code inline in your report; the lead writes the files. Review milestone **<name>** in <paths/diff range>. Requirements: `docs/auto-builder/REQUIREMENTS.md`; acceptance criteria and expected outcome: `TASKS.md` row <id>. Compare the implementation with the requirements and list missing or partial functionality. Examine edge cases and failure paths, the architectural decisions in `DECISIONS.md`, and security and reliability concerns. Challenge the assumptions the implementer made (list the ones you find). Do not approve by default: report severity-ranked findings with file:line and a suggested fix, and state exactly what you did **not** check. Do not modify files.

The lead triages findings: blockers and majors must be fixed (then the failed check and regression checks re-run) or reported as blockers (see SKILL.md); minors are logged in `TASKS.md`.

## Failure recovery record

When a check or review fails, write in `PROGRESS.md` before fixing: the failing check, the **root cause** (not the symptom), the smallest fix, and the attempt number (1 of 3; the authoritative counter is the Status block in `TASKS.md`). One record per root cause is enough, and a trivial failure (a typo) may be a single line. If the same failure persists after attempt 3, stop that milestone and record the blocker; do not retry the same approach.
