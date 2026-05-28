"""Study mechanics: the statistical engine.

One study tests one hypothesis with a chosen sample size. The decision statistic
Z is drawn from a Normal centered on the noncentrality (`true_effect * sqrt(n)`)
with unit variance. QRP intensity q ∈ [0, 1] inflates the effective false-positive
rate from `alpha` toward `qrp_alpha_max` (caps aggressive p-hacking).

Correlated errors (ρ > 0 from a shared base model) are deliberately OFF in Phase 0;
they enter in a later phase as a shared shock injected into Z.
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
) -> tuple[bool, float]:
    """Run one study; return (significant, observed_effect_estimate).

    - Significance is a two-sided z-test at level `effective_alpha(qrp, cfg)`.
    - Under null (true_effect = 0): P(significant) = α_eff.
    - Under alternative: P(significant) ≈ Φ(d√n − z_{1−α_eff/2}).
    """
    if sample_size < 2:
        raise ValueError(f"sample_size must be >= 2, got {sample_size}")

    alpha_eff = effective_alpha(qrp_intensity, study_cfg)
    z_crit = float(norm.ppf(1.0 - alpha_eff / 2.0))

    lam = hypothesis.true_effect * np.sqrt(sample_size)     # noncentrality
    z = rng.normal(loc=lam, scale=1.0)
    significant = bool(abs(z) > z_crit)

    observed_effect = float(z / np.sqrt(sample_size))
    return significant, observed_effect
