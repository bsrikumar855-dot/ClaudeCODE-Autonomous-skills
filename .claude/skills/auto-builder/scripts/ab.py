#!/usr/bin/env python3
"""AUTO-BUILDER read-only helper (optional). Standard library only; writes nothing.

Run it as:  python3 -I ab.py <command> [options]   (-I = isolated mode: nothing is imported
from the current directory, which is the user's project)

Commands
  graph           Validate the task table in TASKS.md, compute parallel waves, detect ownership
                  conflicts, and (optionally) check that the files actually changed stay inside
                  the declared ownership.
  browser-report  Check the FORMAT and internal consistency of a BROWSER-QA.md report. It proves
                  nothing about behaviour and must never be cited as verification.
  state           Resume check: compare what TASKS.md and PROGRESS.md CLAIM with what git and the
                  working tree SHOW (verified commits, stale evidence, dirty files by owner,
                  retry counters). It prints counters and never resets or changes anything.

Design rules (enforced by tests/test_ab.py):
  * read-only: no file writes, no deletes, no network, no eval/exec, no shell;
  * all input is untrusted: sizes are capped, paths are confined to the project root,
    refs are validated, git runs from a fixed allow-list with repo config neutralised;
  * output has control characters stripped.
Exit codes: 0 ok (warnings allowed), 1 problems found, 2 usage or unparseable input.
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import hashlib
import datetime

MAX_FILE_BYTES = 1_000_000
MAX_LINES = 20_000
MAX_ROWS = 500
MAX_GIT_OUTPUT = 5_000_000
MAX_ARTIFACT_BYTES = 50_000_000
MAX_WORKERS_PER_WAVE = 4  # must equal the "concurrent workers per wave" cap in SKILL.md Limits

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,30}$")
SHA_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
FLAGS_ALLOWED = {"high-risk", "human-decision", "shared-file"}
DONE_WORDS = {"done", "complete", "completed", "verified"}
CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
STATE_DIR = "docs/auto-builder"

# Files that are shared by nature: a task owning one of these is auto-flagged `shared-file`.
SHARED_PATTERNS = [
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "cargo.lock", "go.sum", "gemfile.lock",
    "composer.lock", "package.json", "pyproject.toml", "requirements*.txt", "go.mod", "cargo.toml",
    "*schema*", "*/migrations/*", "migrations/*", "*.sql", "index.*", "*/index.*", "__init__.py", "*/__init__.py",
    "*routes*", "*urls.py", "*.snap", "*__snapshots__*", "*.generated.*", "*.min.js", "dist/*",
]


class Problem(Exception):
    """Unparseable or unsafe input: exit code 2."""


def clean(text):
    return CONTROL_RE.sub("", str(text))


# --------------------------------------------------------------------------- safe input

def resolve_root(path):
    root = os.path.realpath(path or ".")
    if not os.path.isdir(root):
        raise Problem(f"root is not a directory: {clean(path)}")
    return root


def read_text(path, root):
    """Read a regular, non-symlink file that lives inside root, with size caps."""
    full = os.path.join(root, path) if not os.path.isabs(path) else path
    try:
        st = os.lstat(full)
    except OSError:
        raise Problem(f"cannot read: {clean(path)}")
    if os.path.islink(full) or not os.path.isfile(full):
        raise Problem(f"refusing non-regular file or symlink: {clean(path)}")
    real = os.path.realpath(full)
    if os.path.commonpath([real, root]) != root:
        raise Problem(f"path escapes the project root: {clean(path)}")
    if st.st_size > MAX_FILE_BYTES:
        raise Problem(f"file too large (> {MAX_FILE_BYTES} bytes): {clean(path)}")
    with open(real, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read(MAX_FILE_BYTES + 1)
    if text.count("\n") > MAX_LINES:
        raise Problem(f"too many lines (> {MAX_LINES}): {clean(path)}")
    return text


def run_git(root, args):
    """Run an allow-listed, read-only git command with repo configuration neutralised."""
    allowed = {"rev-parse", "merge-base", "diff", "status", "log", "cat-file", "ls-files"}
    if not args or args[0] not in allowed:
        raise Problem("internal: git subcommand not allowed")
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
        "HOME": os.devnull,
    }
    cmd = ["git", "--no-pager", "--no-optional-locks", "-c", "core.fsmonitor=false", "-c", "core.pager=cat",
           "-c", "core.hooksPath=" + os.devnull, "-c", "diff.external=", "-C", root] + args
    try:
        res = subprocess.run(cmd, cwd=root, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                             timeout=20, shell=False, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return 1, b""
    return res.returncode, res.stdout[:MAX_GIT_OUTPUT]


def valid_ref(ref):
    return ref == "HEAD" or bool(SHA_RE.match(ref))


# --------------------------------------------------------------------------- markdown tables

def find_table(text, heading):
    """Return (header_cells, rows) of the first table after a '## <heading>' line."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^#{2,3}\s+" + re.escape(heading) + r"\b", line.strip()):
            start = i + 1
            break
    if start is None:
        raise Problem(f"no '{heading}' section found")
    header, rows = None, []
    for line in lines[start:]:
        s = line.strip()
        if s.startswith("#") and header is not None:
            break
        if not s.startswith("|"):
            if header is not None and not s:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(cells)
        if len(rows) > MAX_ROWS:
            raise Problem(f"too many rows (> {MAX_ROWS})")
    if header is None:
        raise Problem(f"no table under '{heading}'")
    return header, rows


