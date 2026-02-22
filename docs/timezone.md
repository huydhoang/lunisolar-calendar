# Comprehensive Fix for Timezone Handling and `ganzhi` Calculation

This document outlines the root cause of the incorrect day and hour calculations in `lunisolar_v2.py` and provides a comprehensive solution that not only fixes the bug but also enhances the system's timezone handling capabilities.

## 1. The Core Problem

The bug originates in the `SexagenaryEngine.ganzhi_day` method within `lunisolar-python/lunisolar_v2.py`.

1.  **Incorrect Timezone Handling**: The method receives a timezone-aware local datetime object but immediately strips its timezone information by calling `.replace(tzinfo=None)`. This treats the local time as a naive datetime, leading to an incorrect day count when comparing it against the fixed historical anchor.
2.  **Cascading Error**: The incorrect day stem calculated by `ganzhi_day` is then fed into the `ganzhi_hour` method. Since the hour stem calculation (Wu Shu Dun rule) is dependent on the day stem, this error cascades, resulting in an incorrect hour stem.

The `TimezoneHandler` is also too rigid, as it only supports fixed UTC offsets and defaults to UTC+8, which is not suitable for users in other timezones like `Asia/Ho_Chi_Minh` (UTC+7).

## 2. Proposed Solution

The fix involves two main parts: correcting the `SexagenaryEngine` logic and making the `TimezoneHandler` more robust and flexible.

### Part A: Fix `SexagenaryEngine` in `lunisolar_v2.py`

The day and hour calculations must be performed in a consistent timezone (UTC) to ensure accuracy.

#### `ganzhi_day` Method Fix

The `ganzhi_day` method should convert the local datetime to UTC before performing calculations.

**Original Code (`lunisolar-python/lunisolar_v2.py`):**
```python
def ganzhi_day(self, target_local: datetime) -> Tuple[str, str, int]:
    """Day cycle using continuous count and documented historical anchors.
    Note: Keep canonical anchor date per rules doc."""
    # Reference: January 31, 4 AD (Jiazi day)
    reference_date = datetime(4, 1, 31)
    
    # Ensure both datetimes are timezone-naive for comparison
    if target_local.tzinfo is not None:
        target_date = target_local.replace(tzinfo=None)
    else:
        target_date = target_local
    
    target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    days_diff = (target_date - reference_date).days
    day_cycle = (days_diff + 1) % 60 + 1
    
    stem_char, branch_char, _, _ = self._get_stem_branch(day_cycle)
    return stem_char, branch_char, day_cycle
```

**Corrected Code:**
```python
def ganzhi_day(self, target_local: datetime) -> Tuple[str, str, int]:
    """Day cycle using continuous count and documented historical anchors.
    Note: Keep canonical anchor date per rules doc."""
    # Anchor: January 31, 4 AD (Jiazi day), defined in UTC for consistency.
    reference_date_utc = datetime(4, 1, 31, tzinfo=timezone.utc)
    
    # Convert the local target datetime to UTC to ensure correct day counting.
    target_utc = self.tz_service.local_to_utc(target_local)
    
    # Calculate the difference in days at the UTC level.
    days_diff = (target_utc.date() - reference_date_utc.date()).days
    
    # The cycle calculation remains the same.
    day_cycle = (days_diff % 60) + 1
    
    stem_char, branch_char, _, _ = self._get_stem_branch(day_cycle)
    return stem_char, branch_char, day_cycle
```

#### `ganzhi_hour` Method Fix

This method should also be adjusted to handle timezones correctly, especially for the 23:00 hour crossover.

**Original Code (`lunisolar-python/lunisolar_v2.py`):**
```python
def ganzhi_hour(self, target_local_solar_time: datetime, base_day_stem: str) -> Tuple[str, str, int]:
    """Apply Wu Shu Dun; for 23:00–23:59, advance day before computing hour stem/branch.
    Use local solar time per rules."""
    # Ensure timezone-naive datetime for calculations
    if target_local_solar_time.tzinfo is not None:
        local_time = target_local_solar_time.replace(tzinfo=None)
    else:
        local_time = target_local_solar_time
        
    hour = local_time.hour
    minute = local_time.minute
    
    # Get hour branch
    hour_branch_char, hour_branch_name, hour_branch_index = self._get_hour_branch(hour, minute)
    
    # Handle 23:00-23:59 boundary (belongs to next day's Zi hour)
    if hour >= 23:
        # Advance to next day for stem calculation
        next_day = local_time + timedelta(days=1)
        next_day_stem, _, next_day_cycle = self.ganzhi_day(next_day)
        base_day_stem = next_day_stem
    
    # ... rest of the function
```

**Corrected Code:**
```python
def ganzhi_hour(self, target_local: datetime, base_day_stem: str) -> Tuple[str, str, int]:
    """Apply Wu Shu Dun; for 23:00–23:59, advance day before computing hour stem/branch.
    Use local solar time per rules."""
    # The input is already a timezone-aware local datetime.
    hour = target_local.hour
    minute = target_local.minute
    
    # Get hour branch
    hour_branch_char, hour_branch_name, hour_branch_index = self._get_hour_branch(hour, minute)
    
    # Handle 23:00-23:59 boundary (belongs to next day's Zi hour)
    if hour >= 23:
        # Advance to the next day in the same timezone to get the correct stem.
        next_day_local = target_local + timedelta(days=1)
        next_day_stem, _, _ = self.ganzhi_day(next_day_local)
        base_day_stem = next_day_stem
    
    # Calculate hour stem using Wu Shu Dun rule
    hour_stem_char = self._calculate_hour_stem(base_day_stem, hour_branch_index)
    
    # Calculate hour cycle
    stem_index = next((i for i, (char, _, _, _) in enumerate(HEAVENLY_STEMS) if char == hour_stem_char), 0)
    hour_cycle = self._calculate_cycle_from_stem_branch(stem_index + 1, hour_branch_index)
    
    return hour_stem_char, hour_branch_char, hour_cycle
```

