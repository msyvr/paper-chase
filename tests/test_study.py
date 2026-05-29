"""Statistical-engine tests (essential).

If the engine doesn't pin FPR ≈ α and power monotone in n, nothing downstream is
trustworthy. Monte-Carlo with generous tolerance bands (≈ 2σ).
"""
import numpy as np
import pytest

from paper_chase.world import Hypothesis
from paper_chase.study import run_study, effective_alpha
from paper_chase.config import StudyConfig


N_TRIALS = 20_000  # Monte-Carlo budget — fast (~1s) and tight enough for the bands below.


def _fraction_significant(hypothesis: Hypothesis, n: int, q: float, cfg: StudyConfig) -> float:
    rng = np.random.default_rng(42)
    hits = sum(
        run_study(hypothesis, n, q, cfg, rng)[0] for _ in range(N_TRIALS)
    )
    return hits / N_TRIALS


def test_fpr_under_null_no_qrp_is_alpha():
    cfg = StudyConfig(alpha=0.05, qrp_alpha_max=0.50)
    null_hyp = Hypothesis(id=0, is_true=False, true_effect=0.0)
    fpr = _fraction_significant(null_hyp, n=30, q=0.0, cfg=cfg)
    assert 0.04 < fpr < 0.06, f"FPR={fpr} not ≈ 0.05"


def test_fpr_under_null_maxqrp_is_alphamax():
    cfg = StudyConfig(alpha=0.05, qrp_alpha_max=0.50)
    null_hyp = Hypothesis(id=0, is_true=False, true_effect=0.0)
    fpr = _fraction_significant(null_hyp, n=30, q=1.0, cfg=cfg)
    assert 0.47 < fpr < 0.53, f"FPR (with QRP=1)={fpr} not ≈ 0.50"


def test_effective_alpha_interpolates_linearly():
    cfg = StudyConfig(alpha=0.05, qrp_alpha_max=0.50)
    assert effective_alpha(0.0, cfg) == pytest.approx(0.05)
    assert effective_alpha(1.0, cfg) == pytest.approx(0.50)
    assert effective_alpha(0.5, cfg) == pytest.approx(0.275)


def test_power_increases_with_sample_size():
    cfg = StudyConfig(alpha=0.05, qrp_alpha_max=0.50)
    true_hyp = Hypothesis(id=0, is_true=True, true_effect=0.4)
    powers = [_fraction_significant(true_hyp, n=n, q=0.0, cfg=cfg) for n in (10, 30, 100)]
    assert powers[0] < powers[1] < powers[2], f"power not monotone in n: {powers}"
    # Sanity: at d=0.4, n=100, power should be very high (>0.95).
    assert powers[2] > 0.95, f"power at n=100 too low: {powers[2]}"


def test_power_increases_with_effect_size():
    cfg = StudyConfig(alpha=0.05, qrp_alpha_max=0.50)
    powers = []
    for d in (0.1, 0.3, 0.6):
        hyp = Hypothesis(id=0, is_true=True, true_effect=d)
        powers.append(_fraction_significant(hyp, n=30, q=0.0, cfg=cfg))
    assert powers[0] < powers[1] < powers[2], f"power not monotone in d: {powers}"


def test_run_study_rejects_tiny_sample():
    cfg = StudyConfig(alpha=0.05, qrp_alpha_max=0.50)
    hyp = Hypothesis(id=0, is_true=False, true_effect=0.0)
    with pytest.raises(ValueError):
        run_study(hyp, sample_size=1, qrp_intensity=0.0, study_cfg=cfg, rng=np.random.default_rng(0))


# ---- systematic bias (additive noise model) ----

def test_default_bias_arg_ignored_by_test_statistic():
    """``bias = 0`` (the default) is the neutral value — FPR ≈ α as in the no-bias baseline."""
    cfg = StudyConfig(alpha=0.05, qrp_alpha_max=0.50, bias_strength=0.0)
    null_hyp = Hypothesis(id=0, is_true=False, true_effect=0.0)
    rng = np.random.default_rng(42)
    hits = sum(
        run_study(null_hyp, 30, 0.0, cfg, rng, bias=0.0)[0]
        for _ in range(N_TRIALS)
    )
    fpr = hits / N_TRIALS
    assert 0.04 < fpr < 0.06, f"FPR with neutral bias should ≈ α; got {fpr}"


def test_large_positive_bias_pushes_null_to_significance():
    """A bias well above ``z_crit`` should make a null hypothesis reject every time
    (since Z = bias + private and |bias + private| > z_crit with overwhelming probability)."""
    cfg = StudyConfig(alpha=0.05, qrp_alpha_max=0.50, bias_strength=2.0)
    null_hyp = Hypothesis(id=0, is_true=False, true_effect=0.0)
    rng = np.random.default_rng(0)
    # z_crit at α=0.05 (two-sided) ≈ 1.96; bias = 5 → Z = 5 + N(0,1), reject almost surely.
    hits = sum(
        run_study(null_hyp, 30, 0.0, cfg, rng, bias=5.0)[0] for _ in range(200)
    )
    assert hits > 195, f"bias = 5 should yield ~all significance; got {hits}/200"


def test_large_negative_bias_pushes_null_to_significance_too():
    """The test is two-sided — a very negative bias also drives rejection."""
    cfg = StudyConfig(alpha=0.05, qrp_alpha_max=0.50, bias_strength=2.0)
    null_hyp = Hypothesis(id=0, is_true=False, true_effect=0.0)
    rng = np.random.default_rng(0)
    hits = sum(
        run_study(null_hyp, 30, 0.0, cfg, rng, bias=-5.0)[0] for _ in range(200)
    )
    assert hits > 195, f"bias = -5 should yield ~all significance (two-sided); got {hits}/200"


def test_audit_private_noise_does_not_shrink_with_bias_strength():
    """Critical correctness property of the additive-bias model: a study's private
    noise variance must remain 1 regardless of ``bias_strength``. Verify by running
    many studies *with a fixed bias* — the spread of Z values around that bias must
    be (approximately) unit-variance regardless of ``bias_strength``."""
    null_hyp = Hypothesis(id=0, is_true=False, true_effect=0.0)
    rng = np.random.default_rng(0)
    # At the same bias, samples differ only by their private noise. Var should be 1.
    for bs in (0.0, 0.5, 2.0):
        cfg = StudyConfig(alpha=0.05, qrp_alpha_max=0.50, bias_strength=bs)
        # Use observed_effect * sqrt(n) to recover Z; then take variance.
        zs = np.array([
            run_study(null_hyp, 30, 0.0, cfg, rng, bias=0.7)[1] * np.sqrt(30)
            for _ in range(5000)
        ])
        # The spread (variance) of Z around its mean must be ≈ 1 (the private noise).
        var_z = float(zs.var())
        assert 0.90 < var_z < 1.10, (
            f"private noise variance must be 1 regardless of bias_strength; "
            f"bias_strength={bs} produced Var(Z)={var_z}"
        )


def test_bias_strength_validated():
    """StudyConfig must reject negative ``bias_strength``."""
    with pytest.raises(ValueError):
        StudyConfig(bias_strength=-0.1)
    # Positive values, including > 1, are allowed.
    StudyConfig(bias_strength=0.0)
    StudyConfig(bias_strength=1.0)
    StudyConfig(bias_strength=2.5)