def split_list(cell):
    cell = cell.strip()
    if cell in ("", "-"):
        return []
    return [p.strip() for p in cell.split(",") if p.strip()]


def safe_owned_path(p):
    """Strict grammar for 'Files owned' entries; returns an error string or None."""
    if p.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", p) or "\\" in p:
        return f"absolute or non-portable path: {p!r}"
    if any(part == ".." for part in p.split("/")):
        return f"path traversal: {p!r}"
    if re.fullmatch(r"[*?./\[\]]*", p) or p in ("**", "**/*", "*/**"):
        return f"glob matches everything: {p!r}"
    return None


def parse_tasks(text):
    header, rows = find_table(text, "Tasks")
    col = {name: i for i, name in enumerate(header)}
    required = ["id", "dependencies", "owner", "files owned"]
    missing = [r for r in required if r not in col]
    if missing:
        raise Problem("task table missing required column(s): " + ", ".join(missing))
    tasks, errors, seen = {}, [], set()
    for n, r in enumerate(rows, 1):
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))
        tid = r[col["id"]]
        if not ID_RE.match(tid):
            raise Problem(f"row {n}: invalid task id {clean(tid)[:40]!r}")
        if tid in seen:
            raise Problem(f"duplicate task id {tid}")
        seen.add(tid)
        deps = split_list(r[col["dependencies"]])
        for d in deps:
            if not ID_RE.match(d):
                raise Problem(f"{tid}: invalid dependency id {clean(d)[:40]!r}")
        files = split_list(r[col["files owned"]])
        for f in files:
            bad = safe_owned_path(f)
            if bad:
                raise Problem(f"{tid}: {clean(bad)}")
        flags = split_list(r[col["flags"]]) if "flags" in col else []
        for fl in flags:
            if fl not in FLAGS_ALLOWED:
                raise Problem(f"{tid}: unknown flag {clean(fl)[:30]!r} (allowed: {sorted(FLAGS_ALLOWED)})")
        status = r[col["status"]].strip().lower() if "status" in col else ""
        tasks[tid] = {"id": tid, "deps": deps, "owner": r[col["owner"]].strip(), "files": files,
                      "flags": flags, "status": status, "done": status in DONE_WORDS}
    return tasks, errors


# --------------------------------------------------------------------------- analysis

def literal_prefix(p):
    m = re.search(r"[*?\[]", p)
    return p if not m else p[: m.start()]


def overlaps(a, b):
    a, b = a.rstrip("/"), b.rstrip("/")
    if a == b or b.startswith(a + "/") or a.startswith(b + "/"):
        return True
    wild = any(c in a + b for c in "*?[")
    if wild:
        if fnmatch.fnmatchcase(a, b) or fnmatch.fnmatchcase(b, a):
            return True
        la, lb = literal_prefix(a), literal_prefix(b)
        return la.startswith(lb) or lb.startswith(la)
    return False


def is_shared(path):
    low = path.lower()
    base = low.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatchcase(low, p) or fnmatch.fnmatchcase(base, p) for p in SHARED_PATTERNS)


def covered(path, patterns):
    for p in patterns:
        p = p.rstrip("/")
        if path == p or path.startswith(p + "/") or fnmatch.fnmatchcase(path, p):
            return True
    return False


