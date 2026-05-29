"""Pre-registration mitigation.

Models pre-registration of hypotheses and analysis plans: when a study is
pre-registered, the analysis is locked in before data collection, so the
opportunities for QRP (optional stopping, selective reporting, garden of
forking paths) are eliminated at source. The mitigation enforces this by
capping ``qrp_intensity`` on every action.

Default ``qrp_cap = 0.0`` models full pre-registration — analysis locked
before data, no QRP possible. ``qrp_cap`` in ``(0, 1)`` models partial-
pre-registration regimes where some analytic flexibility survives (e.g.,
exploratory follow-ups on pre-registered confirmatory tests).

For Phase 1, coverage is binary — every study is pre-registered (whichever
agent ran it). Fractional coverage (e.g., "half the studies are pre-registered
and half aren't") is a refinement worth exploring later — modelling adoption
dynamics — but not in Phase 1.
"""
from __future__ import annotations
from dataclasses import replace

import numpy as np

from ..agents import Action, ParametricAgent
from ..config import SimConfig
from ..literature import Finding, Literature
from ..world import World
from .base import StudyResult


class PreRegistration:
    """Cap ``qrp_intensity`` of every action at ``qrp_cap``.

    Parameters
    ----------
    qrp_cap
        Maximum allowed effective QRP intensity. Default ``0.0`` corresponds to
        full pre-registration (analysis locked before data). Values in ``(0, 1)``
        model partial-pre-registration regimes.
    """

    def __init__(self, qrp_cap: float = 0.0) -> None:
        if not 0.0 <= qrp_cap <= 1.0:
            raise ValueError(f"qrp_cap must be in [0, 1], got {qrp_cap}")
        self.qrp_cap = qrp_cap

    def constrain_action(
        self,
        action: Action,
        rng: np.random.Generator,
    ) -> Action:
        """Cap ``qrp_intensity`` at ``qrp_cap``; pass through if already below."""
        return replace(
            action,
            qrp_intensity=min(action.qrp_intensity, self.qrp_cap),
        )

    def gate_publish(
        self,
        result: StudyResult,
        finding: Finding,
        literature: Literature,
        rng: np.random.Generator,
    ) -> Finding | None:
        # Pre-registration acts at action time; the publish gate is pass-through.
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
