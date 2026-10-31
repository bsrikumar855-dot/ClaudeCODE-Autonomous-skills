#!/usr/bin/env python3
"""Deliberate-breakage tests: each mutation, applied to a COPY of the repo, must make
tests/validate.py fail with the expected message. Proves the validators detect what they claim to.

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
    ("3-attempt limit defined twice", f"{SK}/SKILL.md", "Iteration limits are defined once: **3** attempts", "Iteration limits: 3 fix attempts and **3** attempts", "defined exactly once"),
]


def run_validate(tree):
    r = subprocess.run([sys.executable, "-I", os.path.join(tree, "tests", "validate.py")], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    fails = 0
    with tempfile.TemporaryDirectory() as tmp:
        base = os.path.join(tmp, "base")
        shutil.copytree(ROOT, base, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
        rc, out = run_validate(base)
        if rc != 0:
            print("FAIL baseline does not pass:\n" + out[:800]); return 1
        print("ok   - baseline passes")
        for name, rel, old, new, expect, *opt in MUTATIONS:
            tree = os.path.join(tmp, "m")
            shutil.rmtree(tree, ignore_errors=True)
            shutil.copytree(base, tree)
            path = os.path.join(tree, rel)
            if old is None:
                os.remove(path)
            else:
                text = open(path, encoding="utf-8").read()
                if old not in text:
                    print(f"FAIL - {name}: mutation target not found in {rel}"); fails += 1; continue
                open(path, "w", encoding="utf-8").write(text.replace(old, new) if opt and opt[0] else text.replace(old, new, 1))
            rc, out = run_validate(tree)
            if rc != 0 and expect.lower() in out.lower():
                print(f"ok   - {name}")
            else:
                print(f"FAIL - {name}: validator rc={rc}, expected message containing {expect!r}\n{out[:400]}"); fails += 1
    print(f"\n{len(MUTATIONS) + 1 - fails}/{len(MUTATIONS) + 1} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
