#!/usr/bin/env python3
"""Static validation for the AUTO-BUILDER package. Standard library only.

Run:  python3 -I tests/validate.py
"""
import os
import re
import stat
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKILL_DIR = os.path.join(ROOT, ".claude", "skills", "auto-builder")
AGENT_DIR = os.path.join(ROOT, ".claude", "agents")

SKILL_KEYS = {
    "name", "description", "when_to_use", "argument-hint", "arguments",
    "disable-model-invocation", "user-invocable", "allowed-tools",
    "disallowed-tools", "model", "effort", "context", "agent", "background",
    "hooks", "paths", "shell", "metadata", "license", "compatibility",
}
AGENT_KEYS = {
    "name", "description", "tools", "disallowedTools", "model", "permissionMode",
    "maxTurns", "autoCompactWindow", "skills", "mcpServers", "hooks", "memory",
    "background", "omitClaudeMd", "effort", "isolation", "color",
    "initialPrompt", "experimental",
}
COLORS = {"red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"}
KNOWN_TOOLS = {
    "Read", "Edit", "Write", "Bash", "Grep", "Glob", "WebSearch", "WebFetch",
    "Agent", "NotebookEdit",
}
EXPECTED_AGENTS = {
    "product-manager", "researcher", "architect", "frontend-engineer",
    "backend-engineer", "ai-engineer", "qa-engineer", "critical-reviewer",
    "security-engineer",
}
# Least-privilege snapshot: (tools, disallowedTools, a keyword that must stay in the description).
# The first eight entries pin the originally shipped restrictions and responsibilities.
EXPECTED_AGENT_SPEC = {
    "product-manager": ({"Read", "Grep", "Glob", "WebSearch", "WebFetch"}, set(), "acceptance criteria"),
    "researcher": ({"Read", "Grep", "Glob", "WebSearch", "WebFetch"}, set(), "primary sources"),
    "architect": ({"Read", "Grep", "Glob"}, set(), "architecture"),
    "frontend-engineer": ({"Read", "Edit", "Write", "Bash", "Grep", "Glob"}, set(), "frontend"),
    "backend-engineer": ({"Read", "Edit", "Write", "Bash", "Grep", "Glob"}, set(), "backend"),
    "ai-engineer": ({"Read", "Edit", "Write", "Bash", "Grep", "Glob", "WebSearch", "WebFetch"}, set(), "LLM"),
    "qa-engineer": ({"Read", "Bash", "Grep", "Glob"}, {"Edit", "Write"}, "test"),
    "critical-reviewer": ({"Read", "Grep", "Glob", "Bash"}, {"Edit", "Write"}, "reviews"),
    "security-engineer": ({"Read", "Bash", "Grep", "Glob"}, {"Edit", "Write", "WebFetch", "WebSearch"}, "security"),
}
SECURITY_AGENT_TOPICS = [
    "threat model", "attack surface", "owasp", "authentication", "authorization", "api security",
    "sql", "injection", "xss", "csrf", "ssrf", "secrets", "dependenc", "database", "privacy",
    "file upload", "input validation", "deployment", "prompt injection", "insecure tool execution",
    "data leakage", "excessive", "regression", "critical", "high", "medium", "low", "confirmed",
    "potential", "[redacted]", "destructive", "production", "paid", "evidence", "never claim",
    "not technically restricted", "network", "npm audit", "you specify", "keeps blocking",
    "static inspection", "automated scanning", "penetration", "not performed", "can never be accepted", "open residual risk",
]
EXPECTED_DIRS = ["workflows", "principles", "templates", "scripts", "references"]
SECRET_PATTERNS = [
    (r"sk-[A-Za-z0-9]{20,}", "API-key-like string"),
    (r"AKIA[0-9A-Z]{16}", "AWS key id"),
    (r"gh[pousr]_[A-Za-z0-9]{30,}", "GitHub token"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key"),
    (r"/home/[A-Za-z0-9_.-]+/", "local Linux path"),
    (r"/Users/[A-Za-z0-9_.-]+/", "local macOS path"),
    (r"[A-Za-z]:\\Users\\", "local Windows path"),
]

errors = []
checks = 0


def err(msg):
    errors.append(msg)


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        err(msg)
    return cond


def rel(p):
    return os.path.relpath(p, ROOT)


def parse_frontmatter(path):
    """Return (dict of top-level keys -> raw value, body) or (None, text)."""
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    fm, body = text[4:end], text[end + 5:]
    data, last = {}, None
    for line in fm.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t":
            if last is None:
                err(f"{rel(path)}: indented line before any key: {line!r}")
            continue
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if not m:
            err(f"{rel(path)}: unparseable frontmatter line: {line!r}")
            continue
        last = m.group(1)
        raw = m.group(2).strip()
        if raw[:1] in ("'", '"'):
            if len(raw) < 2 or raw[-1] != raw[0]:
                err(f"{rel(path)}: unterminated quoted value for '{last}'")
        elif raw[:1] in (">", "|", "[", "{") or not raw:
            if last in ("name", "description", "tools", "disallowedTools", "model"):
                err(f"{rel(path)}: '{last}' must be a single-line plain value (block/flow/empty forms are not validated here)")
        elif ": " in raw or raw.endswith(":") or " #" in raw:
            err(f"{rel(path)}: '{last}' contains ': ' or ' #' unquoted, which is invalid/ambiguous YAML; quote it")
        if last in data:
            err(f"{rel(path)}: duplicate key {last}")
        data[last] = m.group(2).strip().strip("\"'")
    try:  # Extra rigor when PyYAML happens to be installed; the hand parser above is the baseline.
        import yaml
        yaml.safe_load(fm)
    except ImportError:
        pass
    except Exception as e:  # real YAML parse error
        err(f"{rel(path)}: frontmatter is not valid YAML: {str(e).splitlines()[0]}")
    return data, body


def check_skill():
    path = os.path.join(SKILL_DIR, "SKILL.md")
    if not ok(os.path.isfile(path), "missing .claude/skills/auto-builder/SKILL.md"):
        return
    fm, body = parse_frontmatter(path)
    if not ok(fm is not None, "SKILL.md: missing or unterminated frontmatter"):
        return
    ok(fm.get("name") == "auto-builder", "SKILL.md: name must be 'auto-builder'")
    ok(os.path.basename(SKILL_DIR) == fm.get("name"), "SKILL.md: name must equal its directory name")
    ok(bool(fm.get("description")), "SKILL.md: description required")
    ok(len(fm.get("description", "")) <= 1536, "SKILL.md: description over 1536 chars")
    for k in fm:
        ok(k in SKILL_KEYS, f"SKILL.md: unknown frontmatter key '{k}'")
    for k in ("disable-model-invocation", "user-invocable"):
        if k in fm:
            ok(fm[k].lower() in {"true", "false", "yes", "no", "on", "off", "1", "0"},
               f"SKILL.md: {k} must be boolean")
    n = open(path, encoding="utf-8").read().count("\n")
    ok(n < 500, f"SKILL.md: {n} lines (keep under 500)")
    ok("$ARGUMENTS" in body, "SKILL.md: body should use $ARGUMENTS")
    for d in EXPECTED_DIRS:
        ok(os.path.isdir(os.path.join(SKILL_DIR, d)), f"missing skill directory: {d}/")
    for sub in ("workflows", "templates"):
        d = os.path.join(SKILL_DIR, sub)
        ok(os.path.isdir(d) and any(f.endswith(".md") for f in os.listdir(d)),
           f"{sub}/ has no markdown files")


def check_agents():
    found = set()
    for f in sorted(os.listdir(AGENT_DIR)):
        if not f.endswith(".md"):
            continue
        path = os.path.join(AGENT_DIR, f)
        fm, body = parse_frontmatter(path)
        if not ok(fm is not None, f"{rel(path)}: missing frontmatter"):
            continue
        name = fm.get("name", "")
        found.add(name)
        ok(name == f[:-3], f"{rel(path)}: name '{name}' must match filename")
        ok(bool(re.fullmatch(r"[a-z0-9][a-z0-9-]*", name)), f"{rel(path)}: bad name '{name}'")
        ok(bool(fm.get("description")), f"{rel(path)}: description required")
        ok(len(body.strip()) > 200, f"{rel(path)}: prompt body too short")
        for k in fm:
            ok(k in AGENT_KEYS, f"{rel(path)}: unknown frontmatter key '{k}'")
        ok(bool(fm.get("tools", "").strip()), f"{rel(path)}: 'tools' is required (omitting it grants all tools)")
        for key in ("tools", "disallowedTools"):
            raw_list = fm.get(key, "")
            parts = [x.strip() for x in raw_list.split(",")]
            ok(all(parts) or not raw_list, f"{rel(path)}: empty entry in {key}")
            for t in [x for x in parts if x]:
                ok(t in KNOWN_TOOLS, f"{rel(path)}: unknown tool '{t}' in {key}")
        ok(fm.get("model", "inherit") in {"inherit", "sonnet", "opus", "haiku", "fable"} or fm.get("model", "").startswith("claude-"),
           f"{rel(path)}: invalid model '{fm.get('model')}'")
        if "color" in fm:
            ok(fm["color"] in COLORS, f"{rel(path)}: invalid color '{fm['color']}'")
        if "maxTurns" in fm:
            ok(fm["maxTurns"].isdigit() and int(fm["maxTurns"]) > 0, f"{rel(path)}: maxTurns must be a positive number")
        ok("Agent" not in fm.get("tools", ""), f"{rel(path)}: nested spawning not intended")
        if name in EXPECTED_AGENT_SPEC:
            want_tools, want_deny, kw = EXPECTED_AGENT_SPEC[name]
            have_tools = {t.strip() for t in fm.get("tools", "").split(",") if t.strip()}
            have_deny = {t.strip() for t in fm.get("disallowedTools", "").split(",") if t.strip()}
            ok(have_tools == want_tools, f"{rel(path)}: tools changed: {sorted(have_tools)} != {sorted(want_tools)}")
            ok(have_deny == want_deny, f"{rel(path)}: disallowedTools changed: {sorted(have_deny)} != {sorted(want_deny)}")
            ok(kw.lower() in fm.get("description", "").lower(), f"{rel(path)}: description lost responsibility keyword '{kw}'")
        if name in ("critical-reviewer", "architect", "product-manager", "researcher", "qa-engineer", "security-engineer"):
            ok("Edit" not in fm.get("tools", "") and "Write" not in fm.get("tools", ""),
               f"{rel(path)}: reviewer/read-only role must not have Edit/Write")
    names = [n for n in found]
    ok(len(names) == len(set(names)), "duplicate agent names")
    ok(len(found) == 9 and len(EXPECTED_AGENTS) == 9, f"exactly nine specialist agents required, found {len(found)}")
    ok(found == EXPECTED_AGENTS, f"agents mismatch: missing={EXPECTED_AGENTS - found} extra={found - EXPECTED_AGENTS}")


def md_files():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules"}]
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(base, f)


def check_links():
    pat = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
    for path in md_files():
        text = re.sub(r"```.*?```", "", open(path, encoding="utf-8").read(), flags=re.S)
        for target in pat.findall(text):
            if re.match(r"^(https?:|mailto:|#)", target):
                continue
            t = target.split("#")[0]
            if not t:
                continue
            ok(os.path.exists(os.path.normpath(os.path.join(os.path.dirname(path), t))),
               f"{rel(path)}: broken link -> {target}")


def check_scripts():
    scripts = [os.path.join(ROOT, "install.sh"), os.path.join(ROOT, "tests", "test-install.sh")]
    sdir = os.path.join(SKILL_DIR, "scripts")
    for base, _, files in os.walk(sdir):
        scripts += [os.path.join(base, f) for f in files if f.endswith(".sh")]
    for p in scripts:
        if not ok(os.path.isfile(p), f"missing script {rel(p)}"):
            continue
        ok(bool(os.stat(p).st_mode & stat.S_IXUSR), f"{rel(p)}: not executable")
        ok(open(p).readline().startswith("#!"), f"{rel(p)}: missing shebang")
        r = subprocess.run(["bash", "-n", p], capture_output=True, text=True)
        ok(r.returncode == 0, f"{rel(p)}: syntax error: {r.stderr.strip()}")
    ok(os.path.isfile(os.path.join(ROOT, "install.ps1")), "missing install.ps1")
    # Scripts referenced from docs must exist.
    for path in md_files():
        for m in re.findall(r"scripts/(?:hooks/)?[A-Za-z0-9_-]+\.sh", open(path, encoding="utf-8").read()):
            ok(os.path.exists(os.path.join(SKILL_DIR, m)), f"{rel(path)}: references missing script {m}")


def section(text, heading, level="###"):
    m = re.search(rf"^{level} {re.escape(heading)}.*?$(.*?)(?=^#{{2,3}} |\Z)", text, flags=re.S | re.M)
    return m.group(1) if m else ""


def check_protocol():
    """The Quality protocol must be wired into the workflow, templates and docs, not just present."""
    skill = open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8").read()
    qp = section(skill, "Quality protocol", "##")
    if not ok(bool(qp), "SKILL.md: missing '## Quality protocol' section"):
        return
    ok(len(re.findall(r"^\d\. \*\*", qp, flags=re.M)) == 7, "Quality protocol must have 7 numbered items")
    for phrase in ("milestone gate", "Verified", "Partially verified", "Untested", "root cause",
                   "not independent", "completion standard", "not a guarantee", "no extra approval"):
        ok(phrase.lower() in qp.lower(), f"Quality protocol missing '{phrase}'")
    # Enforcement points in the phases that must use it
    wired = {"Phase 2": "measurable acceptance criteria", "Phase 4": "verification gate",
             "Phase 5": "passed its gate", "Phase 6": "milestone gate", "Phase 7": "completion standard",
             "Phase 8": "partially verified"}
    for ph, needle in wired.items():
        body = re.search(rf"^### {ph} .*?$(.*?)(?=^#{{2,3}} |\Z)", skill, flags=re.S | re.M)
        ok(bool(body) and needle.lower() in body.group(1).lower(), f"SKILL.md {ph} does not enforce: '{needle}'")
    # Bounds: 3 attempts, 5 passes per milestone, consistent everywhere
    ok("3 fix attempts" in skill and "default 5 passes per milestone" in skill, "SKILL.md bounds (3 attempts / 5 passes per milestone) missing")
    ok("full Phase 5–7 passes" not in skill, "SKILL.md still has the old project-wide pass budget")
    tasks = open(os.path.join(SKILL_DIR, "templates", "TASKS.md"), encoding="utf-8").read()
    ok("0 / 5" in tasks and "max 3" in tasks and "Milestone gates" in tasks and "Acceptance checklist" in tasks,
       "templates/TASKS.md must carry the budget, attempt limit, milestone gates and acceptance checklist")
    verification = open(os.path.join(SKILL_DIR, "workflows", "verification.md"), encoding="utf-8").read()
    for phrase in ("Milestone gate checklist", "Evidence vocabulary", "Reviewer brief", "Failure recovery record", "1 of 3"):
        ok(phrase in verification, f"workflows/verification.md missing '{phrase}'")
    # State files named in SKILL.md == templates shipped
    line = next((l for l in skill.splitlines() if l.startswith("`PROJECT.md`")), "")
    named = set(re.findall(r"`([A-Z-]+\.md)`", line))
    shipped = {f for f in os.listdir(os.path.join(SKILL_DIR, "templates")) if f.endswith(".md")}
    ok(named == shipped, f"state files in SKILL.md vs templates differ: {named ^ shipped}")
    ok("PROGRESS.md" in shipped, "missing PROGRESS.md template")
    # All nine agents referenced by SKILL.md and none invented
    ref = set(re.findall(r"\| `([a-z-]+)` \|", skill))
    ok(ref == EXPECTED_AGENTS, f"agents in SKILL.md table differ from shipped: {ref ^ EXPECTED_AGENTS}")
    # Optional hooks must stay off by default: no shipped settings, installers never write settings
    ok(not any(os.path.exists(os.path.join(ROOT, ".claude", f)) for f in ("settings.json", "settings.local.json")),
       "repo must not ship a .claude/settings*.json (hooks must stay opt-in)")
    for f in ("install.sh", "install.ps1"):
        ok("settings.json" not in open(os.path.join(ROOT, f), encoding="utf-8").read(), f"{f} must not touch settings.json")
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    ok("optional, off by default" in readme.lower(), "README must say hooks are off by default")
    # Docs must not overclaim the protocol
    for p in (os.path.join(ROOT, "README.md"), os.path.join(ROOT, "site", "pages", "features.html")):
        t = open(p, encoding="utf-8").read().lower()
        ok("not a guarantee" in t, f"{rel(p)}: must state the protocol is not a guarantee")
    # CI / GitHub YAML must parse when PyYAML is available
    try:
        import yaml
        for base, _, files in os.walk(os.path.join(ROOT, ".github")):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    try:
                        yaml.safe_load(open(os.path.join(base, f), encoding="utf-8"))
                        ok(True, "")
                    except Exception as e:
                        ok(False, f".github/{f}: invalid YAML: {str(e).splitlines()[0]}")
    except ImportError:
        pass


def table_rows(text, first_col_header):
    """Parse a markdown table whose header starts with first_col_header; return list of cell lists."""
    lines, out, on = text.splitlines(), [], False
    for l in lines:
        if l.startswith("|") and l.lower().lstrip("| ").startswith(first_col_header.lower()):
            on = True
            continue
        if on:
            if not l.startswith("|"):
                break
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            out.append(cells)
    return out


def check_router():
    """Router table, playbooks, discovery/arena rules, principles, untrusted-data and limits (mechanism tests)."""
    wf = os.path.join(SKILL_DIR, "workflows")
    pb = os.path.join(SKILL_DIR, "playbooks")
    skill = open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8").read()
    router_path = os.path.join(wf, "router.md")
    if not ok(os.path.isfile(router_path), "missing workflows/router.md"):
        return
    router = open(router_path, encoding="utf-8").read()
    cats = ["new-project", "new-feature", "bug-fix", "investigation", "refactoring", "performance",
            "security-assessment", "code-review", "research", "testing", "documentation", "release-deployment"]
    rows = table_rows(router, "Category")
    ok([r[0] for r in rows] == cats, f"router table categories differ: {[r[0] for r in rows]}")
    for r in rows:
        if len(r) != 4:
            ok(False, f"router row malformed: {r}")
            continue
        cat, play, spec, gates = r
        path, _, anchor = play.partition("#")
        if cat != "new-project":
            f = os.path.join(SKILL_DIR, path)
            if ok(os.path.isfile(f), f"router: playbook missing for {cat}: {play}") and anchor:
                ok(re.search(rf"^## {re.escape(anchor)}\b", open(f, encoding="utf-8").read(), flags=re.M) is not None,
                   f"router: anchor '#{anchor}' not found in {path}")
        for sp in [x.strip() for x in spec.split(",") if x.strip()]:
            ok(sp in EXPECTED_AGENTS, f"router: unknown specialist '{sp}' for {cat}")
        kv = dict(x.strip().split(":", 1) for x in gates.split(";") if ":" in x)
        ok("security" in kv and kv["security"] in ("if-triggered", "always"), f"router: {cat} must have security:if-triggered|always (never 'no')")
    by = {r[0]: r for r in rows if len(r) == 4}
    if "security-assessment" in by:
        ok("security:always" in by["security-assessment"][3].replace(" ", ""), "security-assessment must have security:always")
    if "release-deployment" in by:
        ok("approval:always" in by["release-deployment"][3].replace(" ", ""), "release-deployment must have approval:always")
    for phrase in ("trivial bypass", "user's own message", "gates are **added**", "never removed", "one** focused question",
                   "never ask", "one milestone row", "has **not been run**", "judged by what the change touches"):
        ok(phrase.lower() in router.lower(), f"router.md missing: '{phrase}'")
    # routing eval set
    fx = os.path.join(ROOT, "tests", "fixtures", "routing-eval.json")
    if ok(os.path.isfile(fx), "missing tests/fixtures/routing-eval.json"):
        import json
        data = json.load(open(fx, encoding="utf-8"))
        ok(data.get("status") == "NOT RUN", "routing eval set must be labelled status NOT RUN")
        valid = set(cats) | {"ask", "trivial"}
        kinds = {c["kind"] for c in data["cases"]}
        ok(len(data["cases"]) >= 24, "routing eval set too small")
        ok({"clear", "ambiguous", "trivial", "adversarial"} <= kinds, f"eval set must cover clear/ambiguous/trivial/adversarial, has {kinds}")
        ok(all(c["expected"] in valid and set(c.get("acceptable", [])) <= valid for c in data["cases"]), "eval set references an unknown category")
        ok(all(c["expected"] in ("ask", "trivial") or c["expected"] in cats for c in data["cases"]), "bad expected category")
        ok(sum(1 for c in data["cases"] if c["kind"] == "ambiguous") >= 3, "need ambiguous cases")
        ok(set(data["categories"]) == set(cats) and all(any(c["expected"] == k for c in data["cases"]) for k in cats),
           "eval set must have at least one case per category")
    # playbooks
    principles = open(os.path.join(SKILL_DIR, "principles", "engineering-principles.md"), encoding="utf-8").read()
    ids = [f"P{n:02d}" for n in range(1, 14)]
    for pid in ids:
        ok(re.search(rf"^\| {pid} \|", principles, flags=re.M) is not None, f"principle {pid} missing")
    names = ("Simplicity", "Maintainability", "Testability", "Security by design", "Least privilege", "API design",
             "Error handling", "Performance", "Observability", "Documentation", "Dependency management",
             "Backward compatibility", "Evidence-based completion")
    ok(all(n in principles for n in names), "principles file missing one of the 13 required topics")
    ok(all("Verify by" in principles for _ in [0]) and principles.count("|") > 13 * 4, "principles need a 'Verify by' column")
    used = set()
    expected_files = {"feature.md", "bug-fix.md", "refactor.md", "performance.md", "security-assessment.md",
                      "inquiry.md", "test-and-docs.md", "release.md"}
    ok(os.path.isdir(pb) and set(os.listdir(pb)) == expected_files, f"playbooks differ: {set(os.listdir(pb)) ^ expected_files if os.path.isdir(pb) else 'missing dir'}")
    for f in sorted(expected_files):
        t = open(os.path.join(pb, f), encoding="utf-8").read()
        ok(len(t.splitlines()) <= 60, f"playbooks/{f} too long")
        ok(not re.search(r"^\W*(Specialists|Gates)\b", t, flags=re.M), f"playbooks/{f} restates specialists/gates (router.md is the only place)")
        ok(not re.search(r"(≤|at most|up to|max(imum)?)\s*\d", t, flags=re.I), f"playbooks/{f} states a numeric cap (see SKILL.md Limits)")
        if f in ("inquiry.md", "test-and-docs.md"):
            sections = re.split(r"^## ", t, flags=re.M)[1:]
            for sec in sections:
                ok(all(h in sec for h in ("**Steps**", "**Principles**", "**Completion criteria**")), f"playbooks/{f} section '{sec.splitlines()[0]}' incomplete")
        else:
            ok(all(h in t for h in ("## Steps", "## Principles", "## Completion criteria")), f"playbooks/{f} missing Steps/Principles/Completion criteria")
        used |= set(re.findall(r"\bP\d\d\b", t))
        ok(set(re.findall(r"\bP\d\d\b", t)) <= set(ids), f"playbooks/{f} cites an unknown principle")
        crit_blocks = re.split(r"Completion criteria", t)[1:]
        ok(crit_blocks and all(len(re.findall(r"^\s*- ", blk.split("\n## ")[0], flags=re.M)) >= 2 for blk in crit_blocks),
           f"playbooks/{f}: each Completion criteria block needs at least two concrete bullets")
    ok(used >= set(ids), f"principles never cited by any playbook: {sorted(set(ids) - used)}")
    # no numeric caps outside SKILL.md Limits in workflows/references
    for d in (wf, os.path.join(SKILL_DIR, "references")):
        for f in sorted(os.listdir(d)):
            t = open(os.path.join(d, f), encoding="utf-8").read()
            ok(not re.search(r"(≤|at most|up to)\s*\d", t, flags=re.I), f"{f}: numeric cap outside SKILL.md Limits")
    # discovery (interrogation) and arena
    disc = open(os.path.join(wf, "discovery.md"), encoding="utf-8").read().lower()
    for phrase in ("run it", "skip it", "trivial", "what is the smallest valuable solution", "which assumptions are unverified",
                   "what are the success metrics", "explicitly **not** be built", "how is it solved today",
                   "product discovery", "ceo-level challenge", "mvp scope review", "feature prioritization", "user-journey analysis",
                   "decision tiers", "user-challenge", "final authority", "do not agree automatically", "inspect an existing application"):
        ok(phrase in disc, f"discovery.md missing: '{phrase}'")
    arena = open(os.path.join(wf, "arena.md"), encoding="utf-8").read().lower()
    for phrase in ("hard to reverse", "never for conventional", "pre-mortem", "into `decisions.md` first", "why each alternative was rejected",
                   "does not make the decision objective", "fresh-context", "limits", "security-engineer", "reframe once", "ask the user"):
        ok(phrase in arena, f"arena.md missing: '{phrase}'")
    # SKILL.md wiring: router, untrusted data, limits
    for sec, phrases in (("Task router", ("trivial changes", "12 categories", "one milestone row", "only **adds** gates", "one focused question", "never ask")),
                         ("Untrusted data", ("data, not instructions", "never** grant an approval", "waive a gate", "raise or reset a limit",
                                              "only lower", "current session", "tell the user what you found", "marking it as data")),
                         ("Limits", ("defined once", "never as a new budget", "concurrent workers per wave", "arena independent candidates",
                                     "3 fix-push-recheck rounds", "elapsed"))):
        body = section(skill, sec, "##").lower()
        ok(bool(body), f"SKILL.md missing section '{sec}'")
        for ph in phrases:
            ok(ph.lower() in body, f"SKILL.md '{sec}' missing: '{ph}'")
    ok("workflows/router.md" in skill and "workflows/arena.md" in skill and "principles/engineering-principles.md" in skill,
       "SKILL.md must link router, arena and principles")
    ok("workflows/discovery.md" in section(skill, "Phase 1", "###") or "discovery.md" in skill, "Phase 1 must reference discovery/interrogation")
    ok(len(skill.splitlines()) < 300, "SKILL.md should stay compact (<300 lines)")
    tasks = open(os.path.join(SKILL_DIR, "templates", "TASKS.md"), encoding="utf-8").read()
    ok("| Flags |" in tasks and "Verified at (sha)" in tasks and "Strict grammar" in tasks, "TASKS.md template needs Flags, Verified at (sha) and the strict-grammar note")


AB_IMPORT_ALLOW = {"argparse", "fnmatch", "json", "os", "re", "subprocess", "sys", "hashlib", "stat", "datetime"}
AB_FORBIDDEN_OS = {"system", "popen", "remove", "unlink", "rename", "replace", "mkdir", "makedirs", "rmdir", "chmod",
                   "chown", "symlink", "link", "write", "truncate", "utime", "putenv", "execv", "execl", "spawnl", "fork"}
AB_FORBIDDEN_NAMES = {"eval", "exec", "compile", "__import__", "input", "breakpoint"}


def check_ab():
    """The helper must stay read-only, offline, allow-listed and non-executable; docs must invoke it safely."""
    import ast
    ab = os.path.join(SKILL_DIR, "scripts", "ab.py")
    if not ok(os.path.isfile(ab), "missing scripts/ab.py"):
        return
    src = open(ab, encoding="utf-8").read()
    tree = ast.parse(src)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            imports.add((node.module or "").split(".")[0])
    ok(imports <= AB_IMPORT_ALLOW, f"ab.py imports outside the allow-list: {sorted(imports - AB_IMPORT_ALLOW)}")
    # forbidden calls / names
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == "os" and f.attr in AB_FORBIDDEN_OS:
                ok(False, f"ab.py calls os.{f.attr} (must be read-only)")
            if isinstance(f, ast.Name) and f.id in AB_FORBIDDEN_NAMES:
                ok(False, f"ab.py calls {f.id}()")
            if isinstance(f, ast.Name) and f.id == "open":
                mode = None
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value
                for kw in node.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = kw.value.value
                ok(mode in (None, "r", "rb"), f"ab.py opens a file with mode {mode!r} (read-only only)")
            for kw in node.keywords:
                if kw.arg == "shell":
                    ok(isinstance(kw.value, ast.Constant) and kw.value.value is False, "ab.py must not use shell=True")
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Attribute) and t.value.attr == "environ":
                    ok(False, "ab.py writes os.environ")
    # subprocess is confined to run_git and git is allow-listed
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        uses = any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "subprocess" for n in ast.walk(fn))
        if uses:
            ok(fn.name == "run_git", f"ab.py uses subprocess outside run_git (in {fn.name})")
    for needle in ("--no-pager", "--no-optional-locks", "core.fsmonitor=false", "GIT_CONFIG_NOSYSTEM", "shell=False", "timeout="):
        ok(needle in src, f"ab.py git hardening missing: {needle}")
    ok("allowed = {" in src and "rev-parse" in src, "ab.py must allow-list git subcommands")
    ok("writes nothing" in src.lower(), "ab.py docstring must state it writes nothing")
    ok(not (os.stat(ab).st_mode & 0o111), "ab.py must ship non-executable (invoke as python3 -I)")
    # cap consistency with SKILL.md Limits
    skill = open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8").read()
    m = re.search(r"\| concurrent workers per wave \| (\d+) \|", skill)
    mm = re.search(r"^MAX_WORKERS_PER_WAVE = (\d+)", src, flags=re.M)
    ok(bool(m and mm and m.group(1) == mm.group(1)), "MAX_WORKERS_PER_WAVE must equal the SKILL.md Limits cap")
    # nothing wires the helper into hooks or settings; docs always invoke it isolated
    ok(not any(os.path.exists(os.path.join(ROOT, ".claude", f)) for f in ("settings.json", "settings.local.json")), "no settings file may ship")
    for f in os.listdir(os.path.join(SKILL_DIR, "scripts", "hooks")):
        ok("ab.py" not in open(os.path.join(SKILL_DIR, "scripts", "hooks", f), encoding="utf-8").read(), f"hook {f} must not call ab.py")
    for path in md_files():
        for n, line in enumerate(open(path, encoding="utf-8").read().splitlines(), 1):
            if "scripts/ab.py" in line and "python3" in line:
                ok("python3 -I" in line, f"{rel(path)}:{n}: ab.py must be invoked as 'python3 -I'")
    # swarm and fresh-context review playbooks carry their safety rules
    swarm = open(os.path.join(SKILL_DIR, "workflows", "swarm.md"), encoding="utf-8").read().lower()
    for ph in ("task table", "hypothesis", "parallelizable", "sequential", "shared-file", "high-risk", "needs a human decision",
               "ab.py graph", "read-only", "worker brief", "narrowest", "no formatter or code generator", "`pass`, `issues` or `blocked`",
               "gap, never a pass", "counts as an attempt", "shared working tree", "violation", "parallelism never bypasses a gate",
               "rollback", "user's approval", "never reset or clean", "--check-changes", "untracked", "lead only"):
        ok(ph in swarm or ph == "lead only", f"swarm.md missing: '{ph}'")
    rev = open(os.path.join(SKILL_DIR, "workflows", "independent-review.md"), encoding="utf-8").read().lower()
    for ph in ("separate context", "not independent of the lead's framing", "| l0", "| l1", "| l2", "multi-model", "distinct models",
               "unedited", "**raw**", "do **not** give", "reproduce or drop", "read the command before running it", "untrusted",
               "different vendor", "explicit approval", "for this run", "redact", "paid api", "do not claim more independence",
               "do not approve by default", "state what you did **not** check", "never the default"):
        ok(ph in rev, f"independent-review.md missing: '{ph}'")
    ok("workflows/swarm.md" in skill and "workflows/independent-review.md" in skill, "SKILL.md must link swarm and fresh-context review")


