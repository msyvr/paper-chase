"""Phase 1.C — mitigation comparison on the Pareto plane.

Sweeps the novelty:replication reward ratio across each of the three Phase-1
mitigations (plus the no-mitigation baseline and an all-on combination) at a
fixed moderate correlated-error strength (ρ = 0.5) and a context space large
enough for the invariance mitigation to operate (n_contexts = 4).

Plots one trajectory per mitigation on the precision–recall (Pareto) plane.
Pareto dominance between mitigations is read directly off the plot: a
trajectory that lies up-and-to-the-right of another at the same incentive
pressure dominates.

Run:
    uv run python scripts/run_mitigation_comparison.py

Output: a fresh per-run directory under ``results/`` containing
    config.json                 — SimConfig + sweep spec + git state
    data.csv                    — per-(mitigation, novelty_weight, seed) results
    mitigation_comparison.png   — the figure
"""
from __future__ import annotations

import math

import numpy as np
import matplotlib.pyplot as plt

from paper_chase.config import (
    SimConfig, IncentiveConfig, WorldConfig, StudyConfig,
)
from paper_chase.simulation import run
from paper_chase.plots import plot_pareto_plane
from paper_chase.mitigations import (
    PreRegistration, ReplicationAndRetraction, InvarianceRequirement,
)
from paper_chase.results_io import (
    make_run_dir, save_config_json, save_data_csv, capture_git_state,
)


# ---- Sweep parameters ----
NOVELTY_WEIGHTS = [1.0, 2.0, 5.0, 10.0, 20.0, 50.0]
N_SEEDS = 10
REPLICATION_WEIGHT = 1.0
EFFORT_COST_PER_SAMPLE = 0.02
RHO = 0.5                # moderate correlated errors — where invariance should start to matter
N_CONTEXTS = 4           # gives invariance room (k up to 4 = must hit every context)
N_HYPOTHESES = 10_000    # 10x the default so the action budget can't saturate recall;
                         # matches the realistic "vast hypothesis space, scarce attention"
                         # regime. With ~2.25 novel studies per hypothesis (uniform
                         # selection over 22,500 novel actions / 10,000 H), `none`
                         # recall lands around 0.75 — a "moderately-studied effects"
                         # regime where the replication-crisis dynamic is the
                         # interpretable feature.
N_STEPS = 500            # SimConfig default. Deliberately kept here rather than
                         # bumped: under uniform hypothesis selection, raising
                         # n_steps re-saturates `none` recall at ~1.0 (the very
                         # artifact we're avoiding). The regime where high-k
                         # invariance can function while `none` recall stays
                         # diagnostic requires non-uniform attention (power-law
                         # selection over hypotheses), tracked in FUTURE_WORK.md.


# Mitigation factories — fresh instances per sim because some mitigations are
# stateful (e.g., InvarianceRequirement maintains a per-hypothesis evidence
# buffer that must reset between independent runs).
#
# Pre-registration is modeled as *leaky* (qrp_cap=0.1) — perfect enforcement
# (qrp_cap=0.0) isn't realistic and would only show an upper bound; we want a
# fair comparison against output-side filters. Invariance is swept over its
# strictness parameter k ∈ {2, 3, 4} since k=2 is the weakest setting and the
# project's deeper claim is that higher k dominates under correlated errors.
MITIGATION_FACTORIES = {
    "none":                          lambda: [],
    "pre-registration (leaky)":      lambda: [PreRegistration(qrp_cap=0.1)],
    "replication+retraction":        lambda: [ReplicationAndRetraction(audit_fraction=0.1)],
    "invariance (k=2)":              lambda: [InvarianceRequirement(k_contexts=2)],
    "invariance (k=3)":              lambda: [InvarianceRequirement(k_contexts=3)],
    "invariance (k=4)":              lambda: [InvarianceRequirement(k_contexts=4)],
    "all-on":                        lambda: [
        PreRegistration(qrp_cap=0.1),
        ReplicationAndRetraction(audit_fraction=0.1),
        InvarianceRequirement(k_contexts=3),
    ],
}


