# Playbook: bug fix

Runs inside one milestone row of `TASKS.md`; uses its counters, the Quality protocol and the Security gate (see SKILL.md).

## Steps
1. Reproduce: obtain the failing behaviour with a command, test or recorded steps. If it cannot be reproduced, say so and stop at diagnosis; do not guess a fix.
2. Diagnose to the **root cause** (the first wrong decision, not the symptom); state the cause and the evidence.
3. Test first (`workflows/tdd.md`): write the smallest failing test (or repro script) and confirm it fails for the right reason.
4. Fix minimally; rerun the failing test; then the regression checks. Never weaken a test to make it pass.
5. Check for the same defect elsewhere (same pattern, same assumption).
6. Review the diff with a fresh-context reviewer; Security gate if the change touches an in-scope area (judged by what the diff touches, not by the label "bug fix").

## Principles
P03, P07, P13

## Completion criteria
- The reproduction fails before the fix and passes after (both outputs recorded).
- Regression checks pass; no unrelated files changed.
- Root cause and why it was missed are stated in one or two sentences in the report.
