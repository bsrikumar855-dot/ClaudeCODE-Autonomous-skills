#!/usr/bin/env python3
"""Behaviour and hostile-input tests for .claude/skills/auto-builder/scripts/ab.py.

Everything runs in temp directories; the real repository is never modified.
Run:  python3 -I tests/test_ab.py
"""
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AB = os.path.join(ROOT, ".claude", "skills", "auto-builder", "scripts", "ab.py")
GENV = {"PATH": os.environ.get("PATH", ""), "HOME": "/nonexistent", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1"}

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("ok   - " if cond else "FAIL - ") + name + ("" if cond else f"  [{detail}]"))


def ab(args, cwd, env=None, timeout=60):
    r = subprocess.run([sys.executable, "-I", AB] + args, cwd=cwd, capture_output=True, text=True,
                       timeout=timeout, env=env)
    return r.returncode, r.stdout, r.stderr


def tasks_md(rows, header="| ID | Task | Milestone | Dependencies | Acceptance criteria | Verification | Status | Owner | Files owned | Flags |",
             sep=None):
    cols = header.count("|") - 1
    sep = sep or "|" + "---|" * cols
    return "# Execution backlog\n\n## Tasks\n\n" + header + "\n" + sep + "\n" + "\n".join(rows) + "\n\n## Blockers\n"


def row(i, deps="-", status="todo", owner="backend-engineer", files="src/a.py", flags=""):
    return f"| {i} | t | M1 | {deps} | c | v | {status} | {owner} | {files} | {flags} |"


def project(content, name="TASKS.md"):
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "docs", "auto-builder"))
    with open(os.path.join(d, "docs", "auto-builder", name), "w", encoding="utf-8") as fh:
        fh.write(content)
    return d


def tree_hash(path):
    h = hashlib.sha256()
    for base, dirs, files in os.walk(path):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(base, f)
            h.update(p.encode())
            if os.path.isfile(p) and not os.path.islink(p):
                h.update(open(p, "rb").read())
    return h.hexdigest()


def git(d, *a):
    return subprocess.run(["git", "-C", d] + list(a), capture_output=True, text=True, env=GENV)


def git_project(content):
    d = project(content)
    git(d, "init", "-q")
    git(d, "config", "user.email", "t@t")
    git(d, "config", "user.name", "t")
    os.makedirs(os.path.join(d, "src"))
    open(os.path.join(d, "src", "a.py"), "w").write("x=1\n")
    open(os.path.join(d, "src", "b.py"), "w").write("y=1\n")
    git(d, "add", "-A")
    git(d, "commit", "-qm", "base")
    return d


