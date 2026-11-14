"""Synthetic additive relative-flux model; no real telescope data."""
from dataclasses import dataclass
import numpy as np

FAMILIES = ('quiet', 'variable', 'gapped')

@dataclass
class LightCurve:
    time: np.ndarray
    flux: np.ndarray
    sigma: float
    truth: dict
    stellar: np.ndarray
    transit: np.ndarray


def simulate(seed=101, family='variable', depth_ppm=1200):
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or not 0 <= seed <= 1000000:
        raise ValueError('seed must be an integer from 0 to 1000000')
    if family not in FAMILIES:
        raise ValueError('unknown stellar family')
    if isinstance(depth_ppm, bool) or not isinstance(depth_ppm, (int, float)) or not np.isfinite(depth_ppm) or not 0 <= depth_ppm <= 5000:
        raise ValueError('depth_ppm must be finite and between 0 and 5000')
    rng = np.random.default_rng(seed)
    time = np.arange(0., 27., .03)
    # All random draws precede depth injection: paired depths share noise/gaps.
    period = rng.uniform(1.6, 5.2)
    epoch = rng.uniform(0, period)
    duty = rng.uniform(.035, .065)
    rotation = rng.uniform(7, 12)
    phase = rng.uniform(0, 2*np.pi)
    amplitude = .00025 if family == 'quiet' else .0035
    stellar = amplitude*(np.sin(2*np.pi*time/rotation + phase) + .25*np.sin(4*np.pi*time/rotation + .3))
    noise = rng.normal(0, .0008, len(time))
    keep = rng.random(len(time)) > (.3 if family == 'gapped' else .05)
    if family == 'gapped':
        keep &= ~((time > 11) & (time < 14))
    distance = np.abs((time-epoch+period/2) % period - period/2)
    # A trapezoid (20% ingress/egress), not the detector's ideal box.
    half = period*duty/2
    shape = np.clip((half-distance)/(.2*half), 0, 1)
    transit = -depth_ppm*1e-6*shape
    flux = 1 + stellar + noise + transit
    return LightCurve(time[keep], flux[keep], .0008,
                      dict(seed=int(seed), family=family, period_days=float(period), epoch_days=float(epoch),
                           duty_fraction=float(duty), depth_ppm=float(depth_ppm), kind='synthetic trapezoid'),
                      stellar[keep], transit[keep])
