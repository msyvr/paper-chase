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
all-on}; 10 seeds per condition. Systematic-bias active at
`bias_strength = 0.5` (moderate — per-(h, ctx) bias SD = 0.5 vs. unit-variance
sampling noise). The hypothesis space is sized to represent the realistic
"vast hypothesis space, scarce attention" regime: `n_hypotheses = 10,000`
against ~22,500 novel actions over the run gives ~2.25 studies per
hypothesis under uniform random selection — most plausible hypotheses go
unstudied, recall stays meaningfully below 1.0 even without any mitigation.
`n_contexts = 4` so k = 4 is the strictest possible invariance bar (finding
must appear in every context). Pre-registration is modeled as *leaky*:
qrp_cap = 0.1 allows residual analytic flexibility, since perfect enforcement
is unrealistic and would only set an upper bound.
Script: [`scripts/run_mitigation_comparison.py`](../scripts/run_mitigation_comparison.py).

> **Note on the noise model.** This run uses the corrected additive-bias
> noise model: `Z = δ + bias + private` with `bias ~ N(0, bias_strength²)`
> per (h, ctx) and `private ~ N(0, 1)` per study, both independent and
> additive. An earlier version used a Gaussian-copula formulation
> (`Z = δ + ρ·shared + sqrt(1-ρ²)·private`) which preserved total per-study
> variance at 1 by trading private noise for shared noise as ρ rose. That
> formulation artificially shrank audit-replicate noise at high ρ, giving
> the same-base-model audit (`ReplicationAndRetraction`) an unrealistic
> advantage. The qualitative Pareto-frontier shape below is unchanged from
> the prior run, but absolute precision numbers are 5–10 percentage points
> lower because the corrected model has higher total noise (Var(Z) under H0
> = 1 + bias_strength² = 1.25, not 1).

**Result.**

![Phase 1.C mitigation comparison](images/phase-1c-mitigation-comparison.png)

**Interpretation.** A multi-mitigation Pareto frontier emerges, traced by
both the leaky pre-reg / `none` cluster on the high-recall end and the
invariance strictness gradient (k = 2 → 3 → 4) on the high-precision end:

| Mitigation | Precision range | Recall range | Position |
|---|---|---|---|
| `none` | 0.31–0.40 | 0.74–0.77 | Baseline; QRP-driven precision loss with novelty pressure |
| `pre-reg (leaky)` | ≈ 0.45 | ≈ 0.72 | Pareto-dominates `none` (mild gain in both axes) |
| `invariance (k=2)` | 0.71–0.84 | 0.36–0.39 | **On the frontier** — trades recall for precision |
| `replication+retraction` | 0.91–0.94 | ≈ 0.21 | **On the frontier** — audit retracts many TPs given sparse confirming evidence |
| `invariance (k=3)` | 0.97–0.99 | 0.10–0.11 | **On the frontier** — high precision, low recall |
| `invariance (k=4)` | ≈ 1.00 | ≈ 0.01 | Extreme: publishes almost nothing |
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
exp(−2.25 × effective_power) ≈ 0.75–0.80. Systematic bias at `bias_strength`
= 0.5 doesn't reduce per-study power directly — it just inflates the
average false-positive rate by adding a per-(h, ctx) offset to Z. This is
the model's honest output for "moderately-studied effects in a vast
hypothesis space" — the regime where the replication-crisis dynamic is
interpretable.

**Why high-k invariance publishes so little**: with ~2.25 studies per H and
uniform context sampling over 4 contexts, the expected number of distinct
contexts hit per H is 4 × (1 − (3/4)^2.25) ≈ 1.85. So k = 2 catches ~38% of
true H, k = 3 catches ~11%, k = 4 catches ~1%. **This is a real finding, not
an artifact: strict invariance is data-hungry.** The regime where high-k
invariance shines is one where attention concentrates on a subset of
hypotheses — i.e., real scientific practice, where well-studied topics
accumulate evidence across many labs/contexts while the long tail goes
unstudied. The non-uniform-selection upgrade that would model this is
tracked in [FUTURE_WORK.md](../FUTURE_WORK.md).

**Why `all-on` collapses to k=4-like behavior**: the strictest filter in the
stack dominates. Once k = 3 invariance is in place, it gates publication so
strictly that adding pre-reg and audit changes little.

**Phase 1.D** below tests this directly.

---

## Phase 1.D — Bias-strength sensitivity

**What was run.** Sweep of `bias_strength` across {0, 0.25, 0.5, 0.75, 1.0}
at fixed `novelty_weight = 10`, over four mitigations: `none`,
`pre-registration (leaky, qrp_cap=0.1)`, `replication+retraction
(audit_fraction=0.1)`, and `invariance (k=2)`. 10 seeds per condition. Same
regime as Phase 1.C (n_hypotheses=10000, n_contexts=4, n_steps=500, uniform
hypothesis selection). High-k invariance (k=3, k=4) was excluded — Phase 1.C
established they publish almost nothing in this sparse-attention regime.
Script: [`scripts/run_bias_sensitivity.py`](../scripts/run_bias_sensitivity.py).