def main() -> None:
    params = f"nw{NOVELTY_WEIGHTS[0]:g}-{NOVELTY_WEIGHTS[-1]:g}_seeds{N_SEEDS}_rho{RHO}_nctx{N_CONTEXTS}_nh{N_HYPOTHESES}_nsteps{N_STEPS}"
    run_dir = make_run_dir(experiment="mitigation_comparison", params=params)
    print(f"Run dir: {run_dir}")

    base_world = WorldConfig(n_hypotheses=N_HYPOTHESES, n_contexts=N_CONTEXTS, seed=0)
    base_study = StudyConfig(correlated_error_rho=RHO)

    save_config_json(
        run_dir / "config.json",
        base_cfg=SimConfig(world=base_world, study=base_study, n_steps=N_STEPS),
        sweep={
            "mitigations": list(MITIGATION_FACTORIES.keys()),
            "novelty_weights": list(NOVELTY_WEIGHTS),
            "n_seeds": N_SEEDS,
            "fixed_replication_weight": REPLICATION_WEIGHT,
            "fixed_effort_cost_per_sample": EFFORT_COST_PER_SAMPLE,
            "rho": RHO,
            "n_contexts": N_CONTEXTS,
            "n_hypotheses": N_HYPOTHESES,
            "n_steps": N_STEPS,
            "mitigation_parameters": {
                "pre-registration (leaky)": "PreRegistration(qrp_cap=0.1)",
                "replication+retraction":   "ReplicationAndRetraction(audit_fraction=0.1)",
                "invariance (k=2)":         "InvarianceRequirement(k_contexts=2)",
                "invariance (k=3)":         "InvarianceRequirement(k_contexts=3)",
                "invariance (k=4)":         "InvarianceRequirement(k_contexts=4)",
                "all-on":                   "PreRegistration(qrp_cap=0.1) + ReplicationAndRetraction(audit_fraction=0.1) + InvarianceRequirement(k_contexts=3)",
            },
        },
        git_state=capture_git_state(),
    )

    # Per-seed raw rows; aggregates derived from these for the plot.
    rows: list[dict] = []
    aggregates: dict[str, dict] = {}

    for mit_name, factory in MITIGATION_FACTORIES.items():
        aggregates[mit_name] = {
            "nw": [], "precision_mean": [], "precision_sd": [],
            "recall_mean": [], "recall_sd": [],
        }
        for nw in NOVELTY_WEIGHTS:
            precisions: list[float] = []
            recalls: list[float] = []
            for seed in range(N_SEEDS):
                cfg = SimConfig(
                    world=base_world,
                    study=base_study,
                    incentive=IncentiveConfig(
                        novel_weight=nw,
                        replication_weight=REPLICATION_WEIGHT,
                        effort_cost_per_sample=EFFORT_COST_PER_SAMPLE,
                    ),
                    n_steps=N_STEPS,
                    seed=seed,
                )
                result = run(cfg, mitigations=factory())
                last = result.history[-1]
                tc = float(last["truth_content"])
                dr = float(last["discovery_rate"])
                rows.append({
                    "mitigation": mit_name,
                    "novel_weight": nw,
                    "seed": seed,
                    "truth_content": tc,
                    "discovery_rate": dr,
                    "n_standing": last["n_standing"],
                })
                # Skip NaN points (empty literature → NaN precision) from the
                # aggregates so the plot doesn't break, but keep them in CSV.
                if not (math.isnan(tc) or math.isnan(dr)):
                    precisions.append(tc)
                    recalls.append(dr)
                print(
                    f"mit={mit_name:>23}  nw={nw:>5.1f}  seed={seed}  "
                    f"tc={tc:.3f}  dr={dr:.3f}  n={last['n_standing']}"
                )

            if precisions:
                aggregates[mit_name]["nw"].append(nw)
                aggregates[mit_name]["precision_mean"].append(float(np.mean(precisions)))
                aggregates[mit_name]["precision_sd"].append(
                    float(np.std(precisions, ddof=1)) if len(precisions) > 1 else 0.0
                )
                aggregates[mit_name]["recall_mean"].append(float(np.mean(recalls)))
                aggregates[mit_name]["recall_sd"].append(
                    float(np.std(recalls, ddof=1)) if len(recalls) > 1 else 0.0
                )

    save_data_csv(run_dir / "data.csv", rows)

    # Plot: one trajectory per mitigation on the Pareto plane.
    fig, ax = plt.subplots(figsize=(9, 8))
    for i, mit_name in enumerate(MITIGATION_FACTORIES.keys()):
        agg = aggregates[mit_name]
        if not agg["nw"]:
            print(f"warning: no plotable points for mitigation {mit_name!r}")
            continue
        plot_pareto_plane(
            truth_means=agg["precision_mean"],
            truth_sds=agg["precision_sd"],
            discovery_means=agg["recall_mean"],
            discovery_sds=agg["recall_sd"],
            label=mit_name,
            color=f"C{i}",
            mark_ideal=(i == 0),
            ax=ax,
        )

    ax.set_title(
        "Phase 1.C — Mitigation comparison (Pareto plane)\n"
        f"ρ = {RHO}, n_contexts = {N_CONTEXTS}, novelty-weight sweep, "
        f"{N_SEEDS} seeds/point"
    )
    fig.tight_layout()

    fig_path = run_dir / "mitigation_comparison.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    print(f"\nSaved: {fig_path}")


if __name__ == "__main__":
    main()