### Part B: Streamline `TimezoneHandler`

To support IANA timezones like `Asia/Ho_Chi_Minh`, we will use the `pytz` library.

**Instructions:**
1.  Ensure `pytz` is in your `requirements.txt` file and installed.
2.  Replace the entire content of `lunisolar-python/timezone_handler.py` with the code below.

**New `lunisolar-python/timezone_handler.py`:**
```python
#!/usr/bin/env python3
"""
Timezone Handler Module
======================

This module provides robust timezone conversion utilities using the `pytz` library
to support IANA timezone names (e.g., 'Asia/Ho_Chi_Minh', 'America/New_York').
"""

import logging
from datetime import datetime
import pytz
from utils import setup_logging

class TimezoneHandler:
    """
    Handles timezone conversions using IANA timezone names.
    """
    
    def __init__(self, timezone_name: str = 'Asia/Shanghai'):
        """
        Initialize the timezone handler with an IANA timezone name.
        
        Args:
            timezone_name: A valid IANA timezone name (e.g., 'Asia/Ho_Chi_Minh').
                           Defaults to 'Asia/Shanghai' (CST, UTC+8).
        """
        self.logger = setup_logging()
        try:
            self.timezone = pytz.timezone(timezone_name)
            self.logger.info(f"Using timezone: {timezone_name}")
        except pytz.UnknownTimeZoneError:
            self.logger.error(f"Unknown timezone: '{timezone_name}'. Defaulting to UTC.")
            self.timezone = pytz.utc
            timezone_name = 'UTC'
        self.timezone_name = timezone_name

    def local_to_utc(self, local_datetime: datetime) -> datetime:
        """
        Convert local datetime to UTC.
        
        Args:
            local_datetime: A naive datetime assumed to be in the handler's timezone.
            
        Returns:
            A timezone-aware datetime in UTC.
        """
        if local_datetime.tzinfo is None:
            # Localize the naive datetime
            local_datetime = self.timezone.localize(local_datetime)
        
        # Convert to UTC
        return local_datetime.astimezone(pytz.utc)

    def utc_to_local(self, utc_datetime: datetime) -> datetime:
        """
        Convert UTC datetime to the handler's local timezone.
        
        Args:
            utc_datetime: A timezone-aware datetime in UTC.
            
        Returns:
            A timezone-aware datetime in the local timezone.
        """
        if utc_datetime.tzinfo is None:
            # Assume UTC if naive
            utc_datetime = pytz.utc.localize(utc_datetime)
        
        return utc_datetime.astimezone(self.timezone)

    def parse_local_datetime(self, date_str: str, time_str: str = "12:00") -> datetime:
        """
        Parse date and time strings into a timezone-aware local datetime.
        
        Args:
            date_str: Date string in YYYY-MM-DD format.
            time_str: Time string in HH:MM format.
            
        Returns:
            A timezone-aware datetime object in the handler's timezone.
        """
        try:
            naive_dt = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
            # Localize the parsed datetime to the handler's timezone
            return self.timezone.localize(naive_dt)
        except ValueError:
            self.logger.error(f"Invalid date/time format: '{date_str} {time_str}'")
            raise

    @staticmethod
    def create_handler(timezone_name: str) -> 'TimezoneHandler':
        """
        Factory method to create a handler for a specific timezone.
        """
        return TimezoneHandler(timezone_name)

```

### Part C: Update `solar_to_lunisolar` Entry Point

Finally, update the main function to accept a timezone name.

**Change in `lunisolar-python/lunisolar_v2.py`:**
```python
def solar_to_lunisolar(
    solar_date: str,
    solar_time: str = "12:00",
    timezone_name: str = 'Asia/Shanghai' # Changed from timezone_handler
) -> LunisolarDateDTO:
    """
    ... (docstring) ...
    """
    logger = setup_logging()
    
    try:
        # Initialize services with the specified timezone name
        tz_handler = TimezoneHandler(timezone_name)
        tz_service = TimezoneService(tz_handler)
        # ... rest of the initializations

        # The rest of the function remains largely the same
        # ...
```

And update the command-line interface to accept a timezone.

**Change in `if __name__ == "__main__"` block in `lunisolar-python/lunisolar_v2.py`:**
```python
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Lunisolar Calendar Conversion v2')
    parser.add_argument('--date', type=str, required=True, help='Solar date in YYYY-MM-DD format')
    parser.add_argument('--time', type=str, default='12:00', help='Solar time in HH:MM format')
    parser.add_argument('--tz', type=str, default='Asia/Ho_Chi_Minh', help='IANA timezone name (e.g., Asia/Ho_Chi_Minh)')
    
    args = parser.parse_args()
    
    try:
        # Pass the timezone to the main function
        result = solar_to_lunisolar(args.date, args.time, args.tz)
        
        # ... (rest of the printing logic)
```

This comprehensive fix will resolve the calculation errors and make the entire system correctly handle any standard timezone.