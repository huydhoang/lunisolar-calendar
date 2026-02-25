#!/usr/bin/env python3
"""
Python lunisolar batch benchmark.

Measures throughput of solar_to_lunisolar_batch() for contiguous date ranges,
matching the scenarios used in benchmark-range.mjs.

Usage:  python3 benchmark-batch.py
Outputs: python-batch-benchmark-report.md
"""

import time
import sys
import os
from datetime import date, timedelta

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(REPO_ROOT, 'lunisolar-python'))

import config
config.EPHEMERIS_FILE = os.path.join(REPO_ROOT, 'nasa', 'de440s.bsp')

from lunisolar_v2 import solar_to_lunisolar_batch

WARMUP = 2
ITERS = 5
TZ = 'Asia/Shanghai'


def bench(fn, iters=ITERS, warmup=WARMUP):
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(iters):
        t0 = time.perf_counter()
        result = fn()
        times.append((time.perf_counter() - t0) * 1000)
    return {
        'mean_ms': sum(times) / len(times),
        'min_ms': min(times),
        'max_ms': max(times),
        'result': result,
    }


scenarios = [
    {'name': '30-day range',    'start': '2025-01-01', 'end': '2025-01-30'},
    {'name': 'Full-year range', 'start': '2025-01-01', 'end': '2025-12-31'},
]

md = '# Python Batch Benchmark — solar_to_lunisolar_batch()\n\n'
md += 'Measures throughput of `solar_to_lunisolar_batch()` for contiguous date ranges.\n'
md += 'Ephemeris data (DE440s) is computed once per batch.\n\n'
md += f'**Warmup:** {WARMUP} iterations | **Measured:** {ITERS} iterations (mean of {ITERS})\n\n'

for s in scenarios:
    start = date.fromisoformat(s['start'])
    end = date.fromisoformat(s['end'])
    n = (end - start).days + 1
    date_range = [((start + timedelta(days=i)).isoformat(), '12:00') for i in range(n)]

    print(f'\nRunning "{s["name"]}" benchmark...')
    print(f'  Range: {s["start"]} → {s["end"]} ({n} days)')

    try:
        r = bench(lambda: solar_to_lunisolar_batch(date_range, TZ, quiet=True))
        print(f'  Python: {r["mean_ms"]:.1f} ms ({n} dates)')

        md += f'## {s["name"]} ({n} days)\n\n'
        md += '| Implementation | Mean (ms) | Min (ms) | Max (ms) | Dates |\n'
        md += '|----------------|----------:|---------:|---------:|------:|\n'
        md += (f'| Python (solar_to_lunisolar_batch) |'
               f' {r["mean_ms"]:.1f} | {r["min_ms"]:.1f} | {r["max_ms"]:.1f} | {n} |\n\n')
    except Exception as err:
        print(f'  Python: ERROR - {err}', file=sys.stderr)
        md += f'## {s["name"]} ({n} days)\n\n'
        md += f'**Error:** {err}\n\n'

report_path = os.path.join(os.path.dirname(__file__), 'python-batch-benchmark-report.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(md)
print(f'\nReport written to {report_path}')
