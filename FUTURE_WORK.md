# Future work

Deferred design directions for paper-chase — items intentionally not in the
current phase, with reasoning. Tracked here rather than in code so the design
space stays open to revision. Each section names the idea, why it isn't in
scope yet, and the scaffolding shape if/when it lands.

---

## Within Phase 1

### Cross-model audits in `ReplicationAndRetraction`

The current `ReplicationAndRetraction` audit reuses the same
`(hypothesis, context)` shared error shock as the original study —
modelling *audit-by-same-base-model.* A cross-model audit would draw a fresh,
independent shock — modelling *audit-by-a-different-base-model*, which breaks
correlated-error blind spots.

A single boolean parameter on the mitigation would suffice. Useful as an
explicit comparison: lets the headline result (invariance > replication under
correlated errors) be supplemented with a direct demonstration of when
cross-model replication is sufficient vs. when invariance still wins.

### Cross-context bias persistence (the central-claim stress test)

`simulation.py` draws each `(hypothesis, context)` bias *independently*
(`bias ~ N(0, bias_strength²)` per pair). That cross-context independence is what lets
invariance filter bias (a lucky bias in one context is an independent draw in another) — and it
is the **single assumption most determinative of the project's central claim** (FINDINGS
Finding 2). If a shared base model's bias *persists across contexts* (plausible — the contexts
share the model), multi-context evidence requirements weaken alongside same-base audit, and
invariance's advantage shrinks or disappears.

Scaffolding shape: split the bias into a per-hypothesis component (shared across that
hypothesis's contexts) and a per-(h, ctx) component, mixed by `cross_context_rho ∈ [0, 1]`
(0 = current independent-context model; 1 = bias fully shared across contexts). Re-run the
Phase 1.D invariance-vs-R+R comparison across that knob. Cheap (local sim), highest scientific
value — it tests whether the headline (invariance beats same-base audit under correlated error)
survives when the correlation is *cross-context*, not just within-(h, ctx).

### Fractional pre-registration coverage

`PreRegistration` currently treats coverage as binary — every study is pre-
registered when the mitigation is active, none are when it isn't. A `coverage`
parameter ∈ [0, 1] would model adoption dynamics: a field where pre-registration
is partial. Useful for governance questions like *what fraction of pre-reg
adoption is needed to recover most of the benefit?*

### Non-uniform hypothesis selection (power-law attention)

`ParametricAgent.choose_action` currently picks `target_id` uniformly at random
over `range(world.n_hypotheses)`. Real scientific attention is heavily skewed —
a few hypotheses are studied across many labs/contexts (heavily-replicated
"important" results), while the long tail goes unstudied. With uniform
selection, the invariance mitigations at higher k cannot function under
realistic hypothesis-space-to-action-budget ratios: most true hypotheses simply
don't accumulate enough multi-context evidence.

A power-law (Zipf-style) selection weight over hypotheses would model this
realistically: a subset of H receives heavy multi-study coverage (where
invariance can work), while most receive 0–1 studies (where it cannot). The
expected finding: invariance gives high precision *on the well-studied
fraction* of the literature while leaving the long tail unfiltered — a more
honest picture than the uniform-selection result.

Scaffolding shape: a `selection_weight: str = "uniform" | "zipf"` parameter on
`AgentConfig` (or a callable for general weighting). One-line dispatch in
`choose_action`; everything else unchanged. Pair with a similar refit of
`p_replicate` weighting to bias replications toward already-published findings
(which is what happens in real meta-science).

This was flagged during Phase 1.C analysis: at `n_hypotheses=10000` with
`n_steps=1500`, invariance k≥3 has enough data to function but the comparison
remains artificially flat across hypotheses. Non-uniform selection is the
realism upgrade that makes the regime question disappear.

---

## External validity

### Calibrating bias to a real automated-research system

The map from `bias_strength` to any specific deployed system is illustrative, not measured
(`docs/bias-strength-units.md`). But the external-validity question — *where does real practice
sit on the bias axis?* — is empirically resolvable, because the governing quantity (the
original–auditor correlation) is directly measurable.

Experiment: take a batch of hypotheses/analyses with ground truth (or a set of known-false
ones), run a same-model audit and a different-family-model audit, and measure either (a) the
same-model audit's false-confirm rate on the false items, or (b) the correlation between the two
models' conclusions/errors on the same questions. `corr = bs²/(1+bs²)` backs out the effective
`bias_strength`; reading it against Finding 3 says whether same-base auditing is in its safe or
broken regime for that system.

Why it matters: converts the conditional finding ("same-base audit fails once the
original–auditor correlation passes ~0.5–0.8") into a *calibrated* recommendation for a specific
deployment. The single most decision-relevant follow-up — and, unlike the sim extensions, an
empirical measurement on a real system rather than a model change.

---

## Within the invariance branch (Phase 1, third mitigation)

### Per-agent or per-hypothesis-class context

The starting design for invariance will pick `context_id` uniformly per study,
isolating the invariance mechanism cleanly. Two richer variants worth exploring
once the headline result is established:

- **Per-agent context** — each agent has a fixed setup ("labs use different
  methods/populations"). Ties context to agent heterogeneity, making the
  invariance result less clean but more realistic.
- **Per-hypothesis-class context-sensitivity** — some hypotheses are inherently
  more context-sensitive than others (some effects don't generalise; some do).
  Realistic but adds dimensions to the hypothesis world.

---

## Phase 2 candidates

### Adversarial replication / between-fleet competition

Current audits are good-faith re-tests. Real automated-science deployments
could include adversarial dynamics — multiple labs / companies competing for
finite funding, where one fleet of agents has reward incentives to *knock down*
a rival fleet's findings. This isn't an instinct that emerges from reward-
pursuit alone — it requires either zero-sum reward coupling (rank-based
payoffs) or explicit cross-agent reward structure. Two scaffolding shapes:

- **Lightweight**: `adversarial_audit_fraction` on `ReplicationAndRetraction` —
  fraction of audits done with reduced power or higher α, chosen to maximise
  failure probability. Lets you sweep *what if X% of audits are hostile*
  without modelling intent.
- **Deeper**: `competition_weight` on `IncentiveConfig`, applied so a fraction
  of each agent's reward depends on rank-based comparison to others. This
  rewards "knock down competitors" as a learned strategy — qualitatively
  different model; pairs naturally with the Phase 2 RL agents below.

### RL agents (learning to game)

Replace parametric agents with learning ones. Discovered-gaming becomes
empirical rather than assumed: the model shows *what behaviours adaptive
agents learn* under each incentive regime rather than baking them in. Pair
with `competition_weight` for a real model of competitive automated science.

---

## Phase 1.D candidate (analysis, no new mechanism)

### Early-warning analysis (critical slowing down)

CSD-style indicators on the truth-content time series — rising variance and
autocorrelation as the field approaches a phase transition. Now that
`snapshot_every` defaults to 1, the full-resolution time series is already
captured; this is a pure post-hoc analysis on existing simulation output, no
new simulation mechanism required.