def analyse(tasks, include_done=False):
    errors, warnings = [], []
    active = {k: v for k, v in tasks.items() if include_done or not v["done"]}
    # dependency checks
    for t in tasks.values():
        for d in t["deps"]:
            if d not in tasks:
                errors.append(f"{t['id']}: depends on unknown task {d}")
            if d == t["id"]:
                errors.append(f"{t['id']}: depends on itself")
    # cycles (Kahn) over active tasks, dependencies on done tasks count as satisfied
    indeg = {k: 0 for k in active}
    out = {k: [] for k in active}
    for t in active.values():
        for d in t["deps"]:
            if d in active:
                indeg[t["id"]] += 1
                out[d].append(t["id"])
    queue = sorted(k for k, v in indeg.items() if v == 0)
    order, wave = [], {}
    while queue:
        n = queue.pop(0)
        order.append(n)
        wave[n] = 1 + max([wave[d] for d in active[n]["deps"] if d in active] or [0])
        for m in sorted(out[n]):
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
    cyclic = sorted(k for k in active if k not in wave)
    if cyclic:
        errors.append("dependency cycle involving: " + ", ".join(cyclic))
    # blocked by human decisions
    needs = {k for k, v in active.items() if "human-decision" in v["flags"]}
    blocked, changed = set(), True
    while changed:
        changed = False
        for k, v in active.items():
            if k not in blocked and any(d in needs or d in blocked for d in v["deps"]):
                blocked.add(k)
                changed = True
    # auto shared-file flagging
    auto_shared = {}
    for k, v in active.items():
        hits = [f for f in v["files"] if is_shared(f)]
        if hits and "shared-file" not in v["flags"]:
            auto_shared[k] = hits
    shared = {k for k, v in active.items() if "shared-file" in v["flags"]} | set(auto_shared)
    # per-wave checks
    waves = {}
    for k, w in wave.items():
        waves.setdefault(w, []).append(k)
    for w in sorted(waves):
        ids = sorted(waves[w])
        if len(ids) > MAX_WORKERS_PER_WAVE:
            warnings.append(f"wave {w}: {len(ids)} tasks exceed the concurrent-workers cap ({MAX_WORKERS_PER_WAVE}); split the wave")
        if len(ids) >= 2:
            for k in ids:
                if not active[k]["owner"] or not active[k]["files"]:
                    errors.append(f"wave {w}: parallel task {k} needs an Owner and Files owned")
            for i, a in enumerate(ids):
                for b in ids[i + 1:]:
                    for fa in active[a]["files"]:
                        for fb in active[b]["files"]:
                            if overlaps(fa, fb):
                                errors.append(f"wave {w}: ownership conflict between {a} ({fa}) and {b} ({fb})")
                                break
                        else:
                            continue
                        break
    for k in sorted(auto_shared):
        warnings.append(f"{k}: owns shared file(s) {', '.join(auto_shared[k])}; auto-flagged shared-file (integrate serially)")
    for k in sorted(shared):
        if k in wave and len(waves[wave[k]]) > 1 and any(is_shared(f) for f in active[k]["files"]):
            others = [o for o in waves[wave[k]] if o != k]
            warnings.append(f"{k}: shared-file task runs in wave {wave[k]} alongside {', '.join(sorted(others))}; the lead integrates it last")
    return {"errors": errors, "warnings": warnings, "waves": {str(w): sorted(v) for w, v in sorted(waves.items())},
            "needs_decision": sorted(needs), "blocked_by_decision": sorted(blocked), "shared_file": sorted(shared),
            "high_risk": sorted(k for k, v in active.items() if "high-risk" in v["flags"]),
            "done": sorted(k for k, v in tasks.items() if v["done"])}


def changed_files(root, base):
    files = set()
    rc, out = run_git(root, ["status", "--porcelain=v1", "-z", "--untracked-files=all"])
    if rc != 0:
        raise Problem("git status failed (is this a git repository?)")
    parts = out.decode("utf-8", "replace").split("\0")
    i = 0
    while i < len(parts):
        e = parts[i]
        if len(e) > 3:
            files.add(e[3:])
            if e[0] in "RC":
                i += 1
                if i < len(parts) and parts[i]:
                    files.add(parts[i])
        i += 1
    if base:
        if not valid_ref(base):
            raise Problem("invalid --base (use HEAD or a hex commit id)")
        rc, out = run_git(root, ["diff", "--name-only", "-z", "--no-ext-diff", "--no-textconv", base, "--"])
        if rc != 0:
            raise Problem("git diff failed (unknown --base?)")
        files |= {p for p in out.decode("utf-8", "replace").split("\0") if p}
    return sorted(files)


def check_changes(tasks, wave_ids, changed):
    owned = {}
    for k in wave_ids:
        owned[k] = tasks[k]["files"]
    allp = [p for v in owned.values() for p in v]
    problems = []
    for f in changed:
        if f == ".git" or f.startswith(".git/") or f == STATE_DIR or f.startswith(STATE_DIR + "/"):
            problems.append(f"{f}: state files and .git are lead-only; a worker must not change them")
        elif not covered(f, allp):
            problems.append(f"{f}: outside the declared ownership of the checked tasks")
    return problems


