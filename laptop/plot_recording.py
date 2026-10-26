"""Plot one recording: full accel/gyro traces plus a 5 s zoom, and print a summary.

    python laptop/plot_recording.py data/walk_01.csv            # interactive window
    python laptop/plot_recording.py data/walk_01.csv out.png    # save instead
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ZOOM_S = 5.0
AXES = ("x", "y", "z")


def load(path):
    df = pd.read_csv(path)
    df["t"] = (df["t_ms"] - df["t_ms"].iloc[0]) / 1000.0
    df["amag"] = np.sqrt(df.ax**2 + df.ay**2 + df.az**2)
    return df


def summary(df, name):
    gaps = df["t_ms"].diff().dropna()
    duration = df["t"].iloc[-1]
    print(f"{name}: {len(df)} rows, {duration:.1f} s, {len(df) / duration:.1f} Hz")
    print(f"  gaps: median {gaps.median():.0f} ms, max {gaps.max():.0f} ms, >40 ms: {(gaps > 40).sum()}")
    for a in AXES:
        acc = df["a" + a]
        print(f"  a{a}: mean {acc.mean():6.2f} g, peak |a-mean| {(acc - acc.mean()).abs().max():5.2f} g"
              f" | g{a}: peak {df['g' + a].abs().max():6.0f} deg/s")


def plot(df, name):
    fig, axs = plt.subplots(2, 2, figsize=(14, 7), sharex="col",
                            gridspec_kw={"width_ratios": [3, 1]})
    mid = df["t"].iloc[-1] / 2                     # zoom window from the middle
    zoom = df[(df.t >= mid) & (df.t < mid + ZOOM_S)]

    for col, data in enumerate((df, zoom)):
        for a in AXES:
            axs[0, col].plot(data.t, data["a" + a], lw=0.8, label="a" + a)
            axs[1, col].plot(data.t, data["g" + a], lw=0.8, label="g" + a)
        axs[0, col].plot(data.t, data.amag, lw=0.8, color="k", alpha=0.5, label="|a|")
        axs[1, col].set_xlabel("time (s)")

    axs[0, 0].set_title(f"{name} — full")
    axs[0, 1].set_title(f"{ZOOM_S:.0f} s zoom")
    axs[0, 0].set_ylabel("accel (g)")
    axs[1, 0].set_ylabel("gyro (deg/s)")
    axs[0, 0].legend(loc="upper right", ncol=4)
    axs[1, 0].legend(loc="upper right", ncol=3)
    for ax in axs.flat:
        ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    df = load(path)
    summary(df, path.name)
    fig = plot(df, path.stem)
    if len(sys.argv) > 2:
        fig.savefig(sys.argv[2], dpi=110)
    else:
        plt.show()


if __name__ == "__main__":
    main()
