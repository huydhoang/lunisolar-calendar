"""Shared configuration constants for astronomical data calculations."""

import os
import multiprocessing as mp

# Configuration constants
EPHEMERIS_FILE = 'nasa/de440.bsp'
OUTPUT_DIR = 'output'
AU_TO_M = 149597870700.0
TIDAL_INTERVAL_MINUTES = 4
MANSION_COUNT = 28
MANSION_DEGREES = 360.0 / MANSION_COUNT
EARTH_RADIUS_KM = 6371.0
MOON_MASS_KG = 7.342e22
GRAVITATIONAL_CONSTANT = 6.67430e-11
GM_MOON = 4.902800118e12  # m³/s²
GM_SUN = 1.32712440018e20  # m³/s²

# Processing configuration
NUM_PROCESSES = mp.cpu_count()
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

# Default location (Ecopark)
DEFAULT_LOCATION = (20.95096127916524, 105.93959745655978)

# Celestial bodies configuration
CELESTIAL_BODIES = [
    ('Sun', 'sun'),
    ('Moon', 'moon'),
    ('Venus', 'venus'),
    ('Jupiter', 'jupiter barycenter'),
    ('Saturn', 'saturn barycenter')
]