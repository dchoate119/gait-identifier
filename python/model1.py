"""Model 1 live: peak of one axis over a sliding window -> most likely gait.

Uses the per-class mean/spread from model1.json (trained in laptop/model1.ipynb).
Every half window it classifies the last full window.
"""

import json
import math
from collections import deque
from pathlib import Path

COLUMNS = ["t_ms", "ax", "ay", "az", "gx", "gy", "gz"]   # sample layout from read_batch


class Model1:
    def __init__(self, path=Path(__file__).with_name("model1.json")):
        cfg = json.loads(path.read_text())
        self.col = COLUMNS.index(cfg["axis"])
        self.classes = cfg["classes"]                     # {name: {mean, sd}}
        n = int(cfg["window_s"] * cfg["fs"])
        self.window = deque(maxlen=n)
        self.step = n // 2
        self.new = 0

    def add(self, samples):
        """Feed parsed samples. Returns a prediction dict each half window, else None."""
        result = None
        for s in samples:
            self.window.append(s[self.col])
            self.new += 1
            if len(self.window) == self.window.maxlen and self.new >= self.step:
                self.new = 0
                result = self.classify()
        return result

    def classify(self):
        mean = sum(self.window) / len(self.window)
        peak = max(abs(v - mean) for v in self.window)
        # log of each class's bell curve height at this peak
        logs = {c: -math.log(p["sd"]) - 0.5 * ((peak - p["mean"]) / p["sd"]) ** 2
                for c, p in self.classes.items()}
        top = max(logs.values())
        weights = {c: math.exp(v - top) for c, v in logs.items()}
        total = sum(weights.values())
        probs = {c: round(w / total, 3) for c, w in weights.items()}
        return {"gait": max(probs, key=probs.get), "peak": round(peak, 2), "probs": probs}
