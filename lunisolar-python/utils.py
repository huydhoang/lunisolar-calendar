"""Shared utility functions for astronomical data calculations."""

import os
import csv
import sys
import json
import logging
from typing import List, Dict, Any
from config import OUTPUT_DIR

def setup_logging() -> logging.Logger:
    """Setup logging configuration.
    
    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Ensure StreamHandler uses UTF-8 encoding
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler):
            try:
                handler.setStream(sys.stdout)
                handler.stream.reconfigure(encoding='utf-8')
            except Exception:
                pass
    return logging.getLogger(__name__)

def write_csv_file(filename: str, data: List[Dict[str, Any]], headers: List[str]) -> int:
    """Write data to CSV file with proper directory creation and error handling.
    
    Args:
        filename: Name of the CSV file
        data: List of dictionaries to write
        headers: List of CSV column headers
        
    Returns:
        Number of rows written
    """
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        return len(data)
    except Exception as e:
        print(f"Error writing {filename}: {e}")
        return 0

def write_static_json(file_path: str, data: Any) -> int:
    """Write optimized static JSON data.

    This function ensures the parent directory exists and writes the provided
    data to a JSON file using compact separators to reduce file size.

    Args:
        file_path: Full path (including filename) for the JSON output
        data: JSON-serializable data structure (list or dict)

    Returns:
        Number of top-level items written (len(data) if list, 1 if dict)
    """
    try:
        parent_dir = os.path.dirname(file_path)
        os.makedirs(parent_dir, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        if isinstance(data, list):
            return len(data)
        return 1
    except Exception as e:
        print(f"Error writing {file_path}: {e}")
        return 0

def parse_date_args():
    """Parse common date arguments for individual modules.
    
    Returns:
        Parsed arguments with start_date and end_date
    """
    import argparse
    parser = argparse.ArgumentParser(description='Astronomical Data Calculator Module.')
    parser.add_argument('--start-date', type=str, default='2024-01-01', 
                       help='Start date in YYYY-MM-DD format.')
    parser.add_argument('--end-date', type=str, default='2024-01-07', 
                       help='End date in YYYY-MM-DD format.')
    return parser.parse_args()