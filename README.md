# paper-chase

Agent-based simulation of automated science under publish-or-perish incentives.

Paper-chase is a multi-agent simulation of a scientific publishing ecosystem.
The Pareto frontier for truth-content (precision) and discovery rate (recall)
of the body of literature is evaluated as a function of
incentive pressure and systematic bias.

We start with a validity gate on the statistical engine. As incentives increase
reward for novel results over replication of previously published work, the
literature's precision falls: rising QRP inflates the effective false-positive
rate, so false positives accumulate in the standing literature, driving
truth-content down.

Next, we implement interventions hypothesized to impact either/both precision
and recall. Mapped to the Pareto plane, dominance regimes and tradeoffs are
characterized for baseline, per-intervention, and intervention combinations.

Initial interventions include:

- pre-registration (hypothesis, methods, analysis)
- incentivized replication + retraction
- measurement-invariance requirements

Builds on Smaldino & McElreath, _[The natural selection of bad science](https://royalsocietypublishing.org/rsos/article/3/9/160384/56494/The-natural-selection-of-bad-scienceThe-Natural)_ (RSOS 2016).

## Status

For recent results, see [example runs](example-runs/README.md). For the curated synthesis — established findings by regime, each with mechanism and a status tag — see [FINDINGS.md](FINDINGS.md).

Statistical engine validated (FPR ≈ α at q=0; power monotone in n)

- With no mitigation, the literature's truth-content falls
  as the novelty:replication reward ratio rises; the qualitative crisis dynamic
  is reproduced.

Initial interventions (in progress)

- pre-registration: a modest precision lift (largest at low bias, vanishing as systematic bias takes over — it addresses QRP, not bias) at a small recall cost
- incentivized replication + retraction: raises precision substantially at low–moderate bias and cuts recall; but a same-base audit *inherits* the shared systematic bias, so its precision collapses once that bias is strong — an argument for cross-model audit
- measurement-invariance: the initial uniform sampling algorithm compute-restricted experiments to a small number of invariance-replications, so precision improvements were observed, but the significant reduction in recall dominated this intervention; next up: realistic sampling algorithms

Future extensions:

1. cross-context bias persistence — does invariance keep its advantage when a shared base model's bias persists *across* contexts, not just within? (the load-bearing test; the current model draws each context's bias independently)
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
