"""The core simulation loop.

One step = every agent picks an action, runs a study, possibly publishes.
Mitigations (if any) hook in at three points per step:
  - constrain_action   before the study runs,
  - gate_publish       to suppress or modify the candidate Finding,
  - post_step          for end-of-step replication scans, retractions, etc.

With ``mitigations=None`` (or ``[]``), behavior is identical to the Phase-0
baseline: no mitigations, no correlated errors at ρ=0, no selection, parametric
agents only.
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
from .mitigations import Mitigation, StudyResult


@dataclass
class SimResult:
    history: list[dict]                  # snapshots: step, n_standing, truth_content, discovery_rate, ...
    literature: Literature
    world: World
    agents: list[ParametricAgent]
    cfg: SimConfig


def run(cfg: SimConfig, mitigations: list[Mitigation] | None = None) -> SimResult:
    """Run the simulation and return the result.

    The single source of randomness used by the loop is seeded by `cfg.seed`.
    `cfg.world.seed` independently seeds the ground-truth world (so you can
    re-use a world across sim seeds, or vary either independently).

    Mitigations, if provided, hook in via ``constrain_action``, ``gate_publish``,
    and ``post_step`` (see ``paper_chase.mitigations``). With ``mitigations``
    None or empty, behavior is identical to the Phase-0 baseline.
    """
    rng = np.random.default_rng(cfg.seed)
    world = World(cfg.world)
    agents = make_agents(cfg.agent, rng)
    literature = Literature()
    history: list[dict] = []
    mit_list: list[Mitigation] = list(mitigations) if mitigations else []

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

            # Mitigation hook 1: constrain the action before it executes.
            for m in mit_list:
                action = m.constrain_action(action, rng)

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

            # Mitigation hook 2: gate the publication.
            # Only significant studies produce candidate Findings; mitigations
            # may suppress (return None) or modify the Finding as it flows
            # through the chain.
            if significant:
                candidate: Finding | None = Finding(
                    hypothesis_id=action.target_id,
                    agent_id=agent.id,
                    kind=action.kind,
                    observed_effect=observed_effect,
                    sample_size=action.sample_size,
                    is_true=hypothesis.is_true,
                    timestep=t,
                    context_id=action.context_id,
                )
                if mit_list:
                    result = StudyResult(
                        action=action,
                        significant=significant,
                        observed_effect=observed_effect,
                        hypothesis=hypothesis,
                        agent_id=agent.id,
                        timestep=t,
                    )
                    for m in mit_list:
                        candidate = m.gate_publish(result, candidate, literature, rng)
                        if candidate is None:
                            break
                if candidate is not None:
                    literature.add(candidate)

        # Mitigation hook 3: end-of-step bookkeeping (replications, retractions).
        # Pass the full SimConfig and the shared-shock dict; mitigations that run
        # their own audit studies need both (cfg.study for run_study; shocks to
        # honor the same-(hypothesis, context) shared shock when ρ > 0).
        for m in mit_list:
            m.post_step(t, cfg, shocks, literature, world, agents, rng)

        if t % cfg.snapshot_every == 0 or t == cfg.n_steps - 1:
            history.append(summary(literature, world, t))

    return SimResult(history=history, literature=literature, world=world, agents=agents, cfg=cfg)
