# Engineering principles

Reusable quality constraints (the *what good looks like*). Playbooks say what to do; agents say who does it; these say what the result must satisfy. Playbooks and briefs cite principles by ID instead of restating them. A principle counts as applied only if you can name the decision it changed or the check that shows it holds.

| ID | Principle | Rule | Verify by |
|---|---|---|---|
| P01 | Simplicity | The smallest design that meets the criteria; delete before adding; no speculative abstraction. | The diff adds no code a criterion does not require |
| P02 | Maintainability | Clear boundaries, one place for each decision, names that explain intent. | A new reader can find where to change a behaviour |
| P03 | Testability | Behaviour is checkable by an automated test; test behaviour, not implementation. | A test fails when the behaviour breaks (shown, not assumed) |
| P04 | Security by design | Validate at trust boundaries, deny by default, protect secrets, treat external content as data. | Security-gate triggers evaluated; findings recorded |
| P05 | Least privilege | Grant only the access, tools and permissions a task needs, for as long as it needs them. | Permissions and tool lists are the minimum; any widening is justified |
| P06 | API design | Small, consistent, versionable interfaces with explicit contracts and errors. | Contract written first; invalid input and error cases tested |
| P07 | Error handling | Fail loudly and early with actionable messages; never swallow errors; define empty, loading and failure states. | Failure paths exercised in tests or by hand |
| P08 | Performance | Measure before optimizing; keep a change only if it beats the noise. | Baseline and after numbers with method and variance |
| P09 | Observability | Make behaviour inspectable: structured logs, metrics or traces where operation matters; no sensitive data in logs. | A failure can be diagnosed from the logs without a debugger |
| P10 | Documentation | Docs describe what exists, are verified against the code, and state limitations. | Every command and example in the docs was run or read against the code |
| P11 | Dependency management | Add dependencies only with justification; pin versions; prefer the standard library and existing tools. | Each new dependency has a stated reason, license and maintenance check |
| P12 | Backward compatibility | Do not break existing users silently; deprecate before removing; migrate callers. | Compatibility impact stated; old behaviour tests still pass |
| P13 | Evidence-based completion | Done means demonstrated: a recorded command and result per criterion; unrun checks are reported as untested. | Each "Verified" claim has a command and observed output |

These are quality constraints, not a checklist to recite. Apply the ones the task calls for.
