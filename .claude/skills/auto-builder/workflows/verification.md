# Verification playbook

For each meaningful slice, select checks proportionate to the risk:

- Unit tests for local logic.
- Integration tests for service and data boundaries.
- Contract tests for APIs and schemas.
- End-to-end/browser tests for critical user journeys.
- Type checks, lint, formatting, and production build.
- Security checks for auth, input handling, secrets, dependencies, and data exposure.
- Accessibility and responsive checks for UI.
- Evaluation datasets and explicit metrics for AI behavior.

Run commands from the repository's documented scripts. Capture exact pass/fail output. Fix failures, rerun, and record skipped checks with reasons. A passing build alone does not prove the feature works.