def check_verification2():
    """Browser QA and test-first workflows, the report template, and the checker's contract."""
    wf = os.path.join(SKILL_DIR, "workflows")
    bq = open(os.path.join(wf, "browser-qa.md"), encoding="utf-8").read().lower()
    for ph in ("bring-your-own-browser", "you (the lead) write", "no browser tools", "cannot write files", "project's own end-to-end suite",
               "specific journeys", "browser qa not performed", "untested", "never simulate", "invent a screenshot", "origin allowlist",
               "approved by user: yes", "never production", "ephemeral profile", "test accounts", "test mode", "untrusted data",
               "git-ignored", "success** scenario and a **failure", "console errors", "failed network requests", "375, 768 and 1280",
               "registration", "login", "file upload", "payment", "agent tool-authorization", "ab.py browser-report", "format and internal consistency",
               "proves **no behaviour**", "never cite the checker as verification", "open at least one artifact", "harder, not impossible",
               "same counters", "dev** dependency", "expected, actual, pass or fail"):
        ok(ph in bq, f"browser-qa.md missing: '{ph}'")
    tdd = open(os.path.join(wf, "tdd.md"), encoding="utf-8").read().lower()
    for ph in ("fails for the right reason", "smallest change", "regression", "never weaken the check", "failing-before", "passing-after",
               "narrowest existing test type", "cannot edit files"):
        ok(ph in tdd, f"tdd.md missing: '{ph}'")
    tpl = open(os.path.join(SKILL_DIR, "templates", "BROWSER-QA.md"), encoding="utf-8").read()
    for h in ("- Tool:", "- Environment:", "- Base URL:", "- Origin allowlist:", "- Started:", "- Approved by user:", "## Scenarios",
              "| ID | Kind | URL | Scenario | Expected | Actual | Result | Artifact | sha256 |", "NOT RUN", "none: "):
        ok(h in tpl, f"BROWSER-QA.md template missing: {h}")
    ab = open(os.path.join(SKILL_DIR, "scripts", "ab.py"), encoding="utf-8").read()
    for ph in ("FORMAT CHECK ONLY", "must not be cited as verification", "Origin allowlist", "production", "Approved by user",
               "older than the report", "tracked by git", "credentials", "sha256", "MAX_ARTIFACT_BYTES"):
        ok(ph in ab, f"ab.py browser-report missing: '{ph}'")
    skill = open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8").read()
    ok("browser qa not performed" in skill.lower() and "workflows/browser-qa.md" in skill and "workflows/tdd.md" in skill,
       "SKILL.md must wire browser QA (with the 'not performed' rule) and test-first")
    for pbk, ref in (("feature.md", "workflows/tdd.md"), ("feature.md", "workflows/browser-qa.md"), ("bug-fix.md", "workflows/tdd.md")):
        ok(ref in open(os.path.join(SKILL_DIR, "playbooks", pbk), encoding="utf-8").read(), f"playbooks/{pbk} must reference {ref}")
    ok("BROWSER-QA.md" in skill, "SKILL.md state files must list BROWSER-QA.md")


