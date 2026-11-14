# Statistical model

## Generator

Time is measured in days; flux is relative to a nominal unity baseline. A regular 0.03-day grid spans [0,27). All random draws occur before transit injection, so changing depth preserves noise and observing gaps. Each seed chooses a period uniformly from 1.6–5.2 days, a random epoch, a duty fraction from 0.035–0.065, and a stellar variability period of 7–12 days. The transit is a trapezoid with each ingress/egress occupying 10% of the full duration. Noise is independent normal with sigma 0.0008 (800 ppm). Stellar variation combines a fundamental sinusoid and a quarter-amplitude second harmonic. Amplitude is 250 ppm for quiet stars, 3500 ppm otherwise. Five percent of samples are missing normally; the gapped family drops 30% plus days 11–14.

This intentionally simple additive model does not calculate physical exoplanet radii or orbital parameters. It does not include finite exposure integration or correlated noise. Same-seed family variants share period, noise draws and random masks; they are correlated, not independent stars.

## Search and score

Both methods search the same grid: 421 periods from 1.4 through 5.6 days, 128 phase bins, and box widths of 3, 5, 8 or 11 bins. Every start phase is tried, including boxes that wrap phase zero. Require at least four inside and twenty outside observations. Subtract the first timestamp before folding and round at 1e-10 of a phase bin to stabilize floating-point boundary placement.

For each candidate box, compute inside/outside means and their difference `depth = mean_out - mean_in`. Only dips are allowed. The score is:

```
max(depth, 0) / (sigma * sqrt(1/n_inside + 1/n_outside))
```

With independent equal-variance Gaussian noise and a fixed box, score squared equals the improvement in residual sum of squares divided by sigma squared when replacing one constant level by two fitted levels. A regression test verifies this against an independent exhaustive least-squares calculation. Searching many periods/phases invalidates interpreting the maximum as a single-test normal z-score. Stellar variability and detrending also violate independent residual assumptions. **We do not turn this score into an analytic p-value.**

The overall maximum chooses the reported period, epoch, depth and baseline. A phase-folded box is a fitted approximation to a trapezoid, not a physical transit model. There is no harmonic disambiguation or peak-refinement stage.

## Detrending and calibration

The detrended method subtracts a rolling median and adds one back. Windows use elapsed time rather than adjacent sample count, so a downlink gap is never treated as uniformly observed time. This is an offline symmetric window and may attenuate transit depth, particularly when the window is short relative to transit duration. The search receives only time, flux and nominal measurement sigma—never simulator truth.

For every candidate window, the maximum score is measured on 120 no-transit calibration scenarios. The threshold is the 95th percentile using NumPy's `higher` convention. A candidate requires a score **strictly greater** than this threshold. One threshold is pooled across the three families per method. This is an empirical operating point for this generator and trial grid; it is not a transferable false-alarm guarantee.

The 0.6, 1.2 and 2.4-day windows are tuned on 108 separate signal scenarios. The largest above-threshold fundamental-period recovery count wins; ties favor the shorter window. Test seeds are never used for tuning. Configuration is saved as plain JSON, not executable serialization.

## Why no machine learning?

The experimental question is about detrending and repeated dip detection with an explicit model. A learned classifier would add training-distribution dependence and obscure whether improvement comes from preprocessing or classification. The selected window is a tuned numerical parameter, **not a trained ML model**. A future classifier would need additional signal/artifact families, independent training seeds and calibration before making any justified performance claim.

## References

[Kovács, Zucker & Mazeh (2002), A box-fitting algorithm in the search for periodic transits](https://doi.org/10.1051/0004-6361:20020802) motivates fitting repeated low/high states rather than sinusoids. [NASA's algorithm guide](https://exoplanetarchive.ipac.caltech.edu/docs/pgram/pgram_algo.html) describes period folding and phase-bin box searches and cautions that variability affects statistical significance. The exact finite grid, one-sided score, null calibration, detrending and synthetic generator here are project-specific choices.
