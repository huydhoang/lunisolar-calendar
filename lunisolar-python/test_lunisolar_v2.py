"""
Tests for the lunisolar calendar engine v2.

Validates lunar year calculation, month stems, and batch conversions
for dates before and after the Lunar New Year.

Note: These tests require the NASA DE440 ephemeris file and must be
run from the repository root directory (where nasa/de440.bsp exists).
"""

import unittest
import logging
import sys
import os

# Suppress all logging during tests
logging.disable(logging.CRITICAL)

# The ephemeris file path in config.py is relative to the repo root,
# so we need to ensure tests run from the correct working directory.
_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
_ORIG_CWD = os.getcwd()
os.chdir(_REPO_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lunisolar_v2 import solar_to_lunisolar, solar_to_lunisolar_batch


class TestLunarYearBeforeLunarNewYear(unittest.TestCase):
    """Dates before Lunar New Year should belong to the previous lunar year."""

    def test_jan_2000_is_year_1999(self):
        """Jan 15, 2000 is lunar month 12 of year 1999 (己卯, Rabbit)."""
        result = solar_to_lunisolar('2000-01-15', '12:00', 'Asia/Shanghai', quiet=True)
        self.assertEqual(result.year, 1999)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.year_stem, '己')
        self.assertEqual(result.year_branch, '卯')

    def test_jan_2025_is_year_2024(self):
        """Jan 20, 2025 is lunar month 12 of year 2024 (甲辰, Dragon)."""
        result = solar_to_lunisolar('2025-01-20', '12:00', 'Asia/Shanghai', quiet=True)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.year_stem, '甲')
        self.assertEqual(result.year_branch, '辰')


class TestLunarYearAfterLunarNewYear(unittest.TestCase):
    """Dates after Lunar New Year should belong to the current lunar year."""

    def test_feb_2025_is_year_2025(self):
        """Feb 15, 2025 is lunar month 1 of year 2025 (乙巳, Snake)."""
        result = solar_to_lunisolar('2025-02-15', '12:00', 'Asia/Shanghai', quiet=True)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.year_stem, '乙')
        self.assertEqual(result.year_branch, '巳')

    def test_mid_year_2025(self):
        """Jun 15, 2025 is still year 2025 (乙巳)."""
        result = solar_to_lunisolar('2025-06-15', '12:00', 'Asia/Shanghai', quiet=True)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.year_stem, '乙')
        self.assertEqual(result.year_branch, '巳')


class TestMonth11Year(unittest.TestCase):
    """Month 11 (Zi month) should return the correct lunar year."""

    def test_dec_1999_month_11(self):
        """Dec 15, 1999 is lunar month 11 of year 1999 (己卯)."""
        result = solar_to_lunisolar('1999-12-15', '12:00', 'Asia/Shanghai', quiet=True)
        self.assertEqual(result.year, 1999)
        self.assertEqual(result.month, 11)
        self.assertEqual(result.year_stem, '己')
        self.assertEqual(result.year_branch, '卯')


class TestMonthStemCorrectness(unittest.TestCase):
    """Month stems should be correct, derived from the correct year stem."""

    def test_month_12_stem_jan_2000(self):
        """Month 12 of year 1999 (己卯): month stem should be 丁, branch 丑."""
        result = solar_to_lunisolar('2000-01-15', '12:00', 'Asia/Shanghai', quiet=True)
        self.assertEqual(result.month_stem, '丁')
        self.assertEqual(result.month_branch, '丑')

    def test_month_11_stem_dec_1999(self):
        """Month 11 of year 1999 (己卯): month stem should be 丙, branch 子."""
        result = solar_to_lunisolar('1999-12-15', '12:00', 'Asia/Shanghai', quiet=True)
        self.assertEqual(result.month_stem, '丙')
        self.assertEqual(result.month_branch, '子')

    def test_month_12_stem_jan_2025(self):
        """Month 12 of year 2024 (甲辰): month stem should be 丁, branch 丑."""
        result = solar_to_lunisolar('2025-01-20', '12:00', 'Asia/Shanghai', quiet=True)
        self.assertEqual(result.month_stem, '丁')
        self.assertEqual(result.month_branch, '丑')


class TestBatchConversion(unittest.TestCase):
    """Batch conversion should produce the same results as individual calls."""

    def test_batch_january_dates(self):
        """Batch conversion for January dates should match individual calls."""
        dates = [('2000-01-15', '12:00'), ('2025-01-20', '12:00')]
        batch_results = solar_to_lunisolar_batch(dates, 'Asia/Shanghai', quiet=True)
        self.assertEqual(batch_results[0].year, 1999)
        self.assertEqual(batch_results[0].year_stem, '己')
        self.assertEqual(batch_results[0].year_branch, '卯')
        self.assertEqual(batch_results[1].year, 2024)
        self.assertEqual(batch_results[1].year_stem, '甲')
        self.assertEqual(batch_results[1].year_branch, '辰')


if __name__ == '__main__':
    unittest.main()
