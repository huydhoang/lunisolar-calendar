import { cp, mkdir, access, constants } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const pkgDir = resolve(__dirname, '..');
const src = resolve(pkgDir, '..', 'output', 'json');
const dest = resolve(pkgDir, 'dist', 'data');

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
    console.warn(`[copy-data] Source not found: ${src} — skipping.`);
    return;
  }
  await mkdir(dest, { recursive: true });
  await cp(src, dest, { recursive: true, force: true });
  console.log(`[copy-data] Copied ${src} -> ${dest}`);
}

main().catch((err) => {
  console.error('[copy-data] Error:', err);
  process.exit(1);
});
