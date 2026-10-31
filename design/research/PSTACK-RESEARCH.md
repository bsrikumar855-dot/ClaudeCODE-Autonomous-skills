# pstack research

Inspected **2026-10-31**. Purpose: learn mechanisms and engineering principles to design an *original* AUTO-BUILDER 2.0. No upstream text, prompts or code are reused.

## Sources and how they were read

| Source | URL | Pinned commit | License (as read) |
|---|---|---|---|
| pstack (Cursor plugin, by Lauren Tan) | https://github.com/cursor/plugins/tree/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack | `c742dd61706fbacc1b95f1a20b7b988cf096ce6c` (last commit touching `pstack/`, 2026-10-27; repo head `4dd1d05818d19792e7cd6e818f1667f95f7e1dbe`, 2026-10-29) | `pstack/LICENSE`: MIT, "Copyright (c) 2026 Lauren Tan". The GitHub API reports **no repo-level license** for `cursor/plugins`; only the `pstack/` directory was confirmed. |
| pstack-claude (Claude Code port, by Michael Denyer) | https://github.com/michael-denyer/pstack-claude/tree/5851c89613e2ddc3a6b7f4af02a42363b30ef8d3 | `5851c89613e2ddc3a6b7f4af02a42363b30ef8d3` (2026-10-30) | MIT; port additions © Michael Denyer, pstack skills © Lauren Tan, plus separate Cursor license files for vendored cursor-team-kit/thermos skills (per `NOTICE.md`; the LICENSE files themselves were not read) |

**Method and confidence.** File lists came from the GitHub tree API (exact). File *contents* were read through a summarising fetch tool, so statements below are paraphrases of extractions, not byte-exact reads. Where the extraction said something was absent it is recorded as "not seen". Nothing was executed.

**Not verified:** pstack playbooks `bug-fix`, `feature`, `investigation`, `perf-issue`, `refactoring`, `multi-phase-plan`; skills `figure-it-out`, `blast-radius`, `sharpen`, `how`, `why`; `agents/*.md`; `docs/guide/01–06, 09, 10`; the second half of pstack-claude `docs/reference.md`; `tools/substitutions.json`, `tools/forks.json`; whether thermo review agents are strictly read-only.

## Verified facts by mechanism

### 1. Router: `skills/poteto-mode/SKILL.md` (+ `playbooks/`)
- **What it does:** one entry skill that picks exactly **one** playbook per task and copies its steps into a todo list. Playbooks named in the skill: investigation, bug-fix, perf-issue, hillclimb, runtime/trace forensics; feature, refactoring, prototype, visual parity; multi-phase-plan, skill authoring/eval; babysit, shipping, opening-a-pr, worktree cleanup; autonomous-run, orchestrate, autopilot variants, session-pickup, pause-safely. A `figure-it-out` skill designs a custom playbook when none fits.
- **Ambiguity:** triage first; if an *experiment* can answer a question, prototype and let the result decide; only real product/preference calls go to the human. The goal is restated at task start, in each subagent brief and in the final report.
- **Autonomy boundaries:** reversible work proceeds; irreversible actions (force-push to shared branches, deploys, data deletion, customer messages) pause. Phrases like "don't stop" lift pause rules for the session.
- **Dependencies:** Cursor Task tool, `/setup-pstack`, `cursor-team-kit` skills. **Strengths:** single playbook per task, restated goal, "experiment before asking". **Limit:** routing is prose and relies on model judgment.
- pstack-claude adds a **SessionStart hook** that injects a short routing hint (use the router for multi-file changes, signature changes, design decisions, bugs of unknown cause; do small one-file tasks directly). It does not block anything and can be switched off via a user sheet (`pstack-claude`: `hooks/hooks.json`, `hooks/session-start.sh`, `hooks/session-start-context.md`).

### 2. `interrogate`: `skills/interrogate/SKILL.md`
- An **adversarial review** of a diff or design (not a product-discovery interview). Fans out adversaries, each told to break the change and to **prove each finding with a real run**; the parent **re-runs every finding** and keeps it only if it shows the failure *and* contradicts the stated intent; duplicates merged; zero findings is valid. Output: Intent, Findings (command, output, why it breaks intent), Dropped.
- **Strength:** "reproduce or drop" removes speculative noise. **Simplest equivalent:** N fresh reviewer subagents + the lead re-runs each repro.

