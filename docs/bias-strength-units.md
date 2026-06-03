# `bias_strength` — units and conversions

`bias_strength` (in `StudyConfig`) is the standard deviation of the per-(hypothesis, context)
systematic bias in the decision statistic. This note explains what it means and how to read it in
units meaningful *outside* the model — because the same underlying quantity (systematic,
non-sampling error shared across repeated measurements) is discussed in several different
vocabularies depending on the field.

## The model

Each study collapses to one z-score-like statistic (`paper_chase/study.py`):

```
Z = (true_effect · √n)  +  bias  +  private
      └── signal λ ──┘       │         └── fresh sampling noise ~ N(0, 1)
                             └── per-(hypothesis, context) bias ~ N(0, bias_strength²),
                                 drawn once and reused for every study of that (h, ctx)
```

A study is "significant" (publishable) when `|Z| > z_crit ≈ 1.96` (α = 0.05). The sampling-noise
term is fixed at unit variance, so **everything in Z is in units of one study's standard error**
(z-score units). Two reference points anchor the scale:

- the significance bar, **z_crit ≈ 1.96**;
- a **genuine effect** contributes **λ ≈ 2.2** (`effect_size_mean · √n̄ = 0.4 · √30`).

So `bias_strength` is the SD of the model's systematic blind-spot, in single-study standard errors.
`bias_strength = 1` ≈ one standard error — roughly half the significance bar, ≈0.46× a real effect.

## Conversion table

| `bias_strength` | ÷ a real effect (λ≈2.2) | spurious Cohen's *d* (n=30) | repeat-study corr | bias-sustained FP fraction | R+R precision\* |
|---|---|---|---|---|---|
| 0.0 | 0     | 0    | 0.00 | 0%   | 0.93 |
| 0.5 | 0.23× | 0.09 | 0.20 | ~0%  | 0.91 |
| 1.0 | 0.46× | 0.18 | 0.50 | 5%   | 0.82 |
| 1.5 | 0.68× | 0.27 | 0.69 | 19%  | 0.54 |
| 2.0 | 0.91× | 0.37 | 0.80 | 33%  | 0.30 |
| 5.0 | 2.3×  | 0.91 | 0.96 | 69%  | 0.11 |

\* same-base replication+retraction precision at this regime (Phase 1.D, 30 seeds; FINDINGS Finding 3).

## Formulas

| quantity | formula | reading |
|---|---|---|
| bias ÷ a real effect | `bias_strength / λ`, `λ ≈ 2.2` | sample-size-invariant; systematic error vs the signal |
| spurious Cohen's *d* | `bias_strength / √n` (≈ `/5.48` at n=30) | the bias re-expressed as an effect size; *n*-dependent |
| repeat-study correlation | `bias_strength² / (1 + bias_strength²)` | intraclass / test–retest correlation of two studies of the same (h, ctx) |
| bias-sustained FP fraction | `2·(1 − Φ(z_crit / bias_strength))`, `z_crit ≈ 1.96` | share of false hypotheses bias alone pushes past significance |

## The columns are four vocabularies for one thing

Each column is how "systematic, non-sampling error shared across repeated measurements" is discussed
in a different literature — fluency converting between them is generally useful:

- **standard-error / z-score units** (`bias_strength` itself) — frequentist hypothesis testing; the bias as a standardized shift in the test statistic.
- **effect size (Cohen's *d*) / "÷ a real effect"** — psychology, biomedical, meta-analysis; the bias as a spurious effect, or as a signal-to-systematic ratio.
- **intraclass / test–retest correlation** — psychometrics, reliability and measurement theory; how correlated repeated measurements of the same thing are. (Also the LLM-native reading: re-query the same model and its answers agree at this rate.)
- **tail probability / false-discovery fraction** — multiple-testing and FDR; the rate at which nulls cross the significance line on bias alone.

A "reliability of 0.80" (psychometrics), a "bias of *d* ≈ 0.37" (meta-analysis), and "a third of
nulls spuriously significant" (FDR) are the *same regime* described three ways.

## Calibrating to a real system (open)

The map from `bias_strength` to any *specific* deployed system is **illustrative, not measured** —
the project's central external-validity question. The bridge: the **repeat-study correlation**
column is directly measurable on a real automated-research system. Run the same model (or the
original model and a candidate auditor) on the same questions, measure how correlated their
conclusions/errors are; `corr = bs²/(1+bs²)` backs out the effective `bias_strength`, and you read
the regime off the table.

A priori: two runs of the *same* model share its entire systematic structure (only temperature adds
independence), so same-model auditing plausibly sits high on the axis (corr ≥ 0.8) — the regime
where same-base audit fails; human science (different labs, methods, instruments) sits near
`bias_strength = 0`, which is why replication works there. **Measuring the correlation on a real
system is the calibration experiment the model points to** — and the most direct way to know where
practice lands on this axis.
