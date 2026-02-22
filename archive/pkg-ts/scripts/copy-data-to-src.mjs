// Copies precomputed JSON from repository output/json into package src/data/precomputed
// so the manifest generator can statically reference them for bundlers.

import { cp, mkdir, access, constants } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const pkgDir = resolve(__dirname, '..');                 // pkg/
const repoRoot = resolve(pkgDir, '..');                  // repo root
const src = resolve(repoRoot, 'output', 'json');         // output/json
const dest = resolve(pkgDir, 'src', 'data', 'precomputed'); // pkg/src/data/precomputed

async function exists(p) {
  try {
    await access(p, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

async function main() {
  if (!(await exists(src))) {
    console.warn(`[copy-data-to-src] Source not found: ${src} — skipping.`);
    return;
  }
  await mkdir(dest, { recursive: true });
  await cp(src, dest, { recursive: true, force: true });
  console.log(`[copy-data-to-src] Copied ${src} -> ${dest}`);
}

main().catch((err) => {
  console.error('[copy-data-to-src] Error:', err);
  process.exit(1);
});