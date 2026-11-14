# Evaluation protocol

The experiment compares two methods on exactly the same observations. Data splits are by entire scenario seed, before tuning. All family and depth variants of a seed remain within its split.

| Stage | Seeds | Cases and purpose |
|---|---|---|
| Null calibration | 1001–1040 | 40 seeds × 3 families = 120 nulls; run raw plus all 3 candidate windows |
| Window selection | 2001–2012 | 12 × 3 families × 3 depths = 108 signals; evaluate all 3 windows |
| Held-out signals | 3001–3024 | 24 × 3 × 3 = 216 signals; raw versus frozen selected window |
| Held-out nulls | 4001–4040 | 40 × 3 = 120 nulls; raw versus frozen selected window |

Depths: 600, 1200, 2400 ppm. Families: quiet, variable, gapped. Total: 1,476 searches. The source of truth is `results/benchmark.json`; CSV contains all 672 held-out method evaluations. `calibration.json` preserves all 480 calibration scores, `config.json` contains the three validation aggregates and selected window, and `demos.json` contains the first held-out seed in each family/depth and null family with full arrays.

Recovery requires both score > method threshold and absolute fractional period error ≤ 0.02. A half/double-period alias is a failure. `period_recovered` records period accuracy independent of the threshold; `alarm` records the threshold decision. `recovered` combines them. Null cases only contribute alarms, never recovery. No labels are passed into the search. Test truth is used only after predictions.

## Actual results and interpretation

Selected window: 1.2 days (70/108 validation recoveries). Raw: 19/216 recoveries, 5/120 null alarms. Detrended: 153/216 recoveries, 6/120 null alarms. Period-only counts are 89 and 168 respectively. Median measured search times in the committed run were approximately 26 ms raw and 30 ms detrended on the local machine; these are single-run descriptive measurements, not portable benchmarks.

The pooled thresholds are 17.5992 (raw) and 4.9185 (detrended). Quiet-star raw sensitivity is penalized by variable-star calibration cases. These results do not compare against a family-specific threshold or another production implementation. We deliberately report this limitation rather than interpreting the result as an unrestricted algorithm ranking.

Gapped nulls produce 4/40 alarms for each method. The finite calibration set and family dependence prevent a guaranteed 5% false-alarm rate. There are only 24 independent test seeds, with correlated family/depth variants; counting 216 signals as independent would overstate precision. Research-figure bands resample those 24 complete seed groups with replacement, 2,000 times using seed 77, and show percentile 95% intervals. They describe uncertainty within this simulator, not model misspecification or real-sky performance.

## Reproduction

Use the pinned environment in the README. `python -m transitweave.experiment --output artifacts/reproduction` writes a fresh full run without overwriting published evidence. Compare every field except `seconds`, which is machine-dependent. `--quick` uses two seeds per split; it exercises calibration, tuning, evaluation and writing, but its counts and selected window are not a valid replacement for the full study. Plotting always reads `results/` unless the script is deliberately changed.

Tests verify independent least-squares equivalence, time/flux translation stability, phase wrapping, deterministic paired noise, gap handling, split separation, rejection of invalid inputs, saved summary consistency, committed search replay, API behavior and real browser interactions.