**The claim Phase 1.D is positioned to test.** *Invariance-style mitigations
dominate audit-style ones under sufficiently strong systematic bias.*
Mechanism: same-base audits inherit the per-(h, ctx) bias that drove the
original significance, so a lucky-bias FP gets confirmed by audit;
invariance requires findings across distinct contexts, each with an
independent bias draw, so a single lucky bias cannot carry an FP through.

**Result.**

![Phase 1.D bias sensitivity](images/phase-1d-bias-sensitivity.png)

| Mitigation | Precision at bs=0 | Precision at bs=1 | Recall (~stable) |
|---|---|---|---|
| `none` | 0.41 | 0.22 | 0.76 |
| `pre-registration (leaky)` | 0.57 | 0.28 | 0.72 |
| `replication+retraction` | 0.93 | 0.82 | 0.19 → 0.27 |
| `invariance (k=2)` | 0.82 | 0.47 | 0.39 → 0.37 |

**Where the data points.** At k=2 in this regime, the predicted crossover
does not appear: R+R's precision falls slowly (0.93 → 0.82) while
invariance(k=2)'s falls steeply (0.82 → 0.47), so the gap widens with bias
rather than closing. **k=2 invariance is not the version of the claim that
matters here** — the natural next test is *strict* invariance (k → n_contexts)
under a regime where it has the data to function. That test isn't possible
under the current uniform-attention model: at ~2.25 studies/H, k=3 catches
~11% of true H and k=4 catches ~2% — too few findings to compare meaningfully
against R+R. Phase 2's non-uniform-attention upgrade is the prerequisite for
running it.

**Why k=2 invariance leaks**: each context's bias is an independent N(0,1)
draw (at bs=1.0). For a false H to clear invariance k=2 by chance, it needs
positive bias in any 2 of 4 contexts — a non-trivial probability. The filter
catches FPs whose bias was lucky in only one context, but lets through FPs
whose bias was lucky in two. **The filter scales with k**: at k=4, the false
H needs lucky bias in all 4 contexts — much rarer. So the bias-robustness
prediction is geometrically tied to k, and k=2 is structurally the weakest
version of the test.

**Why R+R holds up at this regime**: audit replicates draw *fresh* private
noise (this is the variance-fix; the previous broken model artificially
shrank it). Lucky-by-private FPs get retracted at every audit cycle
regardless of bias; only lucky-by-bias FPs (where the bias alone is enough
to drive the audit Z above threshold) survive. At bs=1.0, that fraction
grows but doesn't overwhelm — total FP retention rises slowly. R+R's
per-finding-independent audit is structurally fit for catching the FPs that
are easiest to catch (lucky-private), and that's most of them at moderate
bias.

**Where this points next**:

1. **Phase 2 — non-uniform hypothesis selection** (FUTURE_WORK.md). The
   prerequisite for testing high-k invariance. Under power-law attention,
   heavily-studied H accumulate the multi-context coverage that lets k=3,
   k=4 invariance actually filter; the long tail keeps `none` recall
   meaningful. This unlocks the *real* invariance vs. R+R comparison.

2. **Phase 2.B — cross-base audit comparison**. A small extension to
   `ReplicationAndRetraction` (one boolean parameter) that draws a fresh
   bias per audit instead of inheriting the (h, ctx) bias. The interesting
   question: does R+R-under-cross-base still hold up at high bias? If yes,
   the result generalizes (audit is structurally fit). If no, the project's
   claim survives as "invariance dominates *same-base* R+R, but cross-base
   R+R is equivalent."

3. **Sensitivity sweeps within each mitigation**. `audit_fraction`,
   `audit_sample_size`, `k_contexts` × `n_contexts` joint sweeps — to map
   the parameter space rather than test single points.

**One observation to carry forward**: pre-registration (leaky) does *not*
defend against bias-driven FPs in this model — its trajectory falls in
parallel with `none`, just shifted up by the QRP-clamp's effect. Pre-reg
addresses one source of inflated significance (QRP); bias is a separate
source; pre-reg doesn't touch it. This suggests a useful refinement to the
mitigation taxonomy: distinguish *source-of-error* mitigations (pre-reg ↔
QRP, audit ↔ random per-study noise, invariance ↔ per-context bias) and
expect each to address only its corresponding noise source.

**Contrast with the broken-noise-model run** (preserved here as a record of
what the model-fix changed): the prior Phase 1.D showed R+R precision
*staying flat* and recall rising sharply with the old ρ parameter — an
artifact of the Gaussian-copula form shrinking audit private noise at
high ρ. Under the corrected additive-bias model, R+R precision *does* fall
with bias (modestly) and recall rises (modestly) — both effects are real
but smaller than the artifact made them look. The diagnostic value of the
fix: it changed what we *thought* the answer was, and revealed what the
actual model says.
