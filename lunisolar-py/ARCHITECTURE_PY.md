# Architecture: Python Implementation

## 1. Purpose

The Python implementation performs high-precision astronomical calculations (new moons, solar terms, sexagenary cycles, auspicious-day systems) using NASA's JPL DE440 ephemeris via Skyfield. It also exposes the full lunisolar calendar engine and the Bazi (Four Pillars) analysis framework as importable packages.

## 2. Package Structure

After the 2026-02-28 modular refactor, `lunisolar-py/` is organised into focused packages. Top-level `*.py` files are thin backward-compatible facades.

```
lunisolar-py/
├── shared/                  # Shared constants & dataclasses
│   ├── constants.py         # HEAVENLY_STEMS, EARTHLY_BRANCHES, PRINCIPAL_TERMS, derived lookups
│   └── models.py            # PrincipalTerm, MonthPeriod, LunisolarDateDTO
│
├── ephemeris/               # Low-level ephemeris wrappers
│   ├── solar_terms.py       # calculate_solar_terms()
│   └── moon_phases.py       # calculate_moon_phases()
│
├── lunisolar/               # Lunisolar calendar engine
│   ├── api.py               # solar_to_lunisolar(), solar_to_lunisolar_batch()
│   ├── ephemeris_service.py # EphemerisService — new moons & principal terms
│   ├── month_builder.py     # MonthBuilder, TermIndexer, LeapMonthAssigner
│   ├── sexagenary.py        # SexagenaryEngine — year/month/day/hour ganzhi
│   ├── resolver.py          # LunarMonthResolver, ResultAssembler
│   ├── timezone_service.py  # TimezoneService
│   ├── window_planner.py    # WindowPlanner
│   └── __main__.py          # python -m lunisolar
│
├── huangdao/                # Auspicious-day systems
│   ├── constants.py         # EarthlyBranch / GreatYellowPathSpirit enums, lookup tables
│   ├── construction_stars.py# ConstructionStars (12-star system)
│   ├── great_yellow_path.py # GreatYellowPath.calculate_spirit()
│   ├── calculator.py        # HuangdaoCalculator, print_month_calendar()
│   └── __main__.py          # python -m huangdao
│
├── bazi/                    # Four Pillars (Bazi) analysis
│   ├── core.py              # BaziChart
│   ├── ten_gods.py          # Ten Gods
│   ├── branch_interactions.py
│   ├── luck_pillars.py
│   ├── projections.py
│   └── cli.py / __main__.py
│
├── lunisolar_v2.py          # Facade → lunisolar package
├── huangdao_systems_v2.py   # Facade → huangdao package
├── solar_terms.py           # Facade → ephemeris.solar_terms
├── moon_phases.py           # Facade → ephemeris.moon_phases
├── utils.py                 # setup_logging(), write_csv_file(), …
├── config.py                # OUTPUT_DIR, ephemeris path
├── timezone_handler.py      # TimezoneHandler (pytz wrapper)
└── main.py                  # Bulk data generation orchestrator
```

## 3. Key Data Flows

**Lunisolar conversion** (`python -m lunisolar --date YYYY-MM-DD`):
1. `api.solar_to_lunisolar()` creates service objects and delegates to `LunarMonthResolver`.
2. `EphemerisService` loads `nasa/de440.bsp` via Skyfield and computes new moons + principal terms.
3. `MonthBuilder` assembles month periods; `LeapMonthAssigner` applies the no-zhongqi leap rule.
4. `SexagenaryEngine` derives year/month/day/hour ganzhi with the Wu Shu Dun rule.
5. `ResultAssembler` packages everything into a `LunisolarDateDTO`.

**Auspicious days** (`python -m huangdao -y YYYY -m MM`):
1. `HuangdaoCalculator` calls `solar_to_lunisolar_batch()` for each day in the month.
2. `ConstructionStars.get_star()` looks up the 12-building-star for each day.
3. `GreatYellowPath.calculate_spirit()` derives the Yellow/Black Path spirit from the day's branch.
4. `print_month_calendar()` renders the combined table to stdout.

## 4. Shared Constants & Models (`shared/`)

All packages import canonical data from `shared/` rather than defining local copies:

| Symbol | Description |
|---|---|
| `HEAVENLY_STEMS` | Tuple of 10 stem objects with char, pinyin, element, polarity |
| `EARTHLY_BRANCHES` | Tuple of 12 branch objects with char, pinyin, animal, element |
| `PRINCIPAL_TERMS` | List of 12 principal solar terms (zhongqi) |
| `STEM_CHARS` / `BRANCH_CHARS` | Plain character lists derived from the above |
| `BRANCH_INDEX` | `{char: index}` lookup |
| `EARTHLY_BRANCH_PINYIN` | `{char: pinyin}` lookup |
| `LunisolarDateDTO` | Frozen dataclass — canonical conversion result |
