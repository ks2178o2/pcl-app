# CORS Fix Deployment Guide

## Problem
The frontend deployed at `https://dev.hero.labs.pitcrewlabs.ai` was trying to connect to `http://localhost:8001`, causing CORS errors.

## Changes Made

### 1. Frontend API URL Configuration
- **Created**: `apps/realtime-gateway/src/utils/apiConfig.ts`
  - Utility function that intelligently determines API URL
  - Uses `VITE_API_URL` if set
  - In production (https or non-localhost), uses relative URLs
  - In development, defaults to `http://localhost:8001`

### 2. Updated BulkImport Component
- **Modified**: `apps/realtime-gateway/src/pages/BulkImport.tsx`
  - Replaced hardcoded `API_BASE_URL` with `getApiUrl()` utility
  - All API calls now use the new utility function

### 3. Backend CORS Configuration
- **Modified**: `apps/app-api/main.py`
  - Added `https://dev.hero.labs.pitcrewlabs.ai` to default allowed origins
  - CORS now allows requests from production domain

## Deployment Steps

### Frontend Deployment
1. **Rebuild the frontend** with the new changes:
   ```bash
   cd apps/realtime-gateway
   npm run build
   ```

2. **Deploy the built files** to AWS

3. **Optional**: Set `VITE_API_URL` environment variable during build if API is on a different domain:
   ```bash
   VITE_API_URL=https://api.dev.hero.labs.pitcrewlabs.ai npm run build
   ```
   
   If API is served from the same domain (common in production), you don't need to set this - relative URLs will be used automatically.

### Backend Deployment
1. **Deploy the updated backend** with the new CORS configuration

2. **Verify CORS environment variable** (if using):
   ```bash
   # In your backend environment, ensure CORS_ORIGINS includes production domain:
   CORS_ORIGINS=http://localhost:3000,http://localhost:3005,https://dev.hero.labs.pitcrewlabs.ai
   ```

3. **Restart the backend server** to apply changes

## Verification

After deployment, verify:
1. Open `https://dev.hero.labs.pitcrewlabs.ai/bulk-upload`
2. Check browser console - should no longer see CORS errors
3. API calls should succeed (relative URLs if same domain, or configured URL if different)

## Alternative: Explicit API URL

If your API is served from a different domain/port in production, set the `VITE_API_URL` environment variable during the build:

```bash
# Example: API on different subdomain
VITE_API_URL=https://api.dev.hero.labs.pitcrewlabs.ai

# Example: API on different port (not recommended for production)
VITE_API_URL=https://dev.hero.labs.pitcrewlabs.ai:8001

# Then build
npm run build
```

## Notes

- The utility function detects production by checking if the protocol is `https:` or hostname is not `localhost`
- Relative URLs work when frontend and backend are served from the same domain
- CORS configuration in backend now includes the production domain by default
- All changes are backward compatible with local development

