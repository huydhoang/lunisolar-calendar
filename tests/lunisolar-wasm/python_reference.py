#!/usr/bin/env python3
"""
Generate reference lunisolar results from the Python implementation (DE440s).

Reads a JSON array of Unix-epoch millisecond timestamps from stdin,
outputs a JSON array of results to stdout.

Usage:
    echo '[1705305000000, 1705391400000]' | python3 python_reference.py --tz Asia/Shanghai
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone
import pytz

# Set up path so we can import from lunisolar-python/
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(REPO_ROOT, 'lunisolar-python'))

# Override config BEFORE importing lunisolar_v2
import config
config.EPHEMERIS_FILE = os.path.join(REPO_ROOT, 'nasa', 'de440s.bsp')

from lunisolar_v2 import solar_to_lunisolar
from huangdao_systems_v2 import HuangdaoCalculator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tz', default='Asia/Shanghai', help='IANA timezone')
    args = parser.parse_args()

    tz = pytz.timezone(args.tz)
    timestamps_ms = json.loads(sys.stdin.read())
    results = []

    huangdao = HuangdaoCalculator(args.tz)

    for ts_ms in timestamps_ms:
        # Convert UTC timestamp to local date/time in the target timezone
        dt_utc = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        dt_local = dt_utc.astimezone(tz)
        date_str = dt_local.strftime('%Y-%m-%d')
        time_str = dt_local.strftime('%H:%M')

        try:
            r = solar_to_lunisolar(date_str, time_str, args.tz, quiet=True)

            # Huangdao: construction star + great yellow path
            date_obj = datetime(dt_local.year, dt_local.month, dt_local.day)
            info = huangdao.calculate_day_info(date_obj, r)

            results.append({
                'tsMs': ts_ms,
                'lunarYear': r.year,
                'lunarMonth': r.month,
                'lunarDay': r.day,
                'isLeapMonth': r.is_leap_month,
                'yearStem': r.year_stem,
                'yearBranch': r.year_branch,
                'yearCycle': r.year_cycle,
                'monthStem': r.month_stem,
                'monthBranch': r.month_branch,
                'monthCycle': r.month_cycle,
                'dayStem': r.day_stem,
                'dayBranch': r.day_branch,
                'dayCycle': r.day_cycle,
                'hourStem': r.hour_stem,
                'hourBranch': r.hour_branch,
                'hourCycle': r.hour_cycle,
                'constructionStar': info['star'],
                'gypSpirit': info['gyp_spirit'],
                'gypPathType': info['gyp_path_type'],
            })
        except Exception as e:
            results.append({'tsMs': ts_ms, 'error': str(e)})

    json.dump(results, sys.stdout, ensure_ascii=False)


if __name__ == '__main__':
    main()
