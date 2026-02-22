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

    @staticmethod
    def create_cst_handler() -> 'TimezoneHandler':
        """
        Create a timezone handler configured for China Standard Time.
        
        Returns:
            TimezoneHandler instance for CST (UTC+8)
        """
        return TimezoneHandler('Asia/Shanghai')