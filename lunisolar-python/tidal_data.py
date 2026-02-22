"""Tidal data and lunar mansion calculation module.

This module calculates gravitational tidal acceleration vectors from the Sun and Moon
at a given location, along with lunar mansion positions at 4-minute intervals.

Usage:
    python tidal_data.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD [--lat LAT] [--lon LON]

Example:
    python tidal_data.py --start-date 2025-01-01 --end-date 2025-01-02
    python tidal_data.py --start-date 2025-01-01 --end-date 2025-01-02 --lat 40.7128 --lon -74.0060
"""

import argparse
from datetime import datetime, timedelta
from typing import List, Tuple
import numpy as np
from skyfield.api import utc, load, wgs84
from config import (EPHEMERIS_FILE, TIDAL_INTERVAL_MINUTES, MANSION_COUNT, 
                   MANSION_DEGREES, GM_MOON, GM_SUN, DEFAULT_LOCATION)
from utils import setup_logging, write_csv_file

def calculate_tidal_data(start_time: datetime, end_time: datetime, 
                        location_data: Tuple[float, float]) -> List[str]:
    """Calculate tidal acceleration and lunar mansion index at 4-minute intervals.
    
    Args:
        start_time: Start datetime for calculation
        end_time: End datetime for calculation
        location_data: Tuple of (latitude, longitude)
        
    Returns:
        List of CSV-formatted strings for each interval
    """
    logger = setup_logging()
    try:
        lat, lon = location_data
        ts = load.timescale()
        eph = load(EPHEMERIS_FILE)
        earth, moon, sun = eph['earth'], eph['moon'], eph['sun']
        topo = wgs84.latlon(lat, lon)
        observer = earth + topo
        
        time_diff_minutes = (end_time - start_time).total_seconds() / 60
        num_4min_points = int(time_diff_minutes / TIDAL_INTERVAL_MINUTES) + 1
        
        rows = []
        for i in range(num_4min_points):
            current_time = start_time + timedelta(minutes=TIDAL_INTERVAL_MINUTES) * i
            t = ts.from_datetime(current_time)
            
            # Get positions
            pos_earth_center = earth.at(t).position.m
            pos_observer = observer.at(t).position.m
            pos_moon = moon.at(t).position.m
            pos_sun = sun.at(t).position.m
            
            # Calculate relative positions
            r_obs = pos_observer - pos_earth_center 
            d_moon = pos_moon - pos_earth_center 
            d_sun = pos_sun - pos_earth_center 
            
            def tidal_acc(d_body, gm):
                """Calculate tidal acceleration for a celestial body."""
                r_body = np.linalg.norm(d_body)
                d_obs_to_body = d_body - r_obs
                r_obs_to_body = np.linalg.norm(d_obs_to_body)
                return gm * (d_obs_to_body / r_obs_to_body**3 - d_body / r_body**3)
            
            # Calculate tidal accelerations
            a_moon = tidal_acc(d_moon, GM_MOON)
            a_sun = tidal_acc(d_sun, GM_SUN)
            a_total = a_moon + a_sun
            magnitude = np.linalg.norm(a_total)
            
            # Calculate lunar mansion index
            pos = observer.at(t).observe(moon)
            lon_deg = pos.ecliptic_latlon()[1].degrees
            mansion_index = int(lon_deg // MANSION_DEGREES) + 1
            if mansion_index > MANSION_COUNT:
                mansion_index = 1
            
            # Convert datetime to timestamp
            timestamp = current_time.timestamp()
            rows.append(f"{timestamp},{a_total[0]:.12e},{a_total[1]:.12e},{a_total[2]:.12e},{magnitude:.12e},{lon_deg:.6f},{mansion_index}\n")
        
        return rows
    except Exception as e:
        logger.error(f"Error calculating tidal data: {e}")
        return []
    finally:
        if 'eph' in locals():
            del eph

def parse_args():
    """Parse command line arguments for tidal data calculation."""
    parser = argparse.ArgumentParser(description='Tidal Data and Lunar Mansion Calculator.')
    parser.add_argument('--start-date', type=str, default='2024-01-01', 
                       help='Start date in YYYY-MM-DD format.')
    parser.add_argument('--end-date', type=str, default='2024-01-07', 
                       help='End date in YYYY-MM-DD format.')
    parser.add_argument('--lat', type=float, default=DEFAULT_LOCATION[0],
                       help=f'Latitude (default: {DEFAULT_LOCATION[0]})')
    parser.add_argument('--lon', type=float, default=DEFAULT_LOCATION[1],
                       help=f'Longitude (default: {DEFAULT_LOCATION[1]})')
    return parser.parse_args()

def main():
    """Main function for tidal data calculation."""
    logger = setup_logging()
    args = parse_args()
    
    logger.info("🌊 Tidal Data & Lunar Mansion Calculator")
    logger.info(f"Calculating tidal data from {args.start_date} to {args.end_date}")
    logger.info(f"Location: {args.lat:.6f}°N, {args.lon:.6f}°E")
    logger.info(f"Interval: {TIDAL_INTERVAL_MINUTES} minutes")
    
    # Parse dates
    start_time = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=utc)
    end_time = datetime.strptime(args.end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=utc)
    location_data = (args.lat, args.lon)
    
    # Calculate tidal data
    rows = calculate_tidal_data(start_time, end_time, location_data)
    
    if rows:
        # Parse tidal data from CSV format to dictionary format
        data = []
        for row in rows:
            parts = row.strip().split(',')
            if len(parts) >= 7:
                data.append({
                    'timestamp': parts[0],
                    'tidal_acceleration_x': parts[1],
                    'tidal_acceleration_y': parts[2], 
                    'tidal_acceleration_z': parts[3],
                    'magnitude': parts[4],
                    'moon_ecliptic_longitude': parts[5],
                    'arabic_mansion_index': parts[6]
                })
        
        # Write to CSV
        count = write_csv_file('tidal_lunar_4min.csv', data, 
                             ['timestamp', 'tidal_acceleration_x', 'tidal_acceleration_y', 'tidal_acceleration_z', 
                              'magnitude', 'moon_ecliptic_longitude', 'arabic_mansion_index'])
        logger.info(f"✅ Successfully calculated {count:,} tidal data points")
        logger.info(f"📄 Results saved to output/tidal_lunar_4min.csv")
    else:
        logger.warning("⚠️ No tidal data calculated for the specified date range")

if __name__ == '__main__':
    main()