# Project category guide

Identify the category (a project may span several), then apply the matching emphasis. Use only what fits; these are prompts for judgment, not a checklist to complete.

| Category | Discovery focus | Architecture focus | Verification focus | Lead agents |
|---|---|---|---|---|
| **AI/ML application** | Task definition, data availability, quality bar, cost/latency budget | Model/provider choice, data flow, fallback, caching | Eval set with explicit metrics; regression cases; cost/latency measurement | ai-engineer, backend-engineer |
| **AI agent / multi-agent** | Which decisions are autonomous vs human; failure tolerance | Tool contracts, permissions, state, termination limits, observability | Scripted scenarios, tool-misuse tests, loop/budget limits | ai-engineer, architect, critical-reviewer |
| **Full-stack app** | Core journey, auth/data model needs | API contract first, schema, auth boundary, deployment target | E2E journey in a browser + API contract tests + migrations | frontend-engineer, backend-engineer, qa-engineer |
| **Frontend app** | Users, devices, design system, accessibility needs | Component structure, state, data fetching, routing | Component/unit tests, real-browser check, responsive + keyboard + a11y | frontend-engineer, qa-engineer |
| **Backend / API** | Consumers, SLAs, data ownership | Contract (OpenAPI/schema), persistence, idempotency, authn/z | Contract tests, validation/error paths, load sanity, migration dry-run | backend-engineer, architect |
| **Developer tool / CLI / library** | Who installs it, existing alternatives, ergonomics | Public API surface, config, packaging, cross-platform | Install in a clean env, docs examples run, semver/compat | backend-engineer, qa-engineer |
| **Research project** | Question, hypotheses, baselines, what counts as evidence | Reproducible pipeline, seeds, data/version tracking | Re-run reproduces results; no cherry-picked claims; limitations stated | researcher, ai-engineer |
| **Automation system** | Trigger, frequency, failure impact, who is notified | Idempotency, retries, dry-run mode, secrets, scheduling | Dry-run + failure injection; no unintended side effects | backend-engineer, critical-reviewer |
| **Data engineering** | Sources, volume, freshness, consumers, data quality rules | Schema/contracts, lineage, incremental loads, backfills | Row-count and quality assertions, idempotent re-runs, sample-data tests | backend-engineer, ai-engineer |

## Cross-cutting defaults

- Reuse the repository's stack. In an empty repo choose mainstream, well-documented tools you can verify locally.
- Side effects on real systems (writes, sends, deploys, spend) are off by default and gated behind a dry-run or explicit approval.
- Anything stochastic (LLMs, ML) needs a measurable evaluation, not "looks good".
