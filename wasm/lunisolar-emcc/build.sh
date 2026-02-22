#!/usr/bin/env bash
# Build the Emscripten C→WASM variant of the lunisolar calendar.
# Requires the Emscripten SDK (emcc) to be on PATH.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$SCRIPT_DIR"

OUT_DIR="$ROOT_DIR/pkg"
mkdir -p "$OUT_DIR"

emcc lunisolar.c \
  -O3 \
  -s WASM=1 \
  -s MODULARIZE=1 \
  -s EXPORT_NAME="createLunisolarEmcc" \
  -s EXPORTED_FUNCTIONS='["_from_solar_date", "_malloc", "_free"]' \
  -s EXPORTED_RUNTIME_METHODS='["ccall", "cwrap", "HEAPF64", "HEAPU32", "UTF8ToString", "stringToUTF8"]' \
  -s ALLOW_MEMORY_GROWTH=1 \
  -s ENVIRONMENT="node" \
  -s EXPORT_ES6=1 \
  -o "$OUT_DIR/lunisolar_emcc.mjs"

echo "Built: $OUT_DIR/lunisolar_emcc.mjs + $OUT_DIR/lunisolar_emcc.wasm"
ls -lh "$OUT_DIR/lunisolar_emcc.mjs" "$OUT_DIR/lunisolar_emcc.wasm"
