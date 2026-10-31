# Test-first workflow

Use for bug fixes and for features where acceptance criteria can be expressed as tests.

1. **Pin the behaviour** in one sentence: what must be true after the change.
2. **Choose the narrowest existing test type** that can express it (unit before integration before end to end), in the project's own framework.
3. **Write a small test from the intended behaviour**, not from the current implementation.
4. **Run it and confirm it fails for the right reason** (the assertion about the behaviour fails, not a typo or an import error). Record the failing output.
5. **Make the smallest change** that makes it pass.
6. **Rerun it, then the regression checks.** Record the passing output.
7. **Never weaken the check**: do not loosen assertions, delete tests, add skips or retries, or edit a test to fit a wrong implementation.

If a failing test is impractical (a visual defect, an environment issue), use a repro script, a snapshot or a log check instead, and say so.

Evidence for the report: the failing-before output and the passing-after output for each behaviour.

Who does what: `qa-engineer` specifies the test and runs it; an engineer (or you) writes it, since `qa-engineer` cannot edit files.
