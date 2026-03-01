"""Moon illumination calculation module.

This module calculates moon illumination percentage at 2-hour intervals
using vectorized approach for efficient computation.

Usage:
    python moon_illumination.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD

Example:
    python moon_illumination.py --start-date 2025-01-01 --end-date 2025-12-31
"""

from datetime import datetime, timedelta
from typing import List
import numpy as np
from skyfield.api import utc, load
from config import EPHEMERIS_FILE
from utils import setup_logging, write_csv_file, parse_date_args

def calculate_moon_illumination(start_time: datetime, end_time: datetime) -> List[str]:
    """
    Calculate moon illumination percentage at 2-hour intervals using vectorized approach.
    
    Args:
        start_time: Start datetime for calculation
        end_time: End datetime for calculation
    
    Returns:
        List of CSV-formatted strings for each interval
    """
    logger = setup_logging()
    try:
        ts = load.timescale()
        eph = load(EPHEMERIS_FILE)
        earth, moon, sun = eph['earth'], eph['moon'], eph['sun']
        
        # Calculate total time span and number of 2-hour intervals
        time_diff_hours = (end_time - start_time).total_seconds() / 3600
        num_intervals = int(time_diff_hours / 2) + 1
        
        # Determine optimal chunk size based on date range
        # For very long ranges (>10 years), use smaller chunks to manage memory
        total_days = (end_time - start_time).days
        if total_days > 3650:  # >10 years
            chunk_size = 4380  # ~1 year of 2-hour intervals
        elif total_days > 365:  # >1 year
            chunk_size = 8760  # ~2 years of 2-hour intervals
        else:
            chunk_size = min(num_intervals, 17520)  # ~4 years max or all intervals
        
        rows = []
        
        # Process in chunks for memory efficiency
        for chunk_start in range(0, num_intervals, chunk_size):
            chunk_end = min(chunk_start + chunk_size, num_intervals)
            
            # Generate datetime list for this chunk
            chunk_dates = []
            for i in range(chunk_start, chunk_end):
                current_time = start_time + timedelta(hours=2) * i
                if current_time <= end_time:
                    chunk_dates.append(current_time)
            
            if not chunk_dates:
                break
                
            # Vectorized calculation for the chunk
            t = ts.from_datetimes(chunk_dates)
            
            # Get positions for all times at once
            earth_pos = earth.at(t).position.km
            moon_pos = moon.at(t).position.km
            sun_pos = sun.at(t).position.km
            
            # Calculate vectors FROM MOON for all times
            moon_to_earth = earth_pos - moon_pos
            moon_to_sun = sun_pos - moon_pos
            
            # Calculate phase angle using vectorized operations
            dot_product = np.einsum('ij,ij->j', moon_to_earth, moon_to_sun)
            earth_magnitude = np.linalg.norm(moon_to_earth, axis=0)
            sun_magnitude = np.linalg.norm(moon_to_sun, axis=0)
            
            cos_phase_angle = dot_product / (earth_magnitude * sun_magnitude)
            cos_phase_angle = np.clip(cos_phase_angle, -1.0, 1.0)
            
            phase_angle = np.arccos(cos_phase_angle)
            
            # Convert to illumination percentage
            illumination_fraction = (1 + np.cos(phase_angle)) / 2
            illumination_percentage = illumination_fraction * 100
            
            # Convert to CSV format
            for i, (dt, illumination) in enumerate(zip(chunk_dates, illumination_percentage)):
                timestamp = dt.timestamp()
                rows.append(f"{timestamp},{illumination:.6f}\n")
        
        return rows
        
    except Exception as e:
        logger.error(f"Error calculating moon illumination: {e}")
        return []
    finally:
        if 'eph' in locals():
            del eph

def main():
    """Main function for moon illumination calculation."""
    logger = setup_logging()
    args = parse_date_args()
    
    logger.info("🌕 Moon Illumination Calculator")
    logger.info(f"Calculating moon illumination from {args.start_date} to {args.end_date}")
    logger.info("Interval: 2 hours")
    
    # Parse dates
    start_time = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=utc)
    end_time = datetime.strptime(args.end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=utc)
    
    # Calculate moon illumination
    rows = calculate_moon_illumination(start_time, end_time)
    
    if rows:
        # Parse moon illumination data from CSV format to dictionary format
        data = []
        for row in rows:
            parts = row.strip().split(',')
            if len(parts) >= 2:
                data.append({
                    'timestamp': parts[0],
                    'illumination_percentage': parts[1]
                })
        
        # Write to CSV
        count = write_csv_file('moon_illumination.csv', data, 
                             ['timestamp', 'illumination_percentage'])
        logger.info(f"✅ Successfully calculated {count:,} moon illumination data points")
        logger.info(f"📄 Results saved to output/moon_illumination.csv")
    else:
        logger.warning("⚠️ No moon illumination data calculated for the specified date range")

if __name__ == '__main__':
    main()