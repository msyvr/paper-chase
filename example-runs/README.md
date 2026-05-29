# example-runs

Each section is the **latest** result from running the relevant phase's script.
Re-runs overwrite the entry and image in place; git history preserves prior
versions. This is the public face of "what running this produces right now."

---

## Phase 0 — Validity gate

**What was run.** Sweep of the novelty:replication reward ratio across
{1, 2, 5, 10, 20, 50}, holding replication weight at 1.0; 3 seeds per
condition. No mitigations, no correlated errors, parametric agents only.
Script: [`scripts/run_baseline.py`](../scripts/run_baseline.py).

**Result.**

![Phase 0 validity gate](images/phase-0-validity-gate.png)

**Interpretation.** Truth-content (precision) falls as the novelty:replication
ratio rises — the qualitative replication-crisis dynamic the model is meant to
reproduce. Discovery rate (recall) stays saturated near 1.0: with 50 agents
over 500 steps, every true hypothesis gets studied enough times that at least
one significant result lands eventually, so the standing literature catches
them all. The Pareto-plane trajectory drifts from the upper-right toward the
lower-right as pressure increases — same data, the precision–recall trade-off
visualised directly.

Validity gate passed: the engine produces the known phenomenon under the
simplest configuration, licensing the work to proceed to mitigations.
