"""The core simulation loop.

One step = every agent picks an action, runs a study, possibly publishes.

(current) Phase 0 baseline: 
no mitigations, no correlated errors, no selection, parametric agents only.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

from .config import SimConfig
from .world import World
from .agents import make_agents, ParametricAgent
from .study import run_study
from .literature import Literature, Finding
from .incentives import compute_reward
from .metrics import summary


@dataclass
class SimResult:
    history: list[dict]                  # snapshots: step, n_standing, truth_content, discovery_rate, ...
    literature: Literature
    world: World
    agents: list[ParametricAgent]
    cfg: SimConfig


def run(cfg: SimConfig) -> SimResult:
    """Run the simulation and return the result.

    The single source of randomness used by the loop is seeded by `cfg.seed`.
    `cfg.world.seed` independently seeds the ground-truth world (so you can
    re-use a world across sim seeds, or vary either independently).
    """
    rng = np.random.default_rng(cfg.seed)
    world = World(cfg.world)
    agents = make_agents(cfg.agent, rng)
    literature = Literature()
    history: list[dict] = []

    # Per-(hypothesis, context) shared error shock. Drawn once when the (h, ctx)
    # pair is first studied, then reused for the rest of the run. Models "the
    # shared substrate has the same blind spot every time it sees this hypothesis
    # in this setup." Only populated when ρ > 0, to preserve exact RNG sequencing
    # against the Phase-0 baseline.
    shocks: dict[tuple[int, int], float] = {}
    use_shocks = cfg.study.correlated_error_rho > 0.0

    for t in range(cfg.n_steps):
        for agent in agents:
            action = agent.choose_action(world, literature, cfg.incentive, rng)
            hypothesis = world[action.target_id]

            if use_shocks:
                key = (action.target_id, action.context_id)
                if key not in shocks:
                    shocks[key] = float(rng.standard_normal())
                shared_shock = shocks[key]
            else:
                shared_shock = 0.0

            significant, observed_effect = run_study(
                hypothesis=hypothesis,
                sample_size=action.sample_size,
                qrp_intensity=action.qrp_intensity,
                study_cfg=cfg.study,
                rng=rng,
                shared_shock=shared_shock,
            )
            reward = compute_reward(action.kind, significant, action.sample_size, cfg.incentive)
            agent.receive_reward(reward)

            # Phase-1 mitigation-2 variant: credit the original author when a
            # replication succeeds. No-op when the credit is 0 (Phase-0 default).
            # Agents are indexed by their `id`, which equals their list position
            # (see `make_agents`), so the lookup is O(1).
            if (
                significant
                and action.kind == "replication"
                and action.original_author_id is not None
                and cfg.incentive.replication_credit_to_original_author > 0.0
            ):
                agents[action.original_author_id].receive_reward(
                    cfg.incentive.replication_credit_to_original_author
                )

            if significant:
                literature.add(
                    Finding(
                        hypothesis_id=action.target_id,
                        agent_id=agent.id,
                        kind=action.kind,
                        observed_effect=observed_effect,
                        sample_size=action.sample_size,
                        is_true=hypothesis.is_true,
                        timestep=t,
                        context_id=action.context_id,
                    )
                )

        if t % cfg.snapshot_every == 0 or t == cfg.n_steps - 1:
            history.append(summary(literature, world, t))

    return SimResult(history=history, literature=literature, world=world, agents=agents, cfg=cfg)
