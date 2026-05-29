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

**Regime.** Same as Phase 1.D — bias_strength ∈ [0, 1.0], novelty_weight =
10, n_contexts = 4, uniform attention.

**Result.** Invariance(k=2) precision falls steeply with bias_strength
(0.82 at bs=0 → 0.47 at bs=1.0) while R+R precision falls modestly (0.93 →
0.82). The gap *widens* against invariance as bias rises. See
[Phase 1.D](example-runs/README.md#phase-1d--bias-strength-sensitivity),
commit `2cb5d1e`.

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

**Status.** Preliminary (one n_contexts, one bias range, one attention
model).

---

## 3. Same-base replication+retraction holds up at moderate bias correlation (≤ 0.5)

**Regime.** Phase 1.D — bias_strength ∈ [0, 1.0], corresponding to
correlation between same-(h, ctx) studies of ∈ [0, 0.5]. Same-base audit:
audit shares the per-(h, ctx) systematic bias; private (sampling) noise is
fresh.

**Result.** R+R precision falls modestly with bias_strength (0.93 → 0.82
across the sweep). Recall *rises* slightly (0.19 → 0.27) because at higher
bias, true positives with positive systematic bias clear significance more
reliably and audit confirms them. See [Phase 1.D](example-runs/README.md#phase-1d--bias-strength-sensitivity).

**Mechanism.** Audit effectiveness depends on the audit's ability to
distinguish lucky-by-private FPs (where the original's significance
required favourable random sampling) from signal-bearing TPs. At moderate
correlation, lucky-by-private FPs are caught by the audit's fresh sampling
draw, which is independent of the original. Only lucky-by-bias FPs (where
the systematic bias alone is strong enough to drive significance) survive
audit, and at bs ≤ 1.0 these are a minority.

**Real-world translation.** For LLM-based audit of LLM-generated findings,
R+R is likely sufficient when the bias-derived correlation between original
and audit is moderate (corresponding roughly to "LLMs that produce different
outputs from different sampling temperatures even on the same prompt"). For
domains where the audit LLM is the same model as the generator AND the
model is highly confident on its blind spots (correlation ≥ 0.7–0.9),
expect R+R to fail — switch to cross-model audit or multi-context invariance.

**What hasn't been tested.** The high-correlation regime (bias_strength
≥ 2.0, correlation ≥ 0.8) where R+R is mechanistically expected to break.
This is a cheap sweep extension worth running before Phase 2: bs ∈ {0,
0.5, 1.0, 2.0, 5.0} would establish where the breakdown actually occurs.

**Status.** Preliminary (only moderate-correlation regime tested;
high-correlation prediction mechanistically clear but empirically
unconfirmed).

---

## 4. Pre-registration addresses QRP, not systematic bias

**Regime.** Phase 1.D bias sweep with pre-registration (leaky, qrp_cap=0.1).

**Result.** Pre-reg precision falls in parallel with `none` as
bias_strength rises (0.57 → 0.28 vs. `none` 0.41 → 0.22). Pre-reg shifts
precision up by a roughly constant ~0.15 across the range (the QRP
suppression) but **does not reduce the slope** (the bias degradation). See
[Phase 1.D](example-runs/README.md#phase-1d--bias-strength-sensitivity).

**Mechanism.** Pre-registration clamps `qrp_intensity` at the action stage —
it caps how much a researcher can inflate effective α through analytic
flexibility. Systematic bias enters the test statistic *additively* and is
unaffected by anything the researcher does. Two independent sources of
false positives; pre-reg addresses only one. The slope of `none` and
pre-reg curves on the precision-vs-bias panel is the visual signature: same
slope means same bias-sensitivity; different intercepts means different QRP
exposure.

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

**Status.** Established (the parallel-slope behaviour is consistent across
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

## Open questions worth elevating to findings later

The findings above are what we can say with mechanism and evidence today.
The questions below are conjectures we've identified but not yet tested —
likely candidates for entries once Phase 2 and the cheap extensions land.

- **At high bias correlation (bs ≥ 2, correlation ≥ 0.8), does same-base
  R+R break down?** Mechanistically expected; sweep is cheap.
- **At high k under non-uniform attention, does invariance dominate same-base
  R+R?** The proper test of the project's central claim.
- **Does cross-base audit close the gap between same-base R+R and
  invariance?** Tests whether the project's claim is really about
  audit-semantics or about mitigation-type.
- **Does non-uniform (power-law) attention recover realistic recall while
  letting high-k invariance function?** The decoupling Phase 2 aims for.

Each becomes a finding when an experiment establishes its regime.
