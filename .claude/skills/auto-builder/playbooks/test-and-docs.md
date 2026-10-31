# Playbook: testing and documentation

Both produce artifacts and must be checked against the real code. Each runs inside one milestone row of `TASKS.md` and follows the Quality protocol (see SKILL.md).

## testing

**Steps**
1. Identify what must be tested: acceptance criteria, user journeys, risky paths, recent changes.
2. Find gaps: what has no test, or only a weak one (assertions that cannot fail).
3. Specify tests with `qa-engineer`; engineers write them (`qa-engineer` cannot edit); run them.
4. Prove each new test can fail (run it against a deliberately broken case or the pre-fix code where practical).
5. Record results with evidence states.

**Principles** P03, P13

**Completion criteria**
- New tests pass and are shown to fail when the behaviour is wrong.
- Remaining gaps are listed as Untested.

## documentation

**Steps**
1. Identify the audience and what they need to do.
2. Coverage map: list the public surface (commands, APIs, config) and which docs cover it; list gaps and stale statements.
3. Write or update; verify every command, path and example against the code by running or reading it.
4. Ask the user before narrative rewrites, security-relevant wording or removals; fix factual details directly.

**Principles** P10, P13

**Completion criteria**
- Every command, path and example in the new text was verified against the code or run.
- No claim without support; limitations are stated.
