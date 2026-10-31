# Playbook: performance optimization

Runs inside one milestone row of `TASKS.md`; uses its counters, the Quality protocol and the Security gate (see SKILL.md).

## Steps
1. Define the metric and the target (latency, throughput, memory, startup) and the workload it is measured on.
2. **Baseline**: measure before changing anything; run enough repetitions to see the variance; record the method.
3. **Profile** to find where the time actually goes; form a hypothesis with a predicted effect.
4. Make one change at a time; keep correctness tests passing.
5. **Benchmark** after each change under the same conditions; keep a change only if the improvement exceeds the measured noise.
6. Verify no regression in correctness or in other metrics; document the trade-off.

## Principles
P08, P09, P01, P13

## Completion criteria
- Before and after numbers with the method and variance are recorded; the target is met, or the shortfall is stated.
- Correctness tests pass; complexity added is justified by the measured gain.
- No claim of improvement without a measurement.
