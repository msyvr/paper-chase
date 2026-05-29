"""Invariance-requirement mitigation.

Publication requires significance across ``k_contexts`` distinct contexts before
the field accepts a finding. Models *a discovery only counts if it travels* —
results that hold in only one setup may be context-specific artifacts, or
correlated-error blind spots (if ρ > 0). The headline result the project is
designed to test: under correlated errors, *invariance* dominates *replication*
because cross-context agreement breaks the shared shock, while same-context
replication just re-confirms it.

Mechanic: significant findings are buffered (suppressed at ``gate_publish``)
until ``k_contexts`` distinct ``context_id`` values have produced significance
on a given hypothesis. Once the threshold is reached, the most recent finding
is released to the literature. Subsequent significant findings on already-
published hypotheses pass through (they're confirmations, not new discoveries).

Requires :attr:`WorldConfig.n_contexts` ≥ ``k_contexts`` to be able to publish
anything. The default ``k_contexts=2`` is the minimum nontrivial requirement.
"""
from __future__ import annotations
from collections import defaultdict

import numpy as np

from ..agents import Action, ParametricAgent
from ..config import SimConfig
from ..literature import Finding, Literature
from ..world import World
from .base import StudyResult


class InvarianceRequirement:
    """Buffer significant findings until ``k_contexts`` distinct contexts agree.

    Parameters
    ----------
    k_contexts
        Number of distinct contexts that must each have produced a significant
        finding on a hypothesis before that hypothesis is admitted to the
        literature. Default 2 (minimum nontrivial). Requires
        ``WorldConfig.n_contexts >= k_contexts``; otherwise publication is
        unachievable and the literature stays empty.
    """

    def __init__(self, k_contexts: int = 2) -> None:
        if k_contexts < 1:
            raise ValueError(f"k_contexts must be >= 1, got {k_contexts}")
        self.k_contexts = k_contexts
        # Per-hypothesis evidence buffer: hypothesis_id -> set of contexts that
        # have produced significance on it so far. Cleared on publication.
        self._pending_evidence: dict[int, set[int]] = defaultdict(set)

    def constrain_action(
        self,
        action: Action,
        rng: np.random.Generator,
    ) -> Action:
        # No action-time intervention.
        return action

    def gate_publish(
        self,
        result: StudyResult,
        finding: Finding,
        literature: Literature,
        rng: np.random.Generator,
    ) -> Finding | None:
        h_id = result.action.target_id

        # Subsequent significant findings on already-published hypotheses pass
        # through — they're confirmations of an existing discovery, not a new
        # publication. (If a hypothesis was published then retracted, the
        # mitigation re-starts evidence-accumulation; that's a corner case worth
        # being aware of.)
        if any(f.hypothesis_id == h_id for f in literature.standing):
            return finding

        # Otherwise: accumulate context evidence.
        self._pending_evidence[h_id].add(result.action.context_id)

        if len(self._pending_evidence[h_id]) >= self.k_contexts:
            # Threshold met — release the latest finding as the discovery
            # announcement and clear the buffer.
            del self._pending_evidence[h_id]
            return finding

        # Need more context evidence before publication.
        return None

    def post_step(
        self,
        t: int,
        cfg: SimConfig,
        biases: dict[tuple[int, int], float],
        literature: Literature,
        world: World,
        agents: list[ParametricAgent],
        rng: np.random.Generator,
    ) -> None:
        return None
