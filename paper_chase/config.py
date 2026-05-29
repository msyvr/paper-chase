"""Configuration dataclasses

Configs are frozen and validated at construction. Split-by-concern
(World/Study/Agent/Incentive/Sim) to keep sweep design legible: 
each sweep varies one config's fields, holding the others fixed.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorldConfig:
    """The hypothesis pool (ground truth). Agents don't see this."""

    n_hypotheses: int = 1000
    # TODO sensitivity-check base_rate_true
    base_rate_true: float = 0.10        # fraction with a real effect (low, for realism)
    # TODO sensitivity-check effect_size_mean
    effect_size_mean: float = 0.4       # Cohen's-d-like; modest but findable
    effect_size_sd: float = 0.15
    # Number of distinct measurement contexts a study can be run in. When > 1,
    # each Action.context_id is drawn uniformly from range(n_contexts); when = 1,
    # context_id is fixed at 0 and the agent skips the rng draw (preserving RNG
    # sequencing against single-context baselines). The InvarianceRequirement
    # mitigation needs n_contexts >= k_contexts to be able to publish anything.
    n_contexts: int = 1
    seed: int = 0

    def __post_init__(self) -> None:
        if not 0.0 <= self.base_rate_true <= 1.0:
            raise ValueError(f"base_rate_true must be in [0, 1], got {self.base_rate_true}")
        if self.n_hypotheses <= 0:
            raise ValueError(f"n_hypotheses must be positive, got {self.n_hypotheses}")
        if self.effect_size_mean <= 0:
            raise ValueError(f"effect_size_mean must be positive, got {self.effect_size_mean}")
        if self.n_contexts <= 0:
            raise ValueError(f"n_contexts must be positive, got {self.n_contexts}")


@dataclass(frozen=True)
class StudyConfig:
    """Statistical engine: FPR, power, QRP inflation."""

    alpha: float = 0.05                  # per-study significance threshold (match IRL convention)
    # TODO sensitivity-check qrp_alpha_max; coin-flip value selected as not modeling outright fraud
    # justified by Simmons, Nelson & Simonsohn (2011), False-Positive Psychology result: 0.6 max
    qrp_alpha_max: float = 0.50          # ceiling on QRP-inflated false-positive rate
    # Strength of per-(hypothesis, context) systematic bias in the decision statistic.
    # The model is *additive*: each (h, ctx) draws a fixed bias b ~ N(0, bias_strength²)
    # once, then every study of that (h, ctx) sees the same b added to its noncentrality,
    # with a *fresh, unscaled* private noise term on top:
    #     Z = δ + bias + private,  bias ~ N(0, bias_strength²),  private ~ N(0, 1)
    # This is the right structure for "studies share a systematic bias but each has its
    # own independent sampling noise" — Var(private) does NOT depend on bias_strength.
    # (The previous formulation used a Gaussian-copula trick that traded private for
    # shared noise to keep total variance at 1; that's mathematically valid as a pure
    # correlation parameter but it artificially shrinks audit-replicate noise at high
    # ρ — same-base audits become near-deterministic, which doesn't reflect how
    # systematic bias actually works.)
    # bias_strength = 0 → independent errors (Phase-0 default; human-science baseline).
    # bias_strength ≈ 1 → per-(h,ctx) bias has the same scale as sampling noise.
    # bias_strength > 1 → bias dominates; systematic limitation drives most outcomes.
    bias_strength: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 < self.alpha < 1.0:
            raise ValueError(f"alpha must be in (0, 1), got {self.alpha}")
        if not self.alpha <= self.qrp_alpha_max < 1.0:
            raise ValueError(f"qrp_alpha_max must satisfy alpha <= qrp_alpha_max < 1, got {self.qrp_alpha_max}")
        if self.bias_strength < 0.0:
            raise ValueError(
                f"bias_strength must be >= 0, got {self.bias_strength}"
            )


@dataclass(frozen=True)
class AgentConfig:
    """Trait distributions for the parametric agent population (heterogeneous)."""

    n_agents: int = 50
    qrp_mean: float = 0.3                # baseline QRP-propensity distribution
    qrp_sd: float = 0.2
    effort_mean: float = 30.0            # sample-size distribution
    effort_sd: float = 10.0
    p_replicate: float = 0.10            # baseline replication propensity

    def __post_init__(self) -> None:
        if self.n_agents <= 0:
            raise ValueError(f"n_agents must be positive, got {self.n_agents}")
        if not 0.0 <= self.qrp_mean <= 1.0:
            raise ValueError(f"qrp_mean must be in [0, 1], got {self.qrp_mean}")
        if not 0.0 <= self.p_replicate <= 1.0:
            raise ValueError(f"p_replicate must be in [0, 1], got {self.p_replicate}")
        if self.effort_mean < 2:
            raise ValueError(f"effort_mean must be >= 2, got {self.effort_mean}")


@dataclass(frozen=True)
class IncentiveConfig:
    """The reward structure — the engine driving QRP responsiveness."""

    novel_weight: float = 10.0           # reward for a positive novel publication
    replication_weight: float = 1.0      # reward for a successful replication (paid to the replicator)
    effort_cost_per_sample: float = 0.02            # per-unit-sample cost: models cost associated with a study
    # Phase-1 mitigation-2 variant: credit paid to the ORIGINAL author of a finding
    # when someone else successfully replicates it. Default 0 → Phase-0 unchanged.
    # NOTE: the credit dispatch is wired in `simulation.run`, but the agent's
    # QRP-pressure response in `ParametricAgent.choose_action` does NOT yet factor
    # expected back-end credit, so setting this > 0 in Phase 0 just pays out, it
    # does not deter QRP. The deterrence wiring lands in Phase 1.
    replication_credit_to_original_author: float = 0.0

    def __post_init__(self) -> None:
        if self.novel_weight < 0 or self.replication_weight < 0 or self.effort_cost_per_sample < 0:
            raise ValueError("reward weights and effort cost must be non-negative")
        if self.replication_credit_to_original_author < 0:
            raise ValueError("replication_credit_to_original_author must be non-negative")


@dataclass(frozen=True)
class SimConfig:
    """Top-level simulation config — composed of the per-concern configs."""

    world: WorldConfig = field(default_factory=WorldConfig)
    study: StudyConfig = field(default_factory=StudyConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    incentive: IncentiveConfig = field(default_factory=IncentiveConfig)
    n_steps: int = 500
    seed: int = 0
    snapshot_every: int = 1              # record summary every N steps (default 1 = full resolution)

    def __post_init__(self) -> None:
        if self.n_steps <= 0:
            raise ValueError(f"n_steps must be positive, got {self.n_steps}")
        if self.snapshot_every <= 0:
            raise ValueError(f"snapshot_every must be positive, got {self.snapshot_every}")
