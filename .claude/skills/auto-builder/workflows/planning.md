# Planning and architecture playbook

1. Map requirements to existing code and system boundaries.
2. Identify dependencies, data flows, interfaces, security boundaries, and operational concerns.
3. Prefer a small number of cohesive components and existing project conventions.
4. Break delivery into dependency-aware vertical slices grouped into milestones. Each milestone has an expected outcome, *measurable* acceptance criteria (a behaviour you can observe, a command, or a threshold) and a verification gate; no criterion may be unfalsifiable ("fast", "works well").
5. Identify tasks safe to parallelize and assign disjoint ownership.
6. Request an independent architecture/plan critique for broad or high-risk changes. Have the architect list the security-sensitive design decisions (auth model, data access, trust boundaries, external integrations, AI tool permissions); where the Security gate applies, hand them to `security-engineer` for a threat model before implementation (see security.md).
7. Apply Checkpoint A (see SKILL.md): pause for approval only when a consequential choice is involved or the user asked for it; otherwise record the plan and proceed.

A plan is not a promise: revise it when evidence from implementation or tests invalidates an assumption.
