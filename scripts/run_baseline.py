"""Phase 0 validity gate.

Sweep incentive pressure (novelty:replication reward ratio) and plot two views
of the same data:
  (a) truth-content (precision) and discovery rate (recall) vs. incentive pressure
  (b) the precision–recall Pareto plane traced by the pressure sweep
      (markers colored by novelty weight; colorbar shows the mapping)

If the engine reproduces the qualitative crisis, truth-content (precision) falls
as the novelty weight rises while discovery rate (recall) stays roughly flat —
in the Pareto plane the trajectory drifts from the upper-right toward the lower-
right. If it doesn't, fix the model — DON'T proceed to mitigations.

Run:
    uv run python scripts/run_baseline.py

Output: a fresh per-run directory under ``results/`` containing
    config.json          — SimConfig + sweep spec + git state (commit + dirty/diff)
    data.csv             — per-(novelty_weight, seed) results
    validity_gate.png    — the figure
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from paper_chase.config import SimConfig, IncentiveConfig
from paper_chase.simulation import run
from paper_chase.plots import plot_metrics_vs_pressure, plot_pareto_plane
from paper_chase.results_io import (
    make_run_dir, save_config_json, save_data_csv, capture_git_state,
)


# Sweep the novelty reward, holding replication weight at 1.0. The ratio is the
# "incentive pressure" axis: higher = stronger publish-or-perish.
NOVELTY_WEIGHTS = [1.0, 2.0, 5.0, 10.0, 20.0, 50.0]
N_SEEDS = 3                            # repeat each setting for sampling-variance control
REPLICATION_WEIGHT = 1.0
EFFORT_COST_PER_SAMPLE = 0.02


def main() -> None:
    # Per-run output directory.
    params = f"nw{NOVELTY_WEIGHTS[0]:g}-{NOVELTY_WEIGHTS[-1]:g}_seeds{N_SEEDS}"
    run_dir = make_run_dir(experiment="baseline", params=params)
    print(f"Run dir: {run_dir}")

    # Save the full reproducibility record up front (config + sweep spec + git state).
    save_config_json(
        run_dir / "config.json",
        base_cfg=SimConfig(),
        sweep={
            "novelty_weights": list(NOVELTY_WEIGHTS),
            "n_seeds": N_SEEDS,
            "fixed_replication_weight": REPLICATION_WEIGHT,
            "fixed_effort_cost_per_sample": EFFORT_COST_PER_SAMPLE,
        },
        git_state=capture_git_state(),
    )

    # Per-seed raw rows; aggregates derived from these for the plot.
    rows: list[dict] = []
    truth_means, truth_sds = [], []
    discovery_means, discovery_sds = [], []

    for nw in NOVELTY_WEIGHTS:
        tcs, drs = [], []
        for seed in range(N_SEEDS):
            cfg = SimConfig(
                incentive=IncentiveConfig(
                    novel_weight=nw,
                    replication_weight=REPLICATION_WEIGHT,
                    effort_cost_per_sample=EFFORT_COST_PER_SAMPLE,
                ),
                seed=seed,
            )
            result = run(cfg)
            last = result.history[-1]
            tc = float(last["truth_content"])
            dr = float(last["discovery_rate"])
            n_st = int(last["n_standing"])
            tcs.append(tc)
            drs.append(dr)
            rows.append({
                "novel_weight": nw,
                "seed": seed,
                "truth_content": tc,
                "discovery_rate": dr,
                "n_standing": n_st,
            })
            print(
                f"novel_weight={nw:>5.1f}  seed={seed}  "
                f"truth_content={tc:.3f}  discovery_rate={dr:.3f}  n_standing={n_st}"
            )
        truth_means.append(float(np.mean(tcs)))
        truth_sds.append(float(np.std(tcs, ddof=1)))
        discovery_means.append(float(np.mean(drs)))
        discovery_sds.append(float(np.std(drs, ddof=1)))

    save_data_csv(run_dir / "data.csv", rows)

    # Compose the two plots into one figure and save.
    fig, (ax_curves, ax_pareto) = plt.subplots(1, 2, figsize=(14, 5))
    plot_metrics_vs_pressure(
        NOVELTY_WEIGHTS, truth_means, truth_sds, discovery_means, discovery_sds,
        ax=ax_curves,
    )
    plot_pareto_plane(
        truth_means, truth_sds, discovery_means, discovery_sds,
        colorby=NOVELTY_WEIGHTS,
        colorby_label="rewards: novel/replicate",
        ax=ax_pareto,
    )
    fig.suptitle(
        "Validity gate — literature reliability under incentive pressure  "
        f"(no mitigation, no correlated errors; {N_SEEDS} seeds per point)",
        y=1.02,
    )
    fig.tight_layout()

    fig_path = run_dir / "validity_gate.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    print(f"\nSaved: {fig_path}")


if __name__ == "__main__":
    main()
