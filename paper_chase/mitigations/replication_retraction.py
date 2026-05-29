"""Replication-and-retraction mitigation.

Models post-publication scrutiny: each step, sample a fraction of standing
findings, run a fresh study on each, and retract any whose audit replication
is non-significant. The audit study uses the SAME shared error shock as the
original (per (hypothesis, context) from the sim's ``shocks`` dict) — modelling
"audit by the same base model." This is the realistic baseline; cross-model
audits (audit using a different base model → independent shock) is a planned
variant.

This is the "+retraction" side of "incentivized replication + retraction." The
"incentivized" side lives in :class:`IncentiveConfig` (raise ``replication_weight``
to reward agent-driven replications more, set
``replication_credit_to_original_author > 0`` to pay original authors when their
work successfully replicates — the latter now also deters QRP at the source via
:meth:`ParametricAgent.choose_action`).
"""
from __future__ import annotations

import numpy as np

from ..agents import Action, ParametricAgent
from ..config import SimConfig
from ..literature import Finding, Literature
from ..study import run_study
from ..world import World
from .base import StudyResult


class ReplicationAndRetraction:
    """Periodically audit standing literature via independent replication; retract failures.

    Parameters
    ----------
    audit_fraction
        Fraction of currently-standing findings to audit per step. ``0.0`` =
        never audit (no retractions); ``1.0`` = audit every standing finding
        every step. Realistic values are small (real fields audit a tiny slice
        per period).
    audit_sample_size
        Sample size for audit replications. ``None`` (default) reuses the
        original finding's sample size — a fair re-test at the same effort.
        Override (e.g., to a larger value) to model audits-with-more-power.
    audit_qrp_intensity
        QRP intensity for audit studies. ``0.0`` (default) = pristine audit
        (the auditor doesn't p-hack). Values > 0 model audits that themselves
        have some methodological flexibility.
    """

    def __init__(
        self,
        audit_fraction: float = 0.1,
        audit_sample_size: int | None = None,
        audit_qrp_intensity: float = 0.0,
    ) -> None:
        if not 0.0 <= audit_fraction <= 1.0:
            raise ValueError(f"audit_fraction must be in [0, 1], got {audit_fraction}")
        if not 0.0 <= audit_qrp_intensity <= 1.0:
            raise ValueError(f"audit_qrp_intensity must be in [0, 1], got {audit_qrp_intensity}")
        if audit_sample_size is not None and audit_sample_size < 2:
            raise ValueError(f"audit_sample_size must be >= 2 or None, got {audit_sample_size}")
        self.audit_fraction = audit_fraction
        self.audit_sample_size = audit_sample_size
        self.audit_qrp_intensity = audit_qrp_intensity

    def constrain_action(
        self,
        action: Action,
        rng: np.random.Generator,
    ) -> Action:
        # No action-time effect; the audit lives entirely in post_step.
        return action

    def gate_publish(
        self,
        result: StudyResult,
        finding: Finding,
        literature: Literature,
        rng: np.random.Generator,
    ) -> Finding | None:
        # No publish-time gate; we audit downstream.
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
        standing = list(literature.standing)
        n_to_audit = int(len(standing) * self.audit_fraction)
        if n_to_audit == 0:
            return

        # Sample without replacement.
        indices = rng.choice(len(standing), size=n_to_audit, replace=False)

        for idx in indices:
            target = standing[int(idx)]
            hypothesis = world[target.hypothesis_id]
            sample_size = (
                self.audit_sample_size
                if self.audit_sample_size is not None
                else target.sample_size
            )
            # Same-base-model audit: reuse the shared shock the original saw.
            # If ρ = 0 (shocks dict empty) the lookup falls back to 0, which is
            # the correct neutral value for independent-error studies.
            shared_shock = shocks.get((target.hypothesis_id, target.context_id), 0.0)

            significant, _ = run_study(
                hypothesis=hypothesis,
                sample_size=sample_size,
                qrp_intensity=self.audit_qrp_intensity,
                study_cfg=cfg.study,
                rng=rng,
                shared_shock=shared_shock,
            )

            if not significant:
                literature.retract(target)
