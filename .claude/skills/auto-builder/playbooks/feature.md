# Playbook: new feature

Runs inside one milestone row of `TASKS.md`; uses its counters, the Quality protocol and the Security gate (see SKILL.md). Routing, specialists and gates are in `workflows/router.md`.

## Steps
1. Understand: restate the outcome; read the code the feature touches and its tests; list assumptions.
2. Product check, if the feature is substantial (triggers and skip rules in `workflows/discovery.md`): smallest valuable slice, what not to build, measurable acceptance criteria.
3. Plan: tasks with dependencies and owned files (task graph); arena only if a hard-to-reverse design decision exists (`workflows/arena.md`).
4. Implement slice by slice, tests first for each acceptance criterion where practical (`workflows/tdd.md` once available); follow existing conventions.
5. Verify: tests, regression, real user path (browser QA if there is a UI), Security gate if triggered.
6. Review: fresh-context reviewer on the integrated result.
7. Update docs and state files; report verified / partially verified / untested.

## Principles
P01, P03, P06, P07, P12, P13

## Completion criteria
- Every acceptance criterion has a recorded result (Verified, or listed as Partially verified/Untested with the reason).
- Existing tests still pass; new behaviour has tests.
- Documentation and public interfaces updated; backward-compatibility impact stated.
- Review findings: no open blocker or major; Security gate satisfied if it applied.
