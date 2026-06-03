# Findings

What we know about specific regimes from experiment plus mechanism. Each entry
is a claim about behaviour in a defined parameter region, the mechanism behind
it, what it implies for real-world automated-science governance, and what
hasn't yet been tested. The translation paragraphs are forward-looking
suggestions — they hold *if* the modelled mechanism reflects the real
mechanism, which is a separate question for each entry.

This document is the curated counterpart to `example-runs/README.md` (which
records what individual runs produce). Findings live here when they
generalise across runs or matter as design guides.

**Two load-bearing modeling assumptions** shape much of what follows, and several
findings are *mechanistic consequences* of them — predictable in closed form, with the
simulation confirming rather than discovering them. (1) The decision statistic is
*additive*: `Z = noncentrality + bias + private`, with a per-(h, ctx) systematic
`bias ~ N(0, bias_strength²)` and a fresh `private ~ N(0, 1)`. (2) Each context's bias
is an *independent* draw. Assumption (2) is what lets invariance filter bias; if real
systematic biases persist across contexts (plausible for models sharing training data),
that advantage shrinks. Treat the `bias_strength` ↔ real-system mappings below as
illustrative, not measured.

Status legend:
- **Established** — observed across multiple runs, mechanism understood, robust to expected variations.
- **Preliminary** — observed in a specific regime; mechanism understood but generalisation untested.
- **Framing** — a synthesis or taxonomy that organises results; not a single experimental result.

---

## 1. Multi-mitigation Pareto frontier; no single dominant mitigation

**Regime.** n_hypotheses = 10000, n_contexts = 4, bias_strength = 0.5,
n_steps = 500, uniform hypothesis selection, novelty_weight ∈ [1, 50], 10
seeds. Mitigations: none, pre-registration (leaky qrp_cap=0.1),
replication+retraction (audit_fraction=0.1), invariance (k ∈ {2, 3, 4}),
all-on.

