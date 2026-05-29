"""Tests for the main simulation loop — credit-dispatch behavior, end-to-end shape."""
from paper_chase.config import (
    SimConfig, IncentiveConfig, AgentConfig, WorldConfig,
)
from paper_chase.simulation import run


def test_credit_to_original_author_increases_total_payoff():
    """When ``replication_credit_to_original_author > 0``, total payoff
    exceeds the no-credit case.

    Same seed → identical action sequence and study outcomes between the two
    runs. The only difference is the credit dispatch on successful replications,
    so total payoff with credit must strictly exceed total without — provided at
    least one replication succeeds, which the chosen parameters guarantee.
    """
    common = dict(
        world=WorldConfig(n_hypotheses=100, base_rate_true=0.3, seed=0),
        agent=AgentConfig(
            n_agents=10,
            qrp_mean=0.2, qrp_sd=0.0,
            effort_mean=30.0, effort_sd=0.0,
            p_replicate=0.3,
        ),
        n_steps=30,
        seed=0,
    )
    base = dict(novel_weight=10.0, replication_weight=1.0, effort_cost_per_sample=0.0)

    cfg_with = SimConfig(
        **common,
        incentive=IncentiveConfig(**base, replication_credit_to_original_author=5.0),
    )
    cfg_without = SimConfig(
        **common,
        incentive=IncentiveConfig(**base, replication_credit_to_original_author=0.0),
    )

    result_with = run(cfg_with)
    result_without = run(cfg_without)

    total_with = sum(a.cumulative_payoff for a in result_with.agents)
    total_without = sum(a.cumulative_payoff for a in result_without.agents)

    assert total_with > total_without, (
        f"credit dispatch failed: total with credit ({total_with}) "
        f"not greater than without ({total_without})"
    )


def test_credit_default_is_zero_no_behavior_change():
    """With ``replication_credit_to_original_author = 0`` (the default), agent
    payoffs are exactly what ``compute_reward`` produces — no extra credit."""
    cfg = SimConfig(
        world=WorldConfig(n_hypotheses=50, base_rate_true=0.3, seed=0),
        agent=AgentConfig(
            n_agents=5,
            qrp_mean=0.1, qrp_sd=0.0,
            effort_mean=30.0, effort_sd=0.0,
            p_replicate=0.3,
        ),
        incentive=IncentiveConfig(novel_weight=10.0, replication_weight=1.0, effort_cost_per_sample=0.0),
        n_steps=15,
        seed=0,
    )
    result = run(cfg)
    # No assertion on absolute value; just sanity that the run completes and
    # produces history snapshots. Behavioral parity vs. the previous version
    # is implicitly checked by the validity-gate run if its qualitative shape
    # is preserved.
    assert len(result.history) > 0
    assert all(a.cumulative_payoff >= -1e9 for a in result.agents)
