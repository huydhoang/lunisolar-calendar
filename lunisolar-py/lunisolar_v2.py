#!/usr/bin/env python3
"""
Lunisolar Calendar Engine v2 — Backward-compatible Facade
==========================================================

Real code lives in the ``lunisolar/`` package.  This file re-exports every
public name so that existing ``from lunisolar_v2 import ...`` statements
continue to work without modification.
"""

from shared.constants import HEAVENLY_STEMS, EARTHLY_BRANCHES, PRINCIPAL_TERMS
from shared.models import PrincipalTerm, MonthPeriod, LunisolarDateDTO

from lunisolar.api import (
    solar_to_lunisolar,
    solar_to_lunisolar_batch,
    get_stem_pinyin,
    get_branch_pinyin,
)
from lunisolar.timezone_service import TimezoneService
from lunisolar.window_planner import WindowPlanner
from lunisolar.ephemeris_service import EphemerisService
from lunisolar.month_builder import MonthBuilder, TermIndexer, LeapMonthAssigner
from lunisolar.sexagenary import SexagenaryEngine
from lunisolar.resolver import LunarMonthResolver, ResultAssembler


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Lunisolar Calendar Conversion v2')
    parser.add_argument('--date', type=str, required=True, help='Solar date in YYYY-MM-DD format')
    parser.add_argument('--time', type=str, default='12:00', help='Solar time in HH:MM format')
    parser.add_argument('--tz', type=str, default='Asia/Ho_Chi_Minh', help='IANA timezone name (e.g., Asia/Ho_Chi_Minh)')

    args = parser.parse_args()

    try:
        result = solar_to_lunisolar(args.date, args.time, args.tz)

        year_stem_pinyin = get_stem_pinyin((result.year_cycle - 1) % 10)
        year_branch_pinyin = get_branch_pinyin((result.year_cycle - 1) % 12)
        month_stem_pinyin = get_stem_pinyin((result.month_cycle - 1) % 10)
        month_branch_pinyin = get_branch_pinyin((result.month_cycle - 1) % 12)
        day_stem_pinyin = get_stem_pinyin((result.day_cycle - 1) % 10)
        day_branch_pinyin = get_branch_pinyin((result.day_cycle - 1) % 12)
        hour_stem_pinyin = get_stem_pinyin((result.hour_cycle - 1) % 10)
        hour_branch_pinyin = get_branch_pinyin((result.hour_cycle - 1) % 12)

        print(f"Solar: {args.date} {args.time}")
        print(f"Lunisolar: {result.year}-{result.month}-{result.day} {result.hour}:00")
        print(f"Leap month: {result.is_leap_month}")
        print(f"Year: {result.year_stem}{result.year_branch} ({year_stem_pinyin}{year_branch_pinyin}) [{result.year_cycle}]")
        print(f"Month: {result.month_stem}{result.month_branch} ({month_stem_pinyin}{month_branch_pinyin}) [{result.month_cycle}]")
        print(f"Day: {result.day_stem}{result.day_branch} ({day_stem_pinyin}{day_branch_pinyin}) [{result.day_cycle}]")
        print(f"Hour: {result.hour_stem}{result.hour_branch} ({hour_stem_pinyin}{hour_branch_pinyin}) [{result.hour_cycle}]")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)