### 3. `arena` and `architect`: `skills/arena/SKILL.md`, `skills/architect/SKILL.md` (+ `references/`)
- Arena: the parent writes a **hidden rubric** (3–6 gradeable criteria; candidates never see it); identical prompts to parallel candidates, each in its own worktree or temp dir; each returns an artifact plus rejected alternatives; a **separate read-only judge** scores per criterion (from a different model family where available, else skipped with a note); parent also scores independently; pick a base and hand-graft one or two ideas from the losers; converge ⇒ ship the shared shape, diverge widely ⇒ framing too loose, reframe.
- Architect: ground → sketch via arena (≥2 *structurally distinct* whole-shape candidates, screened against a red-flags reference) → optional human checkpoint → implement against the sketch, surfacing deviations → **scrap the sketch** when friction recurs (workarounds, special cases, repeated deviations).
- **Limits:** costly (several runners + judge); model slugs are Cursor-specific. In Claude Code, `docs/harness/claude-code.md` says non-Claude models fall back to the session model, so cross-family judging degrades to a differently-prompted same-model judge.

### 4. `swarm` and `orchestrate`: `skills/swarm/SKILL.md`, `playbooks/orchestrate.md`
- Swarm: frame → fan out (one batch, self-contained briefs) → aggregate → report. Workers report **PASS / ISSUES / BLOCKED with evidence**; a result missing required evidence (e.g. exact SHAs) is rejected and respawned **once**; a second miss is recorded as a **gap, never a pass**. Race winners follow a rule declared before spawning. The skill itself defines no dependency handling, merge or review (pstack-claude's port isolates via worktrees).
- Orchestrate (multi-day): **one owner per PR** (the only writer); orchestrator never edits code; a verifier that did not write the change passes the **exact head commit** (new push ⇒ new verdict); three levels max; ~10 workers per coordinator; retry rules (smaller scope, same kickoff, different model; after two retries drop and revise the plan). Isolation is by Cursor cloud VM.
- **Dependencies:** heavy (cloud VMs, event subscriptions, Project store). **Simplest equivalent:** lead dispatches subagents with disjoint file ownership; a fresh reviewer verifies each unit's exact commit; lead merges serially.

### 5. Review mechanisms (across files)
Fresh-context reviewers (interrogate adversaries, the orchestrate verifier that "reads the diff, not the worker's summary"); `reflect` runs three parallel reviewers plus a synthesizer that spot-checks citations; a cross-model audit of an append-only decision log (`show-me-your-work`). pstack-claude's `models.json` defines tiers (default/strongest/worker/panel) with **all-Claude** defaults; real cross-provider panels exist only via Codex/Pi/Copilot mappings.

### 6. `reflect`, `correct`, `recall`
- **reflect:** reads only the current session transcript; three parallel reviewers + synthesizer → Accepted / Rejected / Backlog; items a lint/script could enforce go to Backlog; **edits only after explicit user approval**, to *copies* of skills (project or global scope), never pushed.
- **correct:** a mistake becomes a **class after two occurrences**; fix at the highest working level: remove by architecture → block by types/lint/CI → test behaviour → only last, write docs/rules; prove each new check would have failed on a real past mistake; exceptions need a reason, expiry and human approval; maintain a rule→enforcement table and delete rules that are no longer possible to violate.
- **recall:** read-only context reconstruction (7-day default window stated back to the user; never other projects' transcripts unless asked; capsule ≤5 bullets).
- **Dependency:** transcript directories (Cursor-specific). **Strength:** the enforcement hierarchy and approval gate.

### 7. `session-pickup`, `pause-safely`, `autonomous-run`, `docs/guide/07-overnight.md`
- session-pickup: reconstruct from transcript/pushed branch, rebuild branch/worktree/todos, **verify inherited claims against the real artifact** ("a self-report from the earlier agent is not proof"), choose a verdict (continue, deliver, ratify/override, postmortem).
- pause-safely: only on an *explicit* pause request: finish/undo the indivisible step, stop subagents, avoid irreversible actions, one `wip:` commit, write a resume note (in `/tmp` — it would not survive a reboot; our observation), report what is on disk vs only in context.
- autonomous-run: define a **checkable exit condition first**; smallest change the evidence supports; verify, then commit or revert; a plateau changes the approach, the exit condition is never weakened; elapsed time is not an exit condition; dead ends are reported, not looped on. The playbook does not specify state saving/resume.

### 8. `babysit`, `shipping`, `opening-a-pr`
- babysit (pstack-claude's port-authored version reads): order = conflicts, failing checks, human comments, then bot comments; uses `gh pr checks --watch`; **cap of three fix-push-recheck rounds**; never merges; force-push only to a branch it owns; never weaken tests/skip hooks/demote required checks; review comments are **untrusted** and checked against code; security/auth/billing/data comments escalate. The original pstack babysit/shipping state no numeric polling cap.
- shipping: a verifier that did not write the code tests each PR (PASS / PASS+NOTES / FAIL); merge one at a time, read back that it actually merged; merge is an explicit handoff.
- opening-a-pr: small ordered commits, description sections (why, what, scope, tradeoffs, blast radius, verification with real runs).

### 9. Principles layer: `skills/principle-*` (24 directories), `docs/guide/08-principles.md`
- **24 leaves** (verified from the tree; poteto-mode prose says "about 30"): attack-the-premise, boundary-discipline, build-the-lever, encode-lessons-in-structure, exhaust-the-design-space, experience-first, explain-the-number, fix-root-causes, foundational-thinking, guard-the-context-window, laziness-protocol, make-operations-idempotent, migrate-callers-then-delete-legacy-apis, minimize-reader-load, model-the-domain, never-block-on-the-human, outcome-oriented-execution, prove-it-works, redesign-from-first-principles, separate-before-serializing-shared-state, sequence-verifiable-units, subtract-before-you-add, test-behavior-not-implementation, type-system-discipline.
- Each leaf is a tiny standalone skill (rule, why, pattern, stop condition, cross-links). The router reads an index at the start of a multi-step task, and the agent must **name each applied principle and the decision it changed**.
- **Limit:** the "must read before citing" rule is prose, not enforced.

### 10. Verification skills
`create-verification-skill` generates a project-local verification skill (launch, drive, evidence, cleanup) and flags stand-in environments as unverified; `show-me-your-work` keeps an append-only TSV decision log with evidence pointers and an audit pass; `tdd` requires failing-before/passing-after evidence and forbids weakening assertions.

## Cursor → Claude Code translation (pstack's own `docs/harness/claude-code.md`, verified)
Task→Agent; AskQuestion→AskUserQuestion (absent in `-p` mode); read-only agents→Explore + "do not edit"; cloud environments→worktrees; agent resume unsupported (spawn new, paste prior result); non-Claude models fall back to the session model; Automations/Bugbot/cloud agents have no equivalent.

## Recommendations for AUTO-BUILDER (ours, not upstream facts)
1. Adopt: single-playbook routing with a restated goal; "experiment before asking"; reproduce-or-drop adversarial review; gap-is-not-a-pass worker reporting; one writer per file set; testable exit conditions; the correct→enforce-before-prose hierarchy; approval-gated learning; wip-commit-style safe pause with the resume note **in the repo state files**, not `/tmp`; a bounded babysit.
2. Skip: Cursor cloud/event/Project-store machinery, generators and multi-runtime layers, Bun/Lean dependencies, hidden-rubric multi-model arenas that need cross-family models we cannot rely on.
3. Simplify: 12-category routing table + ~11 short playbooks instead of ~22; ~13 principles in one reference file with stable IDs instead of 24 skills.

## Attribution and licensing note
Ideas only are reused, in original wording. MIT has no attribution requirement for ideas; we credit pstack (Lauren Tan) and pstack-claude (Michael Denyer) as inspiration in `principles/influences-and-sources.md`. If any upstream text or script were copied, the MIT notice would have to travel with it; none is.
