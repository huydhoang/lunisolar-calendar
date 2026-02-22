"""Solar terms calculation module.

This module calculates the 24 traditional solar terms based on the sun's
position on the ecliptic between specified start and end dates.

Usage:
    python solar_terms.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD

Example:
    python solar_terms.py --start-date 2025-01-01 --end-date 2025-12-31
"""

from datetime import datetime
from typing import List, Tuple
from skyfield.api import utc, load
from skyfield import almanac, almanac_east_asia as almanac_ea
from config import EPHEMERIS_FILE
from utils import setup_logging, write_csv_file, parse_date_args

def calculate_solar_terms(start_time: datetime, end_time: datetime) -> List[Tuple[int, int, str, str, str]]:
    """Calculate solar terms between start and end times.
    
    Args:
        start_time: Start datetime for calculation
        end_time: End datetime for calculation
        
    Returns:
        List of tuples containing (unix_timestamp, index, zht, zhs, vn)
    """
    logger = setup_logging()
    try:
        ts = load.timescale()
        eph = load(EPHEMERIS_FILE)
        t0 = ts.from_datetime(start_time)
        t1 = ts.from_datetime(end_time)
        t, tm = almanac.find_discrete(t0, t1, almanac_ea.solar_terms(eph))
        results = []
        for tmi, ti in zip(tm, t):
            dt_obj = ti.utc_datetime()
            unix_timestamp = int(dt_obj.timestamp())
            idx = tmi
            zht = almanac_ea.SOLAR_TERMS_ZHT[idx] if hasattr(almanac_ea, 'SOLAR_TERMS_ZHT') else ''
            zhs = almanac_ea.SOLAR_TERMS_ZHS[idx] if hasattr(almanac_ea, 'SOLAR_TERMS_ZHS') else ''
            vn = almanac_ea.SOLAR_TERMS_VN[idx] if hasattr(almanac_ea, 'SOLAR_TERMS_VN') else ''
            results.append((unix_timestamp, idx, zht, zhs, vn))
        return results
    except Exception as e:
        logger.error(f"Error calculating solar terms: {e}")
        return []
    finally:
        if 'eph' in locals():
            del eph

def main():
    """Main function for solar terms calculation."""
    logger = setup_logging()
    args = parse_date_args()
    
    logger.info("☀️ Solar Terms Calculator")
    logger.info(f"Calculating solar terms from {args.start_date} to {args.end_date}")
    
    # Parse dates
    start_time = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=utc)
    end_time = datetime.strptime(args.end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=utc)
    
    # Calculate solar terms
    results = calculate_solar_terms(start_time, end_time)
    
    if results:
        # Convert to dictionary format for CSV writing
        data = [{'timestamp': timestamp, 'index': idx, 
                'traditional_chinese': zht, 'simplified_chinese': zhs, 
                'vietnamese': vn} 
               for timestamp, idx, zht, zhs, vn in results]
        
        # Write to CSV
        count = write_csv_file('solar_terms.csv', data, 
                             ['timestamp', 'index', 'traditional_chinese', 'simplified_chinese', 'vietnamese'])
        logger.info(f"✅ Successfully calculated {count} solar terms")
        logger.info(f"📄 Results saved to output/solar_terms.csv")
    else:
        logger.warning("⚠️ No solar terms found in the specified date range")

if __name__ == '__main__':
    main()