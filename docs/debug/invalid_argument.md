python lunisolar-python/main.py --start-date 1600-01-01 --end-date 2600-12-31
2025-10-07 12:59:56,154 - INFO -
================================================================================
2025-10-07 12:59:56,154 - INFO - 🌙 ASTRONOMICAL DATA CALCULATOR
2025-10-07 12:59:56,154 - INFO - Parallel computation of celestial events, lunar phases, solar terms & tidal data
2025-10-07 12:59:56,154 - INFO - ================================================================================
2025-10-07 12:59:56,154 - INFO - ⚡ Processing Configuration:
2025-10-07 12:59:56,154 - INFO - • CPU cores utilized: 12
2025-10-07 12:59:56,154 - INFO - • Parallel tasks: Events, Moon Phases, Solar Terms, Tidal+Mansion Data
2025-10-07 12:59:56,154 - INFO -
📅 Calculation Period:
2025-10-07 12:59:56,154 - INFO - • Duration: 365608 days
2025-10-07 12:59:56,154 - INFO - • Start: 1600-01-01 00:00:00 UTC
2025-10-07 12:59:56,154 - INFO - • End: 2600-12-31 23:59:59 UTC
2025-10-07 12:59:56,154 - INFO -

---

2025-10-07 12:59:56,154 - INFO - 🚀 Starting parallel calculations...

📊 Generating moon phases and solar terms
2025-10-07 12:59:56,154 - INFO - 📡 Submitting calculation tasks...
2025-10-07 12:59:56,170 - INFO - 🌙 Submitted moon phases calculation
2025-10-07 12:59:56,173 - INFO - ☀️ Submitted solar terms calculation
2025-10-07 12:59:56,174 - INFO - ⏳ Processing results...
2025-10-07 13:01:39,912 - INFO - ✓ Moon phases: 24761 phases calculated
2025-10-07 13:01:39,912 - INFO - ✓ Solar terms: 24024 terms calculated
2025-10-07 13:01:39,950 - INFO -
💾 Building JSON output chunks...
C:\Users\Huy\Downloads\code\lunisolar-ts\lunisolar-python\main.py:127: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
return datetime.utcfromtimestamp(int(ts)).year
C:\Users\Huy\Downloads\code\lunisolar-ts\lunisolar-python\main.py:129: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
return datetime.utcfromtimestamp(int(float(ts))).year
2025-10-07 13:01:39,950 - ERROR -
❌ Error during calculation: [Errno 22] Invalid argument
2025-10-07 13:01:39,951 - ERROR - Please check your input parameters and try again.
