"""Metric tests on hand-built literatures — exact, no Monte-Carlo."""
import math
import numpy as np
import pytest

from paper_games.config import WorldConfig
from paper_games.world import World, Hypothesis
from paper_games.literature import Literature, Finding
from paper_games.metrics import truth_content, discovery_rate


def _world_with_n_true(n_hypotheses: int, n_true: int) -> World:
    """Construct a World, then overwrite hypotheses to have exactly `n_true` true ones (ids 0..n_true-1)."""
    cfg = WorldConfig(n_hypotheses=n_hypotheses, base_rate_true=0.0, seed=0)
    world = World(cfg)
    world.hypotheses = [
        Hypothesis(id=i, is_true=(i < n_true), true_effect=(0.4 if i < n_true else 0.0))
        for i in range(n_hypotheses)
    ]
    return world


def _add(lit: Literature, hyp_id: int, is_true: bool) -> None:
    lit.add(Finding(
        hypothesis_id=hyp_id, agent_id=0, kind="novel",
        observed_effect=0.4, sample_size=30, is_true=is_true, timestep=0,
    ))


def test_truth_content_empty_is_nan():
    lit = Literature()
    assert math.isnan(truth_content(lit))


def test_truth_content_all_true_is_one():
    lit = Literature()
    for i in range(5):
        _add(lit, hyp_id=i, is_true=True)
    assert truth_content(lit) == 1.0


def test_truth_content_all_false_is_zero():
    lit = Literature()
    for i in range(5):
        _add(lit, hyp_id=i, is_true=False)
    assert truth_content(lit) == 0.0


def test_truth_content_3tp_3fp_is_half():
    lit = Literature()
    for i in range(3):
        _add(lit, hyp_id=i, is_true=True)
    for i in range(3):
        _add(lit, hyp_id=100 + i, is_true=False)
    assert truth_content(lit) == 0.5


def test_discovery_rate_three_of_five_true_published():
    world = _world_with_n_true(n_hypotheses=10, n_true=5)
    lit = Literature()
    for i in range(3):                                  # publish 3 of the 5 true ones
        _add(lit, hyp_id=i, is_true=True)
    assert discovery_rate(lit, world) == pytest.approx(0.6)


def test_discovery_rate_dedupes_multiple_publications_of_same_truth():
    world = _world_with_n_true(n_hypotheses=10, n_true=5)
    lit = Literature()
    for _ in range(4):                                  # same true hypothesis published 4 times
        _add(lit, hyp_id=0, is_true=True)
    assert discovery_rate(lit, world) == pytest.approx(0.2)  # 1 of 5 true hypotheses discovered


def test_retraction_removes_from_standing():
    lit = Literature()
    _add(lit, hyp_id=0, is_true=False)
    _add(lit, hyp_id=1, is_true=True)
    fp = lit.standing[0]
    lit.retract(fp)
    assert truth_content(lit) == 1.0
    assert len(lit.retracted) == 1