**Result.** At least four mitigations (pre-reg leaky, invariance k=2, R+R,
invariance k=3) sit on the precision–recall Pareto frontier at distinct
trade-off points. No mitigation Pareto-dominates another on the frontier.
Established in [Phase 1.C](example-runs/README.md#phase-1c--mitigation-comparison-pareto-plane),
figure `example-runs/images/phase-1c-mitigation-comparison.png`, commit
`cf3b8de`.

**Mechanism.** Each mitigation addresses a different source of false
positives. Pre-reg addresses QRP (researcher-inflated effective α). R+R
addresses per-finding random noise (lucky private sampling draws).
Invariance addresses per-(hypothesis, context) systematic bias (lucky
per-context offset). These sources contribute additively to total FPR and
manifest in different parts of the test statistic, so mitigations operate
on different terms and produce different precision–recall trades.

**Real-world translation.** For real automated-science governance, expect a
mitigation *portfolio* to outperform any single mitigation. The right
mitigation depends on which error source dominates in the deployment
context, not on which is "best" in general. A governance framework that
mandates one mitigation (e.g., pre-registration only) addresses one source
of error and leaves others unmitigated.

**What hasn't been tested.** Whether the frontier shape persists at higher
k under non-uniform attention, or whether cross-base audit shifts R+R off
the frontier. The multi-mitigation principle is expected to hold under
these variations, but the specific positions and crossovers will move.

**Status.** Established (same frontier shape pre- and post-noise-model-fix,
across two regime sweeps).

---

## 2. k=2 invariance is the structurally weakest version of the multi-context filter

**Regime.** Phase 1.D — bias_strength ∈ {0, 0.5, 1.0, 2.0, 5.0},
novelty_weight = 10, n_contexts = 4, uniform attention, 30 seeds (subset of the densified sweep).

**Result.** Invariance(k=2) precision falls faster than R+R across the
moderate-bias range, then converges to R+R at the extreme:

| bias_strength | R+R precision | Inv(k=2) precision | Gap (R+R − Inv) |
|---|---|---|---|
| 0.0 | 0.929 ± 0.004 | 0.822 ± 0.010 | +0.107 |
| 0.5 | 0.912 ± 0.005 | 0.715 ± 0.017 | +0.197 |
| 1.0 | 0.825 ± 0.008 | 0.459 ± 0.027 | +0.366 |
| 2.0 | 0.295 ± 0.005 | 0.175 ± 0.013 | +0.120 |
| 5.0 | 0.112 ± 0.001 | 0.113 ± 0.006 | −0.001 |

(30 seeds; ± is the 95% t-CI for the mean.)

R+R precision is greater than or equal to invariance(k=2) precision at
every bias_strength tested. They converge at bs=5 only because both have
collapsed to the `none` precision floor (~0.11). The predicted invariance
crossover does not occur at k=2. See
[Phase 1.D](example-runs/README.md#phase-1d--bias-strength-sensitivity).

**Mechanism.** Each context's bias is an independent N(0, bias_strength²)
draw. For a false H to clear invariance(k) by chance, it needs positive
bias of sufficient magnitude in k of n_contexts contexts. At n_contexts=4,
bias_strength=1.0, k=2, the probability that this happens for a random
false H is non-trivial — roughly P(bias > threshold)² for the relevant
combinations. The filter's strength scales geometrically with k: at k=4 the
false H must be lucky in *every* context, which is much rarer. **k=2 is
structurally the minimum bar and so structurally the most permissive
version of the test.**

**Real-world translation.** A "studies must replicate in at least 2
contexts" requirement — the natural minimum for any multi-context
evidence rule — is too permissive to filter out lucky-bias false positives
when systematic bias is moderate or strong. Multi-context evidence
requirements in real automated-science governance should explicitly choose
k based on expected bias strength and number of available contexts, not
default to "more than one context."

**What hasn't been tested.** How invariance k=3 and k=4 compare to R+R
under high bias. Sparse uniform attention precludes this; the non-uniform
attention upgrade is the prerequisite. Also untested: whether the result is
sensitive to n_contexts (we've only tested 4).

**Load-bearing assumption.** Invariance's bias-robustness depends entirely on each
context's bias being an *independent* draw (`simulation.py` draws `N(0, bias_strength²)`
per `(h, ctx)`). If systematic biases persist across contexts — plausible when the
underlying model is shared, as for LLMs trained on overlapping data — the multi-context
bar no longer breaks the bias, and invariance's advantage shrinks or disappears. This is
the single assumption most determinative of the project's central claim; a
correlated-cross-context arm is needed to test it.

**Status.** Preliminary (one n_contexts, one bias range, one attention
model).

---

## 3. Same-base R+R precision falls steeply between bias_strength = 1 and 2 — a normal-tail effect, not a discontinuity

**Regime.** Phase 1.D, densified — bias_strength ∈ {0, 0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 5.0},
n_contexts=4, uniform attention, novelty_weight=10, 30 seeds. Same-base audit:
audit inherits the per-(h, ctx) systematic bias; private (sampling) noise
is fresh.

**Result.** R+R precision is high and slowly-falling up to bs=1.0, then falls steeply and
smoothly through the 1→2 window:

| bias_strength | Corr | bias-sustained FP frac. | R+R precision | R+R recall |
|---|---|---|---|---|
| 0.0 | 0.00 | 0.000 | 0.929 ± 0.004 | 0.189 ± 0.006 |
| 0.5 | 0.20 | 0.000 | 0.912 ± 0.005 | 0.217 ± 0.006 |
| 1.0 | 0.50 | 0.050 | 0.825 ± 0.008 | 0.274 ± 0.007 |
| 1.25 | 0.61 | 0.117 | 0.706 ± 0.010 | 0.306 ± 0.006 |
| 1.5 | 0.69 | 0.191 | 0.537 ± 0.010 | 0.339 ± 0.006 |
| 1.75 | 0.75 | 0.263 | 0.393 ± 0.007 | 0.366 ± 0.007 |
| **2.0** | **0.80** | **0.327** | **0.295 ± 0.005** | **0.392 ± 0.006** |
| 5.0 | 0.96 | 0.690 | 0.112 ± 0.001 | 0.640 ± 0.005 |

(30 seeds; ± is the 95% t-CI for the mean. "bias-sustained FP frac." is the closed-form
`P(|bias| > z_crit) = 2·(1 − Φ(1.96 / bias_strength))` — the fraction of false positives bias
alone can sustain past the audit. In interpretable units: a genuine effect contributes ≈2.2 to
Z, so `bias_strength`=2 is a model blind-spot ≈0.9× the size of a real effect — and an 0.80
correlation between two same-model re-runs; see
[`docs/bias-strength-units.md`](docs/bias-strength-units.md) for the full conversion table.)
The 1→2 window is now densely sampled: precision descends
monotonically (0.825 → 0.706 → 0.537 → 0.393 → 0.295) and tracks the smooth rise of the
closed-form FP fraction. So the transition is **steep but smooth**, as predicted in closed
form — not a discontinuity. A same-base audit can only retract a false positive whose
significance came from *sampling* noise; it cannot retract one driven by the shared *bias*,
because the audit reuses the same per-(h, ctx) bias and redraws only the private term. At
extreme bias, precision falls to the `none` floor (≈ base_rate_true: publication becomes
nearly truth-independent).

**Mechanism.** Audit effectiveness depends on the audit's ability to
distinguish lucky-by-private FPs (where the original's significance
required favourable random sampling) from signal-bearing TPs. The audit's
fresh private noise breaks the original lucky-private draw, retracting
those FPs. But the audit *inherits* the per-(h, ctx) bias, so any FP whose
bias alone was enough to clear z_crit is confirmed by the audit. Below the
transition (bs ≤ 1), bias alone is rarely sufficient — bias + private together
is the dominant FP path, and audit catches it. Above it (bs ≥ 2),
bias alone is the dominant FP path, and audit cannot retract it.

**Real-world translation.** *The `bias_strength` ↔ real-system correlation mapping is
illustrative, not measured; the numeric thresholds here are conjectural until anchored
to a real system.* The robust, transferable claim is qualitative: a same-base audit
catches only *sampling-driven* errors, not errors from a *shared model bias* — so it is
an argument for **cross-model audit** (an independent bias draw) whenever the original
and the auditor share a base model. The conjectural quantitative read: if same-model
outputs are weakly correlated (bs ≲ 1), same-base R+R may suffice; if strongly
correlated / near-deterministic (bs ≳ 2), it is expected to break, and one should
switch to cross-model audit or a bias-addressing mitigation (invariance with sufficient
k).

**What hasn't been tested.** Whether the transition location depends on
n_contexts, novelty_weight, audit_sample_size, or audit_fraction. We've
only tested a single point in those parameter spaces; the transition might
shift with them.

**Status.** Established. The 1→2 transition is now densely sampled (30 seeds, 95% CIs):
precision descends monotonically and smoothly, tracking the closed-form normal-tail driver,
and reproduces the original endpoints. Direction, magnitude, and shape are all resolved. What
remains open is only the transition's *location* under other (n_contexts, audit) settings.

---

## 4. Pre-registration addresses QRP, not systematic bias

**Regime.** Phase 1.D bias sweep with pre-registration (leaky, qrp_cap=0.1).

**Result.** Pre-reg lifts precision over `none` by suppressing QRP, but the lift is
largest at low bias and **shrinks to nothing as bias dominates**: the pre-reg − `none`
precision gap runs 0.18 (bs=0) → 0.13 (bs=0.5) → 0.06 (bs=1) → ~0.01 (bs≥2), both curves
converging onto the ~0.11 floor at high bias. Pre-reg moves the intercept (QRP exposure),
not the bias-driven descent — so it cannot defend against bias-driven FPs. See
[Phase 1.D](example-runs/README.md#phase-1d--bias-strength-sensitivity).

**Mechanism.** Pre-registration clamps `qrp_intensity` at the action stage —
it caps how much a researcher can inflate effective α through analytic
flexibility. Systematic bias enters the test statistic *additively* and is
unaffected by anything the researcher does. Two independent sources of
false positives; pre-reg addresses only one. The visual signature on the
precision-vs-bias panel: pre-reg sits above `none` at low bias (the QRP lift) but
converges onto it as bias rises — the lift is bias-orthogonal, and the bias-driven
descent is untouched.

**Real-world translation.** Pre-registration mandates cannot substitute for
bias-addressing mitigations. If the deployment's primary FP source is
base-model systematic limitation (not researcher analytic flexibility),
pre-registration provides essentially no precision lift over no mitigation
at all. Governance frameworks should diagnose the dominant error source
before mandating a mitigation — "we pre-registered" does not mean "all
error sources are addressed."

**What hasn't been tested.** Pre-reg under cross-base evaluation, or under
QRP regimes extreme enough that the QRP suppression dominates other
dynamics.

**Status.** Established (the QRP-lift-then-converge behaviour is consistent across
all bias_strength values tested and is mechanistically transparent).

---

## 5. Mitigation taxonomy by source-of-error

**Regime.** Conceptual synthesis from Phase 1.C and Phase 1.D; applies
wherever the modelled noise structure holds.

**Result.** Three distinct false-positive sources, each addressed by a
specific mitigation type:

| Error source | Mechanism | Mitigation type |
|---|---|---|
| QRP (researcher-inflated effective α) | Action-stage analytic flexibility | Pre-registration (clamp `qrp_intensity`) |
| Per-finding random noise | Sampling variation; lucky private draws | Replication+retraction (fresh audit draws catch them) |
| Per-(h, ctx) systematic bias | Base-model blind spot in a specific context | Invariance (multi-context evidence breaks single-context bias) |

Each mitigation provides essentially no protection against error sources it
isn't designed for. Phase 1.D pre-reg-vs-bias demonstrates this directly
(same slope, different intercept).

**Mechanism.** Each error source enters the decision statistic Z through a
different mechanism — QRP through the test threshold (effective α), random
noise through the private term, systematic bias through the per-(h, ctx)
offset. Mitigations target specific mechanisms and operate on specific
terms.

**Real-world translation.** Useful design principle for real
automated-science governance: catalogue the error sources expected in your
deployment, then match each to its mitigation. No single mitigation
addresses all sources. A composite mitigation framework should pair
pre-registration (against analytic flexibility) with cross-model audit OR
invariance (against systematic bias) with appropriate sample-size
requirements (against random sampling noise) — each component covers a
distinct gap.

**What hasn't been tested.** Higher-order error sources we haven't modelled
yet — adversarial replication, social dynamics, cross-model correlation
through shared training data, attention-skew biases. The taxonomy might
need extension as the model grows.

**Status.** Framing (a synthesis organising experimental results, not a
single experimental result; supported by the Phase 1.D pre-reg-vs-bias
observation).

---

## 6. High-k invariance is data-hungry under uniform attention

**Regime.** Phase 1.C — n_hypotheses=10000, n_contexts=4, n_steps=500,
~2.25 studies per H, uniform random hypothesis selection.

**Result.** Invariance recall by k under this regime:

| k | Recall (true H released) |
|---|---|
| 2 | ~38% |
| 3 | ~11% |
| 4 | ~2% |

See [Phase 1.C](example-runs/README.md#phase-1c--mitigation-comparison-pareto-plane).

**Mechanism.** Invariance requires k significant findings in k distinct
contexts before publication. The number of distinct contexts hit per H
follows a coupon-collector distribution: at ~2.25 studies per H over
n_contexts=4, expected distinct contexts hit ≈ 4 × (1 − (3/4)²·²⁵) ≈ 1.85.
Higher k requires more distinct contexts, which requires more studies per
H. Under uniform sparse attention, most H simply don't accumulate enough
multi-context coverage.

**Real-world translation.** A "publish only with k-context replication"
requirement in real automated science is genuinely data-hungry — each
hypothesis needs on the order of 3k studies on average for k-invariance to
function at non-trivial recall. For fields with concentrated attention (a
few topics heavily studied across many labs), invariance works on the
well-studied subset. For the long-tail majority, invariance becomes
equivalent to "don't publish" — a defensible stance but a costly one.

**What hasn't been tested.** Non-uniform attention. In a real field, study
concentration is power-law: a few hypotheses get heavy multi-context
coverage (where k=4 can function), most get 0–1 studies (where invariance
amounts to suppression). The Phase 2 attention model upgrade is the
prerequisite for re-testing high-k invariance under realistic study
distributions.

**Status.** Established (mathematical mechanism plus consistent empirical
observation across runs).

---

## 7. Recall saturation under uniform attention is a modelling artifact

**Regime.** Phase 1.C diagnostic — observed at n_hypotheses=1000 (recall
≈ 1.0 for `none`), fixed by moving to n_hypotheses=10000 (recall ≈ 0.75).

**Result.** At sufficient study-budget-per-H × per-study-power product,
recall for `none` saturates at 1.0 — every true H ends up with at least one
significant finding in the literature. This is independent of any
mitigation and is a property of the action budget vs hypothesis space
ratio under uniform attention. See [Phase 1.C](example-runs/README.md#phase-1c--mitigation-comparison-pareto-plane)
diagnostic, commit `cf3b8de`.

**Mechanism.** Under uniform random hypothesis selection, with budget B
total novel actions over H hypotheses, expected studies per H ≈ B/H. With
per-study power p, recall ≈ 1 − exp(−(B/H) × p). At moderate per-study
power (~0.7) and B/H ≥ ~5, recall asymptotes to 1.0 — most true H get
multiple chances to clear α somewhere.

**Real-world translation.** Real fields don't have uniform attention — most
plausible hypotheses are never studied, a few are studied heavily.
Saturation in real meta-science would only occur for the well-studied
subset, never the long tail. Any modelling of real-world recall needs
non-uniform attention to be representative; uniform random selection
overestimates field-wide recall and produces a misleading picture of
mitigation costs (mitigations that "reduce recall" look worse than they
should because the baseline recall is artificially high).

**What hasn't been tested.** Whether non-uniform attention shifts other
findings in this list. We expect the Pareto frontier shape (Finding 1) and
the mitigation taxonomy (Finding 5) to be robust to attention model, but
invariance recall numbers (Finding 6) and `none` saturation (Finding 7) to
change qualitatively.

**Status.** Established (mathematical mechanism plus empirical observation;
the regime fix is well understood and reproducible).

---

## 8. At extreme bias, no mitigation provides precision lift; `none` Pareto-dominates

**Regime.** Phase 1.D extended at bias_strength = 5.0 (correlation between
same-(h, ctx) studies ≈ 0.96, n_contexts=4, uniform attention,
novelty_weight=10).

**Result.** At bs=5, every tested mitigation collapses to the same
precision (≈ 0.11), which is also the `none` precision. They differ only
in recall — and only in the wrong direction for them:

| Mitigation | Precision | Recall | Position |
|---|---|---|---|
| `none` | 0.106 ± 0.001 | 0.828 ± 0.004 | **Pareto-dominant** |
| `pre-reg (leaky)` | 0.107 ± 0.001 | 0.809 ± 0.004 | Dominated |
| `replication+retraction` | 0.112 ± 0.001 | 0.640 ± 0.005 | Dominated (loses recall to audit retractions) |
| `invariance (k=2)` | 0.113 ± 0.006 | 0.448 ± 0.006 | Dominated (loses recall to multi-context buffering) |

(30 seeds; ± is the 95% t-CI for the mean. The ≈0.11 precision floor is essentially `base_rate_true` = 0.10.)

At this bias regime, every mitigation costs recall without providing
precision in return. `none` Pareto-dominates all four.

**Mechanism.** At bs=5, P(|bias| > z_crit) ≈ 69% per (h, ctx). Bias alone
drives significance for the majority of studies regardless of true effect,
so the literature is overwhelmed with bias-driven findings (false
positives, mostly). Mitigations that depend on filtering significance
patterns lose their grip: R+R audits inherit the same lucky bias and
confirm; invariance's per-context bias draws are not independent enough
across contexts when each is large; pre-reg's QRP clamp doesn't touch
bias. All converge to the bias-dominated FP floor.

**Real-world translation.** **There is a bias regime above which
publication-process mitigations stop helping.** If a deployment's
systematic bias is strong enough (high per-(h, ctx) bias magnitude),
no audit-style or invariance-style intervention can recover precision —
they will only reduce throughput. The actionable inference: **at high
expected bias, the right intervention is at the model/training level**
(reduce the bias itself, or use a different model class), not at the
publication-process level. Process mitigations are useful in a finite band
of bias regimes; outside that band, address the bias directly or accept
high false-positive rates.

This is a strong claim with one important caveat: we have not tested high
k under non-uniform attention. *Strict* invariance (k = n_contexts) might
still filter even at high bias, because the multi-context requirement
becomes geometrically harder for lucky biases to satisfy. The "no
mitigation helps" claim should be read as "no *currently-feasible* mitigation
at the regime currently testable" — Phase 2 might extend the useful band.

**What hasn't been tested.** Whether the convergence point (bs at which
all mitigations collapse to `none` precision) shifts with n_contexts,
audit_sample_size, audit_fraction, or per-study effect size / sample size.
The transition in Finding 3 located the regime shift for R+R; the
analogous transition for invariance and the collapse point for the whole
mitigation set haven't been fully mapped.

**Status.** Established at one parameter setting (extended Phase 1.D);
mechanism is mechanistically transparent. Generalisation to other
(n_contexts, k_contexts, audit parameters) settings is pending.

---

## 9. Cross-model audit partially recovers precision; independence helps, the auditor's own bias caps it

**Regime.** Phase 1.D densified, 30 seeds. Cross-model R+R: the auditor draws its *own*
independent per-(h, ctx) bias ~ N(0, bias_strength²) instead of reusing the original's —
modelling audit-by-a-different-base-model.

**Result.** Cross-model R+R precision exceeds same-base across the moderate-bias band:

| bias_strength | same-base R+R | cross-model R+R | lift |
|---|---|---|---|
| 0.0 | 0.929 ± 0.004 | 0.929 ± 0.004 | 0.000 |
| 1.0 | 0.825 ± 0.008 | 0.851 ± 0.007 | +0.026 |
| 1.25 | 0.706 ± 0.010 | 0.772 ± 0.008 | +0.066 |
| 1.5 | 0.537 ± 0.010 | 0.648 ± 0.011 | **+0.111** |
| 1.75 | 0.393 ± 0.007 | 0.486 ± 0.011 | +0.093 |
| 2.0 | 0.295 ± 0.005 | 0.371 ± 0.010 | +0.076 |
| 5.0 | 0.112 ± 0.001 | 0.114 ± 0.002 | +0.002 |

(30 seeds; ± is the 95% t-CI. bs=0.5 omitted — both ≈0.91, lift ≈0.) The lift is significant
(CIs ≈ ±0.01) across bs ∈ [1, 2], peaks at bs=1.5 (+0.11), and is ≈0 at the endpoints (no bias
at bs=0; both at the floor at bs=5).

**Mechanism.** Same-base audit reuses the original's bias, so it confirms every bias-driven FP.
Cross-model audit draws an *independent* bias, breaking the exact inheritance — so it retracts
the bias-driven FPs same-base cannot. But the cross-model auditor is *itself* biased (same
magnitude, independent draw), so it confirms some FPs by its own bias: the recovery is
**partial, not complete**. At extreme bias the auditor is as overwhelmed as the original → no lift.

**Real-world translation.** Auditing automated science with a *different* model recovers part of
the precision a same-model audit loses — the value is in the auditor's errors being *uncorrelated*
with the original's. But a different model is still a model: the cleaner its independence (and the
lower its own bias on the relevant questions), the more it recovers; at extreme model bias no
audit helps and you fix the model (Finding 8). Actionable read: prefer a different-family auditor,
the further from the original's blind spots the better.

**What hasn't been tested.** Cross-model with a *lower* auditor bias (a less-biased auditor →
fuller recovery). This experiment held the auditor's bias equal to the original's, isolating the
independence effect; a better auditor is a separate, expected lift.

**Status.** Established (the lift is significant across the moderate-bias band; mechanism
transparent and consistent with Finding 8 at the extreme).

---

## Open questions worth elevating to findings later

The findings above are what we can say with mechanism and evidence today.
The questions below are conjectures we've identified but not yet tested —
likely candidates for entries once Phase 2 and the cheap extensions land.

- **At high bias correlation (bs ≥ 2, correlation ≥ 0.8), does same-base
  R+R break down?** Mechanistically expected; sweep is cheap.
- **At high k under non-uniform attention, does invariance dominate same-base
  R+R?** The proper test of the project's central claim.
- ~~Does cross-base audit close the gap between same-base R+R and invariance?~~
  **Answered → Finding 9:** cross-model audit *partially* recovers precision —
  independence breaks the bias-inheritance, but the auditor's own bias caps it. The
  claim is about audit-semantics (independence of the auditor's errors), not
  mitigation-type.
- **Does non-uniform (power-law) attention recover realistic recall while
  letting high-k invariance function?** The decoupling Phase 2 aims for.

Each becomes a finding when an experiment establishes its regime.
