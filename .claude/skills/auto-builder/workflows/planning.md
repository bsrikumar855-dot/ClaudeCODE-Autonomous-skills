# Planning and architecture playbook

1. Map requirements to existing code and system boundaries.
2. Identify dependencies, data flows, interfaces, security boundaries, and operational concerns.
3. Prefer a small number of cohesive components and existing project conventions.
4. Break delivery into dependency-aware vertical slices, each with acceptance criteria and a verification command.
5. Identify tasks safe to parallelize and assign disjoint ownership.
6. Request an independent architecture/plan critique for broad or high-risk changes.
7. Apply Checkpoint A (see SKILL.md): pause for approval only when a consequential choice is involved or the user asked for it; otherwise record the plan and proceed.

A plan is not a promise: revise it when evidence from implementation or tests invalidates an assumption.
