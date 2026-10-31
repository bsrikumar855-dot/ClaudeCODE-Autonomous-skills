# Playbook: security assessment

The Security gate and the details are in `workflows/security.md`; this playbook runs inside one milestone row of `TASKS.md` and uses its counters (see SKILL.md).

## Steps
1. Scope the assessment (paths, components, data) and decide the methods: static inspection, automated scanning, and penetration testing only if explicitly authorized on a local disposable target.
2. Threat model with `security-engineer`: assets, actors, trust boundaries, entry points, abuse cases.
3. Inspect the actual code and configuration; collect findings with evidence (file:line), Confirmed vs Potential, severity.
4. Evaluate exploitability and impact; record in `SECURITY-REVIEW.md`.
5. Remediation: engineers implement minimal fixes and the specified security regression tests; the user decides on any accepted High.
6. Re-check by `security-engineer`; mark Fixed only with evidence.

## Principles
P04, P05, P13

## Completion criteria
- Findings register complete with methods used and what was not checked.
- No open Critical; every High fixed or explicitly accepted by the user and recorded as residual risk.
- The report states "no known confirmed Critical or High findings in the reviewed scope" with its limits, never "secure".
