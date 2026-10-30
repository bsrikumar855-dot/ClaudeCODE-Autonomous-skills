## What and why

## How I verified it
- [ ] `python3 -I tests/validate.py`
- [ ] `bash tests/test-install.sh`
- [ ] If the site changed: `python3 -I site/build.py && python3 -I site/check.py` (and `docs/` is regenerated)
- [ ] Tested in a real Claude Code session? (yes/no, say what you ran)

## Checklist
- [ ] Only documented Claude Code features/frontmatter used (link doc pages if new)
- [ ] `install.sh` and `install.ps1` kept equivalent (if touched)
- [ ] `CHANGELOG.md` updated
- [ ] No secrets, local paths, benchmarks or endorsement claims
