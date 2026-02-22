"""Moon phases calculation module.

This module calculates precise timings for New Moon and Full Moon phases
between specified start and end dates.

Usage:
    python moon_phases.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD

Example:
    python moon_phases.py --start-date 2025-01-01 --end-date 2025-12-31
"""

from datetime import datetime
from typing import List, Tuple
from skyfield.api import utc, load
from skyfield import almanac
from config import EPHEMERIS_FILE
from utils import setup_logging, write_csv_file, parse_date_args

def calculate_moon_phases(start_time: datetime, end_time: datetime) -> List[Tuple[int, int, str]]:
    """Calculate moon phases between start and end times.
    
    Args:
        start_time: Start datetime for calculation
        end_time: End datetime for calculation
        
    Returns:
        List of tuples containing (unix_timestamp, phase_index, phase_name)
    """
    logger = setup_logging()
    try:
        ts = load.timescale()
        eph = load(EPHEMERIS_FILE)
        t0 = ts.from_datetime(start_time)
        t1 = ts.from_datetime(end_time)
        t, y = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))
        results = []
        for ti, yi in zip(t, y):
            if yi in (0, 2):  # New Moon (0) and Full Moon (2)
                dt_obj = ti.utc_datetime()
                unix_timestamp = int(dt_obj.timestamp())
                phase_index = yi
                phase_name = almanac.MOON_PHASES[yi]
                results.append((unix_timestamp, phase_index, phase_name))
        return results
    except Exception as e:
        logger.error(f"Error calculating moon phases: {e}")
        return []
    finally:
        if 'eph' in locals():
            del eph

def main():
    """Main function for moon phases calculation."""
    logger = setup_logging()
    args = parse_date_args()
    
    logger.info("🌙 Moon Phases Calculator")
    logger.info(f"Calculating moon phases from {args.start_date} to {args.end_date}")
    
    # Parse dates
    start_time = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=utc)
    end_time = datetime.strptime(args.end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=utc)
    
    # Calculate moon phases
    results = calculate_moon_phases(start_time, end_time)
    
    if results:
        # Convert to dictionary format for CSV writing
        data = [{'timestamp': timestamp, 'phase_index': phase_index, 'phase': phase} 
                for timestamp, phase_index, phase in results]
        
        # Write to CSV
        count = write_csv_file('moon_phases.csv', data, ['timestamp', 'phase_index', 'phase'])
        logger.info(f"✅ Successfully calculated {count} moon phases")
        logger.info(f"📄 Results saved to output/moon_phases.csv")
    else:
        logger.warning("⚠️ No moon phases found in the specified date range")

if __name__ == '__main__':
    main()