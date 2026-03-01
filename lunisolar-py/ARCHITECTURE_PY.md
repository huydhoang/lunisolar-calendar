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
│   ├── glossary.py            # Authoritative bilingual Term tuples (pure reference data)
│   ├── constants.py         # Algorithm-facing lookup tables (derived from glossary)
│   ├── terminology.py       # format_term() display layer (falls through to glossary)
│   ├── core.py              # build_chart(), from_solar_date()
│   ├── ten_gods.py          # Ten Gods
│   ├── hidden_stems.py      # branch_hidden_with_roles()
│   ├── longevity.py         # Twelve Longevity Stages
│   ├── branch_interactions.py
│   ├── stem_transformations.py
│   ├── punishments.py       # Punishments, harms, fu-yin detection
│   ├── symbolic_stars.py    # Void branches, symbolic star detection
│   ├── structure.py         # Chart structure classification (格局)
│   ├── scoring.py           # Day master scoring, useful god recommendation
│   ├── nayin.py             # Na Yin five-element sounds
│   ├── luck_pillars.py
│   ├── annual_flow.py
│   ├── projections.py
│   ├── analysis.py          # comprehensive_analysis(), analyze_time_range()
│   ├── narrative.py         # generate_narrative()
│   ├── report.py            # Markdown report builder
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

## 5. Bazi Data Layer — Single-Responsibility Boundaries

The `bazi/` package has three data files with distinct, non-overlapping responsibilities.
`glossary.py` is the authoritative source; the other two derive from it.

```
glossary.py ──keys/sets──► constants.py
            └─TERMINOLOGY_LOOKUP──► terminology.py
```

### `glossary.py` — "What is this concept called?"

Authoritative bilingual reference. Every Bazi concept (structures, interactions,
punishments, stems, branches, etc.) is defined as a `Term` tuple:
`(chinese, pinyin, english, vietnamese)`.

- ~1,200 lines of pure data — **no imports from `bazi/`**, no computation.
- Provides keyed lookup dicts (`BRANCH_PAIR_TO_LIU_HE`, `SAN_HE_SET_TO_TERM`, etc.)
  whose keys are the canonical frozensets.
- Master lookup: `TERMINOLOGY_LOOKUP: Dict[str, Term]` maps any Chinese key → full tuple.

**Rule**: If you need to add a new Bazi concept (structure, interaction type, star, etc.),
define it here first as a `Term` tuple.

The name was originally `structure_constants.py` (created for structure classification data)
and renamed to `glossary.py` once scope expanded to cover all Bazi terminology.

### `constants.py` — "What data does the algorithm need?"

Algorithm-facing lookup tables consumed by 17+ computation modules.

- **Derived sets**: `LIU_HE`, `LIU_CHONG`, `SAN_HE`, `XING`, `STEM_TRANSFORMATIONS`, etc.
  are `frozenset` views extracted from `glossary` dict keys.
- **Unique data**: Element/polarity maps, hidden stems, longevity stages, symbolic star
  tables, scoring weights, void branch tables — data that has no bilingual Term equivalent.
- All public names are re-exported via `__init__.py` for backward compatibility.

**Rule**: Never duplicate a frozenset that already exists as a key in `glossary`.
Derive it instead.

### `terminology.py` — "How do we format a term for the user?"

Display formatting for CLI and report output.

- Local translation arrays: `STEM_TRANS`, `BRANCH_TRANS`, `TENGOD_TRANS`, `LIFESTAGE_TRANS`,
  `STAR_TRANS` — optimised for the stem/branch/ten-god terms that appear most often.
- `format_term(chinese_str, fmt)` renders any Chinese term as `"cn/py/en/vi"` or any
  subset. For 2-character GanZhi combinations, it auto-composes from stem + branch.
- **Fallthrough**: If a term isn't in the local arrays, `get_trans_tuple()` looks it up
  in `glossary.TERMINOLOGY_LOOKUP`, so all ~100+ terms there are automatically
  formattable.

**Rule**: Don't add translations to `terminology.py` for concepts that belong in
`glossary.py`. Only add here if the term is a high-frequency stem/branch/ten-god
that benefits from being in a flat local array.
