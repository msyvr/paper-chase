# Example runs

Each section is the most recent result from running the relevant phase's script.
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
{1, 2, 5, 10, 20, 50} × {no mitigation, pre-registration (leaky, qrp*cap=0.1),
replication+retraction, invariance (k=2), invariance (k=3), invariance (k=4),
all-on}; 10 seeds per condition. Systematic-bias active at
`bias_strength = 0.5` (moderate — per-(h, ctx) bias SD = 0.5 vs. unit-variance
sampling noise). The hypothesis space is sized to represent the realistic
"vast hypothesis space, scarce attention" regime: `n_hypotheses = 10,000`
against ~22,500 novel actions over the run gives ~2.25 studies per
hypothesis under uniform random selection — most plausible hypotheses go
unstudied, recall stays meaningfully below 1.0 even without any mitigation.
`n_contexts = 4` so k = 4 is the strictest possible invariance bar (finding
must appear in every context). Pre-registration is modeled as \_leaky*:
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

| Mitigation               | Precision range | Recall range | Position                                                                       |
| ------------------------ | --------------- | ------------ | ------------------------------------------------------------------------------ |
| `none`                   | 0.31–0.40       | 0.74–0.77    | Baseline; QRP-driven precision loss with novelty pressure                      |
| `pre-reg (leaky)`        | ≈ 0.45          | ≈ 0.72       | Pareto-dominates `none` (mild gain in both axes)                               |
| `invariance (k=2)`       | 0.71–0.84       | 0.36–0.39    | **On the frontier** — trades recall for precision                              |
| `replication+retraction` | 0.91–0.94       | ≈ 0.21       | **On the frontier** — audit retracts many TPs given sparse confirming evidence |
| `invariance (k=3)`       | 0.97–0.99       | 0.10–0.11    | **On the frontier** — high precision, low recall                               |
| `invariance (k=4)`       | ≈ 1.00          | ≈ 0.01       | Extreme: publishes almost nothing                                              |
| `all-on`                 | ≈ 1.00          | ≈ 0.04       | Collapses to k=4-like behavior (strictest filter dominates)                    |

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
= 0.5 doesn't reduce per-study power directly; rather, it inflates the
average false-positive rate by adding a per-(h, ctx) offset to Z. This
represents the model's output for "moderately-studied effects in a vast
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

**What was run.** Sweep of `bias_strength` across {0, 0.5, 1.0, 2.0, 5.0}
at fixed `novelty_weight = 10`, over four mitigations: `none`,
`pre-registration (leaky, qrp_cap=0.1)`, `replication+retraction
(audit_fraction=0.1)`, and `invariance (k=2)`. 10 seeds per condition. Same
regime as Phase 1.C (n_hypotheses=10000, n_contexts=4, n_steps=500, uniform
hypothesis selection). High-k invariance (k=3, k=4) was excluded — Phase 1.C
established they publish almost nothing in this sparse-attention regime.
The sweep range was extended to bs=5 to test whether the bias correlation
strong enough to defeat same-base R+R audit actually does so (correlation
between same-(h, ctx) studies = bias_strength² / (1+bias_strength²), so
bs=2 → 0.80, bs=5 → 0.96 — the "same-LLM near-deterministic" regime).
Script: [`scripts/run_bias_sensitivity.py`](../scripts/run_bias_sensitivity.py).

**The claim Phase 1.D is positioned to test.** _Invariance-style mitigations
dominate audit-style ones under sufficiently strong systematic bias._
Mechanism: same-base audits inherit the per-(h, ctx) bias that drove the
original significance, so a lucky-bias FP gets confirmed by audit;
invariance requires findings across distinct contexts, each with an
independent bias draw, so a single lucky bias cannot carry an FP through.

**Result.**

![Phase 1.D bias sensitivity](images/phase-1d-bias-sensitivity.png)

| Mitigation               | bs=0        | bs=0.5      | bs=1        | bs=2            | bs=5        |
| ------------------------ | ----------- | ----------- | ----------- | --------------- | ----------- |
| `none`                   | 0.41 / 0.77 | 0.33 / 0.77 | 0.22 / 0.76 | 0.14 / 0.77     | 0.11 / 0.83 |
| `pre-reg (leaky)`        | 0.57 / 0.72 | 0.45 / 0.71 | 0.28 / 0.72 | 0.15 / 0.73     | 0.11 / 0.81 |
| `replication+retraction` | 0.93 / 0.19 | 0.91 / 0.22 | 0.82 / 0.27 | **0.30 / 0.39** | 0.11 / 0.64 |
| `invariance (k=2)`       | 0.82 / 0.40 | 0.73 / 0.38 | 0.47 / 0.37 | 0.17 / 0.37     | 0.11 / 0.44 |

_(precision / recall, bold marks the R+R cliff)_

**Where the data points.** Two distinct dynamics show up across the
extended range, neither of which is the predicted invariance-overtakes-R+R
crossover:

1. **The R+R cliff is real and dramatic** (bs=1 → bs=2). R+R precision
   collapses from 0.82 to 0.30 over this single doubling of bias_strength.
   This confirms the mechanism the project intuited — at high correlation,
   the audit replicate inherits a per-(h, ctx) bias that's large enough on
   its own to drive significance, so the fresh-private-noise trick no
   longer suffices to retract lucky-bias FPs. **R+R is regime-specific,
   not unconditionally robust.**

