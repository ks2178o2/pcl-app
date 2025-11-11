# Playwright E2E Tests

This directory contains end-to-end tests for the realtime-gateway frontend application using Playwright.

## Setup

Playwright is already configured in the project. To install browsers:

```bash
npx playwright install
```

## Running Tests

```bash
# Run all tests
npm run test:e2e

# Run tests in UI mode (interactive)
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Run tests in debug mode
npm run test:e2e:debug

# View test report
npm run test:e2e:report
```

## Test Structure

- `auth.spec.ts` - Authentication flows (sign in, sign up, password reset)
- `navigation.spec.ts` - Route navigation and 404 handling
- `dashboard.spec.ts` - Sales dashboard functionality
- `bulk-import.spec.ts` - Bulk import/upload features
- `appointments.spec.ts` - Appointments management
- `leads.spec.ts` - Leads management
- `settings.spec.ts` - User settings
- `helpers/` - Shared test utilities

## Configuration

Tests are configured in `playwright.config.ts` at the project root. The base URL defaults to `http://localhost:3000`.

## Notes

- Tests are designed to work with or without authentication
- Many tests check for redirects to `/auth` when unauthenticated
- Tests use flexible selectors to handle different UI states (loading, empty, data)
- The dev server must be running before tests (or use the `webServer` config)

## CI/CD

For CI environments, set `CI=true` to enable retries and reduce parallelism.

