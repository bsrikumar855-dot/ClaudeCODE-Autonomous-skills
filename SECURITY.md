# Security policy

AUTO-BUILDER is a set of instructions, subagent definitions, installer scripts and optional hook scripts. The most security-relevant parts are `install.sh`, `install.ps1`, and `.claude/skills/auto-builder/scripts/hooks/`.

## Reporting a vulnerability

Please use GitHub's **private vulnerability reporting** (repository → Security → *Report a vulnerability*) rather than a public issue. Include the affected file, steps to reproduce and impact. This is a volunteer-maintained project and no response time is guaranteed.

## Scope and known limits

- The skill's safety rules are instructions to a language model, not technical guarantees. Use Claude Code permissions and sandboxing as the enforcement layer.
- `critical-reviewer` and `qa-engineer` have Bash and are only instructed not to modify files.
- `protect-secrets.sh` inspects file paths of Edit/Write/NotebookEdit only; it does not cover Bash or Read.
- `verify-on-stop.sh` executes `AUTO_BUILDER_CHECK_CMD` as shell. Set it only in your own settings; never accept it from an untrusted repository.
