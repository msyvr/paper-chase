# paper-games

Agent-based simulation of automated science under publish-or-perish incentives.

Paper-games is a multi-agent simulation of a scientific publishing ecosystem.
The Pareto frontier for truth-content (precision) and discovery rate (recall)
of the body of literature is evaluated as a function of increasing
incentive pressure and agent scale.

We also implement specific safeguards to identify Pareto dominance and tradeoffs.
Interventions include:

- pre-registration (hypothesis/methods/analysis)
- incentivized replication + retraction
- measurement-invariance requirements

Builds on Smaldino & McElreath, _[The natural selection of bad science](https://royalsocietypublishing.org/rsos/article/3/9/160384/56494/The-natural-selection-of-bad-scienceThe-Natural)_ (RSOS 2016).

## Status

Validity gate implemented

- With no mitigation, the literature's truth-content falls
  as the novelty:replication reward ratio rises: the qualitative crisis dynamic
  is reproduced.

Currently in-flight extensions:

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
