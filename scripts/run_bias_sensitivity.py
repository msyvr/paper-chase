"""Phase 1.D — systematic-bias sensitivity sweep.

The central falsifiable claim: *invariance-style mitigations dominate
audit-style ones under sufficiently strong systematic bias.*

Phase 1.C showed all four mitigations sitting on a Pareto frontier at a
single bias_strength = 0.5. This script traces how each mitigation's position
moves as bias_strength varies, holding everything else fixed. The prediction
under the corrected (additive) noise model:

  * `none`, `pre-registration (leaky)`: precision approximately bias-independent
    (neither addresses the per-(h, ctx) systematic bias mechanism — pre-reg
    clamps QRP, neither touches the bias).
  * `replication+retraction`: precision *falls* as bias_strength rises. The
    audit replicate uses the SAME per-(hypothesis, context) bias as the
    original study, so a lucky positive-bias FP gets confirmed by the audit
    (the bias that drove the original FP also pushes the audit Z above the
    threshold). The audit's *private* noise is fresh and unchanged in scale —
    it can no longer artificially shrink with bias_strength, so it doesn't
    rescue the audit at high bias.
  * `invariance (k=2)`: precision approximately bias-independent or rising.
    The multi-context bar uses *independent* per-(h, ctx) biases, so a lucky
    bias in context A cannot carry a false positive past invariance's
    two-context requirement — the bias in context B is an independent draw.

  ⇒ At some bias_strength the precision curves of R+R and invariance cross.
    Below the crossover, R+R wins; above it, invariance wins.

The regime is the Phase 1.C regime (n_hypotheses=10000, n_contexts=4,
n_steps=500, novelty_weight fixed at 10) — uniform hypothesis selection,
so high-k invariance is not viable here (Phase 1.C found ~2% recall at
k=4). Phase 1.D focuses on the k=2 vs R+R competition, which has enough
data to be meaningful (~38% k=2 recall at this regime). The non-uniform-
attention upgrade tracked in FUTURE_WORK.md will let a later re-run
include the high-k variants.

Run:
    uv run python scripts/run_bias_sensitivity.py

Output: a fresh per-run directory under ``results/`` containing
    config.json             — SimConfig + sweep spec + git state
    data.csv                — per-(mitigation, bias_strength, seed) results
    bias_sensitivity.png    — two-panel figure (precision-vs-bias + Pareto plane)
"""
from __future__ import annotations

import math

import numpy as np
import matplotlib.pyplot as plt

from paper_chase.config import (
    SimConfig, IncentiveConfig, WorldConfig, StudyConfig,
)
from paper_chase.simulation import run
from paper_chase.mitigations import (
    PreRegistration, ReplicationAndRetraction, InvarianceRequirement,
)
from paper_chase.results_io import (
    make_run_dir, save_config_json, save_data_csv, capture_git_state,
)


# ---- Sweep parameters ----
# Extended range to test the high-correlation regime where R+R is
# mechanistically expected to break (same-base audit can't distinguish
# lucky-bias FPs from TPs when bias dominates the signal). Correlation
# between same-(h, ctx) studies = bias_strength² / (1 + bias_strength²):
#   bs=0.0  → corr=0.00 (independent)
#   bs=0.5  → corr=0.20
#   bs=1.0  → corr=0.50 (the previous sweep's max)
#   bs=2.0  → corr=0.80 (LLM-instance-like regime)
#   bs=5.0  → corr=0.96 (extreme; same-LLM near-deterministic)
BIAS_STRENGTHS = [0.0, 0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 5.0]   # SD of per-(h, ctx) bias; densified 1->2 to resolve the transition shape (was [0, 0.5, 1, 2, 5])
N_SEEDS = 10
NOVELTY_WEIGHT = 10.0          # mid-pressure: dynamic is fully developed but not extreme
REPLICATION_WEIGHT = 1.0
EFFORT_COST_PER_SAMPLE = 0.02
N_CONTEXTS = 4
N_HYPOTHESES = 10_000          # same regime as Phase 1.C — sparse-attention world


