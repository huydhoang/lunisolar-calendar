from skyfield import almanac
from math import pi

def _antitransit_ha(latitude, declination, altitude_radians):
    """Return hour angle for antitransit (opposite meridian crossing)."""
    return pi

def find_antitransits(observer, target, start_time, end_time):
    """
    Returns times when target crosses opposite meridian (antitransit).
    
    Example usage:
    ts = load.timescale()
    t0 = ts.utc(2023, 1, 1)
    t1 = ts.utc(2023, 1, 8)
    times = find_antitransits(observer, sun, t0, t1)
    """
    times, _ = almanac._find(observer, target, start_time, end_time, 0.0, _antitransit_ha)
    return times
