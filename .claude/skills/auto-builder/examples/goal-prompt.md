# Example invocations

```text
/auto-builder Build an AI research workspace where users can upload papers, search across them, ask grounded questions, generate summaries, and explore citation relationships.
```

Constraints worth adding when they matter:

- Reuse the existing stack and repository conventions.
- Prefer accessible, responsive UI.
- Define measurable acceptance criteria for retrieval quality and grounded answers.
- Do not deploy or create paid resources without approval.

More goals, by category:

| Category | Example goal |
|---|---|
| AI/ML app | `/auto-builder Add semantic search over our support articles with an evaluation set measuring recall@5` |
| Agent system | `/auto-builder Build a multi-agent triage bot that classifies GitHub issues and drafts replies for human approval` |
| Full-stack | `/auto-builder Build a team habit tracker with auth, a REST API and a React UI` |
| Frontend | `/auto-builder Redesign the settings page to be keyboard accessible and responsive` |
| Backend/API | `/auto-builder Add rate-limited, paginated /v1/orders endpoints with OpenAPI docs and tests` |
| Developer tool | `/auto-builder Create a CLI that lints OpenAPI specs against our style guide` |
| Research | `/auto-builder Reproduce the baseline from <paper> and compare two alternatives on the same data` |
| Automation | `/auto-builder Automate weekly invoice export from the CSV drop folder, with a dry-run mode` |
| Data engineering | `/auto-builder Build an idempotent daily ETL from the sales API into Postgres with quality checks` |
