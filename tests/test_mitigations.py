"""Mitigation tests.

Scaffold invariants:
1. The plumbing must not drift the Phase-0 baseline when no mitigations are
   active (``mitigations=None`` or ``mitigations=[]``).
2. The identity mitigation ``NoMitigation`` must give bit-identical results
   to the no-mitigations case — the publish-gating chain with one pass-through
   link should be indistinguishable from no chain at all.

Pre-registration (Stage 1.B-prereg):
3. ``PreRegistration`` clamps ``qrp_intensity`` at ``qrp_cap`` and preserves all
   other Action fields.
4. Under full pre-registration (qrp_cap=0), the literature's false-positive
   count collapses toward the no-QRP baseline (FPR ≈ α) even when agents have
   high baseline QRP traits and incentive pressure is high.
"""
import numpy as np
import pytest

from paper_chase.agents import Action
from paper_chase.config import (
    SimConfig, IncentiveConfig, AgentConfig, WorldConfig, StudyConfig,
)
from paper_chase.simulation import run
from paper_chase.mitigations import Mitigation, NoMitigation, PreRegistration


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


# ---- pre-registration ----

def test_pre_registration_qrp_cap_validated():
    """``qrp_cap`` must be in [0, 1]."""
    with pytest.raises(ValueError):
        PreRegistration(qrp_cap=-0.1)
    with pytest.raises(ValueError):
        PreRegistration(qrp_cap=1.1)


def test_pre_registration_caps_high_qrp():
    """High ``qrp_intensity`` gets clamped to ``qrp_cap``."""
    pre_reg = PreRegistration(qrp_cap=0.0)
    action = Action(target_id=0, kind="novel", sample_size=30, qrp_intensity=0.9)
    out = pre_reg.constrain_action(action, np.random.default_rng(0))
    assert out.qrp_intensity == 0.0


def test_pre_registration_leaves_low_qrp_alone():
    """``qrp_intensity`` already below the cap passes through unchanged."""
    pre_reg = PreRegistration(qrp_cap=0.3)
    action = Action(target_id=0, kind="novel", sample_size=30, qrp_intensity=0.1)
    out = pre_reg.constrain_action(action, np.random.default_rng(0))
    assert out.qrp_intensity == pytest.approx(0.1)


def test_pre_registration_preserves_other_action_fields():
    """Only ``qrp_intensity`` is changed; everything else is preserved."""
    pre_reg = PreRegistration(qrp_cap=0.0)
    action = Action(
        target_id=42, kind="replication", sample_size=50, qrp_intensity=0.8,
        original_author_id=7, context_id=2,
    )
    out = pre_reg.constrain_action(action, np.random.default_rng(0))
    assert out.target_id == 42
    assert out.kind == "replication"
    assert out.sample_size == 50
    assert out.original_author_id == 7
    assert out.context_id == 2


def test_pre_registration_collapses_fpr_under_pressure():
    """Under full pre-registration the literature's false-positive count collapses.

    Setup: all hypotheses are null (``base_rate_true=0``), agents have high
    baseline QRP, and incentive pressure is high — so every published Finding
    is a false positive and the baseline's α_eff is heavily inflated by QRP.
    With pre-registration (qrp_cap=0), α_eff ≈ α and the publication count
    drops by ~5–10× in this setup. We assert a 3× reduction with margin.
    """
    cfg = SimConfig(
        world=WorldConfig(n_hypotheses=200, base_rate_true=0.0, seed=0),
        agent=AgentConfig(
            n_agents=20, qrp_mean=0.8, qrp_sd=0.0,
            effort_mean=30.0, effort_sd=0.0, p_replicate=0.0,
        ),
        incentive=IncentiveConfig(
            novel_weight=50.0, replication_weight=1.0, effort_cost_per_sample=0.0,
        ),
        n_steps=20,
        seed=0,
    )

    result_baseline = run(cfg, mitigations=None)
    result_prereg = run(cfg, mitigations=[PreRegistration(qrp_cap=0.0)])

    n_baseline = len(result_baseline.literature.standing)
    n_prereg = len(result_prereg.literature.standing)

    assert n_prereg * 3 < n_baseline, (
        f"pre-registration should drastically reduce FPs; "
        f"got baseline={n_baseline}, prereg={n_prereg}"
    )
