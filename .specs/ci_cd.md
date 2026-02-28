Nice — congrats on finishing the package! Below is a compact, practical guide with everything you need to publish a TypeScript npm package (manual + CI). Follow the steps that match how you want to publish (local CLI or automated via GitHub Actions).

# 1) Prep your package (build & metadata)

1. Ensure `package.json` has these fields set:

   * `name` (unique on npm; for scoped packages use `@your-scope/name`)
   * `version` (semver)
   * `main` (point to built CommonJS entry, e.g. `dist/index.cjs.js`)
   * `module` (optional, ESM build)
   * `types` (path to `.d.ts`, e.g. `dist/index.d.ts`)
   * `files` (array of files to include in package) **or** add a `.npmignore`.
   * `repository`, `license`, `description`, `keywords`, `author`, `homepage` (good hygiene)

Minimal example:

```json
{
  "name": "@your-scope/your-package",
  "version": "1.0.0",
  "description": "Short description",
  "main": "dist/index.cjs.js",
  "module": "dist/index.esm.js",
  "types": "dist/index.d.ts",
  "files": ["dist"],
  "repository": {
    "type": "git",
    "url": "git+https://github.com/you/repo.git"
  },
  "scripts": {
    "build": "tsc -p tsconfig.build.json",
    "prepublishOnly": "npm run build"
  }
}
```

2. Build output:

   * Use `tsc` or a bundler (tsup/rollup/webpack). For publishing, produce JS + `.d.ts` declarations.
   * In `tsconfig.json` or `tsconfig.build.json` set `"declaration": true` and output to `dist/`.

3. Make sure not to publish dev files: use `"files"` or `.npmignore`.

# 2) Test the package tarball locally

Before publishing, confirm what will be published:

```bash
# run build first
npm run build

# show what would be packed
npm pack --dry-run

# create a package tarball to inspect
npm pack
# you can extract & inspect the .tgz to ensure correct files are included
```

# 3) Publish manually with npm CLI

1. Create an npm account at [https://www.npmjs.com/](https://www.npmjs.com/) (if you don’t have one).
2. Login locally:

```bash
npm login
# or
npm adduser
```

You’ll be prompted for username, password, and email.

3. If this is a scoped package and you want it public:

```bash
npm publish --access public
```

For unscoped packages:

```bash
npm publish
```

Useful commands:

* `npm whoami` — verify login
* `npm publish --dry-run` — check
* `npm view <pkg>` — view published package
* `npm version patch` — bump version, updates package.json and creates git tag

**Note on 2FA:** If you enabled 2FA on your npm account, you’ll be prompted to enter an OTP when publishing. CI publishing requires an automation token instead of OTP.

# 4) Automate publishing with GitHub Actions

Create a read-and-write npm token:
`npm token create --read-only` (or via npm website create an automation token with `publish` scope). Save it in your GitHub repo secrets as `NODE_AUTH_TOKEN`.

Example `.github/workflows/publish.yml`:

```yaml
name: Publish Package
on:
  push:
    branches:
      - main
    tags:
      - 'v*.*.*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Use Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://registry.npmjs.org'
      - name: Install deps
        run: npm ci
      - name: Build
        run: npm run build
      - name: Publish to npm
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NODE_AUTH_TOKEN }}
        run: |
          npm publish --access public
```

Notes:

* Trigger on tags is common (`git tag v1.2.3 && git push --tags`) so publish runs only for releases.
* Use `npm version` locally (or in CI) to bump the version before tagging.

# 5) Scoped packages / orgs / private packages

* Scoped public: `npm publish --access public`
* Scoped private: use npm organization or `private: true` in package.json (will not publish).
* For org-owned packages, ensure you have permission on npm.

# 6) Post-publish checks & housekeeping

* Check the package page on npm ([https://www.npmjs.com/package/](https://www.npmjs.com/package/)<package-name>).
* Install the published package in a test project `npm i @your-scope/your-package` to ensure it works.
* Keep semantic versioning: `major.minor.patch`.
* If you need to unpublish: `npm unpublish <pkg>@<version>` — be careful; npm limits unpublishes for older packages.

# Quick checklist (TL;DR)

* [ ] `package.json` metadata correct (`name`, `version`, `main`, `types`, `files`)
* [ ] Build script produces `dist/` with `.js` and `.d.ts`
* [ ] `npm login`
* [ ] `npm run build`
* [ ] `npm publish --access public` (for scopeds)
* [ ] (Optional) Add GitHub Action using `NODE_AUTH_TOKEN` for automated publishes

---
