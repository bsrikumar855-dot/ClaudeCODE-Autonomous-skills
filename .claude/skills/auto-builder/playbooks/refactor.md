# Playbook: refactoring

Runs inside one milestone row of `TASKS.md`; uses its counters, the Quality protocol and the Security gate (see SKILL.md).

## Steps
1. State the goal and what must **not** change (behaviour, public interfaces, performance envelope).
2. Pin behaviour: make sure tests cover the code being changed; add characterization tests where they do not.
3. Change in small steps; run the tests after each step; keep every step reversible.
4. Remove dead code and duplicated paths created by the change; do not add features.
5. Review: a fresh-context reviewer checks behaviour preservation and unintended interface changes.

## Principles
P01, P02, P03, P12

## Completion criteria
- Behaviour-preserving tests pass before and after; no public interface change unless the user asked for it.
- The result is measurably simpler (fewer lines, branches, dependencies or duplicated paths), stated in the report.
