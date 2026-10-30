# Security review

Use when the project is in scope for a security review (see workflows/security.md). Otherwise record "Security review not required: <reason>" here.

## Methods used (tick only what was actually done)

- [ ] Static inspection (code, configuration, manifests)
- [ ] Automated scanning (tool and command: ____; evidence to weigh, not proof)
- [ ] Penetration / dynamic testing (only if explicitly authorized, local disposable target; otherwise "not performed")

## Scope and risk profile

- Handles: [ ] authentication [ ] user/personal data [ ] payments [ ] external API [ ] file upload [ ] secrets [ ] external integrations [ ] AI/LLM tools [ ] network deployment
- In scope for security-engineer? (yes / no, reason)

## Threat model

| Asset | Actor / abuse case | Entry point / trust boundary | Required control | Status |
|---|---|---|---|---|

## Findings register

| ID | Severity (Critical / High / Medium / Low) | Confirmed / Potential | Method (static / scan / dynamic) | Location (file:line) | Summary and impact | Fix | Status (Open / Fixed with evidence / Partially fixed / Accepted by user (residual risk)) | Evidence of fix |
|---|---|---|---|---|---|---|---|---|

## Accepted residual risk (High findings only; requires explicit user acceptance; these stay open risks and are never recorded as Fixed. A Critical can never be accepted)

| Finding ID | Residual risk | Accepted by (user) | Date | Mitigation / review date |
|---|---|---|---|---|

## Security gate status

| Checkpoint | Run? | Critical open | High open (not accepted) | Medium/Low tracked | Notes |
|---|---|---|---|---|---|
| Architecture / threat model | | | | | |
| Milestone: | | | | | |
| Final review | | | | | |

## Not checked / limitations
