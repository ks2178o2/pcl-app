# How This Fixes Your AWS Problem

## Your Original Problem

**Error in browser:**
```
Error loading jobs: SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

**Root Cause:**
- Frontend is calling `/api/bulk-import/jobs` (relative URL)
- This hits the frontend server (serving HTML) instead of backend API
- Backend API is at `https://dev.hero.labs.pitcrewlabs.ai:8000`

## Why It's Happening

1. **VITE_API_URL wasn't set at build time**
   - You set it in EB Console (runtime), but Vite needs it at BUILD time
   - Frontend was built without knowing the backend URL
   - So it defaults to relative URLs (`/api/...`)

2. **EB deployment failed**
   - Prebuild hook tried to build frontend on AWS
   - But npm isn't available on Python platform
   - Build failed, so frontend still has old (wrong) URLs

## How Pre-Building Locally Fixes It

### Step 1: Build Locally with VITE_API_URL
```bash
export VITE_API_URL=https://dev.hero.labs.pitcrewlabs.ai:8000
cd apps/realtime-gateway
npm run build
```

**What happens:**
- Vite reads `VITE_API_URL` from environment
- Bakes it into the built JavaScript files
- All API calls will use `https://dev.hero.labs.pitcrewlabs.ai:8000/api/...`

### Step 2: Deploy Built Files
```bash
# The dist/ folder contains the built frontend with correct URLs
git add apps/realtime-gateway/dist/
git commit -m "Pre-built frontend with correct API URL"
git push
```

**What happens:**
- AWS EB deploys the pre-built `dist/` folder
- Frontend code already has correct backend URL baked in
- No build needed on AWS (hook exits gracefully)

### Step 3: Frontend Works
- Frontend makes API calls to: `https://dev.hero.labs.pitcrewlabs.ai:8000/api/bulk-import/jobs`
- Gets JSON response from backend ✅
- No more HTML errors ✅

## The Connection

```
Problem: Frontend → /api/... → Frontend server (HTML) ❌
         (relative URL hits wrong server)

Solution: Frontend → https://dev.hero.labs...:8000/api/... → Backend API (JSON) ✅
         (absolute URL hits correct server)
```

## Why This Works

1. **Build-time vs Runtime:**
   - Vite environment variables are replaced at BUILD time
   - Setting them in EB Console (runtime) doesn't help
   - Must set before `npm run build`

2. **Pre-building solves both problems:**
   - ✅ Frontend built with correct `VITE_API_URL`
   - ✅ No need for npm on AWS (we deploy pre-built files)
   - ✅ Hook exits gracefully (doesn't fail deployment)

## Alternative: If You Want EB to Build

If you want EB to build the frontend (not pre-build locally):

1. **Switch to Node.js platform** (has npm)
2. **Or install Node.js in Python platform** (complex)
3. **Or use Docker platform** (build in Dockerfile)

But pre-building locally is **simpler and faster**.

## Summary

**Your AWS problem:** Frontend can't reach backend API (gets HTML instead of JSON)

**Root cause:** Frontend built without knowing backend URL

**Solution:** Build frontend locally with `VITE_API_URL` set, then deploy the built files

**Result:** Frontend knows where backend is → API calls work → Problem solved ✅

