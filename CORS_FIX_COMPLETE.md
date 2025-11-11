# CORS Fix - Complete Summary

## Problem
The frontend deployed at `https://dev.hero.labs.pitcrewlabs.ai` was trying to connect to `http://localhost:8001`, causing CORS errors because:
1. Frontend code was using hardcoded `localhost:8001` as fallback when `VITE_API_URL` was not set
2. Backend CORS configuration didn't include the production domain

## Solution

### 1. Created Centralized API URL Utility
**File**: `apps/realtime-gateway/src/utils/apiConfig.ts`

- Intelligent API URL detection:
  - Uses `VITE_API_URL` if explicitly set (build-time environment variable)
  - In production (https or non-localhost), uses relative URLs (empty string)
  - In development, defaults to `http://localhost:8001`
- Provides `getApiUrl(endpoint)` function for consistent API calls

### 2. Updated Backend CORS Configuration
**File**: `apps/app-api/main.py`

- Added `https://dev.hero.labs.pitcrewlabs.ai` to default allowed origins
- CORS now allows requests from production domain by default

### 3. Fixed All Frontend Files

Updated **15 files** to use the new `getApiUrl()` utility:

1. ✅ `apps/realtime-gateway/src/pages/BulkImport.tsx` (6 instances)
2. ✅ `apps/realtime-gateway/src/pages/CallStatisticsTest.tsx` (1 instance)
3. ✅ `apps/realtime-gateway/src/hooks/useCallRecords.ts` (2 instances)
4. ✅ `apps/realtime-gateway/src/pages/CallsSearch.tsx` (1 instance)
5. ✅ `apps/realtime-gateway/src/components/ChunkedAudioRecorder.tsx` (1 instance)
6. ✅ `apps/realtime-gateway/src/pages/CallAnalysis.tsx` (5 instances)
7. ✅ `apps/realtime-gateway/src/pages/SystemCheck.tsx` (2 instances)
8. ✅ `apps/realtime-gateway/src/components/CallsDashboard.tsx` (2 instances)
9. ✅ `apps/realtime-gateway/src/services/transcriptAnalysisService.ts` (1 instance)
10. ✅ `apps/realtime-gateway/src/components/TwilioConnectionTest.tsx` (1 instance)
11. ✅ `apps/realtime-gateway/src/components/SMSSender.tsx` (1 instance)
12. ✅ `apps/realtime-gateway/src/components/FollowUpPlanPanel.tsx` (1 instance)
13. ✅ `apps/realtime-gateway/src/components/TwilioDebugTest.tsx` (1 instance)
14. ✅ `apps/realtime-gateway/src/components/admin/AnalysisSettingsManagement.tsx` (2 instances)
15. ✅ `apps/realtime-gateway/src/components/TranscribeFileUpload.tsx` (1 instance)
16. ✅ `apps/realtime-gateway/src/lib/api/rag-features.ts` (18 instances)

**Total**: ~46 instances fixed across 16 files

## Remaining References

The only remaining references to `localhost:8000/8001` are:
- ✅ `apiConfig.ts` - Default fallback for development (expected)
- ✅ `test-setup.ts` - Test configuration (expected)
- ✅ Test files - Test mocks and assertions (expected)

## How It Works

### Production Deployment
When deployed to `https://dev.hero.labs.pitcrewlabs.ai`:
1. `getApiUrl()` detects production (https protocol or non-localhost hostname)
2. Returns empty string for relative URLs
3. API calls use same domain: `https://dev.hero.labs.pitcrewlabs.ai/api/...`
4. No CORS issues since same origin

### Development
When running locally:
1. `getApiUrl()` detects localhost
2. Returns `http://localhost:8001` as fallback
3. API calls work as before

### Explicit Configuration
If `VITE_API_URL` is set during build:
1. Uses that URL exactly
2. Useful for different API domains/subdomains

## Deployment Steps

1. **Rebuild frontend**:
   ```bash
   cd apps/realtime-gateway
   npm run build
   ```

2. **Deploy updated files** to AWS

3. **Restart backend** (if CORS config changed):
   - Backend now includes production domain in default CORS origins
   - Or set `CORS_ORIGINS` environment variable if needed

## Benefits

✅ **No more CORS errors** in production  
✅ **Works automatically** - no environment variable needed if API is on same domain  
✅ **Backward compatible** - development still works with localhost  
✅ **Centralized configuration** - one place to manage API URLs  
✅ **Future-proof** - new code can use `getApiUrl()` utility  

## Testing

After deployment, verify:
1. Open `https://dev.hero.labs.pitcrewlabs.ai/bulk-upload`
2. Check browser console - should see no CORS errors
3. API calls should succeed
4. All features should work normally

## Notes

- The utility function detects production by checking `window.location.protocol === 'https:'` or hostname is not localhost
- Relative URLs work when frontend and backend are served from the same domain
- If API is on a different domain, set `VITE_API_URL` during build
- All changes are backward compatible with local development