def main():
    P = "docs/auto-builder/TASKS.md"
    # ---------------------------------------------------------------- graph behaviour
    d = project(tasks_md([row("T1", files="api/"), row("T2", files="web/"), row("T3", deps="T1,T2", files="tests/")]))
    rc, out, err = ab(["graph", P], d)
    check("graph: valid DAG computes waves", rc == 0 and "wave 1: T1, T2" in out and "wave 2: T3" in out, out + err)
    rc, out, _ = ab(["graph", P, "--json"], d)
    check("graph: --json is valid JSON with waves", json.loads(out)["waves"] == {"1": ["T1", "T2"], "2": ["T3"]})

    d = project(tasks_md([row("T1", deps="T2"), row("T2", deps="T1")]))
    rc, out, _ = ab(["graph", P], d)
    check("graph: cycle detected", rc == 1 and "cycle" in out, out)

    d = project(tasks_md([row("T1", deps="T9")]))
    rc, out, _ = ab(["graph", P], d)
    check("graph: missing dependency detected", rc == 1 and "unknown task T9" in out, out)

    d = project(tasks_md([row("T1", files="src/"), row("T2", files="src/app.py")]))
    rc, out, _ = ab(["graph", P], d)
    check("graph: same-wave ownership overlap (dir prefix) is an error", rc == 1 and "ownership conflict" in out, out)

    d = project(tasks_md([row("T1", files="src/*.py"), row("T2", files="src/a.py")]))
    rc, out, _ = ab(["graph", P], d)
    check("graph: glob overlap detected", rc == 1 and "ownership conflict" in out, out)

    d = project(tasks_md([row("T1", files="api/"), row("T2", files="web/")]))
    rc, out, _ = ab(["graph", P], d)
    check("graph: disjoint parallel tasks pass", rc == 0 and "OK" in out, out)

    d = project(tasks_md([row("T1", files="package.json")]))
    rc, out, _ = ab(["graph", P], d)
    check("graph: shared-file auto-flag warns", rc == 0 and "auto-flagged shared-file" in out, out)

    d = project(tasks_md([row("T1", files="package.json"), row("T2", files="package.json")]))
    rc, out, _ = ab(["graph", P], d)
    check("graph: two tasks owning a shared file in one wave conflict", rc == 1 and "ownership conflict" in out, out)

    d = project(tasks_md([row("T1", owner=""), row("T2", files="web/")]))
    rc, out, _ = ab(["graph", P], d)
    check("graph: unowned parallel task is an error", rc == 1 and "needs an Owner" in out, out)

    d = project(tasks_md([row("T1", files="x/", flags="human-decision"), row("T2", deps="T1", files="y/"), row("T3", files="z/", flags="high-risk")]))
    rc, out, _ = ab(["graph", P], d)
    check("graph: human-decision blocks dependants; high-risk reported",
          rc == 0 and "needs user decision" in out and "blocked by those decisions: T2" in out and "high-risk" in out, out)

    d = project(tasks_md([row("T1", status="Done", files="a/"), row("T2", deps="T1", files="b/")]))
    rc, out, _ = ab(["graph", P], d)
    check("graph: done tasks are excluded and satisfy dependencies", rc == 0 and "done: T1" in out and "wave 1: T2" in out, out)

    hdr = "| ID | Task | Milestone | Dependencies | Acceptance criteria | Verification | Status | Owner | Files owned |"
    d = project(tasks_md(["| T1 | t | M1 | - | c | v | todo | be | a/ |"], header=hdr))
    rc, out, err = ab(["graph", P], d)
    check("graph: missing Flags column is treated as none", rc == 0, out + err)

    d = project(tasks_md([row(f"T{i}", files=f"d{i}/") for i in range(1, 7)]))
    rc, out, _ = ab(["graph", P], d)
    check("graph: wave larger than the worker cap warns", rc == 0 and "exceed the concurrent-workers cap" in out, out)

    # ---------------------------------------------------------------- strict grammar: fail loudly (exit 2)
    bad = {
        "missing required column": tasks_md([row("T1")], header="| ID | Task | Dependencies | Owner |", sep="|---|---|---|---|"),
        "duplicate id": tasks_md([row("T1"), row("T1")]),
        "invalid id": tasks_md([row("T 1")]),
        "path traversal": tasks_md([row("T1", files="../etc")]),
        "absolute path": tasks_md([row("T1", files="/etc/passwd")]),
        "match-everything glob": tasks_md([row("T1", files="**")]),
        "unknown flag": tasks_md([row("T1", flags="yolo")]),
        "no table": "# nothing\n\n## Tasks\n\nplain text\n",
        "no section": "# nothing\n",
    }
    for name, content in bad.items():
        d = project(content)
        rc, out, err = ab(["graph", P], d)
        check(f"grammar: {name} fails loudly (exit 2)", rc == 2 and err.startswith("ERROR"), f"rc={rc} {err}")

    # ---------------------------------------------------------------- change checks
    d = project(tasks_md([row("T1", status="in progress", files="src/"), row("T2", status="in progress", files="web/")]))
    rc, out, _ = ab(["graph", P, "--changed", "src/a.py", "web/x.js"], d)
    check("changes: files inside ownership pass", rc == 0, out)
    rc, out, _ = ab(["graph", P, "--changed", "src/a.py", "lib/other.py"], d)
    check("changes: out-of-ownership file is flagged", rc == 1 and "lib/other.py" in out, out)
    rc, out, _ = ab(["graph", P, "--changed", "docs/auto-builder/TASKS.md"], d)
    check("changes: state file edit by a worker is flagged", rc == 1 and "lead-only" in out, out)
    rc, out, _ = ab(["graph", P, "--changed", ".git/config"], d)
    check("changes: .git edit is flagged", rc == 1 and "lead-only" in out, out)

    d = git_project(tasks_md([row("T1", status="in progress", files="src/a.py")]))
    git(d, "add", "-A"); git(d, "commit", "-qm", "tasks")
    open(os.path.join(d, "src", "a.py"), "a").write("x=2\n")
    rc, out, _ = ab(["graph", P, "--check-changes"], d)
    check("git mode: change inside ownership passes", rc == 0, out)
    open(os.path.join(d, "src", "b.py"), "a").write("y=2\n")
    open(os.path.join(d, "src", "untracked.py"), "w").write("z\n")
    rc, out, _ = ab(["graph", P, "--check-changes"], d)
    check("git mode: modified unowned and untracked files are flagged",
          rc == 1 and "src/b.py" in out and "src/untracked.py" in out, out)
    rc, out, err = ab(["graph", P, "--check-changes", "--base=--output=/tmp/pwn"], d)
    check("git mode: option-like --base is rejected", rc == 2 and not os.path.exists("/tmp/pwn"), out + err)
    rc, out, err = ab(["graph", P, "--check-changes", "--base", "HEAD;touch /tmp/pwn2"], d)
    check("git mode: shell metacharacters in --base are rejected", rc == 2 and not os.path.exists("/tmp/pwn2"), out + err)
    rc, out, err = ab(["graph", P, "--check-changes", "--base", "HEAD"], d)
    check("git mode: --base HEAD accepted", rc in (0, 1) and "invalid --base" not in err, out + err)

    # ---------------------------------------------------------------- hostile repository configuration
    d = git_project(tasks_md([row("T1", status="in progress", files="src/")]))
    sentinel = os.path.join(d, "PWNED")
    evil = os.path.join(d, "evil.sh")
    open(evil, "w").write(f"#!/bin/sh\ntouch '{sentinel}'\nprintf '\\0'\n")
    os.chmod(evil, 0o755)
    with open(os.path.join(d, ".git", "config"), "a") as fh:
        fh.write(f"\n[core]\n\tfsmonitor = {evil}\n\tpager = touch '{sentinel}'\n[diff]\n\texternal = {evil}\n")
    open(os.path.join(d, "src", "a.py"), "a").write("x=3\n")
    control = subprocess.run(["git", "-C", d, "status", "--porcelain"], capture_output=True, text=True,
                             env={**GENV, "GIT_OPTIONAL_LOCKS": "1"})
    control_fired = os.path.exists(sentinel)
    if os.path.exists(sentinel):
        os.remove(sentinel)
    rc, out, err = ab(["graph", P, "--check-changes", "--base", "HEAD"], d)
    check("hostile .git/config: helper does not execute repo-configured commands", not os.path.exists(sentinel), out + err)
    check("hostile .git/config: control (unprotected git) shows the risk is real or git ignores it",
          control_fired or control.returncode == 0)

    # ---------------------------------------------------------------- path safety and caps
    d = project(tasks_md([row("T1")]))
    rc, out, err = ab(["graph", "../outside.md"], d)
    check("paths: traversal outside root is refused", rc == 2, err)
    outside = os.path.join(tempfile.mkdtemp(), "t.md")
    open(outside, "w").write(tasks_md([row("T1")]))
    rc, out, err = ab(["graph", outside, "--root", d], d)
    check("paths: absolute path outside root is refused", rc == 2, err)
    os.symlink(outside, os.path.join(d, "docs", "auto-builder", "LINK.md"))
    rc, out, err = ab(["graph", "docs/auto-builder/LINK.md"], d)
    check("paths: symlink is refused", rc == 2 and "symlink" in err, err)
    rc, out, err = ab(["graph", "docs"], d)
    check("paths: directory is refused", rc == 2, err)
    big = project("## Tasks\n\n| ID | Dependencies | Owner | Files owned |\n|---|---|---|---|\n" + "| T1 | - | a | b |\n" * 1)
    open(os.path.join(big, "docs", "auto-builder", "TASKS.md"), "w").write("x" * 2_000_000)
    rc, out, err = ab(["graph", P], big)
    check("caps: oversized file is refused", rc == 2 and "too large" in err, err)
    many = project(tasks_md([row(f"T{i}", files=f"d{i}/") for i in range(1, 600)]))
    rc, out, err = ab(["graph", P], many)
    check("caps: too many rows is refused", rc == 2 and "too many rows" in err, err)
    t0 = time.time()
    longline = project(tasks_md(["| T1 | t | M1 | - | " + "a" * 800_000 + " | v | todo | be | x/ | |"]))
    rc, out, err = ab(["graph", P], longline)
    check("caps: very long line is parsed quickly (no ReDoS)", time.time() - t0 < 10 and rc in (0, 2), f"{time.time()-t0:.1f}s rc={rc}")
    esc = project(tasks_md([row("T1", flags="x\x1b[31mred\x07")]))
    rc, out, err = ab(["graph", P], esc)
    check("output: control characters are stripped from messages", rc == 2 and "unknown flag" in err and "\x1b" not in err + out and "\x07" not in err + out, repr(err))

    # ---------------------------------------------------------------- read-only and isolation
    d = git_project(tasks_md([row("T1", status="in progress", files="src/a.py")]))
    git(d, "add", "-A"); git(d, "commit", "-qm", "t")
    open(os.path.join(d, "src", "a.py"), "a").write("x=4\n")
    before = tree_hash(d)
    if os.getuid() != 0:
        for base, dirs, files in os.walk(d):
            for n in dirs + files:
                p = os.path.join(base, n)
                if not os.path.islink(p):
                    os.chmod(p, os.stat(p).st_mode & ~0o222)
        os.chmod(d, os.stat(d).st_mode & ~0o222)
        rc, out, err = ab(["graph", P, "--check-changes", "--base", "HEAD"], d)
        check("read-only: runs on a fully read-only tree (incl. .git)", rc in (0, 1), out + err)
        for base, dirs, files in os.walk(d):
            for n in dirs + files:
                p = os.path.join(base, n)
                if not os.path.islink(p):
                    os.chmod(p, os.stat(p).st_mode | 0o200)
        os.chmod(d, os.stat(d).st_mode | 0o200)
    else:
        rc, out, err = ab(["graph", P, "--check-changes", "--base", "HEAD"], d)
    check("read-only: tree and .git are byte-identical afterwards", tree_hash(d) == before)

    iso = tempfile.mkdtemp()
    mark = os.path.join(iso, "IMPORTED")
    for mod in ("json", "re", "os"):
        pass
    open(os.path.join(iso, "json.py"), "w").write(f"open({mark!r}, 'w').write('x')\n")
    open(os.path.join(iso, "re.py"), "w").write(f"open({mark!r}, 'w').write('x')\n")
    os.makedirs(os.path.join(iso, "docs", "auto-builder"))
    open(os.path.join(iso, "docs", "auto-builder", "TASKS.md"), "w").write(tasks_md([row("T1")]))
    rc, out, err = ab(["graph", P], iso, env={**os.environ, "PYTHONPATH": iso})
    check("isolation: python -I ignores planted modules in cwd and PYTHONPATH", rc == 0 and not os.path.exists(mark), out + err)

    # ---------------------------------------------------------------- shipped file properties
    mode = os.stat(AB).st_mode
    check("shipping: ab.py is not executable", not (mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)))

    # ---------------------------------------------------------------- browser-report
    import datetime
    started = "2026-10-31T10:00:00Z"
    started_ts = datetime.datetime(2026, 10, 31, 10, 0, 0, tzinfo=datetime.timezone.utc).timestamp()

    def bqa(rows, tool="playwright", env="local", base="http://localhost:3000", allow="http://localhost:3000",
            approved="n/a", extra="", files=None):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "docs", "auto-builder"))
        os.makedirs(os.path.join(d, "qa-artifacts"))
        for name, content, mtime in (files or []):
            fp = os.path.join(d, name)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            open(fp, "wb").write(content)
            os.utime(fp, (mtime, mtime))
        head = (f"# Browser QA report\n\n- Tool: {tool}\n- Environment: {env}\n- Base URL: {base}\n- Origin allowlist: {allow}\n"
                f"- Started: {started}\n- Approved by user: {approved}\n{extra}\n## Scenarios\n\n"
                "| ID | Kind | URL | Scenario | Expected | Actual | Result | Artifact | sha256 | Console/network errors |\n"
                "|---|---|---|---|---|---|---|---|---|---|\n")
        open(os.path.join(d, "docs", "auto-builder", "BROWSER-QA.md"), "w").write(head + "\n".join(rows) + "\n")
        return d

    def brow(i="B1", kind="success", url="http://localhost:3000/login", actual="dashboard shown", result="PASS",
             art="qa-artifacts/b1.png", sha=""):
        return f"| {i} | {kind} | {url} | s | e | {actual} | {result} | {art} | {sha} | |"

    R = "docs/auto-builder/BROWSER-QA.md"
    png = b"\x89PNG\r\n\x1a\n" + b"x" * 64
    fresh = started_ts + 60
    good = [("qa-artifacts/b1.png", png, fresh), ("qa-artifacts/b2.png", png, fresh)]
    rows_ok = [brow(), brow("B2", "failure", result="FAIL", actual="error shown", art="qa-artifacts/b2.png")]
    d = bqa(rows_ok, files=good)
    rc, out, err = ab(["browser-report", R], d)
    check("browser-report: consistent report passes the FORMAT check and says so",
          rc == 0 and "FORMAT OK" in out and "FORMAT CHECK ONLY" in out, out + err)
    d = bqa([brow(art="none: tool cannot take screenshots"), brow("B2", "failure", result="FAIL", art="none: no screenshot support")], files=[])
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: 'none: <reason>' artifacts are accepted", rc == 0, out)
    d = bqa([brow(result="NOT RUN", actual="", art="none: not run"), brow("B2", "failure", result="BLOCKED", actual="", art="none: app would not start")], tool="none")
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: tool none with NOT RUN/BLOCKED is honest and passes", rc == 0, out)
    d = bqa([brow(), brow("B2", "failure", result="FAIL", art="qa-artifacts/b2.png")], tool="none", files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: tool none with PASS/FAIL rows is rejected (fabrication)", rc == 1 and "Tool is 'none'" in out, out)
    d = bqa([brow(actual="")], files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: PASS with empty Actual is rejected", rc == 1 and "non-empty Actual" in out, out)
    d = bqa([brow(art="qa-artifacts/missing.png")], files=[])
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: artifact that does not exist is rejected", rc == 1 and "does not exist" in out, out)
    d = bqa([brow()], files=[("qa-artifacts/b1.png", b"", fresh)])
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: empty artifact is rejected", rc == 1 and "empty" in out, out)
    d = bqa([brow()], files=[("qa-artifacts/b1.png", png, started_ts - 86400)])
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: artifact older than Started is rejected (stale/not from this run)", rc == 1 and "older than" in out, out)
    good_sha = hashlib.sha256(png).hexdigest()[:16]
    d = bqa([brow(sha=good_sha)], files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: matching sha256 passes", rc == 0, out)
    d = bqa([brow(sha="0" * 16)], files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: wrong sha256 is rejected", rc == 1 and "sha256 does not match" in out, out)
    d = bqa([brow()], env="production", files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: production environment is rejected", rc == 1 and "production" in out, out)
    d = bqa([brow(url="https://staging.example.com/x")], env="staging", base="https://staging.example.com", allow="https://staging.example.com", files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: non-loopback origin without user approval is rejected", rc == 1 and "needs 'Approved by user: yes'" in out, out)
    d = bqa([brow(url="https://staging.example.com/x")], env="staging", base="https://staging.example.com", allow="https://staging.example.com",
            approved="yes", files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: user-approved staging origin is accepted", rc == 0, out)
    d = bqa([brow(url="https://app.prod.example.com/x")], env="staging", base="https://app.prod.example.com", allow="https://app.prod.example.com",
            approved="yes", files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: production-looking host is rejected even when approved", rc == 1 and "looks like production" in out, out)
    d = bqa([brow(), brow("B2", "failure", url="http://evil.example.net/x", result="FAIL", art="qa-artifacts/b2.png")], files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: URL outside the origin allowlist is rejected", rc == 1 and "not in the Origin allowlist" in out, out)
    d = bqa([brow()], base="http://user:pw@localhost:3000", allow="http://localhost:3000", files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: credentials in a URL are rejected", rc == 1 and "without credentials" in out, out)
    d = bqa([brow(art="../outside.png")], files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: artifact path traversal is rejected", rc == 1 and "path traversal" in out, out)
    d = bqa([brow(art="/etc/hostname")], files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: absolute artifact path is rejected", rc == 1 and "absolute" in out, out)
    d = bqa([brow(art="qa-artifacts/link.png")], files=good)
    os.symlink("/etc/hostname", os.path.join(d, "qa-artifacts", "link.png"))
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: symlinked artifact is rejected", rc == 1 and "symlink" in out, out)
    d = bqa([brow(art="qa-artifacts/session.har")], files=[("qa-artifacts/session.har", png, fresh)])
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: HAR/cookie/session-like artifacts are flagged", rc == 1 and "credentials" in out, out)
    d = bqa(rows_ok, files=good)
    git(d, "init", "-q"); git(d, "add", "qa-artifacts/b1.png")
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: git-tracked artifact produces a warning", rc == 0 and "tracked by git" in out, out)
    d = bqa([brow()], files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: no failure scenario produces a warning", rc == 0 and "no failure-kind scenario" in out, out)
    d = bqa([brow(result="MAYBE")], files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: invalid Result value is rejected", rc == 1 and "Result must be one of" in out, out)
    d = bqa([brow(kind="happy")], files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: invalid Kind value is rejected", rc == 1 and "Kind must be" in out, out)
    d = bqa([brow(art="none:")], files=good)
    rc, out, _ = ab(["browser-report", R], d)
    check("browser-report: 'none' without a reason is rejected", rc == 1 and "needs a reason" in out, out)
    d = bqa([brow()], files=good)
    txt = open(os.path.join(d, R)).read().replace("- Tool: playwright\n", "")
    open(os.path.join(d, R), "w").write(txt)
    rc, out, err = ab(["browser-report", R], d)
    check("browser-report: missing header field fails loudly (exit 2)", rc == 2 and "missing 'tool'" in err, err)
    d = bqa([brow()], files=good)
    txt = open(os.path.join(d, R)).read().replace("Started: 2026-10-31T10:00:00Z", "Started: yesterday")
    open(os.path.join(d, R), "w").write(txt)
    rc, out, err = ab(["browser-report", R], d)
    check("browser-report: unparseable Started fails loudly (exit 2)", rc == 2 and "ISO 8601" in err, err)
    d = bqa([brow("B1\x1b[31m")], files=good)
    rc, out, err = ab(["browser-report", R], d)
    check("browser-report: control characters never reach the output", "\x1b" not in out + err, repr(err))
    d = bqa([brow("B1"), brow("B1")], files=good)
    rc, out, err = ab(["browser-report", R], d)
    check("browser-report: duplicate scenario ids fail loudly (exit 2)", rc == 2, err)
    d = bqa([brow()], files=good)
    open(os.path.join(d, R), "w").write("x" * 2_000_000)
    rc, out, err = ab(["browser-report", R], d)
    check("browser-report: oversized report is refused", rc == 2 and "too large" in err, err)
    d = bqa([brow()], files=good)
    ro = tree_hash(d)
    rc, out, err = ab(["browser-report", R], d)
    check("browser-report: writes nothing", tree_hash(d) == ro)

    failed = [n for n, ok_ in results if not ok_]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
