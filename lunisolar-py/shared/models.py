"""
Shared Data Models
==================

Data classes used across lunisolar, huangdao, and bazi packages.
"""

from datetime import datetime, date
from dataclasses import dataclass


@dataclass(frozen=True)
class PrincipalTerm:
    """Represents a principal solar term with UTC instant and CST date."""
    instant_utc: datetime
    cst_date: date
    term_index: int  # 1..12 for Z1..Z12


@dataclass
class MonthPeriod:
    """Represents a lunar month period with boundaries and term mapping."""
    index: int
    start_utc: datetime
    end_utc: datetime
    start_cst_date: date
    end_cst_date: date
    has_principal_term: bool = False
    is_leap: bool = False
    month_number: int = 0  # 1..12, with Zi month=11


@dataclass(frozen=True)
class LunisolarDateDTO:
    """Complete lunisolar date with stems, branches, and cycles."""
    year: int
    month: int
    day: int
    hour: int
    is_leap_month: bool
    year_stem: str
    year_branch: str
    month_stem: str
    month_branch: str
    day_stem: str
    day_branch: str
    hour_stem: str
    hour_branch: str
    year_cycle: int
    month_cycle: int
    day_cycle: int
    hour_cycle: int