# --------------------------------------------------------------------------- browser report

BQA_TOOLS = {"project-e2e", "session-browser", "playwright", "headless-chrome", "none"}
BQA_ENVS = {"local", "staging", "test"}
BQA_RESULTS = {"PASS", "FAIL", "NOT RUN", "BLOCKED"}
BQA_KINDS = {"success", "failure"}
LOOPBACK = re.compile(r"^(localhost|127\.\d+\.\d+\.\d+|\[::1\]|[a-z0-9-]+\.localhost)$", re.I)
URL_RE = re.compile(r"^(https?)://([^/:@\s]+|\[[0-9a-fA-F:]+\])(:\d{1,5})?(/[^\s]*)?$")
SENSITIVE_ART = re.compile(r"(\.har$|trace\.zip$|cookie|storage[-_]?state|session|token|credential|secret|\.sqlite$)", re.I)


def origin_of(url):
    m = URL_RE.match(url.strip())
    if not m:
        return None, None
    scheme, host, port = m.group(1).lower(), m.group(2).lower(), m.group(3) or ""
    return host, f"{scheme}://{host}{port}"


def parse_header(text):
    head = text.split("\n## ", 1)[0]
    kv = {}
    for line in head.splitlines():
        m = re.match(r"^\s*[-*]\s*([A-Za-z][A-Za-z /-]*?)\s*:\s*(.*)$", line)
        if m:
            kv[m.group(1).strip().lower()] = m.group(2).strip()
    return kv


def parse_started(value):
    v = value.strip().replace("Z", "+00:00").replace(" ", "T", 1)
    try:
        dt = datetime.datetime.fromisoformat(v)
    except ValueError:
        raise Problem("Started must be an ISO 8601 timestamp, e.g. 2026-10-31T10:00:00Z")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.timestamp()


def tracked_by_git(root, rel):
    rc, out = run_git(root, ["ls-files", "-z", "--", rel])
    return rc == 0 and bool(out.strip(b"\0"))


