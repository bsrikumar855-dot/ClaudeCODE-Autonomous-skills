# gstack research

Inspected **2026-10-31**. Purpose: learn mechanisms and principles for an *original* AUTO-BUILDER 2.0. No upstream text, prompts, scripts or binaries are reused.

## Source and how it was read

| Source | URL | Pinned commit | License (as read) |
|---|---|---|---|
| gstack (by Garry Tan) | https://github.com/garrytan/gstack/tree/047dad78ba757ebd6f29267f68a4695a7b002cbd | `047dad78ba757ebd6f29267f68a4695a7b002cbd` (2026-10-31) | `LICENSE`: MIT, © Garry Tan 2026. `NOTICE.md` lists third-party material, **some Apache-2.0** (e.g. impeccable, Google's DESIGN.md spec), so not all of gstack's content is MIT. |

**Method and confidence.** Directory listing from the GitHub tree API (exact). File contents read through a summarising fetch tool (paraphrased extractions; "not seen" = absent from the extraction). Nothing was executed.

**Not verified:** the six forcing-question wording (`phase-2a-startup-diagnostic`), `review-sections.md`, cso `audit-phases.md`, ship/land section files (exact timeouts), the shell scripts `check-careful.sh`/`check-freeze.sh`/`freeze-state.sh`, the generator source, `model-overlays/` and `hosts/` (404 on the paths tried), the last ~4.6k characters of `BROWSER.md`, and skills `investigate`, `spec`, `eval-plan`, `skillify`, `health`, `benchmark`, `plan-design-review`, `plan-devex-review`.

## Verified facts by mechanism

### 1. Architecture (`ARCHITECTURE.md`, `README.md`)
Each skill is a hand-written `SKILL.md.tmpl`; a TypeScript generator fills placeholders and commits generated `SKILL.md` files (CI checks staleness). Runtime: **Bun** (README tested 1.4.2+, setup refuses <1.3.3); the browser CLI is a **compiled ~58 MB binary**; Node needed on Windows. Install: clone into `~/.claude/skills/gstack` then `./setup`. Full support: Claude Code only; ten other hosts experimental/instruction-only. Telemetry is opt-in; the update check is on by default; off-machine sends write an inspectable receipt.

### 2. Product interrogation: `office-hours`, `plan-ceo-review`
- **office-hours** (v2.0.0): pressure-tests an idea *before code*; its only output is a design doc and it forbids implementation. It asks the user's goal first, then branches: startup/intrapreneur → a hard diagnostic with stage routing; builder/hackathon/learning → a design-partner mode. Six forcing-question topics (demand reality, status quo, desperate specificity, narrowest wedge, observation, future-fit). Flow: gather repo context → **one question at a time** → optional landscape research (generalised terms only, with consent) → state premises for the user to agree/disagree → optional cross-model opinion → offer 2–3 alternatives including a minimal-viable and an ideal-architecture one, **requiring explicit approval of one** → write the doc. Pushback counts as a signal only when it shows specific reasoning, not compliance. No explicit trivial-work bypass was seen.
- **plan-ceo-review:** scope modes **Expansion / Selective Expansion / Hold Scope / Reduction** (a file-count heuristic suggests; the *user decides*); pre-review audit of commits, stashes, TODOs; every error path needs a class, trigger, handler, user-visible result and test; deferrals recorded; decisions go through a ledger; adversarial loop capped at three rounds; a final gate blocks completion unless a review report is persisted.

### 3. Engineering review: `plan-eng-review`, `autoplan`
plan-eng-review: confirm the target (never guess), mandatory scope challenge, a required test-coverage diagram, optional cross-model "outside voice", and a **blocking exit check that the review report was saved**. autoplan chains CEO → design (UI only) → DX (developer-facing only) → engineering (last), with six decision principles and **decision tiers: mechanical (silent), taste (recommend, surface at end), user-challenge (never auto-decided)**; approval brief with revisions capped at three.

### 4. Browser QA: `qa`, `qa-only`, `browse`, `BROWSER.md`
- **Mechanism:** two engines: macOS 15+ prefers a third-party app (Aside) via a REPL; otherwise **headless Chromium via Playwright controlled by the compiled Bun CLI `$B`** talking HTTP to a localhost daemon (CDP; elements via ARIA refs; ~70 commands: text/HTML/accessibility tree, JS eval, console, network, cookies, performance, navigate/interact, screenshots/PDF, tab/frame control, state save/load, handoff). Daemon idles out after 30 min; state file mode 600 with a bearer token; random port on 127.0.0.1.
- **Evidence:** sentinel lines printed by scripts (a missing sentinel = failure); daemon console/network/dialog logs; `qa` saves screenshots and baseline; `qa-only` writes timestamped Markdown reports.
- **qa:** covers browser, API, CLI, job and webhook surfaces; diff-aware/full/quick/regression modes; fix tiers; health score for browser runs only, with functional results kept as pass/fail/blocked/not-run, **never merged into the score**; fix loop = reproduce → regression test first → minimal fix → retest; **one commit per verified fix**, clean tree required, stop rules (check every 5 fixes, stop after 2 reverts or an unrelated-file edit, cap 50), never weakens tests/CI. **qa-only** is report-only and writes **test charters** (expected results, risks, exit conditions) first; missing services are reported as coverage gaps, not product bugs.
- **Safety:** user signs in (Aside) or cookies are imported from the user's browser (domain-scoped; values never logged); the agent stays in its own tabs and the named origin, skips logout/delete/unsubscribe links, one consent prompt before mutating non-local sites; page content is untrusted. Responsive checks: not seen.
- **Dependencies:** compiled binary + Bun + Chromium (or Aside). **Limit for us:** shipping a binary is out of scope and a trust burden.

