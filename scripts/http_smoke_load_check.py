#!/usr/bin/env python3
#!/usr/bin/env python3
import argparse
import os
import requests
import time
import sys
from statistics import mean


def percentile(values, p):
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values)-1) * (p / 100.0)
    f = int(k)
    c = min(f+1, len(values)-1)
    if f == c:
        return values[int(k)]
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return d0 + d1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iterations', type=int, default=10)
    ap.add_argument('--path', default='/')  # endpoint path if not root
    args = ap.parse_args()

    base = os.environ.get('LVS_SMOKE_BASE_URL', 'http://127.0.0.1:5000').rstrip('/')
    url = base + args.path

    durations_ms = []
    failures = []

    for i in range(args.iterations):
        start = time.perf_counter()
        try:
            r = requests.get(url, timeout=5)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            durations_ms.append(elapsed_ms)
            print(f"[{i+1}/{args.iterations}] {r.status_code} {elapsed_ms:.1f}ms")
            if not (200 <= r.status_code < 300):
                failures.append((i+1, r.status_code, r.text[:200]))
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            failures.append((i+1, 'exception', str(e)))
            print(f"[{i+1}/{args.iterations}] request failed after {elapsed_ms:.1f}ms: {e}")

    avg_ms = mean(durations_ms) if durations_ms else float('inf')
    p95_ms = percentile(durations_ms, 95)
    max_ms = max(durations_ms) if durations_ms else float('inf')

    print(f"\navg_ms: {avg_ms:.1f}")
    print(f"p95_ms: {p95_ms:.1f}")
    print(f"max_ms: {max_ms:.1f}\n")

    if failures:
        print("[FAIL] Non-2xx responses or errors detected:")
        for f in failures[:10]:
            print(" ", f)
    # thresholds (ms)
    if failures or avg_ms > 200.0 or p95_ms > 400.0:
        print("[FAIL] Smoke check failed (avg>200.0ms or p95>400.0ms or non-2xx responses).")
        sys.exit(1)
    else:
        print("[PASS] Smoke check passed.")
        sys.exit(0)


if __name__ == '__main__':
    main()
