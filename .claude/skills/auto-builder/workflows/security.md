# Security playbook

Risk-based: scale the effort to what the project exposes. This playbook supports the **Security gate** in SKILL.md; the gate's rules (severities, blocking, acceptance) live there and are not repeated here.

## 1. Decide whether a security review is in scope

The trigger list is defined once, in the **Security gate** section of SKILL.md (authentication or authorization, user or personal data, payments, externally reachable APIs, file uploads or untrusted input, secrets, external integrations, deployment configuration, AI/LLM tools with side effects). The lead records the scope decision and reason in `DECISIONS.md` before Phase 3. A milestone that triggers the list makes the project in scope for the final review. When unsure, treat it as in scope.

Trivial projects (none of these apply) get no forced review. The lead runs a short checklist (no hard-coded secrets, input validated at boundaries, dependencies sane, no debug or default credentials) and records "security review not required: <reason>" in `SECURITY-REVIEW.md` or the report, stating that this checklist is the lead's own and **not independent**.

## 2. When `security-engineer` runs

| Point | Trigger | Output |
|---|---|---|
| Architecture (Phase 3) | In scope, and the architect has flagged security-sensitive decisions | Threat model (assets, trust boundaries, abuse cases) and required controls, recorded in `SECURITY-REVIEW.md` |
| Milestone gate (Phase 6) | The milestone triggers the SKILL.md list | Findings for that milestone's changes |
| Before completion (Phase 8) | In scope for the project | Final review across the whole project; confirms earlier findings are fixed, with evidence |

## 3. Division of labour

- **architect:** names the security-sensitive design decisions and the trade-offs.
- **security-engineer:** threat-models, reviews, rates findings, and re-verifies fixes. Independent: it reports even when that contradicts a design decision.
- **engineers (or the lead):** implement the recommended controls (minimal fixes) and write the security regression tests that security-engineer specified. Neither security-engineer nor qa-engineer can edit files.
- **qa-engineer:** validates behavior and runs the security regression tests, confirming they pass and, where practical, fail without the fix. Does not re-rate security findings.
- **critical-reviewer:** judges overall quality and requirement coverage; checks that open security findings are handled but does not redo the security review.

## 4. Security brief (template for `security-engineer`)

> Review <scope: paths/diff range/milestone> of the project at <path> for security. Read `docs/auto-builder/ARCHITECTURE.md`, `REQUIREMENTS.md` and `SECURITY-REVIEW.md`. Inspect the actual code and configuration. Cover the categories relevant here: <list from the project> . Report Confirmed vs Potential findings with severity (Critical/High/Medium/Low), file:line evidence, an exploitation scenario, impact and a minimal fix each, plus a suggested security regression test. Do not run destructive tests, touch production, access external targets or install paid services. Never print secret values. State which methods you used (static inspection, automated scanning, penetration testing: not performed unless authorized). Your Bash access is not technically restricted (it can write files and use the network), so keep to read-only, local checks. List what you did not check. You are read-only; do not modify files. For a fix re-check, give evidence for each finding you mark Fixed.

## 5. Per-category checks (use what applies)

- **Access control and authn/authz:** every route and object access checks identity and permission server-side; no IDOR; session/token expiry and rotation; password hashing with a modern algorithm; rate limits on login and reset.
- **Injection:** all queries parameterized; no shell or template strings built from input; deserialization of untrusted data avoided.
- **XSS/CSRF/SSRF:** output encoding or framework auto-escaping; CSRF protection or SameSite cookies for cookie-auth; outbound fetches restricted (allow-list, no internal addresses).
- **Secrets:** none in code, history, client bundles, logs or CI config; `.env.example` only; rotation documented.
- **Dependencies:** review lockfiles and manifests offline first (high-severity advisories you already know of, unmaintained or risky packages, pinning). Network-using audit commands (`npm audit`, `pip-audit`) send the dependency list to a registry, so run them only when the brief or the user authorizes it (the lead may run them). An audit with no findings is not proof of safety.
- **Database:** least-privilege DB user; no `SELECT *` exposure of sensitive fields; migrations reversible or reviewed; backups and encryption considered.
- **Privacy:** personal data inventory, minimization, retention, no sensitive data in logs or analytics.
- **Uploads and input validation:** type, size, name and path validation; store outside the web root; no execution of uploaded content; safe archive extraction.
- **Deployment config:** debug off, no default credentials, minimal exposed ports, TLS, least-privilege CI/CD tokens, security headers.
- **AI/LLM:** treat model input from users, documents, web pages and tool results as untrusted (prompt injection); constrain tool permissions, side effects and spend; require confirmation for destructive tool actions; no secrets or other users' data in prompts, logs or outputs; don't execute or render model output unsanitized.

## 6. Assurance methods: say which one you used

| Method | What it is | What it can and cannot support |
|---|---|---|
| **Static inspection** | Reading source, configuration and manifests | Finds design and code flaws; cannot show runtime behaviour |
| **Automated scanning** | Linters, static analyzers, dependency audits | Evidence to weigh, not proof; false negatives are common; network-using audits need authorization |
| **Penetration / dynamic testing** | Actively exercising a running system to exploit a weakness | Not performed unless explicitly authorized, and then only against a local disposable instance; never production or third-party targets |

Reports and the final status name the methods actually used and say "penetration testing not performed" when it was not. A clean scan or a static review is never described as a penetration test.

## 7. Recording and tracking

`SECURITY-REVIEW.md` holds the threat model, the findings register (ID, severity, Confirmed/Potential, location, status, evidence of fix) and the gate status. Each fix attempt on a finding counts against the same 3-attempt bound as any other failure, with counters in the `TASKS.md` Status block; the security re-check is part of the same pass, and Medium/Low findings do not consume the pass budget. The register here is the single source of truth; `TASKS.md` links the tasks. A High the user accepted keeps the status **Accepted by user (residual risk)**, is listed under accepted residual risk, and is never recorded as fixed. Security regression tests are listed in `TESTING.md`.

## 8. Wording

Report security status as "no known confirmed Critical or High findings in the reviewed scope" with the scope and limits. Never write "secure" or "vulnerability-free", and never treat a clean scanner run as a pass by itself.
