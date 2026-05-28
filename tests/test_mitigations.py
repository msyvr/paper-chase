"""Mitigation scaffold tests.

Two invariants matter for the scaffold:
1. The plumbing must not drift the Phase-0 baseline when no mitigations are
   active (``mitigations=None`` or ``mitigations=[]``).
2. The identity mitigation ``NoMitigation`` must give bit-identical results
   to the no-mitigations case — i.e., the publish-gating chain with one
   pass-through link should be indistinguishable from no chain at all.
"""
from paper_games.config import (
    SimConfig, IncentiveConfig, AgentConfig, WorldConfig, StudyConfig,
)
from paper_games.simulation import run
from paper_games.mitigations import Mitigation, NoMitigation


def _common_cfg() -> SimConfig:
    """A small but non-trivial run that produces a useful literature for comparison."""
    return SimConfig(
        world=WorldConfig(n_hypotheses=100, base_rate_true=0.3, seed=0),
        agent=AgentConfig(
            n_agents=10, qrp_mean=0.2, qrp_sd=0.0,
            effort_mean=30.0, effort_sd=0.0, p_replicate=0.3,
        ),
        study=StudyConfig(alpha=0.05, qrp_alpha_max=0.50, correlated_error_rho=0.0),
        incentive=IncentiveConfig(novel_weight=10.0, replication_weight=1.0, effort_cost_per_sample=0.0),
        n_steps=20,
        seed=0,
    )


def _literature_summary(result) -> list[tuple]:
    """A hashable summary of standing literature contents, for exact comparison."""
    return [
        (f.hypothesis_id, f.agent_id, f.kind, f.is_true, f.timestep, f.context_id)
        for f in result.literature.standing
    ]


def test_mitigations_none_equals_empty_list():
    """``mitigations=None`` and ``mitigations=[]`` must give bit-identical results."""
    cfg = _common_cfg()
    result_none = run(cfg, mitigations=None)
    result_empty = run(cfg, mitigations=[])

    assert result_none.history == result_empty.history
    assert _literature_summary(result_none) == _literature_summary(result_empty)


def test_no_mitigation_is_identity():
    """``[NoMitigation()]`` must produce the same standing literature and history
    as no mitigations — the gating chain with one pass-through must vanish."""
    cfg = _common_cfg()
    result_baseline = run(cfg, mitigations=None)
    result_identity = run(cfg, mitigations=[NoMitigation()])

    assert result_baseline.history == result_identity.history
    assert _literature_summary(result_baseline) == _literature_summary(result_identity)


def test_chained_no_mitigations_is_still_identity():
    """Multiple ``NoMitigation``s in sequence must still preserve baseline behavior."""
    cfg = _common_cfg()
    result_baseline = run(cfg, mitigations=None)
    result_chain = run(cfg, mitigations=[NoMitigation(), NoMitigation(), NoMitigation()])

    assert result_baseline.history == result_chain.history
    assert _literature_summary(result_baseline) == _literature_summary(result_chain)


def test_no_mitigation_satisfies_mitigation_protocol():
    """``NoMitigation`` must structurally satisfy the ``Mitigation`` protocol."""
    assert isinstance(NoMitigation(), Mitigation)
