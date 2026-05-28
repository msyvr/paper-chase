"""Statistical-engine tests (essential).

If the engine doesn't pin FPR ≈ α and power monotone in n, nothing downstream is
trustworthy. Monte-Carlo with generous tolerance bands (≈ 2σ).
"""
import numpy as np
import pytest

from paper_games.world import Hypothesis
from paper_games.study import run_study, effective_alpha
from paper_games.config import StudyConfig


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


# ---- correlated errors (Stage 1.A) ----

def test_rho0_ignores_shared_shock():
    """With ρ = 0 the shared shock is multiplied out — FPR ≈ α regardless of shock value."""
    cfg = StudyConfig(alpha=0.05, qrp_alpha_max=0.50, correlated_error_rho=0.0)
    null_hyp = Hypothesis(id=0, is_true=False, true_effect=0.0)
    rng = np.random.default_rng(42)
    # A wildly extreme shared shock would force significance if ρ > 0; with ρ = 0
    # it must have no effect.
    hits = sum(
        run_study(null_hyp, 30, 0.0, cfg, rng, shared_shock=100.0)[0]
        for _ in range(N_TRIALS)
    )
    fpr = hits / N_TRIALS
    assert 0.04 < fpr < 0.06, f"FPR with ρ=0 should ≈ α regardless of shock; got {fpr}"


def test_rho1_makes_outcome_deterministic_given_shared_shock():
    """With ρ = 1 there is no private noise — Z = noncentrality + shock, fully shared."""
    cfg = StudyConfig(alpha=0.05, qrp_alpha_max=0.50, correlated_error_rho=1.0)
    null_hyp = Hypothesis(id=0, is_true=False, true_effect=0.0)
    rng = np.random.default_rng(0)

    # |shock| < z_crit ≈ 1.96 → every study must come back non-significant.
    small_shock_results = [
        run_study(null_hyp, 30, 0.0, cfg, rng, shared_shock=0.5)[0] for _ in range(100)
    ]
    assert not any(small_shock_results), "shock below z_crit should yield no significance"

    # |shock| ≫ z_crit → every study must come back significant.
    large_shock_results = [
        run_study(null_hyp, 30, 0.0, cfg, rng, shared_shock=3.0)[0] for _ in range(100)
    ]
    assert all(large_shock_results), "shock well above z_crit should yield all significance"


def test_correlated_error_rho_validated():
    """StudyConfig must reject ρ outside [0, 1]."""
    with pytest.raises(ValueError):
        StudyConfig(correlated_error_rho=-0.1)
    with pytest.raises(ValueError):
        StudyConfig(correlated_error_rho=1.5)