2. **Invariance(k=2) collapses faster than R+R across the entire range.**
   At every bias_strength tested, R+R precision ≥ invariance(k=2)
   precision. They converge at bs=5 (both at 0.11, approximately the
   `none` precision floor) — the predicted crossover does not occur at
   k=2. The multi-context filter at minimum-k is structurally too
   permissive to catch lucky-bias-in-2-of-4-contexts FPs at any tested bias.

3. **At extreme bias (bs=5), all mitigations converge to the `none`
   precision floor (~0.11)**, but only `none` preserves recall (0.83 vs.
   R+R 0.64 vs. invariance 0.44). At this regime, `none` actually
   Pareto-dominates all the mitigations — _they buy nothing at the cost of
   recall_.

**k=2 invariance is not the version of the claim that matters here** — the
natural next test is _strict_ invariance (k → n_contexts) under a regime
where it has the data to function. That test isn't possible under the
current uniform-attention model: at ~2.25 studies/H, k=3 catches ~11% of
true H and k=4 catches ~2% — too few findings to compare meaningfully
against R+R. Phase 2's non-uniform-attention upgrade is the prerequisite
for running it.

**Why k=2 invariance leaks**: each context's bias is an independent N(0,1)
draw (at bs=1.0). For a false H to clear invariance k=2 by chance, it needs
positive bias in any 2 of 4 contexts — a non-trivial probability. The filter
catches FPs whose bias was lucky in only one context, but lets through FPs
whose bias was lucky in two. **The filter scales with k**: at k=4, the false
H needs lucky bias in all 4 contexts — much rarer. So the bias-robustness
prediction is geometrically tied to k, and k=2 is structurally the weakest
version of the test.

**Why R+R holds up at moderate bias but breaks at high bias**: audit
replicates draw _fresh_ private noise (the variance-fix). At low-moderate
bias (bs ≤ 1), most FPs are "lucky-by-bias-AND-private together" — bias
alone is rarely big enough to clear z_crit on its own (z_crit ≈ 1.96; at
bs=1.0, P(|bias| > z_crit) ≈ 5%), so audit's fresh private noise breaks
the combination and retracts FPs. At high bias (bs ≥ 2), P(|bias| > z_crit)
becomes substantial (≈ 32% at bs=2, ≈ 69% at bs=5) — bias alone drives
significance, audit always confirms because it inherits the same bias,
and R+R can no longer distinguish FPs from TPs. The cliff between bs=1
and bs=2 corresponds to this transition.

**Where this points next**:

1. **Phase 2 — non-uniform hypothesis selection** (FUTURE*WORK.md). The
   prerequisite for testing high-k invariance. Under power-law attention,
   heavily-studied H accumulate the multi-context coverage that lets k=3,
   k=4 invariance actually filter; the long tail keeps `none` recall
   meaningful. This unlocks the \_real* invariance vs. R+R comparison at
   the regime (bs ≥ 2) where R+R has just been shown to break.

2. **Phase 2.B — cross-base audit comparison**. A small extension to
   `ReplicationAndRetraction` (one boolean parameter) that draws a fresh
   bias per audit instead of inheriting the (h, ctx) bias. With the
   same-base R+R cliff now empirically located at bs ≈ 1.5–2.0, the
   directly-actionable question is whether cross-base audit pushes the
   cliff to higher bias or eliminates it. If yes, the alignment-relevant
   recommendation is "use cross-base audit when expected bias > some
   threshold." If no, cross-base audit doesn't help and the recommendation
   shifts to invariance.

3. **The "useful band" framing.** Each mitigation appears to be effective
   in a narrow range of bias_strengths. Below: not needed (precision is
   acceptable without intervention). Above: not effective (precision
   collapses regardless). The bands for each mitigation are worth
   characterizing explicitly — that's the actionable artifact for
   real-world governance.

4. **Sensitivity sweeps within each mitigation**. `audit_fraction`,
   `audit_sample_size`, `k_contexts` × `n_contexts` joint sweeps — to map
   the parameter space rather than test single points.

**One observation to carry forward**: pre-registration (leaky) does _not_
defend against bias-driven FPs in this model — its trajectory falls in
parallel with `none`, just shifted up by the QRP-clamp's effect. Pre-reg
addresses one source of inflated significance (QRP); bias is a separate
source; pre-reg doesn't touch it. This suggests a useful refinement to the
mitigation taxonomy: distinguish _source-of-error_ mitigations (pre-reg ↔
QRP, audit ↔ random per-study noise, invariance ↔ per-context bias) and
expect each to address only its corresponding noise source.

**Contrast with the broken-noise-model run** (preserved here as a record of
what the model-fix changed): the prior Phase 1.D showed R+R precision
_staying flat_ and recall rising sharply with the old ρ parameter — an
artifact of the Gaussian-copula form shrinking audit private noise at
high ρ. Under the corrected additive-bias model, R+R precision _does_ fall
with bias (modestly) and recall rises (modestly) — both effects are real
but smaller than the artifact made them look. The diagnostic value of the
fix: it changed what we _thought_ the answer was, and revealed what the
actual model says.