# Mitigation factories — fresh instances per sim (stateful mitigations like
# InvarianceRequirement maintain per-hypothesis evidence buffers that must
# reset between independent runs).
#
# Scope chosen for the comparison Phase 1.D is built around:
#   * `none` — baseline reference; precision should fall with bias (lucky-bias FPs persist)
#   * `pre-registration (leaky)` — bias-orthogonal control (clamps QRP, doesn't touch bias)
#   * `replication+retraction` — audit-style; predicted to degrade with bias
#   * `invariance (k=2)` — invariance-style; predicted to be bias-robust
#
# k=3, k=4 invariance are excluded because at this regime (sparse uniform
# attention) they publish almost nothing (Phase 1.C found ~10% and ~2% recall
# respectively). A future re-run under non-uniform attention will include them.
MITIGATION_FACTORIES = {
    "none":                          lambda: [],
    "pre-registration (leaky)":      lambda: [PreRegistration(qrp_cap=0.1)],
    "replication+retraction":        lambda: [ReplicationAndRetraction(audit_fraction=0.1)],
    "invariance (k=2)":              lambda: [InvarianceRequirement(k_contexts=2)],
}


def main() -> None:
    params = f"bs{BIAS_STRENGTHS[0]:g}-{BIAS_STRENGTHS[-1]:g}_seeds{N_SEEDS}_nw{NOVELTY_WEIGHT:g}_nh{N_HYPOTHESES}"
    run_dir = make_run_dir(experiment="bias_sensitivity", params=params)
    print(f"Run dir: {run_dir}")

    base_world = WorldConfig(n_hypotheses=N_HYPOTHESES, n_contexts=N_CONTEXTS, seed=0)

    save_config_json(
        run_dir / "config.json",
        # Base config snapshot uses bias_strength=0 for the schema; per-sim value set in the loop.
        base_cfg=SimConfig(world=base_world, study=StudyConfig(bias_strength=0.0)),
        sweep={
            "mitigations": list(MITIGATION_FACTORIES.keys()),
            "bias_strengths": list(BIAS_STRENGTHS),
            "n_seeds": N_SEEDS,
            "fixed_novelty_weight": NOVELTY_WEIGHT,
            "fixed_replication_weight": REPLICATION_WEIGHT,
            "fixed_effort_cost_per_sample": EFFORT_COST_PER_SAMPLE,
            "n_contexts": N_CONTEXTS,
            "n_hypotheses": N_HYPOTHESES,
            "mitigation_parameters": {
                "pre-registration (leaky)": "PreRegistration(qrp_cap=0.1)",
                "replication+retraction":   "ReplicationAndRetraction(audit_fraction=0.1)",
                "invariance (k=2)":         "InvarianceRequirement(k_contexts=2)",
            },
        },
        git_state=capture_git_state(),
    )

    # Per-seed raw rows; aggregates derived from these for the plot.
    rows: list[dict] = []
    aggregates: dict[str, dict] = {}

    for mit_name, factory in MITIGATION_FACTORIES.items():
        aggregates[mit_name] = {
            "bias_strength": [], "precision_mean": [], "precision_sd": [],
            "recall_mean": [], "recall_sd": [],
        }
        for bs in BIAS_STRENGTHS:
            precisions: list[float] = []
            recalls: list[float] = []
            for seed in range(N_SEEDS):
                cfg = SimConfig(
                    world=base_world,
                    study=StudyConfig(bias_strength=bs),
                    incentive=IncentiveConfig(
                        novel_weight=NOVELTY_WEIGHT,
                        replication_weight=REPLICATION_WEIGHT,
                        effort_cost_per_sample=EFFORT_COST_PER_SAMPLE,
                    ),
                    seed=seed,
                )
                result = run(cfg, mitigations=factory())
                last = result.history[-1]
                tc = float(last["truth_content"])
                dr = float(last["discovery_rate"])
                rows.append({
                    "mitigation": mit_name,
                    "bias_strength": bs,
                    "seed": seed,
                    "truth_content": tc,
                    "discovery_rate": dr,
                    "n_standing": last["n_standing"],
                })
                if not (math.isnan(tc) or math.isnan(dr)):
                    precisions.append(tc)
                    recalls.append(dr)
                print(
                    f"mit={mit_name:>27}  bs={bs:>4.2f}  seed={seed}  "
                    f"tc={tc:.3f}  dr={dr:.3f}  n={last['n_standing']}"
                )

            if precisions:
                aggregates[mit_name]["bias_strength"].append(bs)
                aggregates[mit_name]["precision_mean"].append(float(np.mean(precisions)))
                aggregates[mit_name]["precision_sd"].append(
                    float(np.std(precisions, ddof=1)) if len(precisions) > 1 else 0.0
                )
                aggregates[mit_name]["recall_mean"].append(float(np.mean(recalls)))
                aggregates[mit_name]["recall_sd"].append(
                    float(np.std(recalls, ddof=1)) if len(recalls) > 1 else 0.0
                )

    save_data_csv(run_dir / "data.csv", rows)

    # Two-panel figure: precision vs bias_strength (headline diagnostic) and
    # the Pareto plane (one trajectory per mitigation across bias_strength).
    fig, (ax_bs, ax_pareto) = plt.subplots(1, 2, figsize=(14, 6))

    for i, mit_name in enumerate(MITIGATION_FACTORIES.keys()):
        agg = aggregates[mit_name]
        if not agg["bias_strength"]:
            print(f"warning: no plotable points for mitigation {mit_name!r}")
            continue
        color = f"C{i}"

        # Left: precision vs bias_strength
        ax_bs.errorbar(
            agg["bias_strength"], agg["precision_mean"], yerr=agg["precision_sd"],
            fmt="o-", capsize=3, color=color, label=mit_name,
        )

        # Right: Pareto plane, one trajectory per mitigation across bias_strength.
        # Annotate endpoints with their bias_strength so direction of travel is legible.
        ax_pareto.errorbar(
            agg["recall_mean"], agg["precision_mean"],
            xerr=agg["recall_sd"], yerr=agg["precision_sd"],
            fmt="o-", capsize=3, alpha=0.75, color=color, label=mit_name,
        )
        ax_pareto.annotate(
            f"bs={agg['bias_strength'][0]:g}",
            (agg["recall_mean"][0], agg["precision_mean"][0]),
            textcoords="offset points", xytext=(6, 6), fontsize=8, color=color,
        )
        ax_pareto.annotate(
            f"bs={agg['bias_strength'][-1]:g}",
            (agg["recall_mean"][-1], agg["precision_mean"][-1]),
            textcoords="offset points", xytext=(6, -10), fontsize=8, color=color,
        )

    # Ideal corner reference on the Pareto plane.
    ax_pareto.plot(
        1.0, 1.0, marker="D", color="goldenrod", markersize=8,
        linestyle="None", label="ideal (1, 1)",
    )

    ax_bs.set_xlabel("bias strength (SD of per-(h, ctx) systematic bias)")
    ax_bs.set_ylabel("truth-content (precision)")
    ax_bs.set_title("Precision vs bias strength — direct comparison")
    ax_bs.set_xlim(-0.05, max(BIAS_STRENGTHS) + 0.05)
    ax_bs.set_ylim(0, 1.05)
    ax_bs.grid(True, alpha=0.3)
    ax_bs.legend(loc="lower left")

    ax_pareto.set_xlabel("discovery rate (recall)")
    ax_pareto.set_ylabel("truth-content (precision)")
    ax_pareto.set_title("Pareto plane — trajectory across bias strength")
    ax_pareto.set_xlim(0, 1.05)
    ax_pareto.set_ylim(0, 1.05)
    ax_pareto.grid(True, alpha=0.3)
    ax_pareto.legend(loc="lower left")

    fig.suptitle(
        f"Phase 1.D — bias-strength sensitivity (novelty_weight = {NOVELTY_WEIGHT:g}, "
        f"n_contexts = {N_CONTEXTS}, {N_SEEDS} seeds/point)",
        y=1.02,
    )
    fig.tight_layout()

    fig_path = run_dir / "bias_sensitivity.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    print(f"\nSaved: {fig_path}")


if __name__ == "__main__":
    main()
