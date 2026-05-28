"""The accumulating published record.

A `Finding` carries the hypothesis id, the agent who ran the study, the observed
effect, and the ground-truth label (`is_true`) — the truth label is what lets us
score truth-content. It is metadata for the metrics, NOT visible to agents'
decision logic.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    hypothesis_id: int
    agent_id: int
    kind: str                            # "novel" or "replication"
    observed_effect: float
    sample_size: int
    is_true: bool                        # ground truth — used by metrics, NOT by agents
    timestep: int


class Literature:
    """Accumulates standing (non-retracted) findings plus an audit trail of retractions."""

    def __init__(self) -> None:
        self._standing: list[Finding] = []
        self._retracted: list[Finding] = []

    @property
    def standing(self) -> list[Finding]:
        return self._standing

    @property
    def retracted(self) -> list[Finding]:
        return self._retracted

    def add(self, finding: Finding) -> None:
        self._standing.append(finding)

    def retract(self, finding: Finding) -> None:
        if finding not in self._standing:
            raise ValueError(f"cannot retract a finding that is not standing: {finding}")
        self._standing.remove(finding)
        self._retracted.append(finding)

    def standing_hypothesis_ids(self) -> list[int]:
        """List of hypothesis ids currently standing (may contain duplicates if multiply published)."""
        return [f.hypothesis_id for f in self._standing]

    def __len__(self) -> int:
        return len(self._standing)
