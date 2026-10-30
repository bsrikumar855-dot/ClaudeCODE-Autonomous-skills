---
title: "Using AUTO-BUILDER: a goal-driven autonomous workflow for Claude Code"
published: false
tags: claudecode, ai, opensource, productivity
canonical_url: https://bsrikumar855-dot.github.io/ClaudeCODE-Autonomous-skills/usage.html
cover_image: https://bsrikumar855-dot.github.io/ClaudeCODE-Autonomous-skills/assets/og-image.png
---

> Disclosure: I'm the author of AUTO-BUILDER. It's an independent, early-release open-source project (Apache-2.0), not affiliated with Anthropic.

Autonomous coding agents often skip planning, trust their own output, and stop after one green build. **AUTO-BUILDER** is a Claude Code skill with eight subagents that wraps a coding session in a repeatable process. This tutorial installs it and walks through a first run.

## 1. Install

```bash
git clone https://github.com/bsrikumar855-dot/ClaudeCODE-Autonomous-skills
cd ClaudeCODE-Autonomous-skills
./install.sh --project --dry-run /path/to/your/repo   # preview
./install.sh --project /path/to/your/repo
```

On Windows use `.\install.ps1 -Project -Path C:\path\to\repo` (note: the PowerShell installer hasn't been executed by the author yet). The installer never overwrites your files unless you pass `--update`.

Check that `.claude/skills/auto-builder/SKILL.md` and eight files in `.claude/agents/` exist, then start a new Claude Code session in that repo.

## 2. Pick a small goal

Start with something you can verify yourself:

```text
/auto-builder Add a /health endpoint with a test and document it in the README. Do not deploy anything.
```

Good goals state the outcome, constraints, and what *not* to do.

## 3. What happens

1. **Reconnaissance:** it reads the repo, notes git state, and finds your test/lint/build commands. Uncommitted changes are recorded as yours and never committed.
2. **Discovery → planning:** it writes requirements with testable acceptance criteria and a `TASKS.md` under `docs/auto-builder/` containing a Status block, an acceptance checklist with an evidence column, and an iteration budget.
3. **Checkpoint A:** if a consequential choice is involved (or you asked for it) it pauses and summarises direction and risks.
4. **Implementation:** work happens on an `auto-builder/<slug>` branch; only the lead commits, by explicit path.
5. **Verification, one milestone at a time:** each milestone passes a gate (tests, regression checks, evidence) and a separate `critical-reviewer` (and `qa-engineer` for user-facing behaviour) inspects meaningful milestones and the final result. Failures are root-caused, fixed and re-checked, within a bounded loop.
6. **Delivery report:** what was built, what was *actually run*, which criteria are Verified / Partially verified / Untested, whether the review was independent, and what you must do next.

## 4. Review like normal

It never pushes or opens a PR on its own. Inspect `git log` and `git diff main...auto-builder/<slug>`, run the tests yourself, then merge if you're happy.

## 5. Make unattended-ish runs smoother

Foreground permission prompts reach you. Pre-allow your test, lint and build commands in Claude Code permissions (narrow rules, not bypass modes). Optionally enable the shipped hooks (see the README) to block edits to secret files and to run your check command before Claude stops. They are off by default and have documented limits.

## Limitations
Early release; not yet validated end-to-end in live sessions by the author; reviewer/QA agents have Bash and are *instructed* not to modify files; the skill's safety rules are model instructions, not guarantees.

Docs: https://bsrikumar855-dot.github.io/ClaudeCODE-Autonomous-skills/ · Repo: https://github.com/bsrikumar855-dot/ClaudeCODE-Autonomous-skills
