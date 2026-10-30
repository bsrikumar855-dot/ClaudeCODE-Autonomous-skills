# Changelog

All notable changes to this project are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/); versioning follows [Semantic Versioning](https://semver.org/).

## [0.1.0] - Unreleased

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
- Eight specialist subagents in `.claude/agents/`: product-manager, researcher, architect, frontend-engineer, backend-engineer, ai-engineer, qa-engineer, critical-reviewer.
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
