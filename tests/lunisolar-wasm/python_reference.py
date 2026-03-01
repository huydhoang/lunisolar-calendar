#!/usr/bin/env python3
"""
Generate reference lunisolar + bazi results from the Python implementation (DE440s).

Reads a JSON array of Unix-epoch millisecond timestamps from stdin,
outputs a JSON array of results to stdout.

Usage:
    echo '[1705305000000, 1705391400000]' | python3 python_reference.py --tz Asia/Shanghai --gender male
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone
import pytz

# Set up path so we can import from lunisolar-py/
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "lunisolar-py"))

# Override config BEFORE importing lunisolar_v2
import config

config.EPHEMERIS_FILE = os.path.join(REPO_ROOT, "nasa", "de440s.bsp")

from lunisolar_v2 import solar_to_lunisolar
from huangdao_systems_v2 import HuangdaoCalculator
from bazi import (
    HEAVENLY_STEMS,
    EARTHLY_BRANCHES,
    STEM_ELEMENT,
    STEM_POLARITY,
    BRANCH_ELEMENT,
    build_chart,
    ten_god,
    changsheng_stage,
    life_stage_detail,
    nayin_for_cycle,
    detect_stem_combinations,
    detect_transformations,
    detect_punishments,
    score_day_master,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tz", default="Asia/Shanghai", help="IANA timezone")
    parser.add_argument(
        "--gender", default="male", help="Gender for bazi analysis (male/female)"
    )
    args = parser.parse_args()

    tz = pytz.timezone(args.tz)
    timestamps_ms = json.loads(sys.stdin.read())
    results = []

    huangdao = HuangdaoCalculator(args.tz)

    for ts_ms in timestamps_ms:
        # Convert UTC timestamp to local date/time in the target timezone
        dt_utc = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        dt_local = dt_utc.astimezone(tz)
        date_str = dt_local.strftime("%Y-%m-%d")
        time_str = dt_local.strftime("%H:%M")

        try:
            r = solar_to_lunisolar(date_str, time_str, args.tz, quiet=True)

            # Huangdao: construction star + great yellow path
            date_obj = datetime(dt_local.year, dt_local.month, dt_local.day)
            info = huangdao.calculate_day_info(date_obj, r)

            entry = {
                "tsMs": ts_ms,
                "lunarYear": r.year,
                "lunarMonth": r.month,
                "lunarDay": r.day,
                "isLeapMonth": r.is_leap_month,
                "yearStem": r.year_stem,
                "yearBranch": r.year_branch,
                "yearCycle": r.year_cycle,
                "monthStem": r.month_stem,
                "monthBranch": r.month_branch,
                "monthCycle": r.month_cycle,
                "dayStem": r.day_stem,
                "dayBranch": r.day_branch,
                "dayCycle": r.day_cycle,
                "hourStem": r.hour_stem,
                "hourBranch": r.hour_branch,
                "hourCycle": r.hour_cycle,
                "constructionStar": info["star"],
                "gypSpirit": info["gyp_spirit"],
                "gypPathType": info["gyp_path_type"],
            }

            # Bazi analysis
            chart = build_chart(
                r.year_cycle, r.month_cycle, r.day_cycle, r.hour_cycle, args.gender
            )
            dm_stem = chart["day_master"]["stem"]
            dm_elem = chart["day_master"]["element"]
            dm_idx = HEAVENLY_STEMS.index(dm_stem)
            day_master_strength_score, day_master_strength = score_day_master(chart)

            entry["bazi"] = {
                "dayMasterStem": dm_stem,
                "dayMasterElement": dm_elem,
                "dayMasterPolarity": STEM_POLARITY[dm_stem],
                "dayMasterStrengthScore": day_master_strength_score,
                "dayMasterStrength": day_master_strength,
                "tenGods": {
                    "year": ten_god(dm_idx, HEAVENLY_STEMS.index(r.year_stem)),
                    "month": ten_god(dm_idx, HEAVENLY_STEMS.index(r.month_stem)),
                    "day": "比肩",
                    "hour": ten_god(dm_idx, HEAVENLY_STEMS.index(r.hour_stem)),
                },
                "lifeStages": {},
                "naYin": {},
                "stemCombinations": [],
                "transformations": [],
                "punishments": [],
            }

            # Life stages for each pillar (Day Master's perspective)
            for pname, p in chart["pillars"].items():
                b_idx = EARTHLY_BRANCHES.index(p["branch"])
                ls = life_stage_detail(dm_idx, b_idx)
                entry["bazi"]["lifeStages"][pname] = {
                    "index": ls["index"],
                    "chinese": ls["chinese"],
                    "english": ls["english"],
                    "strengthClass": ls["strength_class"],
                }

            # Na Yin for each pillar
            for pname, cycle in [
                ("year", r.year_cycle),
                ("month", r.month_cycle),
                ("day", r.day_cycle),
                ("hour", r.hour_cycle),
            ]:
                ny = nayin_for_cycle(cycle)
                if ny:
                    nayin_elem = ny["nayin_element"]
                    if "(" in nayin_elem:
                        nayin_elem = nayin_elem.split("(")[0].strip()
                    entry["bazi"]["naYin"][pname] = {
                        "element": nayin_elem,
                        "chinese": ny["nayin_chinese"],
                        "english": ny["nayin_english"],
                    }

            # Stem combinations
            stem_combos = detect_stem_combinations(chart)
            for sc in stem_combos:
                entry["bazi"]["stemCombinations"].append(
                    {
                        "pair": sc["pair"],
                        "stems": sc["stems"],
                        "targetElement": sc["target_element"],
                    }
                )

            # Transformations (with conditions)
            transformations = detect_transformations(chart)
            for t in transformations:
                entry["bazi"]["transformations"].append(
                    {
                        "pair": t["pair"],
                        "stems": t["stems"],
                        "targetElement": t["target_element"],
                        "monthSupport": t["month_support"],
                        "leadingPresent": t["leading_present"],
                        "blocked": t["blocked"],
                        "severelyClashed": t["severely_clashed"],
                        "proximityScore": t["proximity_score"],
                        "status": t["status"],
                        "confidence": t["confidence"],
                    }
                )

            # Punishments & Harms
            punishments = detect_punishments(chart)
            for p in punishments:
                entry["bazi"]["punishments"].append(
                    {
                        "type": p["type"],
                        "pair": p["pair"],
                        "branches": p["branches"],
                        "severity": p["severity"],
                        "lifeAreas": p["life_areas"],
                    }
                )

            results.append(entry)
        except Exception as e:
            results.append({"tsMs": ts_ms, "error": str(e)})

    json.dump(results, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
