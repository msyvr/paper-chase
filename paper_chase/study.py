"""Study mechanics: the statistical engine.

One study tests one hypothesis with a chosen sample size. The decision statistic
Z decomposes additively into

    Z = noncentrality + bias + private

where the noncentrality is `true_effect · sqrt(n)`, `bias` is a per-
(hypothesis, context) systematic offset (drawn once in the sim loop with
standard deviation `StudyConfig.bias_strength` and reused for every study of
that (h, ctx) pair), and `private` is a fresh standard-normal draw per study
representing sampling noise.

The bias and the private noise are **additive and independent**: Var(Z) under
H0 = bias_strength² + 1. The private-noise variance is fixed at 1 regardless
of bias_strength — this is the right structure for "studies share a systematic
limitation but each has its own sampling noise."

bias_strength = 0 recovers independent errors (the human-science baseline).
bias_strength ≈ 1 means the systematic per-(h, ctx) bias has the same scale
as the sampling noise. bias_strength > 1 means systematic limitations dominate.

QRP intensity q ∈ [0, 1] inflates the effective false-positive rate from `alpha`
toward `qrp_alpha_max` (caps aggressive p-hacking).
"""
from __future__ import annotations
import numpy as np
from scipy.stats import norm

from .world import Hypothesis
from .config import StudyConfig


def effective_alpha(qrp_intensity: float, study_cfg: StudyConfig) -> float:
    """α_eff = α + q · (α_max − α) — linear interpolation toward the QRP ceiling."""
    q = float(np.clip(qrp_intensity, 0.0, 1.0))
    return study_cfg.alpha + q * (study_cfg.qrp_alpha_max - study_cfg.alpha)


def run_study(
    hypothesis: Hypothesis,
    sample_size: int,
    qrp_intensity: float,
    study_cfg: StudyConfig,
    rng: np.random.Generator,
    bias: float = 0.0,
) -> tuple[bool, float]:
    """Run one study; return (significant, observed_effect_estimate).

    Parameters
    ----------
    hypothesis
        The hypothesis being tested. Its ``true_effect`` enters the
        decision statistic as ``true_effect · sqrt(sample_size)``.
    sample_size
        Number of samples in the study (must be >= 2).
    qrp_intensity
        QRP intensity ∈ [0, 1]; raises effective α from ``alpha`` toward
        ``qrp_alpha_max``.
    study_cfg
        Study configuration (α, qrp_alpha_max, bias_strength).
    rng
        The shared sim RNG (consumed for the private noise draw).
    bias
        The pre-drawn per-(hypothesis, context) systematic bias. Callers
        managing repeated studies of the same (h, ctx) pair must supply
        the same value every time (same-base audit); a cross-base audit
        passes a fresh independent draw; an independent-error baseline
        passes 0.

    Notes
    -----
    Var(Z) under H0 = bias_strength² + 1 (NOT 1). The test uses the standard
    z_{α/2} critical value, so non-zero bias_strength inflates the average
    false-positive rate across (h, ctx) draws: pairs with positive bias
    reject often, pairs with negative bias rarely. This is the intended
    behaviour — it models how systematic limitations of a base model
    inflate the literature's effective false-positive rate.
    """
    if sample_size < 2:
        raise ValueError(f"sample_size must be >= 2, got {sample_size}")

    alpha_eff = effective_alpha(qrp_intensity, study_cfg)
    z_crit = float(norm.ppf(1.0 - alpha_eff / 2.0))

    lam = hypothesis.true_effect * np.sqrt(sample_size)     # noncentrality
    private = float(rng.normal(0.0, 1.0))
    z = float(lam + bias + private)
    significant = bool(abs(z) > z_crit)

    observed_effect = float(z / np.sqrt(sample_size))
    return significant, observed_effect