def cmd_browser_report(args):
    root = resolve_root(args.root)
    text = read_text(args.report, root)
    hdr = parse_header(text)
    for key in ("tool", "environment", "base url", "started", "origin allowlist"):
        if not hdr.get(key):
            raise Problem(f"report header is missing '{key}'")
    errors, warnings = [], []
    tool = hdr["tool"].lower()
    if tool not in BQA_TOOLS:
        errors.append(f"Tool must be one of {sorted(BQA_TOOLS)}")
    env = hdr["environment"].lower()
    if env == "production":
        errors.append("Environment 'production' is not allowed: browser QA never targets production")
    elif env not in BQA_ENVS:
        errors.append(f"Environment must be one of {sorted(BQA_ENVS)}")
    started = parse_started(hdr["started"])
    approved = hdr.get("approved by user", "").lower().startswith("yes")
    allow = set()
    for item in re.split(r"[,\s]+", hdr["origin allowlist"]):
        if not item:
            continue
        host, origin = origin_of(item)
        if origin is None:
            errors.append(f"allowlist entry is not a valid http(s) origin without credentials: {clean(item)[:60]}")
        else:
            allow.add(origin)
            if not LOOPBACK.match(host) and not (approved and env in ("staging", "test")):
                errors.append(f"non-loopback origin {clean(origin)[:60]} needs 'Approved by user: yes' and Environment staging/test")
            if re.search(r"(^|[.-])(prod|production|www)([.-]|$)", host) and env != "test":
                errors.append(f"origin {clean(origin)[:60]} looks like production")
    base_host, base_origin = origin_of(hdr["base url"])
    if base_origin is None:
        errors.append("Base URL is not a valid http(s) URL without credentials")
    elif base_origin not in allow:
        errors.append("Base URL origin is not in the Origin allowlist")
    header, rows = find_table(text, "Scenarios")
    col = {n: i for i, n in enumerate(header)}
    need = ["id", "kind", "url", "scenario", "expected", "actual", "result", "artifact"]
    missing = [n for n in need if n not in col]
    if missing:
        raise Problem("scenario table missing column(s): " + ", ".join(missing))
    seen, counts, has_failure_kind, checked = set(), {"PASS": 0, "FAIL": 0, "NOT RUN": 0, "BLOCKED": 0}, False, 0
    for r in rows:
        r = r + [""] * (len(header) - len(r))
        sid = r[col["id"]]
        if not ID_RE.match(sid):
            raise Problem(f"invalid scenario id {clean(sid)[:30]!r}")
        if sid in seen:
            raise Problem(f"duplicate scenario id {sid}")
        seen.add(sid)
        kind, result = r[col["kind"]].lower(), r[col["result"]].upper()
        actual, artifact = r[col["actual"]].strip(), r[col["artifact"]].strip()
        if kind not in BQA_KINDS:
            errors.append(f"{sid}: Kind must be success or failure")
        has_failure_kind = has_failure_kind or kind == "failure"
        if result not in BQA_RESULTS:
            errors.append(f"{sid}: Result must be one of {sorted(BQA_RESULTS)}")
            continue
        counts[result] += 1
        host, origin = origin_of(r[col["url"]])
        if origin is None:
            errors.append(f"{sid}: URL is not a valid http(s) URL without credentials")
        elif origin not in allow:
            errors.append(f"{sid}: URL origin {clean(origin)[:60]} is not in the Origin allowlist")
        if tool == "none" and result in ("PASS", "FAIL"):
            errors.append(f"{sid}: Tool is 'none', so a result of {result} cannot be real (use NOT RUN or BLOCKED)")
        if result in ("PASS", "FAIL"):
            if not actual:
                errors.append(f"{sid}: {result} needs a non-empty Actual")
            if not artifact:
                errors.append(f"{sid}: {result} needs an Artifact path or 'none: <reason>'")
        if not artifact:
            continue
        if artifact.lower().startswith("none"):
            if not re.match(r"^none\s*:\s*\S+", artifact, flags=re.I):
                errors.append(f"{sid}: Artifact 'none' needs a reason ('none: <reason>')")
            continue
        bad = safe_owned_path(artifact)
        if bad:
            errors.append(f"{sid}: artifact {clean(bad)}")
            continue
        full = os.path.join(root, artifact)
        try:
            st = os.lstat(full)
        except OSError:
            errors.append(f"{sid}: artifact does not exist: {clean(artifact)[:80]}")
            continue
        if os.path.islink(full) or not os.path.isfile(full):
            errors.append(f"{sid}: artifact must be a regular file, not a symlink or directory")
            continue
        if os.path.commonpath([os.path.realpath(full), root]) != root:
            errors.append(f"{sid}: artifact escapes the project root")
            continue
        checked += 1
        if st.st_size == 0:
            errors.append(f"{sid}: artifact is empty")
        if st.st_mtime < started - 1:
            errors.append(f"{sid}: artifact is older than the report's Started time (not produced by this run)")
        if SENSITIVE_ART.search(artifact):
            errors.append(f"{sid}: artifact name suggests cookies, tokens, sessions or HAR/trace data; do not keep credentials-bearing files")
        sha = r[col["sha256"]].strip().lower() if "sha256" in col else ""
        if sha:
            if not re.fullmatch(r"[0-9a-f]{12,64}", sha):
                errors.append(f"{sid}: sha256 must be 12-64 hex characters")
            elif st.st_size <= MAX_ARTIFACT_BYTES:
                with open(full, "rb") as fh:
                    digest = hashlib.sha256(fh.read(MAX_ARTIFACT_BYTES + 1)).hexdigest()
                if not digest.startswith(sha):
                    errors.append(f"{sid}: sha256 does not match the artifact")
        if tracked_by_git(root, artifact):
            warnings.append(f"{sid}: artifact is tracked by git; keep artifacts in a git-ignored directory")
    if rows and not has_failure_kind and not hdr.get("no failure scenarios because"):
        warnings.append("no failure-kind scenario: important journeys need a failure path (or state 'No failure scenarios because: ...')")
    if not rows:
        warnings.append("no scenarios in the report")
    return {"errors": errors, "warnings": warnings, "counts": counts, "scenarios": len(rows), "artifacts_checked": checked,
            "tool": tool, "environment": env,
            "notice": "FORMAT CHECK ONLY: this proves no behaviour and must not be cited as verification; open at least one artifact."}


def render_report(result):
    out = [f"tool={result['tool']} environment={result['environment']} scenarios={result['scenarios']} "
           f"PASS={result['counts']['PASS']} FAIL={result['counts']['FAIL']} NOT RUN={result['counts']['NOT RUN']} "
           f"BLOCKED={result['counts']['BLOCKED']} artifacts checked={result['artifacts_checked']}"]
    out += ["WARNING: " + clean(w) for w in result["warnings"]]
    out += ["ERROR: " + clean(e) for e in result["errors"]]
    out.append("FORMAT OK" if not result["errors"] else f"{len(result['errors'])} problem(s)")
    out.append(result["notice"])
    return "\n".join(out)


