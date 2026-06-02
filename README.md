# paper-chase

Agent-based simulation of automated science under publish-or-perish incentives.

Paper-chase is a multi-agent simulation of a scientific publishing ecosystem.
The Pareto frontier for truth-content (precision) and discovery rate (recall)
of the body of literature is evaluated as a function of increasing
incentive pressure and agent scale.

We start by verifying the model. As incentives increase reward for novel results
vs replication of previously published work, we observe decreased precision in
the literature corpus. False negatives increase, generating downward pressure
on truth-content.

Next, we implement interventions hypothesized to impact either/both precision
and recall. Mapped to the Pareto plane, dominance regimes and tradeoffs are
characterized for baseline, per-intervention, and intervention combinations.

Initial interventions include:

- pre-registration (hypothesis, methods, analysis)
- incentivized replication + retraction
- measurement-invariance requirements

Builds on Smaldino & McElreath, _[The natural selection of bad science](https://royalsocietypublishing.org/rsos/article/3/9/160384/56494/The-natural-selection-of-bad-scienceThe-Natural)_ (RSOS 2016).

## Status

For recent results, see [example runs](example-runs/README.md).

Statistical engine validated (FPR ≈ α at q=0; power monotone in n)

- With no mitigation, the literature's truth-content falls
  as the novelty:replication reward ratio rises; the qualitative crisis dynamic
  is reproduced.

Initial interventions (in progress)

- pre-registration: increases precision modestly and has an accompanying decrease in recall
- incentivized replication plus a retraction mechanism: increases precision moderately, decreases recall significantly
- measurement-invariance: the initial uniform sampling algorithm compute-restricted experiments to a small number of invariance-replications, so precision improvements were observed, but the significant reduction in recall dominated this intervention; next up: realistic sampling algorithms

Future extensions:

1. correlated errors from shared base models
2. adaptive (RL) agents that learn to game/reward-hack
3. early-warning detection

## Setup

```bash
uv sync                                # creates .venv, installs deps + dev group, writes uv.lock
uv run pytest                          # statistical engine: FPR ≈ α, power monotone in n
uv run python scripts/run_baseline.py  # produces results/validity_gate.png
```

## Metrics

- **truth-content** = TP / (TP + FP) = precision over the standing literature = 1 − FDR
- **discovery rate** = TP / (TP + FN) = recall (field-level power)
- Pareto gives a read on both and is necessary here since precision is gameable \
  ('publish nothing' maps to precision = 1)

## Acknowledgments

The framing — replication crisis in _automated_ science as a problem worth
stress-testing via simulation of mitigations — is from one of the project
bullets on Konstantinos Voudouris's
[Pivotal mentor profile](https://www.pivotal-research.org/mentors#konstantinos-voudouris).
The implementation here is mine; design choices, stylized parameter values, and errors are mine alone.
