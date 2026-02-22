# Implementation Plan: Lunisolar Calendar System

This document outlines a phased development plan to complete the Python data pipeline and implement the TypeScript npm package.

---

## Phase 1: Finalize and Productionize the Python Data Pipeline

**Goal:** To create a robust, automated pipeline that generates all necessary high-precision astronomical data in its final, optimized format.

- **Task 1.1: Refactor for JSON Output**

  - Create a new utility function in `utils.py` named `write_static_json(file_path, data)`.
  - Modify the `main.py` orchestrator to call this function instead of `write_csv_file`.
  - Implement the data chunking logic. The orchestrator should group data by year and call `write_static_json` for each year, creating the specified directory structure (`output/{data_type}/{year}.json`).

- **Task 1.2: Create `requirements.txt`**

  - Generate a `requirements.txt` file in the project root to formalize dependencies. It should include `skyfield`, `pytz`, `rich`, and `InquirerPy`.

- **Task 1.3: Generate Production Data**

  - Run the finalized pipeline for a comprehensive date range (e.g., 1900-2100).
  - Verify that the JSON files are created correctly in the `output/` directory. This generated data will be bundled with the TypeScript package.

- **Task 1.4: Add Pipeline Documentation**
  - Create a `README.md` file inside the `lunisolar-python/` directory.
  - Document the purpose of the pipeline, how to install dependencies from `requirements.txt`, and the command to run `main.py` to regenerate the data.

---

## Phase 2: TypeScript NPM Package Scaffolding

**Goal:** To set up a modern, professional TypeScript project environment with all necessary tools for development, testing, and publishing.

- **Task 2.1: Initialize Project**

  - Create a new directory for the package (e.g., `pkg/`).
  - Run `npm init -y` inside `pkg/`.
  - Install TypeScript and create a `tsconfig.json` file with strict type checking enabled.
  - Create the `src/` directory for all source code.

- **Task 2.2: Configure Build and Linting Tools**

  - Install development dependencies: `rollup` for bundling, `eslint` for linting, and `prettier` for code formatting.
  - Configure the bundler to output CommonJS and ES Module formats.
  - Set up ESLint and Prettier configuration files to enforce a consistent code style.

- **Task 2.3: Define Core Types**
  - Create a central `src/types.ts` file.
  - Define all public-facing interfaces and types as specified in the architecture document (e.g., `TLunisolarDate`, `TConstructionStar`, `TGreatYellowPathSpirit`).

---

## Phase 3: Implement Core TypeScript Logic

**Goal:** To build the foundational modules of the calendar package that handle data loading, timezone conversion, and the core lunisolar calculations.

- **Task 3.1: Implement `DataLoader`**

  - Create `src/data/DataLoader.ts`.
  - Implement the `getNewMoons(year)` and `getSolarTerms(year)` methods.
  - These methods will use the `fetch` API to dynamically import the required JSON data chunk from the `dist/data/` directory (where the data will be after bundling).
  - Implement an in-memory cache (`private _cache = new Map<string, any>();`) to avoid re-fetching data.

- **Task 3.2: Implement `TimezoneHandler`**

  - Create `src/timezone/TimezoneHandler.ts`.
  - Implement the class to wrap the `Intl.DateTimeFormat` API for accurate, lightweight timezone conversions without external libraries.

- **Task 3.3: Implement `LunisolarCalendar` Core**
  - Create `src/core/LunisolarCalendar.ts`.
  - Implement the `fromSolarDate` static factory method. This method will orchestrate calls to the `DataLoader` and `TimezoneHandler`.
  - Translate the core logic from the Python prototype (`lunisolar_v2.py` and `calculate_auspicious_days.py`) to TypeScript, strictly adhering to the rules in `docs/lunisolar_calendar_rules.md`. This includes:
    - Finding the correct lunar month based on new moon data.
    - Applying the "no-zhongqi" rule to identify leap months.
    - Calculating the lunar day number.
    - Implementing the Gan-Zhi (Stem-Branch) calculations for the year, month, day, and hour, including the 23:00 hour boundary rule.

---

## Phase 4: Implement Huangdao (Yellow Path) Systems

**Goal:** To build the astrological modules that consume the core calendar data.

- **Task 4.1: Implement `ConstructionStars` Module**

  - Create `src/huangdao/ConstructionStars.ts`.
  - The constructor will accept an instance of `LunisolarCalendar`.
  - Implement the `getStar()` method by porting the calculation logic from the Python prototype.

- **Task 4.2: Implement `GreatYellowPath` Module**
  - Create `src/huangdao/GreatYellowPath.ts`.
  - The constructor will also accept an instance of `LunisolarCalendar`.
  - Implement the `getSpirit()` method based on the Python prototype's logic, which uses the lunar month to determine the starting position of the Azure Dragon.

---

## Phase 5: Testing, Documentation, and Validation

**Goal:** To ensure the package is accurate, reliable, and easy for other developers to use.

- **Task 5.1: Set Up Testing Environment**

  - Install and configure a testing framework like `Jest` or `Vitest`.

- **Task 5.2: Write Comprehensive Unit Tests**

  - Create test files for each module (`DataLoader.test.ts`, `LunisolarCalendar.test.ts`, etc.).
  - Validate the `LunisolarCalendar` output against the Python prototype for a wide range of dates.
  - Write specific tests for known edge cases: leap years, leap months, year boundaries (Jan 1st), and the 23:00-23:59 hour rule.

- **Task 5.3: Create API and User Documentation**
  - Write TSDoc comments for all public classes, methods, and types.
  - Generate a static HTML API reference using a tool like `TypeDoc`.
  - Write a comprehensive `README.md` for the package in the `pkg/` directory, including installation instructions and clear usage examples.

---

## Phase 6: Final Packaging and Publishing

**Goal:** To prepare and bundle the package for distribution on npm.

- **Task 6.1: Configure `package.json`**

  - Properly configure the `name`, `version`, `description`, `main` (for CJS), `module` (for ESM), and `types` fields.
  - Use the `files` array to specify which files and directories (`dist/`, `README.md`) should be included in the published package.

- **Task 6.2: Integrate Static Data into Build Process**

  - Configure the build script to copy the `output/` directory generated by the Python pipeline into the final `pkg/dist/data/` directory. This ensures the static data is bundled with the package.

- **Task 6.3: Publish Package**
  - Run the final build script.
  - (Simulated) Run `npm publish` from within the `pkg/` directory to release the package.
