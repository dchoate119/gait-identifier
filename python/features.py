"""Model 2 candidate features for one window of IMU samples.

Shared by the laptop notebooks and the board so both compute exactly the same
numbers. A window is an (n, 6) array: ax, ay, az (g), gx, gy, gz (deg/s).
"""

import numpy as np

FS = 50
BAND_HZ = (0.3, 4.0)     # where stride / pedal rates and their harmonics live
RHYTHM_HALF_HZ = 0.25    # width around the dominant frequency for rhythm strength
PAD = 1024               # zero-pad the FFT so the peak location is finer than 1/window

PAIRS = [("ax", "ay"), ("ay", "az"), ("ax", "az")]


def spectrum(x):
    """Power at each frequency of a signal, mean removed."""
    x = x - x.mean()
    power = np.abs(np.fft.rfft(x * np.hanning(len(x)), PAD)) ** 2
    freqs = np.fft.rfftfreq(PAD, 1 / FS)
    return freqs, power


def corr(a, b):
    sa, sb = a.std(), b.std()
    if sa == 0 or sb == 0:
        return 0.0
    return float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb))


def features(w):
    """Dict of candidate features for one (n, 6) window."""
    w = np.asarray(w, dtype=float)
    ax, ay, az, gx, gy, gz = w.T
    amag = np.sqrt(ax**2 + ay**2 + az**2)
    gmag = np.sqrt(gx**2 + gy**2 + gz**2)
    chans = {"ax": ax, "ay": ay, "az": az, "gx": gx, "gy": gy, "gz": gz}

    # Rhythm, from the shin axis (ay)
    freqs, power = spectrum(ay)
    band = (freqs >= BAND_HZ[0]) & (freqs <= BAND_HZ[1])
    dom = float(freqs[band][power[band].argmax()])
    near = np.abs(freqs - dom) <= RHYTHM_HALF_HZ
    total = power[freqs >= BAND_HZ[0]].sum()

    f = {
        "dom_hz": dom,
        "rhythm": float(power[near].sum() / total) if total > 0 else 0.0,
    }
    # Energy
    for name, x in chans.items():
        f[f"std_{name}"] = float(x.std())
    f["range_amag"] = float(amag.max() - amag.min())
    f["range_gmag"] = float(gmag.max() - gmag.min())
    # Shape
    f["jerk"] = float(np.abs(np.diff(amag)).mean() * FS)        # g/s
    d = amag - amag.mean()
    s = d.std()
    f["kurtosis"] = float((d**4).mean() / s**4) if s > 0 else 0.0
    # Orientation
    for name in ("ax", "ay", "az"):
        f[f"mean_{name}"] = float(chans[name].mean())
    # Coordination
    for a, b in PAIRS:
        f[f"corr_{a}_{b}"] = corr(chans[a], chans[b])
    return f


NAMES = list(features(np.random.default_rng(0).normal(size=(150, 6))).keys())
