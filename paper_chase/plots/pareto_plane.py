"""Precision–recall (Pareto) plane.

Two modes:

  * **Colormap mode** (single trajectory parameterized by a continuous variable):
    pass ``colorby`` (a sequence of numeric values per point) and the markers
    are colored along a colormap, with a colorbar attached to the axes. No
    label-collision issues even when recall saturates near 1.0. Use this for
    Phase 0-style sweeps (one trajectory, parameter varies along it).

  * **Solid-color mode** (one trajectory per mitigation, comparing them):
    leave ``colorby=None`` and pass ``color=`` and ``label=`` to identify the
    mitigation. Call once per mitigation onto the same axes to overlay
    trajectories and read Pareto dominance directly off the plot. Use this for
    Phase 1+ comparisons. Set ``mark_ideal=False`` on subsequent calls so the ideal
    corner is marked only once.

Per-point text labels (``annotations``) are supported in either mode but
recommended only when there are few points and no saturation collisions.
"""
from __future__ import annotations
from typing import Sequence

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import LogNorm, Normalize


def plot_pareto_plane(
    truth_means: Sequence[float],
    truth_sds: Sequence[float],
    discovery_means: Sequence[float],
    discovery_sds: Sequence[float],
    *,
    annotations: Sequence[str | None] | None = None,
    colorby: Sequence[float] | None = None,
    colorby_label: str | None = None,
    colorby_log: bool | None = None,
    cmap: str = "viridis",
    label: str | None = None,
    color: str = "steelblue",
    mark_ideal: bool = False,
    ax: Axes | None = None,
) -> Axes:
    """Plot a trajectory through the precision–recall plane.

    Parameters
    ----------
    truth_means, truth_sds
        Precision values + spread per condition (y axis).
    discovery_means, discovery_sds
        Recall values + spread per condition (x axis).
    annotations
        Optional per-point text labels. Entries that are ``None`` or empty
        strings are skipped — useful for "endpoint labels only".
    colorby
        If given, a numeric value per point used to color the markers via a
        colormap (with a colorbar). Selects **colormap mode**.
    colorby_label
        Label for the colorbar.
    colorby_log
        Force log/linear color normalization. If ``None`` (default), auto-detect:
        log if all values are positive and span > 10×, linear otherwise.
    cmap
        Colormap name (default ``viridis``).
    label
        Legend label for the trajectory (solid-color mode).
    color
        Trajectory color (solid-color mode).
    mark_ideal
        Whether to mark the ``(1, 1)`` ideal corner. Set ``False`` when adding
        further trajectories to the same axes.
    ax
        If provided, draws onto these axes. Otherwise creates a new figure.

    Returns
    -------
    Axes
        The axes used.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 6))

    if colorby is not None:
        _plot_colormap_mode(
            ax, truth_means, truth_sds, discovery_means, discovery_sds,
            colorby=colorby, colorby_label=colorby_label,
            colorby_log=colorby_log, cmap=cmap, label=label,
        )
    else:
        ax.errorbar(
            discovery_means, truth_means,
            xerr=discovery_sds, yerr=truth_sds,
            fmt="o-", capsize=3, alpha=0.75, color=color, label=label,
        )

    if annotations is not None:
        for dx, tc, text in zip(discovery_means, truth_means, annotations):
            if not text:                  # skip None and empty strings
                continue
            ax.annotate(
                text, (dx, tc),
                textcoords="offset points", xytext=(8, -4), fontsize=8,
            )

    if mark_ideal:
        ax.plot(
            1.0, 1.0, marker="*", color="goldenrod", markersize=14,
            linestyle="None", label="ideal (1, 1)",
        )
        ax.legend(loc="lower left")


    ax.set_xlabel("discovery rate (recall)")
    ax.set_ylabel("truth-content (precision)")
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax.set_title("Pareto plane (precision vs. recall)")
    ax.grid(True, alpha=0.3)

    return ax


def _plot_colormap_mode(
    ax: Axes,
    truth_means: Sequence[float],
    truth_sds: Sequence[float],
    discovery_means: Sequence[float],
    discovery_sds: Sequence[float],
    *,
    colorby: Sequence[float],
    colorby_label: str | None,
    colorby_log: bool | None,
    cmap: str,
    label: str | None,
) -> None:
    """Render markers colored by ``colorby`` with a colorbar + subtle line/error bars."""
    values = list(colorby)

    # Auto-detect log vs linear unless caller forced it.
    if colorby_log is None:
        all_positive = all(v > 0 for v in values)
        wide = (max(values) / min(values) > 10.0) if all_positive else False
        use_log = all_positive and wide
    else:
        use_log = colorby_log
    norm = LogNorm(vmin=min(values), vmax=max(values)) if use_log \
        else Normalize(vmin=min(values), vmax=max(values))

    # Subtle connecting line.
    ax.plot(
        discovery_means, truth_means,
        "-", color="gray", alpha=0.4, zorder=1,
    )
    # Subtle error bars (gray, behind the markers).
    ax.errorbar(
        discovery_means, truth_means,
        xerr=discovery_sds, yerr=truth_sds,
        fmt="none", color="gray", alpha=0.5, capsize=3, zorder=2,
    )
    # Colored markers on top.
    sc = ax.scatter(
        discovery_means, truth_means,
        c=values, cmap=cmap, norm=norm,
        s=80, edgecolor="white", linewidths=0.8, zorder=3, label=label,
    )
    # Colorbar attached to the host axes (matplotlib makes room).
    cbar = ax.figure.colorbar(sc, ax=ax, pad=0.02)
    if colorby_label:
        cbar.set_label(colorby_label)
