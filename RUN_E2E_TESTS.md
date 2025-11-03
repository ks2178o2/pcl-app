# How to Run v1.0.5 E2E Tests

**Status:** Playwright setup complete, manual server startup required

---

## Quick Start

### Option 1: Manual Server + Tests (Recommended for first run)

```bash
# Terminal 1: Start development server
cd apps/realtime-gateway
npm run dev

# Wait for server to start (should see "ready in XXXms")

# Terminal 2: Run E2E tests
cd apps/realtime-gateway
npm run test:e2e
```

### Option 2: Debug Mode (Best for development)

```bash
# Terminal 1: Start server
cd apps/realtime-gateway
npm run dev

# Terminal 2: Run with UI mode
cd apps/realtime-gateway
npm run test:e2e:ui
```

### Option 3: Headed Mode (See browser)

```bash
# Terminal 1: Start server
npm run dev

# Terminal 2: Run headed
npm run test:e2e:headed
```

---

## Current Status

**Setup:** ✅ Complete  
**Tests Written:** ✅ Complete  
**Auto-start:** ⚠️ Temporarily disabled (manual start required)

**Why manual?**  
The auto-start was conflicting with existing test infrastructure. Manual startup is actually preferred for debugging.

---

## Test Files Created

1. ✅ `e2e/chunked-recording.spec.ts` - Recording tests
2. ✅ `e2e/failed-uploads-banner.spec.ts` - Banner tests

---

## Next Steps

### To Enable Auto-Start Later:
1. Fix webServer config conflicts
2. Resolve Vitest/Playwright conflicts
3. Update config

### For Now:
**Use manual server startup** - it's actually better for debugging!

---

**Ready to test when you start the server manually!**

