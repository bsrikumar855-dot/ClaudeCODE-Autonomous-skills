# Browser QA report

The lead writes this file. Record only what actually happened. If no browser tool was available, set `Tool: none` and mark every scenario NOT RUN or BLOCKED.

- Tool: <project-e2e | session-browser | playwright | headless-chrome | none>
- Environment: <local | staging | test>
- Base URL: http://localhost:3000
- Origin allowlist: http://localhost:3000
- Started: 2026-01-01T00:00:00Z
- Approved by user: <n/a, or yes for a staging origin the user confirmed>
- Artifact directory: <a git-ignored directory>
- No failure scenarios because: <leave out unless there is a stated reason>

## Scenarios

| ID | Kind | URL | Scenario | Expected | Actual | Result | Artifact | sha256 | Console/network errors |
|---|---|---|---|---|---|---|---|---|---|
| B1 | success | http://localhost:3000/login | log in with the test account | dashboard shown | | NOT RUN | none: not run yet | | |
| B2 | failure | http://localhost:3000/login | log in with a wrong password | error message, no session | | NOT RUN | none: not run yet | | |

Result is PASS, FAIL, NOT RUN or BLOCKED. For PASS and FAIL give `Actual` and an `Artifact` (a path to a file this run produced, under the project, in the git-ignored artifact directory) or `none: <reason>`. `sha256` (12 or more hex characters) is optional.
