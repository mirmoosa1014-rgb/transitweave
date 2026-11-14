"""Disjoint calibration, tuning and held-out evaluation; writes auditable data."""
import argparse
import csv
import json
from pathlib import Path
import time
import numpy as np
from .simulation import FAMILIES, simulate
from .search import analyze, recovered

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = (.6, 1.2, 2.4)
DEPTHS = (600, 1200, 2400)
SPLITS = dict(calibration=list(range(1001, 1041)), validation=list(range(2001, 2013)),
              test=list(range(3001, 3025)), null_test=list(range(4001, 4041)))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def run(output, quick=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    seeds = {k: v[:2] if quick else v for k, v in SPLITS.items()}
    thresholds, calibration, tuning = {}, [], []
    for window in (0, *WINDOWS):
        values = []
        for family in FAMILIES:
            for seed in seeds['calibration']:
                lc = simulate(seed, family, 0)
                score = analyze(lc.time, lc.flux, lc.sigma, window)['score']
                values.append(score)
                calibration.append(dict(seed=seed, family=family, window_days=window, score=score))
        thresholds[str(window)] = float(np.quantile(values, .95, method='higher'))
        print('calibrated window', window, flush=True)
    for window in WINDOWS:
        successes = 0; count = 0
        for family in FAMILIES:
            for seed in seeds['validation']:
                for depth in DEPTHS:
                    lc = simulate(seed, family, depth)
                    fit = analyze(lc.time, lc.flux, lc.sigma, window)
                    successes += bool(fit['score'] > thresholds[str(window)] and recovered(fit, lc.truth))
                    count += 1
        tuning.append(dict(window_days=window, recovered=successes, total=count, recovery_rate=successes/count))
        print('tuned', tuning[-1], flush=True)
    selected = max(tuning, key=lambda x: (x['recovery_rate'], -x['window_days']))['window_days']
    config = dict(selected_window_days=selected, thresholds={'raw': thresholds['0'], 'detrended': thresholds[str(selected)]},
                  all_thresholds=thresholds, seeds=seeds, tuning=tuning,
                  calibration_quantile=.95, threshold_comparison='strictly greater', quick=quick)
    rows=[]; demos=[]
    for split in ('test', 'null_test'):
        for family in FAMILIES:
            for seed in seeds[split]:
                for depth in (DEPTHS if split == 'test' else (0,)):
                    lc = simulate(seed, family, depth)
                    results = {}
                    for method, window in [('raw', 0), ('detrended', selected)]:
                        start = time.perf_counter()
                        fit = analyze(lc.time, lc.flux, lc.sigma, window)
                        elapsed = time.perf_counter()-start
                        alarm = fit['score'] > config['thresholds'][method]
                        rows.append(dict(split=split, family=family, seed=seed, depth_ppm=depth, method=method,
                                         true_period_days=lc.truth['period_days'], period_days=fit['period_days'],
                                         score=fit['score'], alarm=bool(alarm), period_recovered=bool(recovered(fit, lc.truth)),
                                         recovered=bool(alarm and recovered(fit, lc.truth)), seconds=elapsed))
                        results[method] = fit
                    if seed == seeds[split][0]:
                        demos.append(dict(truth=lc.truth, time=lc.time.tolist(), flux=lc.flux.tolist(),
                                          stellar=lc.stellar.tolist(), transit=lc.transit.tolist(), methods=results))
            print('evaluated',split,family,flush=True)
    summary=[]
    for family in FAMILIES:
        for method in ('raw', 'detrended'):
            positives=[r for r in rows if r['family']==family and r['method']==method and r['split']=='test']
            negatives=[r for r in rows if r['family']==family and r['method']==method and r['split']=='null_test']
            summary.append(dict(family=family, method=method, recovered=sum(r['recovered'] for r in positives),
                                signals=len(positives), false_alarms=sum(r['alarm'] for r in negatives), nulls=len(negatives)))
    write_json(output/'config.json',config)
    write_json(output/'calibration.json',calibration)
    write_json(output/'benchmark.json',dict(config=config, summary=summary, rows=rows))
    write_json(output/'demos.json',demos)
    with (output/'benchmark.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps(summary,indent=2),flush=True)
    return config,rows

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--quick',action='store_true');p.add_argument('--output',type=Path)
    args=p.parse_args();run(args.output or ROOT/('artifacts/quick' if args.quick else 'results'),args.quick)
