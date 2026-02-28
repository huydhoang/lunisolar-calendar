"""Moon phases calculation module — facade re-export.

Real code lives in ephemeris/moon_phases.py.
"""
from ephemeris.moon_phases import calculate_moon_phases, main

if __name__ == '__main__':
    main()