# --------------------------------------------------------------------------- resume state

def git_lines(root, args):
    rc, out = run_git(root, args)
    if rc != 0:
        return None
    return [p for p in out.decode("utf-8", "replace").split("\0") if p]


def first_int(text, default=None):
    m = re.search(r"\d+", text or "")
    return int(m.group(0)) if m else default


def table_cell(header, row, *prefixes):
    for i, name in enumerate(header):
        if any(name.startswith(p) for p in prefixes):
            return row[i] if i < len(row) else ""
    return ""


def cmd_state(args):
    root = resolve_root(args.root)
    tasks_path = args.tasks
    text = read_text(tasks_path, root)
    try:
        sh, srows = find_table(text, "Status")
    except Problem:
        return {"state": "none", "attention": [], "notes": ["no Status block found: treat this as a fresh task, not a resume"],
                "counters": {}, "milestones": [], "stale": [], "dirty": [], "in_progress": [], "next": ["start normally"]}
    status = {}
    for r in srows:
        if len(r) >= 2:
            status[r[0].strip().lower()] = r[1].strip()

    def sget(prefix):
        for k, v in status.items():
            if k.startswith(prefix):
                return v
        return ""

    tasks, _ = parse_tasks(text)
    gates = []
    try:
        gh, grows = find_table(text, "Milestone gates")
        for r in grows:
            gates.append({"milestone": table_cell(gh, r, "milestone").strip(), "passed": table_cell(gh, r, "gate passed").strip().lower(),
                          "sha": table_cell(gh, r, "verified at").strip(), "review": table_cell(gh, r, "review").strip().lower(),
                          "command": table_cell(gh, r, "verification command").strip()})
    except Problem:
        pass
    attention, notes = [], []
    repo = run_git(root, ["rev-parse", "--verify", "HEAD"])
    have_git = repo[0] == 0
    head = repo[1].decode().strip() if have_git else ""
    if not have_git:
        attention.append("not a git repository (or no commits): recorded commits cannot be verified")
    # milestone verification anchors
    ms = []
    for g in gates:
        entry = {"milestone": g["milestone"], "passed": g["passed"], "sha": g["sha"], "anchor": "none", "changed_since": []}
        sha = g["sha"]
        if sha:
            if not SHA_RE.match(sha):
                entry["anchor"] = "invalid"
                attention.append(f"{g['milestone']}: 'Verified at' is not a commit id")
            elif have_git:
                rc, _ = run_git(root, ["cat-file", "-e", sha + "^{commit}"])
                if rc != 0:
                    entry["anchor"] = "missing"
                    attention.append(f"{g['milestone']}: verified commit {sha[:12]} does not exist here: re-verify the milestone")
                else:
                    rc, _ = run_git(root, ["merge-base", "--is-ancestor", sha, "HEAD"])
                    if rc == 0:
                        entry["anchor"] = "ok"
                        ch = git_lines(root, ["diff", "--name-only", "-z", "--no-ext-diff", "--no-textconv", sha, "HEAD", "--"]) or []
                        entry["changed_since"] = ch
                    else:
                        entry["anchor"] = "unknown"
                        attention.append(f"{g['milestone']}: verified commit {sha[:12]} is not an ancestor of HEAD (rebased, squashed or another branch): status unknown, re-verify")
        elif g["passed"].startswith("y"):
            entry["anchor"] = "unanchored"
            notes.append(f"{g['milestone']}: gate marked passed but no 'Verified at' commit recorded")
        ms.append(entry)
    by_ms = {m["milestone"].lower(): m for m in ms}
    # working tree
    dirty = []
    if have_git:
        lines = changed_files(root, None)
        dirty = lines
    # ownership attribution
    stale, dirty_report, inprog = [], [], []
    for t in tasks.values():
        status_l = t["status"]
        if status_l in ("in progress", "in-progress", "wip"):
            inprog.append(t["id"])
    mcol_ok = True
    try:
        th, trows = find_table(text, "Tasks")
        mi = th.index("milestone") if "milestone" in th else None
        for r in trows:
            tid = r[th.index("id")]
            tasks[tid]["milestone"] = (r[mi].strip().lower() if mi is not None and mi < len(r) else "")
    except Problem:
        mcol_ok = False
    for t in tasks.values():
        if not t["done"]:
            continue
        m = by_ms.get(t.get("milestone", ""))
        if m is None or m["anchor"] in ("none", "unanchored"):
            notes.append(f"{t['id']}: marked done but its milestone has no verified commit: its evidence is unanchored")
            continue
        if m["anchor"] in ("unknown", "missing", "invalid"):
            stale.append({"task": t["id"], "reason": f"milestone verified commit is {m['anchor']}", "files": []})
            continue
        hit = sorted({f for f in m["changed_since"] + dirty if covered(f, t["files"])})
        if hit:
            stale.append({"task": t["id"], "reason": "owned files changed after the milestone was verified", "files": hit[:20]})
    if stale:
        attention.append("stale evidence (best-effort, by declared ownership): " + ", ".join(x["task"] for x in stale))
    for f in dirty:
        if f == STATE_DIR or f.startswith(STATE_DIR + "/"):
            dirty_report.append({"file": f, "owner": "state file (lead)", "who": "lead"})
            continue
        owners = [t["id"] for t in tasks.values() if covered(f, t["files"])]
        active = [o for o in owners if tasks[o]["status"] in ("in progress", "in-progress", "wip")]
        if active:
            dirty_report.append({"file": f, "owner": ",".join(active), "who": "lead resolves (interrupted in-progress task)"})
        elif owners:
            dirty_report.append({"file": f, "owner": ",".join(owners), "who": "changed after the owning task was recorded: re-verify"})
        else:
            dirty_report.append({"file": f, "owner": "-", "who": "not owned by any task: treat as the user's change; do not commit or touch"})
    if any(d["owner"] == "-" for d in dirty_report):
        attention.append("dirty files owned by no task (the user's): " + ", ".join(d["file"] for d in dirty_report if d["owner"] == "-")[:200])
    # counters (read-only)
    attempts_cell = sget("failing checks")
    pass_cell = sget("pass for this milestone")
    counters = {"pass": clean(pass_cell), "total passes": clean(sget("total passes")), "failing checks": clean(attempts_cell),
                "max attempts recorded in Status": max([int(n) for n in re.findall(r"(?<![\d.])(\d+)(?![\d.])", attempts_cell)] or [0])}
    progress_text = ""
    try:
        progress_text = read_text(args.progress or os.path.join(os.path.dirname(tasks_path), "PROGRESS.md"), root)
    except Problem:
        notes.append("PROGRESS.md not readable: counter cross-check skipped")
    if progress_text:
        recorded = [int(m.group(1)) for m in re.finditer(r"attempt\s+(\d+)\s+of\s+\d+", progress_text, flags=re.I)]
        counters["max attempt recorded in PROGRESS.md"] = max(recorded or [0])
        if recorded and max(recorded) > counters["max attempts recorded in Status"]:
            attention.append(f"counter regression: PROGRESS.md records attempt {max(recorded)} but the Status block shows {counters['max attempts recorded in Status']}: do not reset retry budgets (only the user may)")
    pending = [g["milestone"] for g in gates if not g["passed"].startswith("y") and (not g["review"] or g["review"] in ("no", "n/a", "pending"))]
    if sget("failing checks") and sget("failing checks") not in ("-", "none"):
        notes.append("failed checks recorded: " + clean(sget("failing checks")))
    cmds = [g["command"] for g in gates if g["command"] and not g["passed"].startswith("y")]
    nxt = []
    if any(d["owner"] == "-" for d in dirty_report):
        nxt.append("inspect the user's uncommitted changes first; do not commit or modify them")
    if any(m["anchor"] in ("unknown", "missing", "invalid") for m in ms):
        nxt.append("re-verify the milestones whose verified commit is unknown or missing")
    nxt.append("re-run the current milestone's verification command(s) and compare with the recorded result" + (f" ({clean(cmds[0])[:80]})" if cmds else ""))
    if stale:
        nxt.append("re-verify the stale tasks before building on them")
    if inprog:
        nxt.append("resolve interrupted in-progress tasks: " + ", ".join(inprog))
    nxt.append("then continue from the safest next task; never mark anything complete because a status says so")
    return {"state": "present", "head": head[:12], "attention": attention, "notes": notes, "counters": counters,
            "counters_note": "read-only: this tool never changes or resets counters; only the user may reset a budget",
            "milestones": ms, "stale": stale, "dirty": dirty_report, "in_progress": inprog, "pending_review": pending, "next": nxt}


