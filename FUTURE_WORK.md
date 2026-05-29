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

### Fractional pre-registration coverage

`PreRegistration` currently treats coverage as binary — every study is pre-
registered when the mitigation is active, none are when it isn't. A `coverage`
parameter ∈ [0, 1] would model adoption dynamics: a field where pre-registration
is partial. Useful for governance questions like *what fraction of pre-reg
adoption is needed to recover most of the benefit?*

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
