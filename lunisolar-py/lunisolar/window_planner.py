"""WindowPlanner — plans calculation windows around Winter Solstice anchors."""

from datetime import datetime, timedelta
from typing import Tuple

from skyfield.api import load
from skyfield import almanac

from config import EPHEMERIS_FILE
from utils import setup_logging


class WindowPlanner:
    """Plans calculation windows around Winter Solstice anchors."""
    
    def __init__(self):
        self.logger = setup_logging()
    
    def compute_window(self, target_utc: datetime) -> Tuple[datetime, datetime]:
        """Return [start, end] window framing two consecutive Winter Solstices
        surrounding the target date, expanded by ±30 days to catch edge events."""
        if target_utc.tzinfo is not None:
            target_naive = target_utc.replace(tzinfo=None)
        else:
            target_naive = target_utc
            
        target_year = target_naive.year
        
        solstice_current = self._find_winter_solstice(target_year)
        solstice_prev = self._find_winter_solstice(target_year - 1)
        solstice_next = self._find_winter_solstice(target_year + 1)
        
        if target_naive >= solstice_current:
            anchor_start = solstice_current
            anchor_end = solstice_next
        else:
            anchor_start = solstice_prev
            anchor_end = solstice_current
        
        window_start = anchor_start - timedelta(days=30)
        window_end = anchor_end + timedelta(days=30)
        
        self.logger.debug(f"Computed window: {window_start} to {window_end}")
        return window_start, window_end
    
    def _find_winter_solstice(self, year: int) -> datetime:
        """Find Winter Solstice for a given year."""
        try:
            ts = load.timescale()
            eph = load(EPHEMERIS_FILE)
            
            t0 = ts.utc(year, 1, 1)
            t1 = ts.utc(year + 1, 1, 1)
            t, y = almanac.find_discrete(t0, t1, almanac.seasons(eph))
            
            for time, season in zip(t, y):
                if season == 3:  # Winter solstice
                    solstice_datetime = time.utc_datetime()
                    return solstice_datetime.replace(tzinfo=None)
            
            raise ValueError(f"Winter solstice not found for year {year}")
        except Exception as e:
            self.logger.error(f"Error finding winter solstice for {year}: {e}")
            raise
        finally:
            if 'eph' in locals():
                del eph
