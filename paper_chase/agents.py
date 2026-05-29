"""Parametric agents (Phase 0): fixed traits drawn from a distribution.

Heterogeneity is load-bearing: it gives selection a substrate later, and it
prevents degenerate dynamics now. Each agent draws:
  - baseline_qrp: propensity to p-hack ("rigor trait")
  - effort: sample size used per study
  - p_replicate: probability of replicating an existing standing claim vs. novel

The effective QRP per study is the baseline trait modulated by the current
incentive pressure (novel:replication reward ratio). This modulation means that
sweeping the incentive structure can generate behavioral effects, enabling a
crisis to emerge. This is the minimum mechanism needed for the validity
gate to be a meaningful test.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

from .config import AgentConfig, IncentiveConfig
from .literature import Literature
from .world import World


@dataclass(frozen=True)
class Action:
    target_id: int
    kind: str                            # "novel" or "replication"
    sample_size: int
    qrp_intensity: float
    # For "replication" actions, the agent_id of the author of the specific
    # standing Finding being replicated — used by the loop to dispatch
    # credit-to-original-author when replication succeeds (Phase 1 mitigation-2
    # variant; see IncentiveConfig.replication_credit_to_original_author).
    original_author_id: int | None = None
    # The measurement context this study is run in. The correlated-error shared
    # shock keys on (hypothesis_id, context_id), so two studies sharing a context
    # share their shock; studies in different contexts get independent shocks.
    # Phase 0/1.A: all actions use context_id = 0 (single context). Phase 1.C's
    # invariance mitigation will vary it per study.
    context_id: int = 0


@dataclass(frozen=True)
class AgentTraits:
    baseline_qrp: float
    effort: int
    p_replicate: float


class ParametricAgent:
    """A research lab with fixed traits. Does not learn."""

    def __init__(self, agent_id: int, traits: AgentTraits) -> None:
        self.id = agent_id
        self.traits = traits
        self.cumulative_payoff: float = 0.0

    def choose_action(
        self,
        world: World,
        literature: Literature,
        incentive: IncentiveConfig,
        rng: np.random.Generator,
    ) -> Action:
        # Replicate or do novel work?
        standing = literature.standing
        do_replication = (
            rng.random() < self.traits.p_replicate and len(standing) > 0
        )
        if do_replication:
            kind = "replication"
            # Pick a SPECIFIC standing Finding to replicate (not just a
            # hypothesis_id). The Finding's author_id is needed by the loop to
            # dispatch credit-for-replication when this study succeeds.
            target_finding = standing[int(rng.integers(0, len(standing)))]
            target_id = target_finding.hypothesis_id
            original_author_id: int | None = target_finding.agent_id
        else:
            kind = "novel"
            target_id = int(rng.integers(0, world.n_hypotheses))
            original_author_id = None

        # Effective QRP modulated by incentive pressure.
        # pressure_factor ∈ (0, 1): how much the system rewards novel positives
        # relative to replications. When novel_weight >> replication_weight, pressure ≈ 1.
        #
        # PHASE 1 TODO: when `replication_credit_to_original_author > 0`, expected
        # back-end credit on novel positives should reduce the effective QRP
        # pressure (because QRP-driven false positives forfeit replication credit
        # in expectation). Currently NOT wired — credit dispatch works, but the
        # deterrence behavior won't appear until this calculation is updated.
        total = incentive.novel_weight + incentive.replication_weight
        pressure = incentive.novel_weight / total if total > 0 else 0.0
        effective_qrp = float(np.clip(self.traits.baseline_qrp * pressure, 0.0, 1.0))

        return Action(
            target_id=target_id,
            kind=kind,
            sample_size=self.traits.effort,
            qrp_intensity=effective_qrp,
            original_author_id=original_author_id,
        )

    def receive_reward(self, reward: float) -> None:
        self.cumulative_payoff += reward


def make_agents(cfg: AgentConfig, rng: np.random.Generator) -> list[ParametricAgent]:
    """Construct a heterogeneous population — each agent's traits drawn from the configured distributions."""
    agents: list[ParametricAgent] = []
    for i in range(cfg.n_agents):
        qrp = float(np.clip(rng.normal(cfg.qrp_mean, cfg.qrp_sd), 0.0, 1.0))
        effort = int(max(2, round(rng.normal(cfg.effort_mean, cfg.effort_sd))))
        traits = AgentTraits(baseline_qrp=qrp, effort=effort, p_replicate=cfg.p_replicate)
        agents.append(ParametricAgent(agent_id=i, traits=traits))
    return agents
