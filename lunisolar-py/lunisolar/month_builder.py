"""MonthBuilder, TermIndexer, LeapMonthAssigner — month period construction pipeline."""

import logging
from datetime import datetime
from typing import List

from utils import setup_logging
from shared.models import PrincipalTerm, MonthPeriod
from .timezone_service import TimezoneService


class MonthBuilder:
    """Builds MonthPeriod objects from new moon sequences."""

    def __init__(self, timezone_service: TimezoneService):
        self.logger = setup_logging()
        self.tz_service = timezone_service

    def build_month_periods(self, new_moons: List[datetime]) -> List[MonthPeriod]:
        """Build consecutive MonthPeriods from successive new moon instants,
        carrying both UTC and CST date boundaries."""
        periods = []

        for i in range(len(new_moons) - 1):
            start_utc = new_moons[i]
            end_utc = new_moons[i + 1]

            start_cst_date = self.tz_service.utc_to_cst_date(start_utc)
            end_cst_date = self.tz_service.utc_to_cst_date(end_utc)

            period = MonthPeriod(
                index=i,
                start_utc=start_utc,
                end_utc=end_utc,
                start_cst_date=start_cst_date,
                end_cst_date=end_cst_date
            )
            periods.append(period)

        self.logger.debug(f"Built {len(periods)} month periods")
        return periods


class TermIndexer:
    """Maps principal terms to lunar months using date-only CST comparisons."""

    def __init__(self):
        self.logger = setup_logging()

    def tag_principal_terms(self, periods: List[MonthPeriod], terms: List[PrincipalTerm]) -> None:
        """For each term, find the MonthPeriod whose CST startDate <= term.cstDate < endDate.
        If term.cstDate == period.endCstDate, skip (belongs to next month).
        Set period.hasPrincipalTerm = True."""
        for term in terms:
            for period in periods:
                if period.start_cst_date <= term.cst_date < period.end_cst_date:
                    period.has_principal_term = True
                    self.logger.debug(f"Term Z{term.term_index} mapped to month period {period.index}")
                    break


class LeapMonthAssigner:
    """Assigns month numbers and leap status using no-zhongqi rule."""

    def __init__(self):
        self.logger = setup_logging()

    def assign_month_numbers(self, periods: List[MonthPeriod], anchor_solstice_utc: datetime) -> None:
        """Assign month numbers starting from Zi month (month 11).

        Strategy:
        1. Find the Zi month (contains Winter Solstice) and assign it number 11
        2. Iterate forward from Zi month through all subsequent periods:
           - Regular months (with principal term): increment month number (11->12->1->2->...)
           - Leap months (no principal term): take the preceding month's number
        """
        self.logger.info("=" * 80)
        self.logger.info("MONTH NUMBERING DEBUG - Starting month numbering process")
        self.logger.info("=" * 80)

        zi_month_index = self._find_zi_month(periods, anchor_solstice_utc)
        if zi_month_index == -1:
            raise ValueError("Could not find Zi month containing Winter Solstice")

        self.logger.info(f"Winter Solstice (Z11) at: {anchor_solstice_utc}")
        self.logger.info(f"Zi month (month 11) found at period index: {zi_month_index}")
        self.logger.info(f"  Period start: {periods[zi_month_index].start_cst_date}")
        self.logger.info(f"  Period end: {periods[zi_month_index].end_cst_date}")
        self.logger.info(f"  Has principal term: {periods[zi_month_index].has_principal_term}")

        # Assign Zi month
        periods[zi_month_index].month_number = 11
        periods[zi_month_index].is_leap = False

        # Assign subsequent months (forward pass)
        self.logger.info("\n" + "-" * 80)
        self.logger.info("FORWARD PASS - Assigning months after Zi month (11)")
        self.logger.info("-" * 80)

        current_month_number = 11
        for i in range(zi_month_index + 1, len(periods)):
            period = periods[i]

            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"FORWARD PASS - Processing period index {i}:")
            self.logger.info(f"{'='*60}")
            self.logger.info(f"  Period dates: {period.start_cst_date} to {period.end_cst_date}")
            self.logger.info(f"  Has principal term: {period.has_principal_term}")
            self.logger.info(f"  Current tracker (represents previous month number): {current_month_number}")

            if period.has_principal_term:
                old_value = current_month_number
                self.logger.info(f"\n  HAS PRINCIPAL TERM - This is a REGULAR month")
                self.logger.info(f"  Formula: ({old_value} % 12) + 1 = {(old_value % 12) + 1}")
                current_month_number = (current_month_number % 12) + 1
                period.month_number = current_month_number
                period.is_leap = False
                self.logger.info(f"  -> RESULT: Regular month {current_month_number} assigned")
            else:
                self.logger.info(f"\n  NO PRINCIPAL TERM - This is a LEAP month")
                period.month_number = current_month_number
                period.is_leap = True
                self.logger.info(f"  -> RESULT: Leap month {current_month_number} assigned")

        if zi_month_index > 0:
            self.logger.info("\n" + "-" * 80)
            self.logger.info(f"NOTE: {zi_month_index} period(s) before Zi month exist in window")
            self.logger.info("These are outside the calculation scope and remain unnumbered")
            self.logger.info("-" * 80)

        # Summary
        self.logger.info("\n" + "=" * 80)
        self.logger.info("FINAL MONTH NUMBERING SUMMARY")
        self.logger.info("=" * 80)
        for i, period in enumerate(periods):
            leap_indicator = "LEAP" if period.is_leap else "    "
            term_indicator = "Y" if period.has_principal_term else "N"
            self.logger.info(
                f"Period {i:2d}: Month {period.month_number:2d} [{leap_indicator}] "
                f"Term:{term_indicator} | {period.start_cst_date} to {period.end_cst_date}"
            )
        self.logger.info("=" * 80 + "\n")

    def _find_zi_month(self, periods: List[MonthPeriod], anchor_solstice_utc: datetime) -> int:
        """Find the month period that contains the Winter Solstice."""
        if anchor_solstice_utc.tzinfo is not None:
            solstice_naive = anchor_solstice_utc.replace(tzinfo=None)
        else:
            solstice_naive = anchor_solstice_utc

        for i, period in enumerate(periods):
            if period.start_utc <= solstice_naive < period.end_utc:
                return i
        return -1
