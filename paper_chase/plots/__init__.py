"""Plot helpers.

Each plot lives in its own module with a single `plot_*` function that takes the
data + an optional `ax=` argument. If `ax` is None the function creates its own
figure; if provided, it draws onto the supplied axes (so callers can compose
multiple plots in subplots cleanly).

Plot functions never call `plt.show()` or `fig.savefig()` — that's the caller's job.
"""
from .metrics_vs_pressure import plot_metrics_vs_pressure
from .pareto_plane import plot_pareto_plane

__all__ = ["plot_metrics_vs_pressure", "plot_pareto_plane"]