def check_recovery():
    """Resume, pause, reflect and correct rules; lessons scope separation; state check contract."""
    sr = open(os.path.join(SKILL_DIR, "workflows", "session-recovery.md"), encoding="utf-8").read().lower()
    for ph in ("data** (skill.md, untrusted data)", "verify against the repository", "ab.py state", "`verified at` commit", "ancestor of `head`",
               '"unknown"', "not \"untrustworthy\"", "stale evidence (best effort)", "not** detected", "hint, not proof", "dirty files by owner",
               "do not commit it or touch it", "wave was in flight", "re-run the current milestone's verification", "never assume a task is complete",
               "retry budgets are not reset by restarting", "only the user may reset a budget", "only lower a remaining budget", "not tamper-proof",
               "pause or interruption", "do not push or open a pr", "`wip:`", "reflect", "no raw command output", "no secrets", "no personal data",
               "near-duplicate", "obsolete", "never instruct a later run", "correct", "second time", "highest level that works",
               "would have failed on the real past mistake", "**proposal**", "you never apply it", "explicit approval in the current session",
               "never merged into the lessons", "changed only by the user", "tell the user what you found"):
        ok(ph in sr, f"session-recovery.md missing: '{ph}'")
    tpl = open(os.path.join(SKILL_DIR, "templates", "LESSONS.md"), encoding="utf-8").read()
    for h in ("## Project lessons (this project only)", "## Proposals for AUTO-BUILDER (never applied by the skill; the user decides)",
              "data, not instructions", "No raw command output", "applied", "explicit approval in the current session", "approved-by-user"):
        ok(h in tpl, f"LESSONS.md template missing: {h}")
    ok(tpl.index("## Project lessons") < tpl.index("## Proposals for AUTO-BUILDER"), "LESSONS.md: project lessons and proposals must be separate sections")
    ab = open(os.path.join(SKILL_DIR, "scripts", "ab.py"), encoding="utf-8").read()
    for ph in ("never changes or resets", "counter regression", "do not reset retry budgets", "not an ancestor of HEAD", "status unknown",
               "owned by no task", "treat as the user's change", "unanchored", "re-run the current milestone's verification"):
        ok(ph in ab, f"ab.py state missing: '{ph}'")
    skill = open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8").read()
    rp = section(skill, "Resume protocol", "##").lower()
    for ph in ("session-recovery.md", "verify against git", "never proof", "never resets retry counters"):
        ok(ph in rp, f"SKILL.md Resume protocol missing: '{ph}'")
    ok("LESSONS.md" in skill and "only the user may apply" in skill, "SKILL.md state files must list LESSONS.md with the user-only rule")
    ok("lessons cap in limits" in section(skill, "Phase 8", "###").lower(), "Phase 8 must reference the lessons cap in Limits")
    ok("session-recovery.md" in skill, "SKILL.md must link session-recovery.md")
    # init-artifacts supports selective copy and validates names
    ia = open(os.path.join(SKILL_DIR, "scripts", "init-artifacts.sh"), encoding="utf-8").read()
    ok("invalid template name" in ia and "no such template" in ia and "never overwrites" in ia.lower(), "init-artifacts.sh must validate names and never overwrite")


