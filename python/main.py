"""Ring buffer check: pull batches from the sketch and report the rate every 5 s.

Expect ~50 Hz, max gap ~20 ms and 0 dropped.
"""

import time

from arduino.app_utils import App, Bridge

POLL_S = 0.2
REPORT_S = 5.0
MAX_BATCH = 50   # must match the sketch

received = 0
max_gap = 0
last_t = None
last_sample = ""
report_at = time.monotonic() + REPORT_S


def read_all():
    """Call read_batch until the sketch's buffer is empty."""
    lines = []
    while True:
        batch = Bridge.call("read_batch").splitlines()
        lines += batch
        if len(batch) < MAX_BATCH:
            return lines


def loop():
    global received, max_gap, last_t, last_sample, report_at
    try:
        lines = read_all()
    except Exception as e:  # sketch may not be ready yet
        print(f"waiting for sketch: {e}", flush=True)
        time.sleep(1)
        return

    for line in lines:
        t = int(line.split(",")[0])
        if last_t is not None:
            max_gap = max(max_gap, t - last_t)
        last_t = t
        last_sample = line
    received += len(lines)

    if time.monotonic() >= report_at:
        dropped = Bridge.call("imu_dropped")
        print(f"{received / REPORT_S:5.1f} Hz | max gap {max_gap} ms | "
              f"dropped {dropped} | last {last_sample}", flush=True)
        received = 0
        max_gap = 0
        report_at += REPORT_S

    time.sleep(POLL_S)


App.run(user_loop=loop)
