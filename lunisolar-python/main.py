"""High-Performance Astronomical Data Calculator - Main Orchestrator

This script serves as the main orchestrator for calculating a focused set of astronomical
data points and events within a specified date range. It leverages parallel processing
to efficiently compute:

- **Lunar Phases**: Precise timings for New Moon and Full Moon.
- **Solar Terms**: The 24 solar terms based on the sun's position on the ecliptic.

The script imports calculation functions from modular components and coordinates their execution.
All generated data is saved as chunked JSON files under the 'output/json' directory, grouped by year.

Usage:
    python lunisolar-python/main.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD

Example:
    python lunisolar-python/main.py --start-date 2025-01-01 --end-date 2025-12-31
"""
import os
import time
import argparse
import multiprocessing as mp
from datetime import datetime, timedelta, timezone
from concurrent.futures import ProcessPoolExecutor, as_completed
from skyfield.api import utc
from typing import List, Dict, Any
from rich.console import Console

# Import modular calculation functions
from moon_phases import calculate_moon_phases
from solar_terms import calculate_solar_terms
from config import NUM_PROCESSES, OUTPUT_DIR
from utils import setup_logging, write_static_json

# Initialize Rich console
console = Console()

# Interactive selection removed for lean pipeline: only moon phases and solar terms

# All calculation functions have been moved to separate modules

# Setup logging
logger = setup_logging()