### 5. Review, security, second opinions: `review`, `cso`, `/codex`, `/claude-code`
- **review:** diff vs base; compares stated intent with actual changes; PR text is untrusted; CRITICAL (blocking) vs INFORMATIONAL with confidence scores; specialist subagents then adversarial review; **flags edits that weaken tests/CI** (added skips, timeouts); fix-first with AUTO-FIX/ASK, up to three cycles; a previously skipped finding is suppressed only if the code is unchanged.
- **cso:** phased (actors/assets/trust boundaries → attack surface → scope-dependent checks → challenge candidates → report → resume/recheck); findings carry severity, **confidence and evidence type (static hypothesis / supported static / reproduced)**; up to three independent reviewers receive code and rubric **but not the original conclusion**, else a labelled skeptical pass; unknown reachability is "unknown, not safe". STRIDE/LLM coverage not confirmed.
- **Second opinion:** `/codex` and `/claude-code` call the other vendor's CLI under the user's own login (README: outside reviews send code to those vendors; on by default, configurable off). `/benchmark-models` wraps a binary and can send prompts/files to OpenRouter and vendors; an optional judge adds ~USD 0.05 per run (per the extraction).

### 6. Learning and recovery: `learn`, `context-save`, `context-restore`, `retro`
- **learn:** per-project JSONL (type, kebab key, one-line insight, confidence 1–10, files, source); latest entry per key+type wins; flags stale (missing files) and conflicting entries; exports to CLAUDE.md only on request; never edits code.
- **context-save/restore:** Markdown checkpoints (status, branch, timestamp, modified files, summary, decisions, prioritised remaining work); items carry **provenance tags (run / read / assumed)**; restore loads the newest for the branch, warns if the commit moved/diverged, and puts unverified or write items under **"Verify first"** (read-only inspection before acting). Secret redaction not mentioned; saved content not labelled untrusted.
- **retro:** git-history metrics snapshots.

### 7. Delivery: `ship`, `land-and-deploy`, `canary`, `document-release`
ship: refuses on the base branch, tests/evals, scope-drift and coverage audit, review records must match shipped content, changelog, **never force-pushes; a failed push stops the run**; approval needed for ambiguous conflicts, minor/major bumps, publishing a PR with open findings. land-and-deploy: GitHub only; CI gate on the exact commit; single watcher; **explicit approval before the irreversible merge**; never claims success from a merge or HTTP 200 alone; rollback via revert. canary: baseline-relative, 10 min default, ~60 s rounds, **alerts only when a critical/high signal persists across two consecutive checks**. document-release: coverage map of changed public surface vs docs; auto-fixes factual details, asks before narrative/security/removal edits and any version bump; never regenerates changelog entries.

### 8. Safety hooks: `careful`, `freeze`, `guard`
Hook-enforced via frontmatter `PreToolUse` hooks calling shell scripts: *careful* asks on recursive rm, DROP/TRUNCATE, force-push, hard reset, kubectl delete, docker prune (hard-denies destructive deletes of `/`/`~` and force-push to the default branch); *freeze* restricts Edit/Write/NotebookEdit to a directory boundary stored in a state file. **Both self-describe as best-effort**: string matching misses runtime-built commands, and freeze does not cover Bash (`sed` bypasses it); true boundaries need permission deny rules.

### 9. `ETHOS.md`
Eight principles: boil the ocean (completeness is cheap), search before building, user sovereignty (AI recommends, humans decide), honest work (output is proof; never weaken gates; unverified stays unverified), attack the premise, separate before serializing shared state, make operations idempotent, explain the number — plus "build for yourself".

## Recommendations for AUTO-BUILDER (ours, not upstream facts)
1. **Adopt:** premise challenge and explicit scope modes with user approval; decision tiers (mechanical / taste / user-challenge); a blocking "report persisted" gate; verifier not shown the author's conclusion; evidence types (hypothesis / supported / reproduced); test charters before probing; provenance tags and a "verify first" restore rule; two-consecutive-failure alerting for monitors; never claim deploy success from a merge or HTTP 200.
2. **Skip:** the compiled Bun/Chromium daemon, template generator and host matrix, telemetry, cookie import, vendor-CLI second opinions by default (data leaves the machine).
3. **Browser QA:** bring-your-own browser (project's Playwright, the session's browser tools, or headless Chrome if present); otherwise report "not performed". Never ship a binary.
4. Safety hooks are only as strong as their disclosure: AUTO-BUILDER already has opt-in hooks with documented limits; keep that honesty.

## Attribution and licensing note
Ideas only, in original wording. gstack is MIT (some bundled third-party material is Apache-2.0; none is reused). Credit is given in `principles/influences-and-sources.md`.