def render_state(r):
    out = []
    if r["state"] == "none":
        return "\n".join(["NO STATE"] + ["NOTE: " + clean(n) for n in r["notes"]])
    out.append(f"HEAD {r['head']}  in-progress tasks: {', '.join(r['in_progress']) or '-'}  pending review: {', '.join(r['pending_review']) or '-'}")
    for m in r["milestones"]:
        out.append(f"milestone {clean(m['milestone'])}: verified-at {clean(m['sha'])[:12] or '-'} anchor={m['anchor']} changed-since={len(m['changed_since'])}")
    out.append("counters: " + clean(json.dumps(r["counters"])))
    out.append(clean(r["counters_note"]))
    for d in r["dirty"]:
        out.append(f"dirty: {clean(d['file'])}  owner={clean(d['owner'])}  -> {clean(d['who'])}")
    for x in r["stale"]:
        out.append(f"STALE: {x['task']}: {clean(x['reason'])} {clean(', '.join(x['files']))[:120]}")
    for n in r["notes"]:
        out.append("NOTE: " + clean(n))
    for a in r["attention"]:
        out.append("ATTENTION: " + clean(a))
    out += ["next: " + clean(n) for n in r["next"]]
    out.append("OK" if not r["attention"] else f"{len(r['attention'])} item(s) need attention")
    return "\n".join(out)


