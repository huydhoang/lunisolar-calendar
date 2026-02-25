# Bazi Accuracy Workflow - 2026-02-25

## Summary

Extended the lunisolar accuracy test workflow to include Bazi (Four Pillars of Destiny) results verification, comparing the Python reference implementation against Rust WASM and Emscripten WASM ports.

Also renamed the workflow file from `test-lunisolar-wasm.yml` to `verify-ports-against-python.yml` to accurately reflect its purpose: verifying alignment between the original Python implementation and ports in other languages.

---

## Files Modified

### `tests/lunisolar-wasm/python_reference.py`

**Added:**
- `--gender` CLI argument for bazi analysis (default: 'male')
- Bazi module imports: `build_chart`, `ten_god`, `changsheng_stage`, `life_stage_detail`, `nayin_for_cycle`, `detect_stem_combinations`, `detect_transformations`, `detect_punishments`, `score_day_master`
- `bazi` object in output with:
  - `dayMasterStem`, `dayMasterElement`, `dayMasterPolarity`
  - `dayMasterStrengthScore`, `dayMasterStrength`
  - `tenGods` for year/month/hour pillars
  - `lifeStages` (十二长生) with index, chinese, english, strengthClass per pillar
  - `naYin` (納音) with element, chinese, english per pillar
  - `stemCombinations` (天干合) with pair, stems, targetElement
  - `transformations` (合化) with full condition checking
  - `punishments` (刑害) with type, branches, severity, lifeAreas

---

### `tests/lunisolar-wasm/compare.mjs`

**Added:**
- Helper functions for Emscripten bazi calls:
  - `emccBaziStemElement(stemIdx)`
  - `emccBaziStemPolarity(stemIdx)`
  - `emccBaziBranchElement(branchIdx)`
  - `emccBaziTenGod(dmStemIdx, targetStemIdx)`
  - `emccBaziLifeStage(stemIdx, branchIdx)`
  - `emccBaziNaYin(cycle)`
- Comparison functions:
  - `baziMatch(ref, cand)` - Ten Gods comparison
  - `baziLifeStagesMatch(ref, cand)` - 12 Life Stages comparison
  - `baziNaYinMatch(ref, cand)` - Na Yin comparison
- Bazi analysis computation for Emscripten results
- New summary section: "Bazi (Four Pillars Analysis)" with match counts
- New comparison table: "Bazi Comparison Table" showing Day Master, Ten Gods, Life Stages, Na Yin

**Modified:**
- Updated header comment to mention bazi verification
- Added console output for bazi match statistics

---

### `.github/workflows/verify-ports-against-python.yml` (renamed from `test-lunisolar-wasm.yml`)

**Modified:**
- Workflow name: `"Verify: Port Implementations vs Python Reference"`
- Job name: `"Verify Rust WASM, Emscripten WASM, TypeScript vs Python (DE440s)"`
- Updated path trigger to reference new filename
- Artifact name: `port-verification-report`
- Added path triggers for:
  - `lunisolar-python/bazi.py`
  - `lunisolar-python/nayin.csv`
- Step names updated to clarify purpose (e.g., "Build Rust WASM port")

---

### `ports/lunisolar-rs/src/lib.rs` (NEW)

**Added:**
- `#[wasm_bindgen]` exports for bazi functions:
  - `baziStemElement`, `baziStemPolarity`, `baziBranchElement`
  - `baziTenGod`, `baziChangshengStage`, `baziNaYin`
  - `baziDetectStemCombinations`, `baziDetectTransformations`, `baziDetectPunishments`
  - `baziDetectPhucNgam`, `baziElementRelation`, `baziGanzhiFromCycle`

---

### `tests/lunisolar-wasm/compare.mjs` (Updated)

**Added:**
- Emscripten bazi detection helpers:
  - `emccBaziDetectStemCombinations(pillars)`
  - `emccBaziDetectTransformations(pillars)`
  - `emccBaziDetectPunishments(pillars)`
- Rust WASM bazi analysis section
- Comparison functions for new features:
  - `baziStemCombinationsMatch(ref, cand)`
  - `baziTransformationsMatch(ref, cand)`
  - `baziPunishmentsMatch(ref, cand)`
- Updated summary table with Rust WASM column
- Updated console output with detailed match counts

---

## Files Not Modified (Intentionally Skipped)

