# Deployment Fixes Summary

## ✅ Completed Fixes

### 1. CORS and API URL Configuration
- ✅ Fixed 46 instances of hardcoded `localhost:8001` URLs across 16 files
- ✅ Created centralized `getApiUrl()` utility function
- ✅ Updated backend CORS to include production domain (`https://dev.hero.labs.pitcrewlabs.ai`)
- ✅ All API calls now use `getApiUrl()` utility

### 2. Supabase Client Configuration
- ✅ Updated Supabase client to use environment variables with fallback
- ✅ Fixed hardcoded Supabase edge function URL in SystemCheck.tsx
- ✅ Environment variables: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

### 3. Relative API Calls
- ✅ Fixed EnhancedUploadManager.tsx (3 API calls)
- ✅ Fixed EnhancedContextManagement.tsx (6 API calls)
- ✅ All API calls now use `getApiUrl()` utility

## 🔴 Critical Remaining Issues

### 1. Backend Environment Variables (CRITICAL)
**Required**: Set these environment variables in your AWS deployment:

```bash
SUPABASE_URL=https://xxdahmkfioqzgqvyabek.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here  # REQUIRED
ENVIRONMENT=production
CORS_ORIGINS=https://dev.hero.labs.pitcrewlabs.ai,http://localhost:3000
```

**Impact**: Backend authentication will fail without `SUPABASE_SERVICE_ROLE_KEY`

### 2. Frontend Build Environment Variables (CRITICAL)
**Required**: Set these at BUILD TIME (before `npm run build`):

```bash
export VITE_SUPABASE_URL=https://xxdahmkfioqzgqvyabek.supabase.co
export VITE_SUPABASE_ANON_KEY=your_anon_key_here
# VITE_API_URL is optional - will use relative URLs if not set
```

**Impact**: Frontend authentication will fail if variables are not set

### 3. SPA Routing Configuration (HIGH)
**Required**: Configure nginx/server to serve `index.html` for all routes.

**Nginx Configuration**:
```nginx
location / {
  try_files $uri $uri/ /index.html;
}
```

**Impact**: Direct URLs and browser refresh will return 404

## 📋 Pre-Deployment Checklist

### Frontend Build
- [ ] Set `VITE_SUPABASE_URL` environment variable
- [ ] Set `VITE_SUPABASE_ANON_KEY` environment variable
- [ ] Run `npm run build`
- [ ] Verify build output in `dist/` directory
- [ ] Test build locally with `npm run preview`

### Backend Configuration
- [ ] Set `SUPABASE_SERVICE_ROLE_KEY` environment variable
- [ ] Set `ENVIRONMENT=production` environment variable
- [ ] Set `CORS_ORIGINS` environment variable (or verify defaults)
- [ ] Test backend health endpoint: `GET /health`
- [ ] Test authentication endpoints

### Infrastructure
- [ ] Configure nginx/server for SPA routing
- [ ] Set up SSL/HTTPS certificates
- [ ] Configure load balancer health checks
- [ ] Verify domain DNS settings
- [ ] Test CORS headers in responses

### Testing
- [ ] Test authentication flow
- [ ] Test API calls (check network tab)
- [ ] Test direct URLs (e.g., `/bulk-upload`)
- [ ] Test browser refresh on sub-routes
- [ ] Test file uploads
- [ ] Verify no CORS errors in console
- [ ] Test error scenarios

## 🚨 Common Deployment Errors & Solutions

### Error: "Failed to fetch" / CORS errors
- **Cause**: CORS configuration, API unavailable
- **Fix**: Verify backend CORS allows production domain, check API is running

### Error: "Authentication failed"
- **Cause**: Missing or incorrect Supabase credentials
- **Fix**: Verify `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set at build time

### Error: "404 on refresh" / "Page not found"
- **Cause**: SPA routing not configured
- **Fix**: Configure nginx/server to serve `index.html` for all routes

### Error: "Backend authentication failed"
- **Cause**: Missing `SUPABASE_SERVICE_ROLE_KEY`
- **Fix**: Set backend environment variable

### Error: "API calls to localhost"
- **Cause**: Old build (should be fixed now)
- **Fix**: Rebuild frontend with updated code

## 📝 Files Modified

### Frontend Files (19 files)
1. `apps/realtime-gateway/src/utils/apiConfig.ts` (NEW - utility function)
2. `apps/realtime-gateway/src/pages/BulkImport.tsx` (6 instances)
3. `apps/realtime-gateway/src/pages/CallStatisticsTest.tsx` (1 instance)
4. `apps/realtime-gateway/src/hooks/useCallRecords.ts` (2 instances)
5. `apps/realtime-gateway/src/pages/CallsSearch.tsx` (1 instance)
6. `apps/realtime-gateway/src/components/ChunkedAudioRecorder.tsx` (1 instance)
7. `apps/realtime-gateway/src/pages/CallAnalysis.tsx` (5 instances)
8. `apps/realtime-gateway/src/pages/SystemCheck.tsx` (2 instances)
9. `apps/realtime-gateway/src/components/CallsDashboard.tsx` (2 instances)
10. `apps/realtime-gateway/src/services/transcriptAnalysisService.ts` (1 instance)
11. `apps/realtime-gateway/src/components/TwilioConnectionTest.tsx` (1 instance)
12. `apps/realtime-gateway/src/components/SMSSender.tsx` (1 instance)
13. `apps/realtime-gateway/src/components/FollowUpPlanPanel.tsx` (1 instance)
14. `apps/realtime-gateway/src/components/TwilioDebugTest.tsx` (1 instance)
15. `apps/realtime-gateway/src/components/admin/AnalysisSettingsManagement.tsx` (2 instances)
16. `apps/realtime-gateway/src/components/TranscribeFileUpload.tsx` (1 instance)
17. `apps/realtime-gateway/src/lib/api/rag-features.ts` (18 instances)
18. `apps/realtime-gateway/src/integrations/supabase/client.ts` (environment variables)
19. `apps/realtime-gateway/src/components/admin/EnhancedUploadManager.tsx` (3 instances)
20. `apps/realtime-gateway/src/components/admin/EnhancedContextManagement.tsx` (6 instances)

### Backend Files (1 file)
1. `apps/app-api/main.py` (CORS configuration)

## 🎯 Next Steps

1. **Set Environment Variables**: Configure both frontend (build-time) and backend (runtime) environment variables
2. **Rebuild Frontend**: Run `npm run build` with environment variables set
3. **Configure Server**: Set up nginx/server for SPA routing
4. **Deploy**: Deploy updated frontend and backend
5. **Verify**: Test all functionality in production environment
6. **Monitor**: Set up monitoring and alerts for errors

## 📚 Documentation

- See `DEPLOYMENT_READINESS_CHECKLIST.md` for detailed checklist
- See `CORS_FIX_COMPLETE.md` for CORS fix details
- See `DEPLOYMENT_CHECKLIST.md` for original deployment guide

