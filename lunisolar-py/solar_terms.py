"""Solar terms calculation module — facade re-export.

Real code lives in ephemeris/solar_terms.py.
"""
from ephemeris.solar_terms import calculate_solar_terms, main

if __name__ == '__main__':
    main()