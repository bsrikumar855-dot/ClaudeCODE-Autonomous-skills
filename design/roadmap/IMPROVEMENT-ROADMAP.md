# AUTO-BUILDER 2.0 roadmap (v1.1, after design review)

Ordering from the [gap analysis](../research/AUTOBUILDER-GAP-ANALYSIS.md) and the [review log](../architecture/DESIGN-REVIEW-LOG.md). Each milestone ends with verification and a local commit on `feat/autobuilder-2.0`. Nothing is pushed, merged or released without the user.

| Milestone | Scope | Deliverables | Value test | Exit check |
|---|---|---|---|---|
| **M0 Research, gap analysis** (done) | upstream source audit; capability map | `design/research/*` | avoid rebuilding what exists / what upstream lacks | sources cited; verified vs recommendation |
| **M1 Architecture design** (done) | systems, flows, acceptance, risks; 3-way review | `design/architecture/*`, review log, roadmap, benchmark plan | cheap to fix before code | review findings dispositioned |
| **M2 Foundations + orchestration** | **format foundations first**: `TASKS.md` template (`Flags`, per-milestone `Verified at`, strict grammar), `Limits` section, *Untrusted data* rule, trivial bypass; then router table, 8 playbooks, discovery (interrogation), arena, principles, routing eval set | `SKILL.md` Task router + Limits + Untrusted data; `workflows/{router,arena}.md`, extended `discovery.md`; `playbooks/*`; `principles/engineering-principles.md`; `tests/fixtures/routing-eval.json` | stops forcing bug fixes through a PRD; closes the prompt-injection gap | M1–M4, M9–M11 |
| **M3 Execution intelligence** | swarm, ownership, integration, fresh-context review | `workflows/{swarm,independent-review}.md`; `ab.py graph`; hostile fixtures; static + dynamic read-only tests | mechanical conflict/cycle/ownership detection | M5, M8 |
| **M4 Verification intelligence** | browser QA, TDD, evidence | `workflows/{browser-qa,tdd}.md`; `templates/BROWSER-QA.md`; `ab.py browser-report` | makes fabricated "tested in browser" claims harder | M6 |
| **M5 Learning and recovery** | resume, reflect, correct | `workflows/session-recovery.md`; `templates/LESSONS.md`; `ab.py state`; `init-artifacts.sh` selective copy | resume that verifies reality | M7 |
| **M6 Delivery operations** (opt-in) | PR/CI/release | `playbooks/release.md` with the approval model and caps | bounded, approval-gated delivery | M9 |
| **M7 Final audit and benchmark** | full tests, CI emulation, installers, architecture + security review, docs/site sync, benchmark status | audit report; updated README/site/CHANGELOG; benchmark honestly "not run" unless authorized | honest state of the whole | M11 + review sign-off |

## Ordering decisions
- Review (A-m7) moved the `TASKS.md` format work to the start of M2 because `graph` and `state` both parse it.
- `ab.py` grows one subcommand per milestone (`graph` M3, `browser-report` M4, `state` M5), each tested with deliberate breakage when introduced. `route` and `lessons` were **cut** after review.
- M6 is outside the user's core goal and the riskiest for approvals; it stays opt-in and last before the audit.

## Cut (no meaningful value, or unsafe)
`registry.json`; `ab.py route`; `ab.py lessons`; separate `product-interrogation.md`, `learning.md`, `IMPROVEMENT-PROPOSALS.md`; 4 of the 12 planned playbook files (merged); browser binary/daemon; skill generator; telemetry; cookie import; default external review; auto-merge/deploy; automatic edits to skill files.

## Standing constraints (every milestone)
Nine agents and tool restrictions unchanged; Quality protocol, Security gate, 3 attempts / 5 passes, approvals, hooks off by default; `SKILL.md` far below 500 lines; no duplicated rules (link or ID); `ab.py` shipped non-executable; installer + validator updated with each addition.
