# 90-second walkthrough

1. Start `python -m transitweave.server`; open port 8766. The default is a variable star, seed 3001, 1200 ppm.
2. Read the observation strip. The yellow line is the estimated rolling median, not injected truth.
3. Switch to Raw baseline. Its strongest trial is near the true period, but below its stricter null-calibrated threshold. Switch back to detrended: the candidate passes its own threshold.
4. Move the trial-period slider away from the strongest trial. Watch the dips spread across phase. Return to strongest trial to restore the fitted box.
5. Reveal injected truth. This is an evaluator view; the search never received it.
6. Select the gapped family, zero-depth control and seed 4001; generate again. Explain that nulls may still have peaks, and the benchmark counts false alarms.
7. Read the held-out table, especially 4/40 gapped null alarms. Export the displayed case and inspect the two searches and separately labeled truth.

The README screenshots are actual browser captures, not mockups. All data is synthetic and no local server is published to the internet.