def main():
    """Main function with error handling and improved structure."""
    try:
        # Argument parsing
        parser = argparse.ArgumentParser(description='Astronomical Data Calculator.')
        parser.add_argument('--start-date', type=str, default='2024-01-01', help='Start date in YYYY-MM-DD format.')
        parser.add_argument('--end-date', type=str, default='2024-01-07', help='End date in YYYY-MM-DD format.')
        # Keeping arguments lean: no interactive selection, always generates moon phases and solar terms
        args = parser.parse_args()
        
        selected_files = ["moon_phases", "solar_terms"]

        # Header and configuration
        logger.info("\n" + "=" * 80)
        logger.info("🌙 ASTRONOMICAL DATA CALCULATOR")
        logger.info("   Parallel computation of celestial events, lunar phases, solar terms & tidal data")
        logger.info("=" * 80)
        logger.info(f"⚡ Processing Configuration:")
        logger.info(f"   • CPU cores utilized: {NUM_PROCESSES}")
        logger.info(f"   • Parallel tasks: Events, Moon Phases, Solar Terms, Tidal+Mansion Data")
        # Time and location setup - using UTC timezone
        start_time = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=utc)
        end_time = datetime.strptime(args.end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=utc)
        n_days = (end_time - start_time).days + 1
        logger.info(f"\n📅 Calculation Period:")
        logger.info(f"   • Duration: {n_days} days")
        logger.info(f"   • Start: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info(f"   • End: {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info("\n" + "-" * 80)
        # Parallel computation execution
        logger.info("🚀 Starting parallel calculations...")
        console.print(f"\n[green]📊 Generating moon phases and solar terms[/green]")
        total_start_time = time.time()
        
        num_workers = min(NUM_PROCESSES, 2)
        
        with ProcessPoolExecutor(max_workers=min(NUM_PROCESSES, num_workers)) as executor:
            # Submit tasks conditionally based on selection
            logger.info("   📡 Submitting calculation tasks...")
            futures = {}
            
            if "moon_phases" in selected_files:
                futures["moon_phases"] = executor.submit(calculate_moon_phases, start_time, end_time)
                logger.info("   🌙 Submitted moon phases calculation")
                
            if "solar_terms" in selected_files:
                futures["solar_terms"] = executor.submit(calculate_solar_terms, start_time, end_time)
                logger.info("   ☀️ Submitted solar terms calculation")
            # Collect results with progress tracking
            logger.info("   ⏳ Processing results...")
            
            # Initialize result variables
            moon_phases_results = []
            solar_terms_results = []
            
            # Collect results conditionally with error handling
            if "moon_phases" in selected_files:
                try:
                    moon_phases_results = futures["moon_phases"].result()
                    logger.info(f"   ✓ Moon phases: {len(moon_phases_results)} phases calculated")
                except Exception as e:
                    logger.error(f"   ❌ Moon phases calculation failed: {e}")
                    moon_phases_results = []
                
            if "solar_terms" in selected_files:
                try:
                    solar_terms_results = futures["solar_terms"].result()
                    logger.info(f"   ✓ Solar terms: {len(solar_terms_results)} terms calculated")
                except Exception as e:
                    logger.error(f"   ❌ Solar terms calculation failed: {e}")
                    solar_terms_results = []
        
            
        # Sort and prepare for output (results contain Unix timestamps)
        logger.info(f"\n💾 Building JSON output chunks...")
        # Helper to group by year (platform-independent, avoids time_t range issues)
        def year_from_ts(ts: int) -> int:
            try:
                ts_int = int(ts)
            except Exception:
                ts_int = int(float(ts))
            epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
            dt = epoch + timedelta(seconds=ts_int)
            return dt.year

        files_written = []
        moon_phase_count = 0
        solar_term_count = 0
        events_count = 0

        base_json_dir = os.path.join(OUTPUT_DIR, 'json')

        # Moon phases: split into new_moons and full_moons, store arrays of timestamps
        if "moon_phases" in selected_files and moon_phases_results:
            new_moons_by_year = {}
            full_moons_by_year = {}
            for timestamp, phase_index, _phase in moon_phases_results:
                y = year_from_ts(timestamp)
                if phase_index == 0:  # New Moon
                    new_moons_by_year.setdefault(y, []).append(int(timestamp))
                elif phase_index == 2:  # Full Moon
                    full_moons_by_year.setdefault(y, []).append(int(timestamp))
            # Write JSON per year
            for y, arr in sorted(new_moons_by_year.items()):
                path = os.path.join(base_json_dir, 'new_moons', f"{y}.json")
                count = write_static_json(path, arr)
                moon_phase_count += count
                if count:
                    files_written.append(path)
            for y, arr in sorted(full_moons_by_year.items()):
                path = os.path.join(base_json_dir, 'full_moons', f"{y}.json")
                count = write_static_json(path, arr)
                moon_phase_count += count
                if count:
                    files_written.append(path)

        # Solar terms: store compact pairs [timestamp, index]
        if "solar_terms" in selected_files and solar_terms_results:
            solar_terms_by_year = {}
            for timestamp, idx, *_names in solar_terms_results:
                y = year_from_ts(timestamp)
                solar_terms_by_year.setdefault(y, []).append([int(timestamp), int(idx)])
            for y, arr in sorted(solar_terms_by_year.items()):
                path = os.path.join(base_json_dir, 'solar_terms', f"{y}.json")
                count = write_static_json(path, arr)
                solar_term_count += count
                if count:
                    files_written.append(path)

        total_end_time = time.time()
        execution_time = total_end_time - total_start_time
        logger.info("\n" + "=" * 70)
        logger.info("🎯 ASTRONOMICAL DATA CALCULATION COMPLETED!")
        logger.info("=" * 70)
        logger.info(f"📈 Performance Metrics:")
        logger.info(f"   • Total execution time: {execution_time:.2f} seconds")
        logger.info(f"\n📁 JSON Output Files Generated:")
        if files_written:
            for file in files_written:
                logger.info(f"   • {file}")
        else:
            logger.info(f"   • No files generated (empty data or errors)")
            
        logger.info(f"\n📊 Data Summary:")
        if "moon_phases" in selected_files:
            logger.info(f"   • Moon phases (new+full) timestamps: {moon_phase_count:,}")
        if "solar_terms" in selected_files:
            logger.info(f"   • Solar terms items: {solar_term_count:,}")
            
        # Display Rich summary
        if files_written:
            console.print(f"\n[green]✅ Successfully generated {len(files_written)} file(s)![/green]")
            for file in files_written:
                console.print(f"   📄 {file}")
        else:
            console.print(f"\n[yellow]⚠️ No files generated - all workflows returned empty data or had errors[/yellow]")
        total_data_points = moon_phase_count + solar_term_count
        logger.info(f"\n⏱️  Calculation completed in {execution_time:.2f} seconds")
        logger.info(f"📈 Total data points generated: {total_data_points}")
        logger.info(f"🚀 Processing rate: {total_data_points/execution_time:.1f} data points/second")
        logger.info("\n✅ Done! Moon phases and solar terms calculations completed.")
        return True
    except Exception as e:
        logger.error(f"\n❌ Error during calculation: {e}")
        logger.error("Please check your input parameters and try again.")
        return False

if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)
    success = main()
    if not success:
        exit(1)