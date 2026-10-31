#!/usr/bin/env python3
"""Deliberate-breakage tests: each mutation, applied to a COPY of the repo, must make a check fail
with the expected message. Three kinds, reported separately because they prove different things:
  behaviour : the helper's CODE is broken and tests/test_ab.py must fail (expected message starts "ab:")
  static    : code/scripts/agents/fixtures are broken and tests/validate.py must fail
  wording   : a safety-critical sentence in a markdown file is changed and tests/validate.py must fail.
              This only proves the sentence is pinned; it does NOT show the model would behave differently.

Run:  python3 -I tests/test_mutations.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SK = ".claude/skills/auto-builder"

# (name, file, old, new, expected substring in validator output[, replace_all])
MUTATIONS = [
    ("ab: repo_risks fails open on unreadable config", f"{SK}/scripts/ab.py", '    if rc != 0:\n        raise Problem("could not read the repository\'s git configuration safely (is this a git repository?); refusing working-tree checks")', "    if rc != 0:\n        return []", "ab:fail-closed"),
    ("ab: repo_risks ignores truncated output", f"{SK}/scripts/ab.py", "    if len(out) >= MAX_GIT_OUTPUT:", "    if False:", "ab:config so large"),
    ("ab: status recurses into submodules", f"{SK}/scripts/ab.py", ', "--ignore-submodules=all"]', ']', "ab:submodule"),
    ("ab: dotted diff drivers not denied", f"{SK}/scripts/ab.py", "diff\\.(external$|.*\\.(command|textconv)$)", "diff\\.(external$|[^.]*\\.(command|textconv)$)", "ab:dotted diff driver"),
    ("ab: metadata hosts allowed", f"{SK}/scripts/ab.py", "    if h in METADATA_NAMES or h == \"fd00:ec2::254\":\n        return \"a cloud metadata name or address\"", "    if False:\n        return None", "ab:hosts"),
    ("ab: trailing dot bypasses the metadata block", f"{SK}/scripts/ab.py", 'h = host.strip("[]").lower().rstrip(".")', 'h = host.strip("[]").lower()', "ab:hosts"),
    ("ab: NAT64 metadata address not unwrapped", f"{SK}/scripts/ab.py", "        elif ip in ipaddress.ip_network(\"64:ff9b::/96\"):", "        elif False:", "ab:hosts"),
    ("ab: changed_files stops calling the guard first", f"{SK}/scripts/ab.py", "def changed_files(root, base):\n    require_safe_worktree(root)\n    files = set()", "def changed_files(root, base):\n    files = set()\n    require_safe_worktree(root)", "changed_files must call require_safe_worktree() first"),
    ("ab: stops refusing a hostile repo git config", f"{SK}/scripts/ab.py", "    require_safe_worktree(root)\n    files = set()", "    files = set()", "ab:filter regression"),
    ("ab: accepts any 'lfs' filter command", f"{SK}/scripts/ab.py", "LFS_OK.get(name.lower()) != value.strip()", "False", "ab:non-standard command is refused"),
    ("ab: runs a git found inside the project", f"{SK}/scripts/ab.py", "not inside(os.path.realpath(d), root)", "True", "ab:hijack"),
    ("ab: output keeps newlines (line forgery)", f"{SK}/scripts/ab.py", 'r"[\\x00-\\x1f\\x7f-\\x9f', 'r"[\\x00-\\x09\\x0b-\\x1f\\x7f-\\x9f', "ab:output injection"),
    ("ab: line-length cap removed", f"{SK}/scripts/ab.py", "MAX_LINE_CHARS = 20_000", "MAX_LINE_CHARS = 10**9", "ab:ReDoS"),
    ("ab: ancestry check always says ok", f"{SK}/scripts/ab.py", '                    if rc == 0:\n                        entry["anchor"] = "ok"', '                    if True:\n                        entry["anchor"] = "ok"', "ab:squashed"),
    ("ab: stale detection disabled", f"{SK}/scripts/ab.py", "        if hit:\n            stale.append", "        if False:\n            stale.append", "ab:owned file changed"),
    ("ab: untracked files ignored in ownership check", f"{SK}/scripts/ab.py", '"--untracked-files=all"', '"--untracked-files=no"', "ab:untracked"),
    ("ab: tool none allows PASS", f"{SK}/scripts/ab.py", 'if tool == "none" and result in ("PASS", "FAIL"):', "if False:", "ab:tool none"),
    ("ab: stale artifacts accepted", f"{SK}/scripts/ab.py", "if mtime < started - 1:", "if False:", "ab:older than Started"),
    ("ab: production environment accepted", f"{SK}/scripts/ab.py", '    if env == "production":\n        errors.append("Environment \'production\' is not allowed: browser QA never targets production")\n    elif env not in BQA_ENVS:\n        errors.append(f"Environment must be one of {sorted(BQA_ENVS)}")', "    pass", "ab:production environment"),
    ("ab: wrong sha256 accepted", f"{SK}/scripts/ab.py", "if not hashlib.sha256(data).hexdigest().startswith(sha):", "if False:", "ab:wrong sha256"),
    ("ab: ownership overlap not detected", f"{SK}/scripts/ab.py", '    if a == b or b.startswith(a + "/") or a.startswith(b + "/"):\n        return True', "    if False:\n        return True", "ab:same-wave ownership overlap"),
    ("ab: cycles not detected", f"{SK}/scripts/ab.py", '    if cyclic:\n        errors.append("dependency cycle involving: "', '    if False:\n        errors.append("dependency cycle involving: "', "ab:cycle detected"),
    ("ab: counter regression not detected", f"{SK}/scripts/ab.py", "if recorded and max(recorded) > counters", "if False and max(recorded) > counters", "ab:counter regression"),
    ("router: security row loses gate", f"{SK}/workflows/router.md", "| security:if-triggered; tdd:yes |", "| tdd:yes |", "must have security"),
    ("router: unknown specialist", f"{SK}/workflows/router.md", "security-assessment | playbooks/security-assessment.md | security-engineer, architect, qa-engineer", "security-assessment | playbooks/security-assessment.md | security-engineer, wizard, qa-engineer", "unknown specialist 'wizard'"),
    ("router: playbook anchor missing", f"{SK}/workflows/router.md", "playbooks/inquiry.md#research", "playbooks/inquiry.md#nonsense", "anchor '#nonsense'"),
    ("router: eval-set label removed", "tests/fixtures/routing-eval.json", '"status": "NOT RUN"', '"status": "PASSED"', "NOT RUN"),
    ("router: eval-set loses all ambiguous cases", "tests/fixtures/routing-eval.json", '"kind": "ambiguous"', '"kind": "clear"', "ambiguous", True),
    ("playbook restates gates", f"{SK}/playbooks/bug-fix.md", "## Steps", "Gates: security:never\n\n## Steps", "restates specialists/gates"),
    ("playbook numeric cap", f"{SK}/playbooks/feature.md", "## Principles", "Retry at most 9 times.\n\n## Principles", "numeric cap"),
    ("playbook cites unknown principle", f"{SK}/playbooks/refactor.md", "P01, P02, P03, P12", "P01, P99", "unknown principle"),
    ("playbook completion criteria emptied", f"{SK}/playbooks/performance.md", "- Correctness tests pass; complexity added is justified by the measured gain.\n- No claim of improvement without a measurement.", "", "at least two concrete bullets"),
    ("principle removed", f"{SK}/principles/engineering-principles.md", "| P07 | Error handling |", "| P07x | Error handling |", "principle P07 missing"),
    ("workflow numeric cap", f"{SK}/workflows/arena.md", "Never for conventional", "At most 7 rounds. Never for conventional", "numeric cap outside SKILL.md Limits"),
    ("arena loses rubric-first rule", f"{SK}/workflows/arena.md", "into `DECISIONS.md` first", "somewhere", "into `decisions.md` first"),
    ("discovery loses skip rules", f"{SK}/workflows/discovery.md", "**Skip it**", "**Maybe**", "skip it"),
    ("untrusted-data rule weakened", f"{SK}/SKILL.md", "can **never** grant an approval", "may grant an approval", "never** grant an approval"),
    ("router can remove gates", f"{SK}/SKILL.md", "Routing only **adds** gates, never removes them", "Routing may adjust gates", "only **adds** gates"),
    ("limits section loses babysit cap", f"{SK}/SKILL.md", "3 fix-push-recheck rounds", "some rounds", "3 fix-push-recheck rounds"),
    ("TASKS template loses Flags", f"{SK}/templates/TASKS.md", "| Files owned | Flags |", "| Files owned |", "TASKS.md template needs Flags"),
    ("agent gains Edit tool", ".claude/agents/security-engineer.md", "tools: Read, Bash, Grep, Glob", "tools: Read, Edit, Bash, Grep, Glob", "tools changed"),
    ("agent removed", ".claude/agents/researcher.md", None, None, "exactly nine specialist agents"),
    ("phase 6 disconnected from security gate", f"{SK}/SKILL.md", "Where the Security gate applies to the milestone, run it. ", "", "Phase 6 not connected"),
    ("old 'or accepted' wording for Potential Critical", f"{SK}/SKILL.md", "blocks exactly like a Critical until confirmed and fixed or disproved with evidence (never accepted)", "keeps blocking until confirmed and fixed, disproved with evidence, or accepted", "Potential Critical must never be acceptable"),
    ("ab.py imports socket", f"{SK}/scripts/ab.py", "import subprocess", "import subprocess\nimport socket", "imports outside the allow-list"),
    ("ab.py opens a file for writing (fdopen)", f"{SK}/scripts/ab.py", 'with os.fdopen(fd, "rb") as fh:', 'with os.fdopen(fd, "wb") as fh:', "read-only only"),
    ("ab.py opens with write flags (os.open)", f"{SK}/scripts/ab.py", "os.O_RDONLY | getattr(os, \"O_NOFOLLOW\", 0)", "os.O_RDWR | os.O_CREAT", "write flags"),
    ("ab.py drops O_NOFOLLOW", f"{SK}/scripts/ab.py", 'getattr(os, "O_NOFOLLOW", 0)', "0", "O_NOFOLLOW"),
    ("ab.py allows non-config git subcommand misuse", f"{SK}/scripts/ab.py", '["config", "--local", "--null", "--list"]', '["config", "--global", "--list"]', "config"),
    ("ab.py removes a file", f"{SK}/scripts/ab.py", '    out = CONTROL_RE.sub("", str(text))', "    os.remove('x')\n    out = CONTROL_RE.sub(\"\", str(text))", "calls os.remove"),
    ("ab.py uses shell", f"{SK}/scripts/ab.py", "shell=False", "shell=True", "shell"),
    ("ab.py drops git hardening", f"{SK}/scripts/ab.py", '"core.fsmonitor=false"', '"core.x=false"', "git hardening missing"),
    ("ab.py worker cap drifts from Limits", f"{SK}/scripts/ab.py", "MAX_WORKERS_PER_WAVE = 4", "MAX_WORKERS_PER_WAVE = 9", "MAX_WORKERS_PER_WAVE"),
    ("ab.py shipped executable", f"{SK}/scripts/ab.py", "@chmod+x", "", "non-executable"),
    ("docs invoke ab.py without -I", f"{SK}/workflows/swarm.md", "python3 -I ${CLAUDE_SKILL_DIR}/scripts/ab.py graph`", "python3 ${CLAUDE_SKILL_DIR}/scripts/ab.py graph`", "must be invoked as 'python3 -I'"),
    ("swarm drops ownership violation rule", f"{SK}/workflows/swarm.md", "**violation: record it as a gap**", "fine", "violation: record it as a gap"),
    ("swarm lets parallelism bypass gates", f"{SK}/workflows/swarm.md", "**Parallelism never bypasses a gate.**", "Parallelism is fast.", "parallelism never bypasses a gate"),
    ("review drops reproduce-or-drop", f"{SK}/workflows/independent-review.md", "## Reproduce or drop", "## Reproduce", "reproduce or drop"),
    ("review allows implicit external review", f"{SK}/workflows/independent-review.md", "explicit approval **for this run**", "approval", "for this run"),
    ("browser QA allows simulation", f"{SK}/workflows/browser-qa.md", "Never simulate a browser, invent a screenshot, or write PASS without having run it.", "Simulate if needed.", "never simulate"),
    ("browser QA drops the origin allowlist", f"{SK}/workflows/browser-qa.md", "origin allowlist", "origin list", "origin allowlist"),
    ("browser QA lets the checker be cited", f"{SK}/workflows/browser-qa.md", "**never cite the checker as verification**", "cite the checker", "never cite the checker as verification"),
    ("browser-report drops the notice", f"{SK}/scripts/ab.py", "FORMAT CHECK ONLY", "OK", "FORMAT CHECK ONLY"),
    ("tdd allows weakening checks", f"{SK}/workflows/tdd.md", "**Never weaken the check**", "Weakening is fine", "never weaken the check"),
    ("SKILL drops the not-performed rule", f"{SK}/SKILL.md", 'say "browser QA not performed"', 'say nothing', "'not performed' rule"),
    ("recovery lets a restart reset budgets", f"{SK}/workflows/session-recovery.md", "**Retry budgets are not reset by restarting.**", "Retry budgets reset on restart.", "retry budgets are not reset by restarting"),
    ("recovery trusts recorded status", f"{SK}/workflows/session-recovery.md", "Never assume a task is complete because its status says so;", "Trust the status;", "never assume a task is complete"),
    ("recovery lets the skill apply its own proposals", f"{SK}/workflows/session-recovery.md", "You never apply it", "You may apply it", "you never apply it"),
    ("lessons template merges proposals into lessons", f"{SK}/templates/LESSONS.md", "## Proposals for AUTO-BUILDER (never applied by the skill; the user decides)", "## Notes", "proposals for auto-builder"),
    ("state check loses the counter-regression warning", f"{SK}/scripts/ab.py", "counter regression:", "counter note:", "counter regression"),
    ("state check can claim anchors after a rebase", f"{SK}/scripts/ab.py", "is not an ancestor of HEAD", "is fine", "not an ancestor of HEAD"),
    ("init-artifacts accepts any name", f"{SK}/scripts/init-artifacts.sh", "invalid template name", "ok", "must validate names"),
    ("release allows standing push approval", f"{SK}/playbooks/release.md", "Each push needs its own approval", "One approval covers all pushes", "each push needs its own approval"),
    ("release allows merge in babysit", f"{SK}/playbooks/release.md", "no `gh pr merge`, ", "", "no `gh pr merge`"),
    ("release lets the skill edit CI to pass", f"{SK}/playbooks/release.md", "edit CI/workflow files to pass", "adjust CI", "edit ci/workflow files"),
    ("release trusts comment commands", f"{SK}/playbooks/release.md", "their commands are never executed", "follow their commands", "commands are never executed"),
    ("babysit cap removed from Limits", f"{SK}/SKILL.md", "at most 1 hour elapsed", "no time limit", "1 hour elapsed"),
    ("3-attempt limit stated authoritatively twice", f"{SK}/SKILL.md", "The iteration limits are **3** attempts", "The iteration limits: 3 fix attempts and **3** attempts", "exactly once"),
]


def run_validate(tree):
    r = subprocess.run([sys.executable, "-I", os.path.join(tree, "tests", "validate.py")], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def run_ab(tree):
    r = subprocess.run([sys.executable, "-I", os.path.join(tree, "tests", "test_ab.py")], capture_output=True, text=True, timeout=600)
    return r.returncode, r.stdout + r.stderr


def kind(rel, expect):
    if expect.startswith("ab:"):
        return "behaviour"
    return "wording" if rel.endswith((".md", ".json")) and "fixtures" not in rel and "/agents/" not in rel else "static"


def run_one(base, tmp, idx, item):
    """Apply one mutation to a private copy and return (ok, kind, printed_text)."""
    name, rel, old, new, expect, *opt = item
    expect0 = expect
    tree = os.path.join(tmp, f"m{idx}")
    shutil.copytree(base, tree)
    try:
        path = os.path.join(tree, rel)
        if old is None:  # delete the file
            os.remove(path)
        elif old == "@chmod+x":  # make the file executable
            os.chmod(path, os.stat(path).st_mode | 0o111)
        else:
            text = open(path, encoding="utf-8").read()
            if old not in text:
                return False, None, f"FAIL - {name}: mutation target not found in {rel}"
            replaced = text.replace(old, new) if opt and opt[0] else text.replace(old, new, 1)
            open(path, "w", encoding="utf-8").write(replaced)
        if expect.startswith("ab:"):
            rc, out = run_ab(tree)
            expect = expect[3:]
        else:
            rc, out = run_validate(tree)
        k = kind(rel, expect0)
        if rc != 0 and expect.lower() in out.lower():
            return True, k, f"ok   - [{k}] {name}"
        return False, k, f"FAIL - {name}: rc={rc}, expected message containing {expect!r}\n{out[:400]}"
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def main():
    from concurrent.futures import ThreadPoolExecutor
    with tempfile.TemporaryDirectory() as tmp:
        base = os.path.join(tmp, "base")
        shutil.copytree(ROOT, base, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
        rc, out = run_validate(base)
        if rc != 0:
            print("FAIL baseline does not pass:\n" + out[:800]); return 1
        print("ok   - baseline passes")
        workers = max(2, min(8, os.cpu_count() or 2))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda a: run_one(base, tmp, *a), enumerate(MUTATIONS)))
    fails, tally = 0, {}
    for ok_, k, text in results:
        print(text)
        if ok_:
            tally[k] = tally.get(k, 0) + 1
        else:
            fails += 1
    print("\ndetected by kind: " + ", ".join(f"{k}={v}" for k, v in sorted(tally.items())) +
          "  (wording guards pin a sentence; they do not prove behaviour)")
    print(f"{len(MUTATIONS) + 1 - fails}/{len(MUTATIONS) + 1} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
