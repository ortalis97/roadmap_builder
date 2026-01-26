# Bun Package Manager Reference

A concise reference for using Bun as a package manager in projects where npm is not available.

---

## Table of Contents

1. [Why Bun](#1-why-bun)
2. [Command Equivalents](#2-command-equivalents)
3. [Playwright Setup](#3-playwright-setup)
4. [Common Operations](#4-common-operations)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Why Bun

In environments where npm is restricted (e.g., company policies), Bun serves as a drop-in replacement for:
- Package installation
- Script execution
- Dependency management

Bun is also significantly faster than npm for most operations.

### Installation Path

Bun is typically installed at `~/.bun/bin/bun`. Always use the full path to avoid PATH issues:

```bash
~/.bun/bin/bun --version
```

---

## 2. Command Equivalents

### Package Management

| npm Command | Bun Equivalent |
|------------|----------------|
| `npm install` | `~/.bun/bin/bun install` |
| `npm install package` | `~/.bun/bin/bun add package` |
| `npm install -D package` | `~/.bun/bin/bun add -D package` |
| `npm uninstall package` | `~/.bun/bin/bun remove package` |
| `npm update` | `~/.bun/bin/bun update` |

### Script Execution

| npm Command | Bun Equivalent |
|------------|----------------|
| `npm run dev` | `~/.bun/bin/bun run dev` |
| `npm run build` | `~/.bun/bin/bun run build` |
| `npm run lint` | `~/.bun/bin/bun run lint` |
| `npm test` | `~/.bun/bin/bun test` |
| `npx command` | `~/.bun/bin/bunx command` |

### Examples

```bash
# Install all dependencies
cd client && ~/.bun/bin/bun install

# Add a new dependency
~/.bun/bin/bun add axios

# Add a dev dependency
~/.bun/bin/bun add -D @types/node

# Run development server
~/.bun/bin/bun run dev

# Run a one-off command
~/.bun/bin/bunx create-react-app my-app
```

---

## 3. Playwright Setup

Playwright installation with Bun requires a specific approach since Playwright's browser installation scripts expect npm/npx.

### Install Playwright Package

```bash
cd client
~/.bun/bin/bun add -D @playwright/test
```

### Install Browsers

Use bunx to run Playwright's browser installer:

```bash
~/.bun/bin/bunx playwright install chromium
```

To install all browsers:

```bash
~/.bun/bin/bunx playwright install
```

### Run Playwright Tests

```bash
# Run all tests
~/.bun/bin/bunx playwright test

# Run with UI mode
~/.bun/bin/bunx playwright test --ui

# Run specific test file
~/.bun/bin/bunx playwright test tests/auth.spec.ts

# Generate test code
~/.bun/bin/bunx playwright codegen localhost:5173
```

### Playwright Config

Create `playwright.config.ts` in your client directory:

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  webServer: {
    command: '~/.bun/bin/bun run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

## 4. Common Operations

### Initialize New Project

```bash
~/.bun/bin/bun init
```

### Add Scripts to package.json

Scripts work the same as npm. Define in `package.json`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint . --ext ts,tsx",
    "test": "vitest",
    "e2e": "playwright test"
  }
}
```

Run with:

```bash
~/.bun/bin/bun run dev
~/.bun/bin/bun run lint
```

### Lock File

Bun uses `bun.lockb` (binary format) instead of `package-lock.json`. Both work fine, but bun.lockb is faster to parse.

If you have both, bun will prefer `bun.lockb`. To generate from existing `package-lock.json`:

```bash
# Remove existing bun lock file
rm bun.lockb

# Install from package-lock.json
~/.bun/bin/bun install
```

### Global Packages

```bash
# Install globally
~/.bun/bin/bun add -g typescript

# Run global command
~/.bun/bin/bunx tsc --version
```

---

## 5. Troubleshooting

### "Command not found: bun"

Bun may not be in PATH. Use the full path:

```bash
~/.bun/bin/bun install
```

Or add to PATH in your shell config:

```bash
export PATH="$HOME/.bun/bin:$PATH"
```

### Package Resolution Differences

Bun resolves packages slightly differently than npm. If you encounter issues:

1. Delete `node_modules` and lock files
2. Re-install with bun:

```bash
rm -rf node_modules bun.lockb package-lock.json
~/.bun/bin/bun install
```

### Vite Compatibility

Vite works seamlessly with bun. No special configuration needed:

```bash
~/.bun/bin/bun create vite my-app
cd my-app
~/.bun/bin/bun install
~/.bun/bin/bun run dev
```

### TypeScript Issues

If TypeScript types aren't resolving:

```bash
~/.bun/bin/bun add -D typescript @types/node @types/react @types/react-dom
```

---

## Resources

- [Bun Documentation](https://bun.sh/docs)
- [Bun Package Manager Guide](https://bun.sh/docs/cli/install)
- [Playwright Documentation](https://playwright.dev/docs/intro)
