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

Replication + retraction and QRP-deterrence wiring (Stage 1.B-replication):
5. ``ReplicationAndRetraction`` validates its parameters and retracts FPs at high
   ``audit_fraction`` (and preserves TPs of high power).
6. ``replication_credit_to_original_author > 0`` lowers the effective QRP
   intensity at action-time (the credit-for-replication deterrence wiring).
"""
import numpy as np
import pytest

from paper_chase.agents import Action, AgentTraits, ParametricAgent
from paper_chase.config import (
    SimConfig, IncentiveConfig, AgentConfig, WorldConfig, StudyConfig,
)
from paper_chase.literature import Literature
from paper_chase.simulation import run
from paper_chase.mitigations import (
    InvarianceRequirement,
    Mitigation,
    NoMitigation,
    PreRegistration,
    ReplicationAndRetraction,
)
from paper_chase.world import World


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


# ---- replication + retraction ----

def test_replication_retraction_parameters_validated():
    """Parameter validation: audit_fraction ∈ [0, 1], qrp ∈ [0, 1], sample_size >= 2 (or None)."""
    with pytest.raises(ValueError):
        ReplicationAndRetraction(audit_fraction=-0.1)
    with pytest.raises(ValueError):
        ReplicationAndRetraction(audit_fraction=1.1)
    with pytest.raises(ValueError):
        ReplicationAndRetraction(audit_qrp_intensity=-0.1)
    with pytest.raises(ValueError):
        ReplicationAndRetraction(audit_qrp_intensity=1.1)
    with pytest.raises(ValueError):
        ReplicationAndRetraction(audit_sample_size=1)


def test_replication_retraction_zero_fraction_changes_nothing():
    """With ``audit_fraction=0``, no audits run and the standing literature
    matches the no-mitigation run exactly (no rng draws from this mitigation)."""
    cfg = _common_cfg()
    result_baseline = run(cfg, mitigations=None)
    result_zero = run(cfg, mitigations=[ReplicationAndRetraction(audit_fraction=0.0)])
    assert _literature_summary(result_baseline) == _literature_summary(result_zero)


def test_replication_retraction_removes_false_positives():
    """With ``audit_fraction=1.0`` and a pristine high-power audit, false positives
    in the literature are retracted by their audit replications returning non-
    significant. With all hypotheses null, every published finding is a FP."""
    cfg = SimConfig(
        world=WorldConfig(n_hypotheses=200, base_rate_true=0.0, seed=0),
        agent=AgentConfig(
            n_agents=20, qrp_mean=0.6, qrp_sd=0.0,
            effort_mean=30.0, effort_sd=0.0, p_replicate=0.0,
        ),
        incentive=IncentiveConfig(
            novel_weight=50.0, replication_weight=1.0, effort_cost_per_sample=0.0,
        ),
        n_steps=20,
        seed=0,
    )
    result_baseline = run(cfg, mitigations=None)
    result_with_audit = run(
        cfg,
        mitigations=[ReplicationAndRetraction(
            audit_fraction=1.0, audit_sample_size=100, audit_qrp_intensity=0.0,
        )],
    )

    n_baseline = len(result_baseline.literature.standing)
    n_audited_standing = len(result_with_audit.literature.standing)
    n_audited_retracted = len(result_with_audit.literature.retracted)

    # With α=0.05 audits each step, FPs survive at ~5% per audit round → essentially
    # all of the baseline's FPs end up retracted. Assert a 3× reduction with margin.
    assert n_audited_standing * 3 < n_baseline, (
        f"audit should drastically reduce FP count; "
        f"got baseline={n_baseline}, audited standing={n_audited_standing}"
    )
    assert n_audited_retracted > 0, "some retractions must have occurred"


def test_replication_retraction_preserves_strong_true_positives():
    """High-power audits (n=100) of strong true effects (d=0.8) virtually never
    retract — power is essentially 1, so audit replications are significant."""
    cfg = SimConfig(
        world=WorldConfig(
            n_hypotheses=100, base_rate_true=1.0,
            effect_size_mean=0.8, effect_size_sd=0.0, seed=0,
        ),
        agent=AgentConfig(
            n_agents=10, qrp_mean=0.0, qrp_sd=0.0,
            effort_mean=100.0, effort_sd=0.0, p_replicate=0.0,
        ),
        incentive=IncentiveConfig(
            novel_weight=10.0, replication_weight=1.0, effort_cost_per_sample=0.0,
        ),
        n_steps=20,
        seed=0,
    )
    result = run(
        cfg,
        mitigations=[ReplicationAndRetraction(
            audit_fraction=1.0, audit_sample_size=100, audit_qrp_intensity=0.0,
        )],
    )
    n_standing = len(result.literature.standing)
    n_retracted = len(result.literature.retracted)
    # Effectively all of the standing literature was once a TP. Retractions
    # should be tiny relative to standing.
    assert n_retracted < max(1, n_standing // 10), (
        f"strong TPs should mostly survive audit; "
        f"got standing={n_standing}, retracted={n_retracted}"
    )


# ---- QRP-deterrence wiring (credit-for-replication) ----

def test_credit_for_replication_reduces_effective_qrp():
    """With ``replication_credit_to_original_author > 0``, the agent's
    effective_qrp at action-time drops vs. credit = 0 (same baseline trait,
    same RNG seed)."""
    traits = AgentTraits(baseline_qrp=0.5, effort=30, p_replicate=0.0)
    agent = ParametricAgent(agent_id=0, traits=traits)
    world = World(WorldConfig(n_hypotheses=10, base_rate_true=0.5, seed=0))
    lit = Literature()

    incentive_no_credit = IncentiveConfig(
        novel_weight=10.0, replication_weight=1.0, effort_cost_per_sample=0.0,
        replication_credit_to_original_author=0.0,
    )
    incentive_with_credit = IncentiveConfig(
        novel_weight=10.0, replication_weight=1.0, effort_cost_per_sample=0.0,
        replication_credit_to_original_author=15.0,
    )

    rng1 = np.random.default_rng(0)
    action_no_credit = agent.choose_action(world, lit, incentive_no_credit, rng1)

    rng2 = np.random.default_rng(0)
    action_with_credit = agent.choose_action(world, lit, incentive_with_credit, rng2)

    assert action_with_credit.qrp_intensity < action_no_credit.qrp_intensity, (
        f"credit-for-replication should deter QRP; "
        f"got with={action_with_credit.qrp_intensity}, without={action_no_credit.qrp_intensity}"
    )


def test_credit_for_replication_zero_credit_preserves_baseline_qrp_formula():
    """With ``replication_credit_to_original_author = 0`` (default), the QRP
    pressure formula reduces exactly to the no-deterrence form: pressure =
    novel_weight / (novel + replication)."""
    traits = AgentTraits(baseline_qrp=0.5, effort=30, p_replicate=0.0)
    agent = ParametricAgent(agent_id=0, traits=traits)
    world = World(WorldConfig(n_hypotheses=10, base_rate_true=0.5, seed=0))
    lit = Literature()

    incentive = IncentiveConfig(
        novel_weight=10.0, replication_weight=1.0, effort_cost_per_sample=0.0,
        replication_credit_to_original_author=0.0,
    )
    rng = np.random.default_rng(0)
    action = agent.choose_action(world, lit, incentive, rng)

    # Expected: baseline_qrp * novel / (novel + repl) = 0.5 * 10/11
    expected_pressure = 10.0 / 11.0
    expected_qrp = 0.5 * expected_pressure
    assert action.qrp_intensity == pytest.approx(expected_qrp), (
        f"with credit=0, formula must reduce to baseline; "
        f"got {action.qrp_intensity}, expected {expected_qrp}"
    )


# ---- invariance requirement ----

def test_invariance_requirement_validates():
    """``k_contexts`` must be >= 1."""
    with pytest.raises(ValueError):
        InvarianceRequirement(k_contexts=0)
    with pytest.raises(ValueError):
        InvarianceRequirement(k_contexts=-1)


def test_world_config_n_contexts_validated():
    """``n_contexts`` on WorldConfig must be positive."""
    with pytest.raises(ValueError):
        WorldConfig(n_contexts=0)
    with pytest.raises(ValueError):
        WorldConfig(n_contexts=-1)


def test_invariance_k2_with_n_contexts_1_publishes_nothing():
    """With n_contexts=1 and k_contexts=2, publication is unachievable — no
    second context ever exists. Strong test of the gating mechanism."""
    cfg = SimConfig(
        world=WorldConfig(
            n_hypotheses=10, base_rate_true=1.0,
            effect_size_mean=0.8, effect_size_sd=0.0,
            n_contexts=1, seed=0,
        ),
        agent=AgentConfig(
            n_agents=20, qrp_mean=0.0, qrp_sd=0.0,
            effort_mean=100.0, effort_sd=0.0, p_replicate=0.0,
        ),
        incentive=IncentiveConfig(
            novel_weight=10.0, replication_weight=1.0, effort_cost_per_sample=0.0,
        ),
        n_steps=10,
        seed=0,
    )
    result = run(cfg, mitigations=[InvarianceRequirement(k_contexts=2)])
    assert len(result.literature.standing) == 0, (
        "k=2 should be unachievable when n_contexts=1; literature must be empty"
    )


def test_invariance_k1_admits_first_significant_finding():
    """``k_contexts=1`` is the trivial case — any significant finding publishes
    immediately, behaving like NoMitigation for gating purposes."""
    cfg = _common_cfg()
    result_baseline = run(cfg, mitigations=None)
    result_k1 = run(cfg, mitigations=[InvarianceRequirement(k_contexts=1)])
    # Same RNG sequence, same gate behavior → identical standing literature.
    assert _literature_summary(result_baseline) == _literature_summary(result_k1)


def test_invariance_reduces_publications_under_multiple_contexts():
    """With n_contexts=4 and k_contexts=2, the literature should hold fewer
    findings than the no-mitigation baseline (each finding now represents
    cross-context agreement rather than single-shot significance)."""
    cfg = SimConfig(
        world=WorldConfig(
            n_hypotheses=50, base_rate_true=0.3,
            effect_size_mean=0.4, effect_size_sd=0.1,
            n_contexts=4, seed=0,
        ),
        agent=AgentConfig(
            n_agents=20, qrp_mean=0.3, qrp_sd=0.0,
            effort_mean=30.0, effort_sd=0.0, p_replicate=0.0,
        ),
        incentive=IncentiveConfig(
            novel_weight=10.0, replication_weight=1.0, effort_cost_per_sample=0.0,
        ),
        n_steps=20,
        seed=0,
    )
    result_baseline = run(cfg, mitigations=None)
    result_invariance = run(cfg, mitigations=[InvarianceRequirement(k_contexts=2)])

    n_baseline = len(result_baseline.literature.standing)
    n_invariance = len(result_invariance.literature.standing)

    assert n_invariance < n_baseline, (
        f"invariance should reduce publications; got baseline={n_baseline}, "
        f"invariance={n_invariance}"
    )
    # And the literature must not be empty — k=2 is achievable with n_contexts=4.
    assert n_invariance > 0, "k=2 with n_contexts=4 should be reachable"
