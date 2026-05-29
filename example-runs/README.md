# example-runs

Each section is the **latest** result from running the relevant phase's script.
Re-runs overwrite the entry and image in place; git history preserves prior
versions. This is the public face of "what running this produces right now."

---

## Phase 0 — Validity gate

**What was run.** Sweep of the novelty:replication reward ratio across
{1, 2, 5, 10, 20, 50}, holding replication weight at 1.0; 10 seeds per
condition. No mitigations, no correlated errors, parametric agents only.
`n_hypotheses = 10,000` — the "vast hypothesis space, scarce attention"
regime used throughout Phase 1+, so the baseline → mitigations narrative
reads as one continuous experiment.
Script: [`scripts/run_baseline.py`](../scripts/run_baseline.py).

**Result.**

![Phase 0 validity gate](images/phase-0-validity-gate.png)

**Interpretation.** Truth-content (precision) falls from 0.50 (low pressure)
to 0.39 (high pressure) as the novelty:replication ratio rises — the
qualitative replication-crisis dynamic the model is meant to reproduce.
Discovery rate (recall) sits in 0.73–0.77 across all conditions: with
~22,500 novel actions spread over 10,000 hypotheses, the expected ~2.25
studies per hypothesis is enough to detect most true effects at the
configured per-study power (~0.71 without QRP, ~0.90 with moderate QRP) but
not all of them. Recall rises very slightly with pressure because QRP
inflates effective α and so raises true-positive detection alongside
false-positive rate.

The Pareto-plane trajectory (right panel) drifts from upper-position
(low-pressure, dark) toward lower-position (high-pressure, yellow) at
roughly constant recall — same data, the precision–recall trade-off
visualised directly.

Validity gate passed: the engine produces the known precision-decline
phenomenon at non-saturating recall, licensing the work to proceed to
mitigations.

---

## Phase 1.C — Mitigation comparison (Pareto plane)

**What was run.** Sweep of the novelty:replication reward ratio across
{1, 2, 5, 10, 20, 50} × {no mitigation, pre-registration (leaky, qrp_cap=0.1),
replication+retraction, invariance (k=2), invariance (k=3), invariance (k=4),
all-on}; 10 seeds per condition. Correlated errors active at ρ = 0.5
(moderate). The hypothesis space is sized to represent the realistic
"vast hypothesis space, scarce attention" regime: `n_hypotheses = 10,000`
against ~22,500 novel actions over the run gives ~2.25 studies per
hypothesis under uniform random selection — most plausible hypotheses go
unstudied, recall stays meaningfully below 1.0 even without any mitigation.
`n_contexts = 4` so k = 4 is the strictest possible invariance bar (finding
must appear in every context). Pre-registration is modeled as *leaky*:
qrp_cap = 0.1 allows residual analytic flexibility, since perfect enforcement
is unrealistic and would only set an upper bound.
Script: [`scripts/run_mitigation_comparison.py`](../scripts/run_mitigation_comparison.py).

**Result.**

![Phase 1.C mitigation comparison](images/phase-1c-mitigation-comparison.png)

**Interpretation.** A multi-mitigation Pareto frontier emerges, traced by
both the leaky pre-reg / `none` cluster on the high-recall end and the
invariance strictness gradient (k = 2 → 3 → 4) on the high-precision end:

| Mitigation | Precision range | Recall range | Position |
|---|---|---|---|
| `none` | 0.39–0.50 | 0.73–0.77 | Baseline; QRP-driven precision loss with novelty pressure |
| `pre-reg (leaky)` | ≈ 0.57 | ≈ 0.71 | Pareto-dominates `none` (mild gain in both axes) |
| `invariance (k=2)` | 0.82–0.91 | 0.36–0.40 | **On the frontier** — trades recall for precision |
| `replication+retraction` | 0.94–0.96 | ≈ 0.25 | **On the frontier** — audit retracts many TPs given sparse confirming evidence |
| `invariance (k=3)` | 0.98–0.99 | 0.10–0.12 | **On the frontier** — high precision, low recall |
| `invariance (k=4)` | ≈ 1.00 | ≈ 0.02 | Extreme: publishes almost nothing |
| `all-on` | ≈ 1.00 | ≈ 0.04 | Collapses to k=4-like behavior (strictest filter dominates) |

**Headline finding: there is no single "best" mitigation; the frontier is
populated by multiple mitigations at different trade-off points.** Pre-reg
gives the most recall-preserving gain. Invariance k=2 buys a large precision
jump for moderate recall cost. Replication+retraction and invariance k=3 sit
between, with invariance k=3 slightly higher in precision. Choice depends on
which end of the frontier matters in deployment.

**Why `none` recall lands at ~0.75, not 1.0**: per-study power under default
config (effect size d ≈ 0.4, n = 30 samples, α = 0.05) is ~0.71 without QRP
and ~0.90 with moderate QRP. With ~2.25 studies per H, recall ≈ 1 −
exp(−2.25 × effective_power) ≈ 0.75–0.80. ρ = 0.5 correlated errors reduce
effective independent power slightly. This is the model's honest output for
"moderately-studied effects in a vast hypothesis space" — the regime where
the replication-crisis dynamic is interpretable.

**Why high-k invariance publishes so little**: with ~2.25 studies per H and
uniform context sampling over 4 contexts, the expected number of distinct
contexts hit per H is 4 × (1 − (3/4)^2.25) ≈ 1.85. So k = 2 catches ~38% of
true H, k = 3 catches ~11%, k = 4 catches ~2%. **This is a real finding, not
an artifact: strict invariance is data-hungry.** The regime where high-k
invariance shines is one where attention concentrates on a subset of
hypotheses — i.e., real scientific practice, where well-studied topics
accumulate evidence across many labs/contexts while the long tail goes
unstudied. The non-uniform-selection upgrade that would model this is
tracked in [FUTURE_WORK.md](../FUTURE_WORK.md).

**Why `all-on` collapses to k=4-like behavior**: the strictest filter in the
stack dominates. Once k = 3 invariance is in place, it gates publication so
strictly that adding pre-reg and audit changes little.

**Phase 1.D — ρ-sweep** will trace how the frontier shifts as correlated
errors strengthen. The most actionable comparisons are likely at the
moderately-strict end (pre-reg leaky, invariance k=2, replication+retraction)
where every mitigation has visible recall and precision both. If invariance's
advantage over audit-style mitigations is real, it should sharpen at higher ρ
where shared shocks defeat single-context replication.
