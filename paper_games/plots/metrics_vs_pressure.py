"""Truth-content and discovery rate vs. incentive pressure (log-x)."""
from __future__ import annotations
from typing import Sequence

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes


def plot_metrics_vs_pressure(
    novelty_weights: Sequence[float],
    truth_means: Sequence[float],
    truth_sds: Sequence[float],
    discovery_means: Sequence[float],
    discovery_sds: Sequence[float],
    ax: Axes | None = None,
) -> Axes:
    """Plot truth-content (precision) and discovery rate (recall) against the
    novelty:replication reward ratio on a log-x scale, with seed-variance error
    bars.

    Parameters
    ----------
    novelty_weights
        The x-axis values — one per swept condition.
    truth_means, truth_sds
        Mean and stdev (across seeds) of truth-content per condition.
    discovery_means, discovery_sds
        Mean and stdev (across seeds) of discovery rate per condition.
    ax
        If provided, draws onto these axes. Otherwise creates a new figure.

    Returns
    -------
    Axes
        The axes used (the new one if ``ax`` was None, else the one passed in).
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))

    x = np.asarray(novelty_weights, dtype=float)
    ax.errorbar(
        x, truth_means, yerr=truth_sds, marker="o",
        label="truth-content (precision)", capsize=3,
    )
    ax.errorbar(
        x, discovery_means, yerr=discovery_sds, marker="s",
        label="discovery rate (recall)", capsize=3,
    )
    ax.set_xscale("log")
    ax.set_xlabel("novelty : replication reward ratio  (incentive pressure)")
    ax.set_ylabel("value")
    ax.set_ylim(0, 1.05)
    ax.set_title("Metrics vs. incentive pressure")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    return ax
