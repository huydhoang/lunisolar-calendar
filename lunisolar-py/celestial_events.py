"""Celestial events calculation module.

This module calculates rise, set, transit, and anti-transit times for
celestial bodies (Sun, Moon, planets) between specified start and end dates.

Usage:
    python celestial_events.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD [--lat LAT] [--lon LON]

Example:
    python celestial_events.py --start-date 2025-01-01 --end-date 2025-12-31
    python celestial_events.py --start-date 2025-01-01 --end-date 2025-12-31 --lat 40.7128 --lon -74.0060
"""

import argparse
from datetime import datetime
from typing import List, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
from skyfield.api import utc, load, wgs84
from skyfield import almanac
from skyfield.almanac import find_transits
from antitransit import find_antitransits
from config import EPHEMERIS_FILE, CELESTIAL_BODIES, DEFAULT_LOCATION, NUM_PROCESSES
from utils import setup_logging, write_csv_file

def calculate_body_events(body_data: Tuple[str, str], start_time: datetime, end_time: datetime, 
                         location_data: Tuple[float, float]) -> Tuple[str, List[Tuple[int, str, str]], int]:
    """Calculate rise, set, transit, and antitransit events for a celestial body.
    
    Args:
        body_data: Tuple of (body_name, body_key)
        start_time: Start datetime for calculation
        end_time: End datetime for calculation
        location_data: Tuple of (latitude, longitude)
        
    Returns:
        Tuple of (body_name, list of events with unix timestamps, event count)
    """
    logger = setup_logging()
    try:
        lat, lon = location_data
        ts = load.timescale()
        eph = load(EPHEMERIS_FILE)
        topo = eph['earth'] + wgs84.latlon(lat, lon)
        body_name, body_key = body_data
        body = eph[body_key]
        t0 = ts.from_datetime(start_time)
        t1 = ts.from_datetime(end_time)
        
        # Calculate different event types
        transit_times = find_transits(topo, body, t0, t1)
        antitransit_times = find_antitransits(topo, body, t0, t1)
        rise_times, _ = almanac.find_risings(topo, body, t0, t1)
        set_times, _ = almanac.find_settings(topo, body, t0, t1)
        
        results = []
        
        # Process transit events
        for t in transit_times:
            dt_obj = t.utc_datetime()
            unix_timestamp = int(dt_obj.timestamp())
            results.append((unix_timestamp, body_name, 'transit'))
            
        # Process antitransit events
        for t in antitransit_times:
            dt_obj = t.utc_datetime()
            unix_timestamp = int(dt_obj.timestamp())
            results.append((unix_timestamp, body_name, 'antitransit'))
            
        # Process rise events
        for t in rise_times:
            dt_obj = t.utc_datetime()
            unix_timestamp = int(dt_obj.timestamp())
            results.append((unix_timestamp, body_name, 'rise'))
            
        # Process set events
        for t in set_times:
            dt_obj = t.utc_datetime()
            unix_timestamp = int(dt_obj.timestamp())
            results.append((unix_timestamp, body_name, 'set'))
            
        return body_name, results, len(results)
    except Exception as e:
        logger.error(f"Error calculating events for {body_data[0]}: {e}")
        return body_data[0], [], 0
    finally:
        if 'eph' in locals():
            del eph

def calculate_all_celestial_events(start_time: datetime, end_time: datetime, 
                                  location_data: Tuple[float, float]) -> List[Tuple[int, str, str]]:
    """Calculate celestial events for all bodies using parallel processing.
    
    Args:
        start_time: Start datetime for calculation
        end_time: End datetime for calculation
        location_data: Tuple of (latitude, longitude)
        
    Returns:
        List of tuples containing (unix_timestamp, body_name, event_type)
    """
    logger = setup_logging()
    all_results = []
    total_events = 0
    
    with ProcessPoolExecutor(max_workers=min(NUM_PROCESSES, len(CELESTIAL_BODIES))) as executor:
        # Submit tasks for each celestial body
        futures = [executor.submit(calculate_body_events, body_data, start_time, end_time, location_data) 
                  for body_data in CELESTIAL_BODIES]
        
        # Collect results
        for future in as_completed(futures):
            try:
                body_name, results, count = future.result()
                all_results.extend(results)
                total_events += count
                logger.info(f"✓ {body_name}: {count:,} events calculated")
            except Exception as e:
                logger.error(f"❌ Events calculation failed for a body: {e}")
    
    # Sort results by timestamp
    all_results.sort(key=lambda x: x[0])
    logger.info(f"📊 Total celestial events processed: {total_events:,}")
    
    return all_results

def parse_args():
    """Parse command line arguments for celestial events calculation."""
    parser = argparse.ArgumentParser(description='Celestial Events Calculator.')
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
    """Main function for celestial events calculation."""
    logger = setup_logging()
    args = parse_args()
    
    logger.info("🌟 Celestial Events Calculator")
    logger.info(f"Calculating events from {args.start_date} to {args.end_date}")
    logger.info(f"Location: {args.lat:.6f}°N, {args.lon:.6f}°E")
    logger.info(f"Bodies: {', '.join([body[0] for body in CELESTIAL_BODIES])}")
    
    # Parse dates
    start_time = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=utc)
    end_time = datetime.strptime(args.end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=utc)
    location_data = (args.lat, args.lon)
    
    # Calculate celestial events
    results = calculate_all_celestial_events(start_time, end_time, location_data)
    
    if results:
        # Convert to dictionary format for CSV writing
        data = [{'timestamp': timestamp, 'body': body, 'event': event} 
                for timestamp, body, event in results]
        
        # Write to CSV
        count = write_csv_file('events.csv', data, ['timestamp', 'body', 'event'])
        logger.info(f"✅ Successfully calculated {count} celestial events")
        logger.info(f"📄 Results saved to output/events.csv")
        
        # Show sample events
        logger.info(f"🔍 Sample events (first 5):")
        for i, (timestamp, body, event) in enumerate(results[:5]):
            dt_obj = datetime.fromtimestamp(timestamp)
            logger.info(f"   {i+1}. {body}: {dt_obj.strftime('%Y-%m-%d %H:%M:%S')} - {event}")
    else:
        logger.warning("⚠️ No celestial events found in the specified date range")

if __name__ == '__main__':
    main()