def check_security():
    """The security-engineer agent and the Security gate must exist and be wired into the lifecycle."""
    path = os.path.join(AGENT_DIR, "security-engineer.md")
    if not ok(os.path.isfile(path), "missing .claude/agents/security-engineer.md"):
        return
    body = open(path, encoding="utf-8").read().lower()
    for topic in SECURITY_AGENT_TOPICS:
        ok(topic in body, f"security-engineer.md missing topic/rule: '{topic}'")
    skill = open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8").read()
    gate = section(skill, "Security gate", "##")
    if ok(bool(gate), "SKILL.md: missing '## Security gate' section"):
        g = gate.lower()
        for phrase in ("cannot be accepted", "potential", "never marked fixed", "residual risk", "static inspection",
                       "automated scanning", "penetration testing", "not performed", "single source of truth", "same pass", "never consume the pass budget", "ask for acceptance once",
                       "potential", "decisions.md", "not independent", "unaccepted high blocks", "no user present",
                       "critical", "high", "medium", "low", "blocks", "residual risk", "explicit", "3-attempt",
                       "incomplete", "never silently ignore", "not required", "security-engineer", "architect",
                       "qa-engineer", "critical-reviewer", "re-check", "never \"secure\"", "threat model"):
            ok(phrase in g, f"Security gate missing '{phrase}'")
    wired = {"Phase 3": "security-engineer", "Phase 4": "security gate", "Phase 6": "security gate", "Phase 8": "security status"}
    for ph, needle in wired.items():
        body_ph = re.search(rf"^### {ph} .*?$(.*?)(?=^#{{2,3}} |\Z)", skill, flags=re.S | re.M)
        ok(bool(body_ph) and needle in body_ph.group(1).lower(), f"SKILL.md {ph} not connected to the security gate ('{needle}')")
    qp = section(skill, "Quality protocol", "##").lower()
    ok("security gate" in qp.split("7. **completion standard")[-1], "completion standard must include the Security gate")
    ok("security-engineer" in skill and "workflows/security.md" in skill, "SKILL.md must reference security-engineer and the security playbook")
    approval = section(skill, "Approval policy", "##").lower()
    ok("high security finding" in approval, "Approval policy must list accepting a High security finding as ask-first")
    ok(os.path.isfile(os.path.join(SKILL_DIR, "workflows", "security.md")), "missing workflows/security.md")
    sec = open(os.path.join(SKILL_DIR, "workflows", "security.md"), encoding="utf-8").read().lower()
    for phrase in ("static inspection", "automated scanning", "penetration", "not technically restricted", "never recorded as fixed",
                   "architecture (phase 3)", "milestone gate (phase 6)", "before completion (phase 8)", "trivial",
                   "security brief", "qa-engineer", "critical-reviewer", "ai/llm", "never write \"secure\"", "3-attempt"):
        ok(phrase in sec, f"workflows/security.md missing '{phrase}'")
    for f, needle in (("planning.md", "security-engineer"), ("implementation.md", "security regression"),
                      ("verification.md", "security gate"), ("delivery.md", "security status")):
        t = open(os.path.join(SKILL_DIR, "workflows", f), encoding="utf-8").read().lower()
        ok(needle in t, f"workflows/{f} not updated for the security gate ('{needle}')")
    tpl = os.path.join(SKILL_DIR, "templates", "SECURITY-REVIEW.md")
    ok(os.path.isfile(tpl), "missing templates/SECURITY-REVIEW.md")
    if os.path.isfile(tpl):
        t = open(tpl, encoding="utf-8").read()
        for h in ("Threat model", "Findings register", "Accepted residual risk", "Security gate status", "Methods used",
                  "Accepted by user (residual risk)", "never recorded as Fixed", "Penetration"):
            ok(h in t, f"SECURITY-REVIEW.md missing '{h}'")
    ok("until confirmed and fixed, disproved with evidence, or accepted" not in (skill + open(path, encoding="utf-8").read()).lower(),
       "a Potential Critical must never be acceptable (old 'or accepted' wording present)")
    ok("a critical or high security finding" in skill.lower(), "blocker definition must say 'a Critical or High security finding' (Medium/Low must not block)")
    # Limits stay consistent: only the 3-attempt and 5-pass bounds appear in the skill text
    nums = set(re.findall(r"\b(\d+)(?:-attempt| (?:fix )?attempts| passes| iterations)", skill))
    ok(nums <= {"3", "5"}, f"SKILL.md introduces other retry/iteration limits: {nums}")
    ok(skill.count("default 5 passes per milestone") == 1 and skill.count("3 fix attempts") == 1,
       "retry/iteration limits must each be defined exactly once in SKILL.md")
    # Both installers discover agents by glob, so the ninth agent installs without special-casing
    sh = open(os.path.join(ROOT, "install.sh"), encoding="utf-8").read()
    ps = open(os.path.join(ROOT, "install.ps1"), encoding="utf-8").read()
    ok('"$src_agents"/*.md' in sh and "security-engineer" not in sh, "install.sh must install agents by glob, not by name")
    ok(bool(re.search(r"Get-ChildItem[^\n]*\$srcAgents[^\n]*-Filter \*\.md", ps)) and "security-engineer" not in ps, "install.ps1 must install agents by glob, not by name")
    # No stale agent counts anywhere (docs, site, tests, launch kit)
    stale = re.compile(r"\b(?:eight|8)\b(?: specialist| Claude Code| AUTO-BUILDER| project)? (?:sub)?agents?\b|"
                       r"\beight (?:roles|files|agent)|\b8 (?:subagent|agent)|-eq 8\b", re.I)
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            if f == "validate.py" or not f.endswith((".md", ".html", ".py", ".sh", ".ps1", ".yml", ".json")):
                continue
            pth = os.path.join(base, f)
            hits = [(n, l) for n, l in enumerate(open(pth, encoding="utf-8").read().splitlines(), 1) if stale.search(l)]
            ok(not hits, f"{rel(pth)}: stale agent count at line {hits[0][0]}: {hits[0][1].strip()[:90]}" if hits else "")


def check_hygiene():
    skip_files = {"validate.py"}
    for p in list(md_files()) + [os.path.join(ROOT, "install.sh")]:
        ok(b"\r\n" not in open(p, "rb").read(), f"{rel(p)}: CRLF line endings")
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            if f in skip_files:
                continue
            p = os.path.join(base, f)
            try:
                text = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            for pat, label in SECRET_PATTERNS:
                if re.search(pat, text):
                    err(f"{rel(p)}: contains {label}")
    for junk in (".env", ".DS_Store", "node_modules"):
        ok(not os.path.exists(os.path.join(ROOT, junk)), f"unwanted file/dir present: {junk}")
    for needed in ("README.md", "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md", ".gitignore"):
        ok(os.path.isfile(os.path.join(ROOT, needed)), f"missing {needed}")


def main():
    check_skill()
    check_agents()
    check_links()
    check_scripts()
    check_protocol()
    check_security()
    check_router()
    check_ab()
    check_verification2()
    check_recovery()
    check_hygiene()
    if errors:
        print(f"FAILED: {len(errors)} problem(s) in {checks} checks")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK: {checks} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
