"""EphemerisService — single-pass computation of new moons and principal terms."""

from datetime import datetime, timedelta
from typing import List

from skyfield.api import utc

from utils import setup_logging
from solar_terms import calculate_solar_terms
from moon_phases import calculate_moon_phases
from shared.models import PrincipalTerm


class EphemerisService:
    """Single-pass computation of new moons and principal terms."""

    def __init__(self):
        self.logger = setup_logging()

    def compute_new_moons(self, start: datetime, end: datetime) -> List[datetime]:
        """Return sorted UTC instants of new moons in [start, end].
        One pass only per window."""
        try:
            if start.tzinfo is None:
                start_aware = start.replace(tzinfo=utc)
            else:
                start_aware = start

            if end.tzinfo is None:
                end_aware = end.replace(tzinfo=utc)
            else:
                end_aware = end

            phases = calculate_moon_phases(start_aware, end_aware)
            new_moons = []

            for timestamp, phase_index, phase_name in phases:
                if phase_index == 0:  # New moon
                    new_moon_dt = datetime.fromtimestamp(timestamp, tz=utc).replace(tzinfo=None)
                    new_moons.append(new_moon_dt)

            return sorted(new_moons)
        except Exception as e:
            self.logger.error(f"Error computing new moons: {e}")
            return []

    def compute_principal_terms(self, start: datetime, end: datetime) -> List[PrincipalTerm]:
        """Return principal terms (Z1..Z12) with UTC instants and CST dates
        precomputed for date-only mapping."""
        try:
            if start.tzinfo is None:
                start_aware = start.replace(tzinfo=utc)
            else:
                start_aware = start

            if end.tzinfo is None:
                end_aware = end.replace(tzinfo=utc)
            else:
                end_aware = end

            solar_terms = calculate_solar_terms(start_aware, end_aware)
            principal_terms = []

            for timestamp, idx, zht, zhs, vn in solar_terms:
                if idx % 2 == 0:
                    term_datetime = datetime.fromtimestamp(timestamp, tz=utc).replace(tzinfo=None)
                    principal_term_number = (idx // 2) + 1
                    if principal_term_number > 12:
                        principal_term_number -= 12

                    cst_date = (term_datetime + timedelta(hours=8)).date()

                    principal_terms.append(PrincipalTerm(
                        instant_utc=term_datetime,
                        cst_date=cst_date,
                        term_index=principal_term_number
                    ))

            return principal_terms
        except Exception as e:
            self.logger.error(f"Error computing principal terms: {e}")
            return []
