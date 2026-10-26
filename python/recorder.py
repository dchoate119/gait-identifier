"""CSV recording: one file per Start->Stop, named <label>_<NN>.csv in data/.

Rows are the sketch's read_batch() lines, written as-is and flushed every batch.
"""

import time
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"   # /app/data on the board
HEADER = "t_ms,ax,ay,az,gx,gy,gz\n"
LABELS = ("still", "walk", "run", "bike")


class Recorder:
    def __init__(self):
        self.file = None
        self.path = None
        self.rows = 0
        self.started = 0.0

    @property
    def recording(self):
        return self.file is not None

    def start(self, label):
        if label not in LABELS:
            raise ValueError(f"unknown label {label!r}")
        self.stop()
        DATA_DIR.mkdir(exist_ok=True)
        self.path = next_free(label)
        self.file = open(self.path, "w")
        self.file.write(HEADER)
        self.rows = 0
        self.started = time.monotonic()
        print(f"recording {self.path.name}", flush=True)

    def write(self, lines):
        if not self.recording or not lines:
            return
        self.file.write("\n".join(lines) + "\n")
        self.file.flush()
        self.rows += len(lines)

    def stop(self):
        if not self.recording:
            return
        self.file.close()
        self.file = None
        print(f"saved {self.path.name}: {self.rows} rows, {self.elapsed():.1f} s", flush=True)

    def elapsed(self):
        return time.monotonic() - self.started if self.recording else 0.0

    def status(self):
        return {
            "recording": self.recording,
            "file": self.path.name if self.path else "",
            "rows": self.rows,
            "elapsed": round(self.elapsed(), 1),
        }


def next_free(label):
    """walk_01.csv, walk_02.csv, ... first number not already taken."""
    n = 1
    while (DATA_DIR / f"{label}_{n:02d}.csv").exists():
        n += 1
    return DATA_DIR / f"{label}_{n:02d}.csv"


def recordings():
    """Saved files, newest first, for the page's list."""
    files = sorted(DATA_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"file": p.name, "kb": round(p.stat().st_size / 1024)} for p in files]