# --------------------------------------------------------------------------- commands

def cmd_graph(args):
    root = resolve_root(args.root)
    text = read_text(args.tasks, root)
    tasks, _ = parse_tasks(text)
    result = analyse(tasks, include_done=args.include_done)
    if args.check_changes or args.changed:
        ids = [t for t in (args.tasks_ids.split(",") if args.tasks_ids else []) if t]
        for t in ids:
            if t not in tasks:
                raise Problem(f"unknown task in --ids: {clean(t)[:30]}")
        if not ids:
            ids = [k for k, v in tasks.items() if v["status"] in ("in progress", "in-progress", "wip")]
            if args.wave:
                ids = result["waves"].get(str(args.wave), [])
        if not ids:
            raise Problem("no tasks selected for the change check (use --ids or --wave)")
        changed = [clean(p) for p in args.changed] if args.changed else changed_files(root, args.base)
        result["change_problems"] = check_changes(tasks, ids, changed)
        result["changed"] = changed
        result["errors"] = result["errors"] + result["change_problems"]
    return result


def render(result):
    out = []
    for w, ids in result["waves"].items():
        out.append(f"wave {w}: {', '.join(ids)}")
    if result["done"]:
        out.append("done: " + ", ".join(result["done"]))
    if result["needs_decision"]:
        out.append("needs user decision (not schedulable): " + ", ".join(result["needs_decision"]))
    if result["blocked_by_decision"]:
        out.append("blocked by those decisions: " + ", ".join(result["blocked_by_decision"]))
    if result["high_risk"]:
        out.append("high-risk (review at the milestone gate): " + ", ".join(result["high_risk"]))
    for w in result["warnings"]:
        out.append("WARNING: " + clean(w))
    for e in result["errors"]:
        out.append("ERROR: " + clean(e))
    out.append("OK" if not result["errors"] else f"{len(result['errors'])} problem(s)")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ab.py", description="AUTO-BUILDER read-only helper")
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("graph", help="validate the TASKS.md task graph and ownership")
    g.add_argument("tasks", nargs="?", default="docs/auto-builder/TASKS.md")
    g.add_argument("--root", default=".")
    g.add_argument("--include-done", action="store_true")
    g.add_argument("--check-changes", action="store_true", help="compare changed files (git) with declared ownership")
    g.add_argument("--changed", nargs="*", help="explicit changed paths instead of git (for tests and dry runs)")
    g.add_argument("--base", help="HEAD or a hex commit id to diff against (in addition to the working tree)")
    g.add_argument("--ids", dest="tasks_ids", help="comma-separated task ids whose ownership applies")
    g.add_argument("--wave", type=int, help="check the tasks in this wave")
    g.add_argument("--json", action="store_true")
    b = sub.add_parser("browser-report", help="check the format and consistency of a BROWSER-QA.md report (not evidence)")
    b.add_argument("report", nargs="?", default="docs/auto-builder/BROWSER-QA.md")
    b.add_argument("--root", default=".")
    b.add_argument("--json", action="store_true")
    st = sub.add_parser("state", help="resume check: recorded state versus git and the working tree (read-only)")
    st.add_argument("tasks", nargs="?", default="docs/auto-builder/TASKS.md")
    st.add_argument("--progress", help="PROGRESS.md path (default: next to TASKS.md)")
    st.add_argument("--root", default=".")
    st.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.command == "graph":
            result = cmd_graph(args)
            text = render(result)
        elif args.command == "state":
            result = cmd_state(args)
            text = render_state(result)
            print(json.dumps(result, indent=2) if args.json else text)
            return 1 if result["attention"] else 0
        else:
            result = cmd_browser_report(args)
            text = render_report(result)
    except Problem as exc:
        print("ERROR: " + clean(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2) if args.json else text)
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
