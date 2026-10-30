# Contributing

Thanks for helping improve AUTO-BUILDER. Contributions are welcome under the repository's [Apache-2.0 license](LICENSE).

## Ground rules
- Open an issue first for large changes (new agents, lifecycle changes).
- Use only **documented** Claude Code features. Cite the doc page in the PR when adding frontmatter fields or hooks. Do not invent configuration.
- Keep instructions concise; prefer progressive disclosure (`SKILL.md` links to `workflows/` and `references/`).
- No benchmarks, endorsements or performance claims without reproducible evidence.
- Never commit secrets, personal paths, or private project details.

## Development
```bash
git clone https://github.com/bsrikumar855-dot/ClaudeCODE-Autonomous-skills
cd ClaudeCODE-Autonomous-skills
python3 -I tests/validate.py     # static validation
bash tests/test-install.sh       # installer tests in temp dirs
```
Both must pass; CI runs them on every PR.

## Where things live
| Change | Edit |
|---|---|
| Lifecycle / approval policy | `.claude/skills/auto-builder/SKILL.md` |
| Detailed playbooks | `.claude/skills/auto-builder/workflows/`, `references/` |
| Agent behaviour | `.claude/agents/<name>.md` |
| State-file templates | `.claude/skills/auto-builder/templates/` |
| Install behaviour | `install.sh` **and** `install.ps1` (keep equivalent) |

## Pull requests
- One focused change per PR; update `CHANGELOG.md` under *Unreleased*.
- Describe how you verified it. If you could not test in a real Claude Code session, say so.
- Windows changes: `install.ps1` is currently verified by review only unless you tested it on Windows — note which you did.
