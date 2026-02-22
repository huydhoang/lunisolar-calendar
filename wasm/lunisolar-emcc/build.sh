#!/usr/bin/env bash
# Build the Emscripten C→WASM variant of the lunisolar calendar.
# Links against the Swiss Ephemeris C source from vendor/swisseph/
# and embeds .se1 ephemeris data files for standalone operation.
# Requires the Emscripten SDK (emcc) to be on PATH.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$SCRIPT_DIR"

OUT_DIR="$ROOT_DIR/pkg"
SWE_DIR="$ROOT_DIR/vendor/swisseph"
EPHE_DIR="$ROOT_DIR/wasm/swisseph/ephe"
mkdir -p "$OUT_DIR"

# Swiss Ephemeris core C files
SWE_SRCS=(
  "$SWE_DIR/swecl.c"
  "$SWE_DIR/swedate.c"
  "$SWE_DIR/swehel.c"
  "$SWE_DIR/swehouse.c"
  "$SWE_DIR/swejpl.c"
  "$SWE_DIR/swemmoon.c"
  "$SWE_DIR/swemplan.c"
  "$SWE_DIR/sweph.c"
  "$SWE_DIR/swephlib.c"
)

emcc lunisolar.c ephemeris.c "${SWE_SRCS[@]}" \
  -I"$SWE_DIR" \
  -O3 \
  -s WASM=1 \
  -s MODULARIZE=1 \
  -s EXPORT_NAME="createLunisolarEmcc" \
  -s EXPORTED_FUNCTIONS='["_from_solar_date", "_from_solar_date_auto", "_malloc", "_free"]' \
  -s EXPORTED_RUNTIME_METHODS='["ccall", "cwrap", "HEAPF64", "HEAPU32", "UTF8ToString", "stringToUTF8"]' \
  -s ALLOW_MEMORY_GROWTH=1 \
  -s ENVIRONMENT="node" \
  -s EXPORT_ES6=1 \
  --embed-file "$EPHE_DIR/sepl_18.se1@/ephe/sepl_18.se1" \
  --embed-file "$EPHE_DIR/semo_18.se1@/ephe/semo_18.se1" \
  -o "$OUT_DIR/lunisolar_emcc.mjs"

echo "Built: $OUT_DIR/lunisolar_emcc.mjs + $OUT_DIR/lunisolar_emcc.wasm"
ls -lh "$OUT_DIR/lunisolar_emcc.mjs" "$OUT_DIR/lunisolar_emcc.wasm"