### TypeScript Port (`ports/lunisolar-ts/`)
Per user request, TS port was skipped for bazi comparison.

---

## What Gets Tested

| Feature | Python | Rust WASM | Emcc WASM | TS |
|---------|--------|-----------|-----------|-----|
| Ganzhi (四柱) | Reference | ✅ | ✅ | ✅ |
| Huangdao (黄道) | Reference | ✅ | ✅ | ✅ |
| Ten Gods (十神) | Reference | ✅ | ✅ | ❌ skipped |
| Life Stages (十二长生) | Reference | ✅ | ✅ | ❌ skipped |
| Na Yin (納音) | Reference | ✅ | ✅ | ❌ skipped |
| Stem Combinations (天干合) | Reference | ✅ | ✅ | ❌ skipped |
| Transformations (合化) | Reference | ✅ | ✅ | ❌ skipped |
| Punishments (刑害) | Reference | ✅ | ✅ | ❌ skipped |

---

## Work Done (Future Enhancements Implemented)

### 1. Rust WASM Bazi Functions Exported

Added `#[wasm_bindgen]` exports in `ports/lunisolar-rs/src/lib.rs` for:

- `baziStemElement(stemIdx)` — Return element for a stem index
- `baziStemPolarity(stemIdx)` — Return polarity (Yang/Yin) for a stem index
- `baziBranchElement(branchIdx)` — Return element for a branch index
- `baziTenGod(dmStemIdx, targetStemIdx)` — Return Ten God name
- `baziChangshengStage(stemIdx, branchIdx)` — Return life stage detail
- `baziNaYin(cycle)` — Return Na Yin entry for cycle (1-60)
- `baziDetectStemCombinations(pillarsJson)` — Detect stem combinations (天干合)
- `baziDetectTransformations(pillarsJson, monthBranchIdx)` — Detect transformations (合化)
- `baziDetectPunishments(pillarsJson)` — Detect punishments (刑害)
- `baziDetectPhucNgam(pillarsJson, dynamicStemIdx, dynamicBranchIdx)` — Detect Phục Ngâm
- `baziElementRelation(dmElem, otherElem)` — Return element relation
- `baziGanzhiFromCycle(cycle)` — Convert cycle to stem/branch

### 2. Emscripten Bazi Comparison Tests

Updated `tests/lunisolar-wasm/compare.mjs` with:

- Helper functions for Emscripten bazi detection:
  - `emccBaziDetectStemCombinations(pillars)`
  - `emccBaziDetectTransformations(pillars)`
  - `emccBaziDetectPunishments(pillars)`
- Comparison functions for all bazi features:
  - `baziStemCombinationsMatch(ref, cand)`
  - `baziTransformationsMatch(ref, cand)`
  - `baziPunishmentsMatch(ref, cand)`

### 3. Full Comparison Coverage

Updated report generation to include:

| Test | Rust vs Python | Emcc vs Python |
|------|---------------|---------------|
| Ten Gods (十神) | ✅ | ✅ |
| Life Stages (十二长生) | ✅ | ✅ |
| Na Yin (納音) | ✅ | ✅ |
| Stem Combinations (天干合) | ✅ | ✅ |
| Transformations (合化) | ✅ | ✅ |
| Punishments (刑害) | ✅ | ✅ |

---

## Remaining Future Work

1. **TypeScript Port**: Include if bazi module is implemented in the TS package

---

## Usage

```bash
# Local test
cd tests/lunisolar-wasm
node compare.mjs

# The workflow runs automatically on push to relevant paths
# Or manually via GitHub Actions "workflow_dispatch"
```

---

## Report Output Structure

The generated `compare-report.md` now includes:

```
## Summary
### Ganzhi (Sexagenary Cycle)
### Huangdao (Construction Stars + Great Yellow Path)
### Bazi (Four Pillars Analysis)  ← Updated with Rust WASM column

## Ganzhi Comparison Table
## Huangdao Comparison Table
## Bazi Comparison Table  ← Updated with new features

## Notes (updated with bazi info)
```

The Bazi section now shows a comparison table with both Rust WASM and Emcc vs Python columns for:
- Ten Gods (十神)
- Life Stages (十二长生)
- Na Yin (納音)
- Stem Combinations (天干合)
- Transformations (合化)
- Punishments (刑害)
