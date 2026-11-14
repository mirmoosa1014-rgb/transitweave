"""Binned, one-sided two-level least-squares search with a fixed trial grid."""
import numpy as np

PERIODS = np.linspace(1.4, 5.6, 421)
BINS = 128
WIDTHS = (3, 5, 8, 11)


def observations(time, flux):
    t, y = np.asarray(time, dtype=float), np.asarray(flux, dtype=float)
    if t.ndim != 1 or y.shape != t.shape or not 30 <= len(t) <= 2000:
        raise ValueError('matching one-dimensional arrays of 30–2000 samples required')
    if not np.isfinite(t).all() or not np.isfinite(y).all() or np.any(np.diff(t) <= 0):
        raise ValueError('finite flux and strictly increasing finite times required')
    return t, y


def detrend(time, flux, window_days):
    t, y = observations(time, flux)
    if not np.isfinite(window_days) or not .1 <= window_days <= 5:
        raise ValueError('window must be between 0.1 and 5 days')
    # Time-based windows never assume uniform sampling across gaps.
    lo = np.searchsorted(t, t-window_days/2, side='left')
    hi = np.searchsorted(t, t+window_days/2, side='right')
    trend = np.array([np.median(y[a:b]) for a, b in zip(lo, hi)])
    return y-trend+1, trend


def search(time, flux, sigma, periods=None):
    t, y = observations(time, flux)
    if isinstance(sigma, bool) or not np.isscalar(sigma) or not np.isfinite(sigma) or sigma <= 0:
        raise ValueError('positive finite measurement sigma required')
    grid = PERIODS if periods is None else np.asarray(periods, dtype=float)
    if grid.ndim != 1 or not 1 <= len(grid) <= 2000 or not np.isfinite(grid).all() or np.any(grid <= 0):
        raise ValueError('1–2000 positive finite trial periods required')
    # Time relative to first observation makes the binning translation invariant.
    relative = t-t[0]
    centered = y-y.mean()
    scores, fits = [], []
    for period in grid:
        # Snap only numerical boundary noise (1e-10 of a phase bin).
        bin_id = np.floor(np.round(relative/period*BINS, 10)).astype(int) % BINS
        count = np.bincount(bin_id, minlength=BINS)
        total = np.bincount(bin_id, weights=centered, minlength=BINS)
        nc = np.r_[0, np.cumsum(np.tile(count, 2))]
        yc = np.r_[0, np.cumsum(np.tile(total, 2))]
        start = np.arange(BINS)
        best = (0., 0, WIDTHS[0], 0., float(y.mean()))
        for width in WIDTHS:
            ni = nc[start+width]-nc[start]
            no = len(t)-ni
            si = yc[start+width]-yc[start]
            valid = (ni >= 4) & (no >= 20)
            inside = si/np.maximum(ni, 1)
            outside = -si/np.maximum(no, 1)
            depth = outside-inside
            score = np.where(valid, np.maximum(depth, 0)/(sigma*np.sqrt(1/np.maximum(ni, 1)+1/np.maximum(no, 1))), 0)
            j = int(np.argmax(score))
            if score[j] > best[0]:
                best = (float(score[j]), j, width, float(depth[j]), float(outside[j]+y.mean()))
        scores.append(best[0]); fits.append(best)
    winner = int(np.argmax(scores))
    score, start, width, depth, outside = fits[winner]
    period = float(grid[winner])
    epoch = float(t[0] + ((start+width/2)/BINS % 1)*period)
    return dict(period_days=period, epoch_days=epoch, duration_days=period*width/BINS,
                depth_ppm=depth*1e6, baseline_flux=outside, score=score,
                periods=grid.tolist(), scores=scores)


def analyze(time, flux, sigma, window_days=0):
    t, y = observations(time, flux)
    if window_days:
        cleaned, trend = detrend(t, y, window_days)
    else:
        cleaned, trend = y.copy(), np.full(len(y), np.median(y))
    result = search(t, cleaned, sigma)
    result.update(window_days=float(window_days), flux=cleaned.tolist(), trend=trend.tolist())
    return result


def recovered(fit, truth):
    """Strict fundamental period recovery; half/double aliases count as failures."""
    return truth['depth_ppm'] > 0 and abs(fit['period_days']/truth['period_days']-1) <= .02
