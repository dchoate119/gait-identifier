"""Model 2 live: IMU features over a sliding window -> logistic regression.

Uses the scaler and weights from model2.json (trained in
laptop/model2/model2.ipynb) and the shared feature code in features.py.
Every half window it classifies the last full window.
"""

import json
from collections import deque
from pathlib import Path

import numpy as np

from features import features


class Model2:
    def __init__(self, path=Path(__file__).with_name("model2.json")):
        cfg = json.loads(path.read_text())
        self.names = cfg["features"]
        self.classes = cfg["classes"]
        self.mean = np.array(cfg["scaler_mean"])
        self.scale = np.array(cfg["scaler_scale"])
        self.coef = np.array(cfg["coef"])            # (classes, features)
        self.intercept = np.array(cfg["intercept"])
        n = int(cfg["window_s"] * cfg["fs"])
        self.window = deque(maxlen=n)
        self.step = 12   # predict every 0.24 s at 50 Hz
        self.new = 0

    def add(self, samples):
        """Feed parsed samples. Returns a prediction dict each half window, else None."""
        result = None
        for s in samples:
            self.window.append(s[1:7])               # drop t_ms: ax, ay, az, gx, gy, gz
            self.new += 1
            if len(self.window) == self.window.maxlen and self.new >= self.step:
                self.new = 0
                result = self.classify()
        return result

    def classify(self):
        f = features(np.array(self.window))
        x = (np.array([f[k] for k in self.names]) - self.mean) / self.scale
        scores = self.coef @ x + self.intercept
        p = np.exp(scores - scores.max())
        p /= p.sum()
        probs = {c: round(float(v), 3) for c, v in zip(self.classes, p)}
        return {"model": 2, "gait": max(probs, key=probs.get), "probs": probs,
                "features": {k: round(f[k], 3) for k in self.names}}
