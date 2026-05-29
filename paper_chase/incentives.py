"""Rewards

Significant findings get a publication payoff. Novel positives are worth
more than replication positives (the "novelty premium" that drives the crisis).
A per-unit-sample effort cost discourages infinite effort.
"""
from __future__ import annotations

from .config import IncentiveConfig


def compute_reward(
    kind: str,
    significant: bool,
    sample_size: int,
    incentive: IncentiveConfig,
) -> float:
    """Reward for the outcome of one study."""
    if kind not in ("novel", "replication"):
        raise ValueError(f"unknown kind: {kind!r}")

    payoff = 0.0
    if significant:
        payoff = incentive.novel_weight if kind == "novel" else incentive.replication_weight
    cost = incentive.effort_cost_per_sample * sample_size
    return payoff - cost
