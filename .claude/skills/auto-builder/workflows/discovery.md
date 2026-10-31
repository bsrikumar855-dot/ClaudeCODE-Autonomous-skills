# Discovery playbook

1. Restate the goal, user, and problem in plain language.
2. Inspect the repository and existing product context.
3. Identify primary journeys, constraints, success measures, and non-goals.
4. Research only questions where current facts materially affect the solution.
5. Generate alternatives for major choices; compare value, complexity, risk, cost, and reversibility.
6. Convert the recommended direction into testable requirements.
7. Collect unresolved high-impact questions and raise them together at Checkpoint A (or immediately if they block all progress); document reasonable low-risk assumptions.

Output: concise problem brief, assumptions, scope, alternatives considered, recommendation, acceptance criteria.

## Product interrogation

Challenges the idea before building. The user keeps final authority over product direction.

**Run it** for: new projects; features that add a user-facing capability, change who the product serves, or cost about a milestone or more; any request with an unclear problem, user or success measure.
**Skip it** for: bug fixes, refactors, trivial or cosmetic changes, work that already has a specified requirement and acceptance criteria, or when the user says to skip. Record a skip in one line in `DECISIONS.md`. Do not run the full process for trivial changes.

**Questions** (ground them in the repository and any existing product; inspect an existing application before proposing major change):
1. What problem is being solved, and who has it?
2. How is it solved today, and why is that insufficient?
3. What is the smallest valuable solution?
4. Which assumptions are unverified, and how could each be tested?
5. What are the success metrics?
6. What should explicitly **not** be built?

**Modes** (the user picks one, or the lead recommends one):
- *Product discovery*: problem, user, status quo.
- *CEO-level challenge*: is this the right thing at all? Compare against doing nothing, reusing or buying.
- *MVP scope review*: hold, reduce or expand scope; the lead recommends and the user decides.
- *Feature prioritization*: impact, effort, risk and dependency per candidate.
- *User-journey analysis*: journeys, failure paths, empty and error states, turned into acceptance criteria.

**Decision tiers:** *mechanical* (decide and record); *taste* (recommend, surface at the checkpoint); *user-challenge* (it changes the user's stated direction: present options with a recommendation and never decide alone). Challenge weak ideas respectfully and with evidence; do not agree automatically and do not invent requirements. Write results to `REQUIREMENTS.md` (scope, non-goals, assumptions to verify) and `DECISIONS.md`.
