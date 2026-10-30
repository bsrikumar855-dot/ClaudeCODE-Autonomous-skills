# GitHub repository metadata

## Description (≤350 characters; GitHub's field limit)
```
Autonomous coding agent skill for Claude Code: /auto-builder plus 8 subagents plan, build, test, review and document a project from a goal, with approval checkpoints.
```

## Website
```
https://bsrikumar855-dot.github.io/ClaudeCODE-Autonomous-skills/
```

## Topics (max 20; chosen to match terms developers use on GitHub)
`claude-code` `claude-code-skills` `claude-skills` `agent-skills` `claude-code-subagents` `subagents` `autonomous-agents` `ai-agents` `agentic-coding` `ai-coding-assistant` `coding-agent` `developer-tools` `software-development-workflow` `anthropic` `llm`

(The GitHub topics pages for `agent-skills`, `claude-skills` and `subagents` already list many repositories: the niche is crowded, so the README and site lead with concrete differentiators rather than generic terms.)

## Enable GitHub Pages (manual)
Settings → Pages → *Build and deployment* → Source: **Deploy from a branch** → Branch: `main`, folder `/docs` → Save. First publish typically takes a few minutes. Only works after the site is merged to `main`.

## Equivalent `gh` commands (NOT run; review before executing)
```bash
gh repo edit bsrikumar855-dot/ClaudeCODE-Autonomous-skills \
  --description "Autonomous coding agent skill for Claude Code: /auto-builder plus 8 subagents plan, build, test, review and document a project from a goal, with approval checkpoints." \
  --homepage "https://bsrikumar855-dot.github.io/ClaudeCODE-Autonomous-skills/" \
  --add-topic claude-code --add-topic claude-code-skills --add-topic claude-skills --add-topic agent-skills \
  --add-topic claude-code-subagents --add-topic subagents --add-topic autonomous-agents --add-topic ai-agents \
  --add-topic agentic-coding --add-topic ai-coding-assistant --add-topic coding-agent --add-topic developer-tools \
  --add-topic software-development-workflow --add-topic anthropic --add-topic llm
# Pages from /docs on main:
gh api -X POST repos/bsrikumar855-dot/ClaudeCODE-Autonomous-skills/pages \
  -f "source[branch]=main" -f "source[path]=/docs"
```

## Other settings worth enabling (manual)
- Security → *Private vulnerability reporting* (SECURITY.md refers to it).
- Discussions (optional) for Q&A so issues stay for bugs.
- Upload the social preview (see [social-preview-spec.md](social-preview-spec.md)).
