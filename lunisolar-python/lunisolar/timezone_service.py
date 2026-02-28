"""TimezoneService — handles timezone conversions and CST date-only comparisons."""

from datetime import datetime, timedelta, date
from typing import Optional

from utils import setup_logging
from timezone_handler import TimezoneHandler


class TimezoneService:
    """Handles timezone conversions and CST date-only comparisons."""
    
    def __init__(self, timezone_handler: Optional[TimezoneHandler] = None):
        self.logger = setup_logging()
        self.tz_handler = timezone_handler or TimezoneHandler.create_cst_handler()
    
    def utc_to_cst_date(self, utc_datetime: datetime) -> date:
        """Convert UTC datetime to CST date for date-only comparisons."""
        cst_datetime = utc_datetime + timedelta(hours=8)
        return cst_datetime.date()
    
    def parse_local_datetime(self, date_str: str, time_str: str = "12:00") -> datetime:
        """Parse local date/time string to datetime object."""
        return self.tz_handler.parse_local_datetime(date_str, time_str)
    
    def local_to_utc(self, local_datetime: datetime) -> datetime:
        """Convert local datetime to UTC for astronomical calculations."""
        return self.tz_handler.local_to_utc(local_datetime)
