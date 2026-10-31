# Benchmark plan: AUTO-BUILDER 1.x vs 2.0

**Status: designed, NOT executed. No comparative results exist.** This document must not be cited as evidence of improvement.

## Why it has not been run
A fair comparison needs repeated **live Claude Code sessions** (nondeterministic, multi-hour, token-consuming) for each task × arm × repetition. That spends the user's Claude usage, which requires explicit approval, and no live session of either version has ever been run in this project. Static tests (validators, installer tests, helper-script tests) verify that mechanisms exist and are internally consistent; they say **nothing** about engineering outcomes and are reported separately as "mechanism tests", never as benchmark results.

## Arms
- **A (baseline):** AUTO-BUILDER at `origin/main` commit `7d20514` (1.x with QA protocol and security gate).
- **B (2.0):** `feat/autobuilder-2.0` head at test time.
- Same model, same effort setting, same permissions, same machine; fresh worktree per run; no cross-run memory; arm order randomized; scorer blind to arm.

## Tasks (repeatable fixtures to be built before running)
| ID | Task | Fixture (to build) | Hidden acceptance check |
|---|---|---|---|
| T0 | Trivial change (typo/config) | one-line fix in a small repo | file changed correctly; **overhead measured** (tokens/time/steps vs a bare Claude Code baseline) |
| T1 | Bug fix | small service with a known defect and a thin test suite | hidden failing test now passes; no regression in existing tests |
| T2 | Feature | add a specified endpoint/command to a small app | hidden acceptance tests |
| T3 | New full-stack project | one-paragraph spec (CRUD + auth) | hidden API/E2E tests + build/lint |
| T4 | AI agent | tool-using agent with a stubbed LLM and an adversarial input set | hidden behavioural tests incl. a prompt-injection case |
| T5 | Refactoring | duplicated module to consolidate | behaviour-preservation tests + smaller-surface check |
| T6 | Performance optimization | function with a measured slow path | benchmark with variance; correctness tests |

## Metrics (all measured from artifacts, not self-reports)
| Metric | Measured how |
|---|---|
| Acceptance-criteria completion | % of hidden acceptance checks passing |
| Defects | hidden-test failures + scorer-found defects against a rubric |
| Regression rate | previously passing tests now failing |
| Review findings | count and severity of findings from a *blind external* reviewer, plus findings the arm's own review caught |
| Human intervention count | questions/approvals requested, from the transcript |
| **Verification quality (weighted highest)** | % of "Verified" claims backed by a recorded command/output that the scorer re-runs and reproduces |
| Recovery success | inject an interruption mid-run; % of runs that resume without redoing or losing verified work |
| Time and tokens | wall clock; token usage reported by the harness |
| **False completion claims** | the arm reports done/verified but a hidden check fails or a "Verified" claim does not reproduce |

## Cost and sequencing
A full run (7 tasks × 2 arms × ≥5 repetitions) is on the order of 70 multi-hour live sessions and is not a realistic first step. **Stage 1 (proposed, needs the user's approval and a stated usage ceiling):** T0, T1, T2 and T5, 3 runs per arm as a smoke test, then decide whether to scale. A router **eval set** (`tests/fixtures/routing-eval.json`: labelled requests, including ambiguous and trivial ones) is scored by whether the live lead chose the expected playbook; it is a live eval and is NOT RUN. Optional smoke checks (also not run): router chooses the expected playbook on 3 fixtures; a seeded bug gets a failing test first; an interrupted run resumes without redoing verified work.

## Protocol and statistics
≥5 runs per task per arm for the full study (more for noisy tasks); report per-task medians and the raw runs; confidence intervals or exact counts, not just means; pre-register the scoring rubric before any run; discard no run except for infrastructure failure (documented); report where 2.0 is worse (e.g. cost). Deliberately include tasks where routing/arena should *not* add ceremony, to detect over-engineering overhead.

## Decision rule and blinding (to fix BEFORE any run)
- **Adopt 2.0 only if**, over the Stage 1 tasks, the median hidden-acceptance pass rate on T1, T2 and T5 is at least as high as arm A **and** verification quality (claims reproduced by the scorer) is higher **and** the overhead on T0 (extra steps, tokens, time versus a bare Claude Code run and versus arm A) stays within a limit set in advance (suggested: no more than 25% more tokens than arm A on T0). Otherwise keep 1.x and simplify 2.0.
- **"More review findings" is not better by itself:** score findings against a ground-truth defect list; count confirmed defects found, false positives and findings the arm's own review missed.
- **Blind the scorer:** strip `docs/auto-builder/` state files, branches and report headings before scoring so arm B's artifacts do not identify the arm.
- **Cost ceiling:** the user sets a token or usage ceiling before Stage 1; abort if exceeded.

## Results table (to be filled only from real runs)
| Task | Metric | Arm A | Arm B | n | Notes |
|---|---|---|---|---|---|
| all | all | NOT RUN | NOT RUN | 0 | requires user-approved live runs |

## Mechanism tests that exist instead (not benchmarks)
Registry/routing fixtures, task-graph, resume-state, browser-evidence and lessons checks with deliberate breakage (added in M2–M5). They validate tooling correctness only.
