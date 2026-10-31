# Changelog

All notable changes to this project are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/); versioning follows [Semantic Versioning](https://semver.org/).

## [0.1.0] - Unreleased

### Added (AUTO-BUILDER 2.0 architecture)
- **Task router** (12 categories, trivial bypass, add-only gates) with `workflows/router.md` and 8 short playbooks; routing eval set (`tests/fixtures/routing-eval.json`, labelled NOT RUN).
- Normative **Untrusted-data** rule, a single **Limits** section, per-milestone `Verified at` and `Flags` in the `TASKS.md` template.
- Product interrogation (in `discovery.md`), architecture arena (cheap by default), engineering principles P01–P13.
- Dependency-aware **swarm** workflow and fresh-context review workflow; **browser QA** (bring-your-own-browser, evidence template) and test-first workflow; **session recovery**, reflect/correct and `LESSONS.md`; opt-in PR/CI/release playbook with a strict approval model.
- Optional read-only helper `scripts/ab.py` (`graph`, `state`, `browser-report`), shipped non-executable, with hostile-input tests; selective `init-artifacts.sh`.
- Research and reviewed design under `design/` (pstack and gstack audits at pinned commits, gap analysis, three independent design reviews, honest implementation status, benchmark plan that is **not run**).
- Deliberate-breakage test suite (mutations reported by kind: behaviour, static and wording guards), `tests/run-all.sh`, and CI steps for them.
- Post-implementation reviews found and fixed: a confirmed code-execution path in the helper (repo-local git clean filters; the helper now refuses working-tree git operations when the repository's own git configuration defines commands), a ReDoS, output-injection and git-lookup issues, and several parser/overhead/contradiction problems (see `design/architecture/IMPLEMENTATION-REVIEW-LOG.md`). A final security re-check is recorded there and in the PR.
- Agents, installers and LICENSE unchanged. No live validation; no measured improvement is claimed.

### Added (security engineer)
- **`security-engineer` agent** (9th specialist; read-only, Bash for non-destructive checks, no web tools): threat modeling, OWASP Top 10, authn/authz, API, injection, XSS/CSRF/SSRF, secrets, dependencies, database, privacy, uploads, deployment config, AI/LLM security, security regression tests; evidence-based findings rated Critical/High/Medium/Low.
- **Security gate** in `SKILL.md` and `workflows/security.md`: risk-based invocation at architecture, relevant milestones and before completion; Critical blocks completion and cannot be accepted (a Potential Critical blocks the same way); High needs a fix or explicit user acceptance, and an accepted High stays recorded as open residual risk, never as fixed; Medium/Low tracked; never silently ignored; reports distinguish static inspection, automated scanning and penetration testing (not performed unless authorized); no "secure" claims.
- `SECURITY-REVIEW.md` template; planning, implementation, verification and delivery playbooks updated; validator and installer tests cover the nine-agent set and the gate.
- Existing agent definitions and tool restrictions unchanged; retry/iteration/completion limits unchanged (3 attempts, 5 passes per milestone).

### Added (autonomous QA protocol)
- **Quality protocol** in `SKILL.md`: measurable acceptance criteria, milestone verification gates, independent review at meaningful milestones (with a "not independent" disclosure), Verified / Partially verified / Untested evidence states, regression prevention, root-cause failure recovery, and an explicit completion standard.
- `PROGRESS.md` template; `TASKS.md` template gains a milestone gate table and per-criterion states; verification, planning, implementation and delivery playbooks updated; reviewer brief template.
- Iteration budget is now 5 passes **per milestone** (was project-wide); 3 attempts per failing check unchanged. Agent definitions are unchanged.
- Validator checks that the protocol is wired into the skill, templates and docs.

### Added (launch preparation)
- Static website (`site/` generator, `docs/` output) for GitHub Pages: home, features, installation, usage tutorial, architecture, FAQ; canonical/Open Graph/Twitter metadata, JSON-LD, sitemap.xml, robots.txt, 1280×640 social image.
- `site/check.py` website validator; CI now builds and checks the site.
- GitHub issue forms, pull request template, SECURITY.md, README badges and quick start.
- `launch/` kit: SEO strategy, Search Console guide, GitHub metadata, release notes draft, announcement, community post drafts, DEV tutorial, checklist.

### Added
- `/auto-builder` skill (`.claude/skills/auto-builder/`) implementing a nine-step (Phase 0–8) autonomous development lifecycle with explicit approval checkpoints.
- Nine specialist subagents in `.claude/agents/`: product-manager, researcher, architect, frontend-engineer, backend-engineer, ai-engineer, qa-engineer, security-engineer, critical-reviewer.
- Workflow playbooks, project-category guide, parallel-work guide, and state-file templates.
- Opt-in hook scripts: `protect-secrets.sh` (PreToolUse) and `verify-on-stop.sh` (Stop).
- Installers for Unix (`install.sh`) and Windows (`install.ps1`) with `--dry-run`, existing-file preservation and `--update`.
- Validation (`tests/validate.py`) and installer tests (`tests/test-install.sh`), plus a GitHub Actions workflow.

### Changed (relative to the initial draft of this package)
- Skill is explicit-invoke only (`disable-model-invocation: true`).
- Agent definitions gained `maxTurns`, `color`, structured output formats; reviewer has `disallowedTools: Edit, Write`.
- Added git work-branch/checkpoint-commit policy, bounded fix loop, and category-specific guidance.
- Hardened after an independent audit: case-insensitive, wider `protect-secrets.sh`; bounded, timeout-protected `verify-on-stop.sh`; installer `.bak` numbering, symlink/directory conflict handling, stale-file reporting, symlinked-invocation support; resume protocol, iteration budget, mandatory independent review and dirty-tree git rules in the skill; `qa-engineer` made a read-only auditor.
- Replaced secondary-source citations with official documentation links.
