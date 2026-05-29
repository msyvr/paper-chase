"""The ``Mitigation`` protocol + the identity ``NoMitigation``.

A mitigation hooks into three well-defined points in the simulation loop:

  * ``constrain_action`` — applied in order before each study runs; can modify
    the agent's chosen Action (e.g., pre-reg clamps ``qrp_intensity``).
  * ``gate_publish`` — applied in order after each study; receives a candidate
    Finding (built from the study result) and returns either it (publish),
    a modified version (publish-modified), or ``None`` (suppress). Once any
    mitigation in the chain returns ``None``, the publication is suppressed.
  * ``post_step`` — independent end-of-step hook; runs once per mitigation per
    step. Used for replication scans, retractions, reputation updates.

State is allowed: a mitigation may accumulate evidence across calls
(e.g., invariance counting how many distinct contexts have produced
significance on a given hypothesis). Instances are constructed once per
simulation run and persist for its duration.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np

from ..agents import Action, ParametricAgent
from ..config import SimConfig
from ..literature import Finding, Literature
from ..world import Hypothesis, World


@dataclass(frozen=True)
class StudyResult:
    """The raw study outcome handed to mitigations alongside the candidate Finding.

    The simulation loop builds this for every study (significant or not). It
    carries everything a mitigation might want without re-deriving it: the
    action that produced the study, the significance flag, the observed effect
    estimate, the ground-truth hypothesis (mitigations are allowed to peek;
    they're part of the apparatus, not the agents), the agent who ran it, and
    the step at which it happened.
    """

    action: Action
    significant: bool
    observed_effect: float
    hypothesis: Hypothesis
    agent_id: int
    timestep: int


@runtime_checkable
class Mitigation(Protocol):
    """Structural type for a publication-process intervention."""

    def constrain_action(
        self,
        action: Action,
        rng: np.random.Generator,
    ) -> Action: ...

    def gate_publish(
        self,
        result: StudyResult,
        finding: Finding,
        literature: Literature,
        rng: np.random.Generator,
    ) -> Finding | None: ...

    def post_step(
        self,
        t: int,
        cfg: SimConfig,
        shocks: dict[tuple[int, int], float],
        literature: Literature,
        world: World,
        agents: list[ParametricAgent],
        rng: np.random.Generator,
    ) -> None: ...


class NoMitigation:
    """Identity mitigation: every hook is a no-op.

    Useful as a placeholder, a baseline in mitigation-comparison sweeps, and a
    sanity check that the mitigation plumbing doesn't drift the Phase-0 baseline
    (see ``tests/test_mitigations.py``).
    """

    def constrain_action(
        self,
        action: Action,
        rng: np.random.Generator,
    ) -> Action:
        return action

    def gate_publish(
        self,
        result: StudyResult,
        finding: Finding,
        literature: Literature,
        rng: np.random.Generator,
    ) -> Finding | None:
        return finding

    def post_step(
        self,
        t: int,
        cfg: SimConfig,
        shocks: dict[tuple[int, int], float],
        literature: Literature,
        world: World,
        agents: list[ParametricAgent],
        rng: np.random.Generator,
    ) -> None:
        return None
