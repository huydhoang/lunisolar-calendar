# Publishing Guide for lunisolar-ts

This guide explains how to publish the `lunisolar-ts` package to npm, either manually or via GitHub Actions.

## Prerequisites

1. **npm Account**: Create an account at [npmjs.com](https://www.npmjs.com/) if you don't have one
2. **Repository Access**: Ensure your GitHub repository URL is correctly set in [`package.json`](./package.json:31)
3. **Build Tools**: All dependencies are already configured in the project

## Package Metadata

The package is configured with the following metadata in [`package.json`](./package.json):

- **Name**: `lunisolar-ts` (update if you want a scoped package like `@your-scope/lunisolar-ts`)
- **Version**: `0.1.0` (follows [semantic versioning](https://semver.org/))
- **Main Entry**: `dist/index.cjs` (CommonJS)
- **Module Entry**: `dist/index.mjs` (ES Module)
- **Types**: `dist/index.d.ts` (TypeScript declarations)
- **Files**: Only `dist/`, `README.md`, and `LICENSE` are included in the published package

## Manual Publishing

### 1. Update Package Information

Before publishing, update the following fields in [`package.json`](./package.json):

```json
{
  "author": "Your Name",
  "repository": {
    "url": "git+https://github.com/yourusername/lunisolar-ts.git"
  },
  "bugs": {
    "url": "https://github.com/yourusername/lunisolar-ts/issues"
  },
  "homepage": "https://github.com/yourusername/lunisolar-ts#readme"
}
```

### 2. Test the Build

```bash
cd pkg
npm run build
```

Verify that the `dist/` directory contains:
- `index.cjs` (CommonJS bundle)
- `index.mjs` (ES Module bundle)
- `index.d.ts` (TypeScript declarations)
- Source maps

### 3. Test the Package Locally

Preview what will be published:

```bash
npm pack --dry-run
```

Create a tarball to inspect:

```bash
npm pack
```

This creates a `.tgz` file you can extract and inspect to ensure only the correct files are included.

### 4. Login to npm

```bash
npm login
```

Enter your npm username, password, and email when prompted.

Verify you're logged in:

```bash
npm whoami
```

### 5. Publish

For an unscoped package:

```bash
npm publish
```

For a scoped package (if you change the name to `@your-scope/lunisolar-ts`):

```bash
npm publish --access public
```

### 6. Version Management

To bump the version and create a git tag:

```bash
# Patch release (0.1.0 → 0.1.1)
npm version patch

# Minor release (0.1.0 → 0.2.0)
npm version minor

# Major release (0.1.0 → 1.0.0)
npm version major
```

Then push the tags:

```bash
git push --follow-tags
```

## Automated Publishing with GitHub Actions

The project includes a GitHub Actions workflow at [`.github/workflows/publish.yml`](../.github/workflows/publish.yml:1) that automatically publishes to npm when you push tags.

### Setup

1. **Create an npm Automation Token**:
   - Go to [npmjs.com/settings/tokens](https://www.npmjs.com/settings/your-username/tokens)
   - Click "Generate New Token" → "Automation"
   - Copy the token

2. **Add Token to GitHub Secrets**:
   - Go to your GitHub repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `NODE_AUTH_TOKEN`
   - Value: Paste your npm token
   - Click "Add secret"

### Workflow Trigger

The workflow is triggered by:

1. **Tag Push**: When you push a tag matching `v*.*.*` pattern
2. **Main Branch Push**: When you push to the `main` branch (optional, you may want to remove this)

### Usage

To publish a new version:

```bash
# 1. Bump version (creates a git tag)
npm version patch  # or minor/major

# 2. Push the tag to GitHub
git push --follow-tags

# 3. The GitHub Action will automatically:
#    - Install dependencies
#    - Build the package
#    - Publish to npm
```

### Workflow Details

The workflow ([`.github/workflows/publish.yml`](../.github/workflows/publish.yml)):

1. Checks out the repository
2. Sets up Node.js 20
3. Installs dependencies with `npm ci`
4. Builds the package with `npm run build`
5. Publishes to npm with `npm publish --access public`

## Post-Publishing

After successful publication:

1. **Verify on npm**: Visit `https://www.npmjs.com/package/lunisolar-ts`
2. **Test Installation**: In a new project, run:
   ```bash
   npm install lunisolar-ts
   ```
3. **Update Documentation**: Update the [`README.md`](./README.md) with installation instructions
4. **Create Release Notes**: On GitHub, create a release with changelog

## Build Configuration

The package uses Rollup for bundling, configured in [`rollup.config.mjs`](./rollup.config.mjs:1):

- **Input**: `src/index.ts`
- **Outputs**:
  - CommonJS: `dist/index.cjs`
  - ES Module: `dist/index.mjs`
- **Plugins**: TypeScript, Node Resolve, CommonJS, JSON
- **Features**: Source maps, TypeScript declarations

The [`prepublishOnly`](./package.json:16) script ensures the package is built before every publish.

## Files Included in Package

The published package includes only:

- `dist/` directory (built files)
- `README.md`
- `LICENSE`

All source files, tests, examples, and configuration files are excluded via [`.npmignore`](./.npmignore:1).

## Troubleshooting

### "Package already exists"
- The package name is taken. Change it in [`package.json`](./package.json:2) or use a scoped name like `@your-scope/lunisolar-ts`

### "Authentication required"
- Run `npm login` again
- For CI, ensure `NODE_AUTH_TOKEN` is set in GitHub Secrets

### "Missing files after publish"
- Check [`.npmignore`](./.npmignore) to ensure important files aren't excluded
- Run `npm pack --dry-run` to preview included files

### "Build fails in CI"
- Ensure all dependencies are in `devDependencies` or `dependencies`
- Test locally with `npm ci && npm run build`

## Security Notes

- **Never commit** your npm token to the repository
- Use **automation tokens** (not classic tokens) for CI/CD
- Enable **2FA** on your npm account for manual publishing
- Regularly **rotate** your npm tokens

## Additional Resources

- [npm Publishing Documentation](https://docs.npmjs.com/cli/v9/commands/npm-publish)
- [Semantic Versioning](https://semver.org/)
- [GitHub Actions for npm](https://docs.github.com/en/actions/publishing-packages/publishing-nodejs-packages)