# Launch announcement (draft)

**Title:** AUTO-BUILDER: a goal-driven autonomous development skill for Claude Code

I built AUTO-BUILDER because autonomous coding agents often skip planning, trust their own output, and either ask permission for everything or for nothing. It is a Claude Code skill (`/auto-builder`) with nine subagents that follows a fixed lifecycle:

1. Reconnaissance and discovery
2. Requirements with testable acceptance criteria
3. Architecture and an execution plan in a persistent task file, split into milestones with verification gates
4. Implementation on a work branch (only the lead commits)
5. Verification with real test runs and regression checks, then an **independent** reviewer at meaningful milestones, plus a read-only security engineer agent for projects with security risk
6. A bounded, root-cause-driven fix loop, and a delivery report that labels each criterion Verified, Partially verified or Untested

It asks before deploying, spending money, destructive data operations, handling secrets, or pushing. The installers are non-destructive and support dry runs; the repo ships its own validation and installer tests.

**What it is not:** it is not official, not a background service, and not proven. It has not yet been run end-to-end in live sessions by me, and the Windows installer hasn't been executed. I'd value feedback from people who try it on a small project.

- Repo: https://github.com/bsrikumar855-dot/ClaudeCODE-Autonomous-skills
- Docs and tutorial: https://bsrikumar855-dot.github.io/ClaudeCODE-Autonomous-skills/
- Licence: Apache-2.0
