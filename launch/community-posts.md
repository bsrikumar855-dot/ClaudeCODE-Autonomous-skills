# Community post drafts

General rules: post once per community; read each community's current self-promotion rules first (they change); disclose that you're the author; don't ask for upvotes, stars or reviews; reply to critique with specifics; don't cross-post identical text everywhere on the same hour.

---
## Hacker News (Show HN)
Check the current Show HN guidelines first: it must be something people can try, with no sign-up, and the title shouldn't use marketing language.

**Title:** `Show HN: AUTO-BUILDER – a Claude Code skill that plans, builds, and reviews from a goal`

**First comment (post immediately after submitting):**
> I made this because I kept seeing coding agents jump to code and call it done after one green build. AUTO-BUILDER is a Claude Code skill plus nine subagents that runs: reconnaissance → requirements with acceptance criteria → architecture → task plan in a file → implementation on a branch → verification → independent review → bounded fix loop → report.
>
> Design choices: state lives in files (so it survives context compaction), only the lead commits, reviewers have no edit tools (QA/reviewer have Bash, so that part is instructed, not enforced), and it asks before deploys/spend/destructive ops/pushing.
>
> Honest status: tests cover the installers, hooks and static checks, but I haven't validated the whole skill end-to-end in live sessions yet, and the PowerShell installer is unexecuted. Rules in the skill are instructions to the model, so permissions/sandboxing still matter. Happy to hear where the design is wrong.
> Repo: https://github.com/bsrikumar855-dot/ClaudeCODE-Autonomous-skills

---
## Product Hunt
Check current guidelines (maker account, no vote manipulation). A free open-source dev tool is fine; schedule a launch day you can attend.
- **Name:** AUTO-BUILDER
- **Tagline (≤60):** Goal-driven autonomous dev workflow for Claude Code
- **Description (≤260):** Open-source Claude Code skill with 9 subagents. Give /auto-builder a goal; it plans, builds, verifies, gets an independent review and reports, pausing only for consequential decisions. Apache-2.0.
- **Topics:** Developer Tools, Open Source, Artificial Intelligence, GitHub
- **Maker comment:** "I built this to make autonomous coding sessions more repeatable: plan first, evidence for every claim, a separate reviewer, and approvals only where it matters. It's early: I haven't validated it end-to-end in live sessions and the Windows installer is untested. Feedback on the lifecycle and safety rules is welcome."
- **Media:** the 1280×640 `og-image.png`; a short screen recording of a real run once you have one (don't use mock-ups presented as real).

---
## Reddit (e.g. r/ClaudeAI; check each subreddit's rules and any self-promotion thread)
**Title:** I made an open-source Claude Code skill + 9 subagents that follows plan → build → verify → independent review (early release, feedback wanted)

> Disclosure: I'm the author. AUTO-BUILDER adds `/auto-builder`, which runs a fixed lifecycle with a persistent `TASKS.md` (status, acceptance checklist with evidence, iteration budget), least-privilege subagents, a required independent review, and approval checkpoints for risky actions. Installers are non-destructive and have dry-run.
> Limits: not validated end-to-end in live sessions yet; Windows installer unexecuted; reviewer/QA have Bash (instructed read-only).
> Repo + docs: https://github.com/bsrikumar855-dot/ClaudeCODE-Autonomous-skills
> I'd especially like critique of the approval policy and the subagent tool lists.

---
## LinkedIn
> I released AUTO-BUILDER, an open-source skill for Claude Code that turns a goal into a planned, tested and independently reviewed change set.
>
> The idea is process, not magic: plan with acceptance criteria first, keep project state in files, use specialist subagents with least-privilege tools, require a separate reviewer, and only interrupt the human for consequential decisions (deploys, spend, destructive data ops, secrets, pushes).
>
> It's an early release: static checks and installer tests pass; live end-to-end validation is still ahead, and I say so in the docs. Apache-2.0.
> https://bsrikumar855-dot.github.io/ClaudeCODE-Autonomous-skills/
> #ClaudeCode #AIEngineering #OpenSource #DeveloperTools

---
## X (thread)
1. I open-sourced AUTO-BUILDER: a Claude Code skill + 9 subagents. `/auto-builder <goal>` → plan → build → verify → independent review → report. Early release, Apache-2.0. https://github.com/bsrikumar855-dot/ClaudeCODE-Autonomous-skills
2. The part I care about most: it can't mark things done without evidence. `TASKS.md` has an acceptance checklist with an evidence column, a bounded fix loop and an iteration budget.
3. Safety: asks before deploys, spend, destructive data ops, secrets, pushes. Reviewer/architect/QA have no edit tools. Honest caveat: rules are model instructions; permissions/sandboxing still matter.
4. Status: tests cover installers/hooks/static checks; not yet validated in live sessions; Windows installer unexecuted. Feedback welcome: https://bsrikumar855-dot.github.io/ClaudeCODE-Autonomous-skills/
