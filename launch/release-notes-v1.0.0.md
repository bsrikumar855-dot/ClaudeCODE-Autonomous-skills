# Release notes draft: v1.0.0

> **Decision for you before tagging.** The repository currently declares version **0.1.0** (`CHANGELOG.md`, `SKILL.md` metadata, site footer) and the skill has not been validated in live Claude Code sessions. A `1.0.0` tag signals a stable, supported release. I recommend either (a) tagging **v0.1.0** as the first public release, or (b) running a few real `/auto-builder` sessions first and tagging 1.0.0 afterwards. If you choose 1.0.0 now, bump `CHANGELOG.md` (rename *0.1.0 – Unreleased* to *1.0.0 – date*) and `metadata.version` in `SKILL.md`, rebuild the site (`python3 -I site/build.py`), and keep the limitations section below. I have not changed any version numbers.

---

## AUTO-BUILDER v1.0.0

AUTO-BUILDER is an open-source Claude Code skill plus nine specialist subagents for goal-driven autonomous development. Run `/auto-builder <goal>`; it plans, builds, verifies, independently reviews and documents the work, pausing only at consequential checkpoints.

### Highlights
- **`/auto-builder` skill** with a nine-step lifecycle (Phase 0–8): reconnaissance, discovery, product definition, architecture, execution planning, implementation, independent verification, bounded iteration, delivery.
- **Nine subagents** with least-privilege tools: product-manager, researcher, architect, frontend-engineer, backend-engineer, ai-engineer, qa-engineer, security-engineer, critical-reviewer.
- **Quality protocol:** milestones with verification gates, independent review at meaningful checkpoints, Verified / Partially verified / Untested evidence labels, root-cause failure recovery and a completion standard. These are instructions to the model, not guarantees.
- **Security gate:** for projects with security risk, a read-only `security-engineer` threat-models the design, reviews security-relevant milestones and does a final review. Critical findings block completion and cannot be accepted; High findings need a fix or the user's explicit acceptance, recorded as open residual risk (never as fixed); reports state whether they rest on static inspection, automated scanning or penetration testing. Never reported as "secure"; instructions, not guarantees.
- **Persistent state** in `docs/auto-builder/` (task status and milestone gates, acceptance checklist with evidence, decisions, progress log) and a resume protocol for long runs.
- **Approval policy:** asks before destructive data operations, deploys, spending, secrets, pushing or direction changes.
- **Git behaviour:** work branch, lead-only checkpoint commits by explicit path, never commits your uncommitted changes, never pushes.
- **Installers** for Linux/macOS/WSL/Git Bash and Windows PowerShell: personal or project scope, `--dry-run`, non-destructive by default, `--update` with numbered backups, conflict and stale-file reporting.
- **Optional hooks** (off by default): secret-file edit protection and verify-before-stop.
- **Website:** https://bsrikumar855-dot.github.io/ClaudeCODE-Autonomous-skills/

### Install
```bash
git clone https://github.com/bsrikumar855-dot/ClaudeCODE-Autonomous-skills
cd ClaudeCODE-Autonomous-skills
./install.sh --personal      # or --project /path/to/repo ; Windows: .\install.ps1 -Personal
```

### Quality evidence
- `tests/validate.py`: static validation (frontmatter, links, scripts, hygiene).
- `tests/test-install.sh`: installer and hook behaviour in temp directories.
- `site/check.py`: website metadata, links, sitemap, structured data.
- An independent review pass (reviewer, architect and QA roles) was run before release and its high-priority findings fixed.

### Known limitations
- Not yet validated end-to-end in live Claude Code sessions.
- `install.ps1` has not been executed on Windows by the author.
- Reviewer and QA agents have Bash, which cannot be technically restricted; they are instructed not to modify files.
- The secret-protection hook covers Edit/Write/NotebookEdit paths only, not Bash or Read.
- Worktree isolation for parallel agents is not verified.
- Safety rules are instructions to the model; use Claude Code permissions and sandboxing for enforcement.

### Licence
Apache-2.0. Independent project; not affiliated with or endorsed by Anthropic.
