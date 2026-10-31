# Architecture arena

Compares genuinely different designs for a meaningful decision. It costs tokens, so it is not the default.

## 1. Is it warranted?
Run it only when the decision is **hard to reverse**, spans more than one milestone, or is critical for security, performance or the data model, **and** at least two credible options have different failure modes. Never for conventional or easily reversible choices (a framework already in use, naming, minor libraries). Say so in `DECISIONS.md` when you skip it for a decision that looked big.

## 2. Default (cheap): one architect, two stances, one pre-mortem
Ask `architect` for two structurally different designs, each argued at its strongest, then a **pre-mortem** for the one you lean towards (how it fails in a year). Typical stance pairs: modular monolith vs services; synchronous vs queue-based; centralized vs distributed policy evaluation; deterministic rules vs model-assisted evaluation; minimal moving parts vs strongest isolation.

## 3. Escalation (costly): independent candidates
Only when the decision is hard to reverse or security-critical:
1. Write the decision statement and a **rubric of 3 to 6 criteria** (for example security, complexity, performance, reliability, maintainability, cost) **into `DECISIONS.md` first**, before any candidate exists. Candidates do not see the rubric.
2. Give each candidate a distinct stance and run fresh-context `architect` subagents independently (number: see SKILL.md Limits). Candidates cannot see each other. Each returns a design, its strongest argument, what it rejected, hidden dependencies and failure modes.
3. Add `security-engineer` on the security axis only where the Security gate applies.
4. The lead scores each candidate per criterion and cites evidence for each score. Converged candidates: ship the shared shape. Widely diverged: the framing was loose; reframe once.
5. The lead picks a base and may adopt one or two ideas from the others.

## 4. Record and decide
`DECISIONS.md` entry: decision, options, rubric and scores with evidence, **why each alternative was rejected**, hidden dependencies, failure modes. If the choice changes product direction, cost or data handling, ask the user. State the expected cost at Checkpoint A when the escalation is planned.

The scoring is the lead's judgment. The arena reduces blind spots; it does not make the decision objective, and several agents of the same model share blind spots.
