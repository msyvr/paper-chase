"""Study mechanics: the statistical engine.

One study tests one hypothesis with a chosen sample size. The decision statistic
Z has unit variance and is decomposed into:

    Z = noncentrality + ρ · shared_shock + sqrt(1 − ρ²) · private_noise

where the noncentrality is `true_effect · sqrt(n)`, `shared_shock` is a per-
(hypothesis, context) draw managed by the sim loop, and `private_noise` is a
fresh standard-normal draw per study. ρ = `correlated_error_rho` from `StudyConfig`;
ρ = 0 recovers the independent-error case (Phase 0 / standard ABM-of-science).
ρ = 1 means all studies sharing a (hypothesis, context) see identical Z and
either all reject or all accept — the extreme shared-substrate case.

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
    shared_shock: float = 0.0,
) -> tuple[bool, float]:
    """Run one study; return (significant, observed_effect_estimate).

    - Significance is a two-sided z-test at level `effective_alpha(qrp, cfg)`.
    - Under null (true_effect = 0, ρ = 0): P(significant) = α_eff.
    - Under alternative (ρ = 0): P(significant) ≈ Φ(d√n − z_{1−α_eff/2}).
    - With ρ > 0 the shared component biases Z toward / away from significance
      identically across all studies of the same (hypothesis, context) — so
      pairs of such studies have correlated outcomes. The caller (sim loop)
      is responsible for managing the shared_shock cache; here we just consume.

    By construction, Var(Z) = ρ² + (1 − ρ²) = 1 for any ρ ∈ [0, 1].
    """
    if sample_size < 2:
        raise ValueError(f"sample_size must be >= 2, got {sample_size}")

    alpha_eff = effective_alpha(qrp_intensity, study_cfg)
    z_crit = float(norm.ppf(1.0 - alpha_eff / 2.0))

    lam = hypothesis.true_effect * np.sqrt(sample_size)     # noncentrality
    rho = study_cfg.correlated_error_rho
    private = float(rng.normal(0.0, 1.0))
    z = float(lam + rho * shared_shock + np.sqrt(1.0 - rho * rho) * private)
    significant = bool(abs(z) > z_crit)

    observed_effect = float(z / np.sqrt(sample_size))
    return significant, observed_effect
