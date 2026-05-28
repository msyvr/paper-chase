"""The ground-truth hypothesis world (the answer key)."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

from .config import WorldConfig


@dataclass(frozen=True)
class Hypothesis:
    """A single hypothesis with ground truth.

    Agents see only `id`; the truth (`is_true`, `true_effect`) is the answer key
    the simulation uses to score the literature.
    """

    id: int
    is_true: bool
    true_effect: float                   # 0.0 if not is_true; magnitude (Cohen's d) if is_true


class World:
    """A pool of hypotheses, a fraction of which carry a real effect.

    Indexable: `world[h_id] -> Hypothesis`.
    """

    def __init__(self, cfg: WorldConfig) -> None:
        self.cfg = cfg
        rng = np.random.default_rng(cfg.seed)
        is_true_arr = rng.random(cfg.n_hypotheses) < cfg.base_rate_true
        # Truncated normal effect sizes for the true ones; |Normal(...)| keeps them positive.
        effects = np.where(
            is_true_arr,
            np.abs(rng.normal(cfg.effect_size_mean, cfg.effect_size_sd, cfg.n_hypotheses)),
            0.0,
        )
        self.hypotheses: list[Hypothesis] = [
            Hypothesis(id=i, is_true=bool(is_true_arr[i]), true_effect=float(effects[i]))
            for i in range(cfg.n_hypotheses)
        ]

    @property
    def n_hypotheses(self) -> int:
        return len(self.hypotheses)

    @property
    def n_true(self) -> int:
        return sum(1 for h in self.hypotheses if h.is_true)

    def __getitem__(self, idx: int) -> Hypothesis:
        return self.hypotheses[idx]

    def __len__(self) -> int:
        return len(self.hypotheses)
