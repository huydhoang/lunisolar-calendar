# Gemini Project Context: Lunisolar-TS

## Project Overview

This project contains the Python implementation for a comprehensive, high-precision astronomical and astrological calculator focused on the traditional Chinese lunisolar calendar. The Python scripts serve two primary purposes:

1.  **Data Pipeline:** To generate high-precision astronomical data (e.g., moon phases, solar terms, planetary events) that will be consumed by a downstream TypeScript npm package.
2.  **Prototyping:** To serve as a reference implementation and prototype for the core calendar and Huangdao (Yellow Path) system logic.

The calculations are powered by the `skyfield` library and NASA's JPL DE440 ephemeris data, ensuring a high degree of accuracy.

The primary functions of this project are:

- **Lunisolar Calendar Conversion:** Converting Gregorian calendar dates to their lunisolar counterparts, including the correct year, month, day, and hour with their corresponding Heavenly Stems and Earthly Branches (Gan-Zhi).
- **Auspicious Day Calculation:** Implementing traditional Chinese day selection methods, including the "Twelve Construction Stars" (十二建星) and the "Great Yellow Path" (大黄道) systems.
- **Astronomical Data Generation:** Calculating various celestial events such as moon phases, solar terms, planetary rise/set times, tidal forces, and moon illumination percentages.

The architecture is modular, with specific calculations encapsulated in their own scripts within the `data/` directory. The system is designed for performance, utilizing multiprocessing to parallelize computations.

## Building and Running

### Virtual Environment

```bash
uv venv --python 3.12
Using CPython 3.12.9
Creating virtual environment at: .venv
Activate with: source .venv/Scripts/activate
```

### Dependencies

The project relies on several Python libraries. You can install them using pip. A `requirements.txt` file should be created with the following content:

```txt
skyfield
pytz
rich
InquirerPy
```

Install the dependencies with the following command:

```bash
uv pip install -r requirements.txt
```

### Running the Calculators

The project has two main entry points:

1.  **Main Data Orchestrator (`data/main.py`)**
    This script provides an interactive command-line interface to generate various astronomical data files.

    **Usage:**

    ```bash
    python data/main.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD
    ```

    - `--start-date`: The beginning of the calculation period.
    - `--end-date`: The end of the calculation period.
    - `--batch-mode`: (Optional) Runs without the interactive prompt and generates all available data files.

    The script will save the generated data into CSV files in an `output/` directory (which it will create if it doesn't exist).

2.  **Auspicious Days Calculator (`data/calculate_auspicious_days.py`)**
    This script provides a detailed daily analysis based on the integrated "Twelve Construction Stars" and "Great Yellow Path" systems.

    **Usage:**

    ```bash
    python data/calculate_auspicious_days.py --year YYYY --timezone TZ
    ```

    - `--year`: The year to analyze (e.g., 2025).
    - `--timezone`: (Optional) The timezone for calculations (e.g., `Asia/Ho_Chi_Minh`). Defaults to `Asia/Ho_Chi_Minh`.

    This script prints a formatted calendar and detailed daily information directly to the console.

## Development Conventions

- **Modularity:** The codebase is well-organized into modules, each with a specific responsibility (e.g., `moon_phases.py`, `solar_terms.py`). This separation of concerns makes the project maintainable and easy to extend.
- **Configuration:** A central `data/config.py` file is used to store shared constants like file paths, astronomical constants, and processing settings.
- **Documentation:** The code is extensively documented with detailed docstrings that not only explain the code's function but also the traditional Chinese calendar rules and astronomical principles behind the calculations. The `docs/` directory provides further in-depth explanations.
- **Data-Driven:** The calculations are driven by high-precision ephemeris data from NASA, located in the `nasa/` directory.
- **Clarity and Rules-Compliance:** The `data/lunisolar_v2.py` module is a prime example of the project's focus on correctly implementing the complex, nuanced rules of the traditional lunisolar calendar, such as the "no-zhongqi" rule for leap months and proper timezone handling (CST).

## Key Files

- `data/main.py`: The main entry point for generating bulk astronomical data.
- `data/huangdao_systems.py`: A comprehensive, standalone tool for calculating and displaying auspicious days based on the two traditional Chinese systems: Great Yellow Path (also referred to as the 12 Spirits) and the 12 Construction Stars (also referred to as the Lesser or Small Yellow Path).
- `data/lunisolar_v2.py`: A clean, modular, and rule-compliant engine for converting solar dates to the full lunisolar representation, including the sexagenary cycles (Gan-Zhi). It depends on `data/timezone_handler.py` for timezone handling.
- `data/config.py`: Contains all shared configuration variables and constants.
- `data/*.py`: Other files in this directory (`celestial_events.py`, `moon_phases.py`, `solar_terms.py`, etc.) are specialized modules for specific calculations.
- `docs/`: Contains essential documentation explaining the lunisolar calendar rules, including the two main Huangdao (Yellow Path) systems: the Great Yellow Path and the 12 Construction Stars.
- `nasa/de440.bsp`: The JPL ephemeris data file, which is the core data source for all astronomical calculations.
