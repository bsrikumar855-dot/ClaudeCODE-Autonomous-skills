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
}
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
        if name in ("critical-reviewer", "architect", "product-manager", "researcher", "qa-engineer"):
            ok("Edit" not in fm.get("tools", "") and "Write" not in fm.get("tools", ""),
               f"{rel(path)}: reviewer/read-only role must not have Edit/Write")
    names = [n for n in found]
    ok(len(names) == len(set(names)), "duplicate agent names")
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
