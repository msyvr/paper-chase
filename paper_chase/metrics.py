"""Literature metrics.

  truth_content   = TP / (TP + FP)   = precision over the currently-standing literature  (= 1 - FDR)
  discovery_rate  = TP / (TP + FN)   = recall: fraction of TRUE hypotheses with a standing positive

Pareto-optimize for the pair: precision alone can be gamed (publish nothing gives precision = 1).

A "standing finding" counts as a TP iff its hypothesis is actually true. A true
hypothesis counts as discovered iff at least one of its findings is standing.

Note: precision is computed *per standing finding*, so a hypothesis published more
than once contributes multiple times to the denominator (the literature can carry
duplicate entries). This is intentional — precision over the literature-as-published —
but a per-hypothesis variant is a reasonable alternative if duplicate-publication
dynamics become a focus.
"""
from __future__ import annotations
import math

from .literature import Literature
from .world import World


def truth_content(literature: Literature) -> float:
    """Precision = TP / (TP + FP). NaN if literature is empty."""
    standing = literature.standing
    if not standing:
        return math.nan
    tp = sum(1 for f in standing if f.is_true)
    return tp / len(standing)


def discovery_rate(literature: Literature, world: World) -> float:
    """Recall = (# true hypotheses with at least one standing finding) / (# true hypotheses)."""
    if world.n_true == 0:
        return math.nan
    discovered_true_ids = {f.hypothesis_id for f in literature.standing if f.is_true}
    return len(discovered_true_ids) / world.n_true


def summary(literature: Literature, world: World, step: int) -> dict:
    return {
        "step": step,
        "n_standing": len(literature.standing),
        "n_retracted": len(literature.retracted),
        "truth_content": truth_content(literature),
        "discovery_rate": discovery_rate(literature, world),
    }
