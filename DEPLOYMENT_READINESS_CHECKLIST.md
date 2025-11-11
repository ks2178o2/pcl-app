# Deployment Readiness Checklist

## ✅ Completed Fixes

### 1. CORS Configuration
- ✅ Fixed hardcoded `localhost:8001` API URLs (46 instances across 16 files)
- ✅ Created centralized `getApiUrl()` utility function
- ✅ Updated backend CORS to include production domain
- ✅ API calls now use relative URLs in production automatically

## 🔴 Critical Issues to Fix

### 1. Hardcoded Supabase Credentials (CRITICAL)
**File**: `apps/realtime-gateway/src/integrations/supabase/client.ts`

**Issue**: Supabase URL and key are hardcoded, preventing environment-specific configuration.

**Fix Required**:
```typescript
// Change from:
const SUPABASE_URL = "https://xxdahmkfioqzgqvyabek.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = "eyJhbGciOiJIUzI1NiIs...";

// To:
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || "https://xxdahmkfioqzgqvyabek.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || "fallback-key";
```

**Impact**: 
- Frontend authentication will fail if Supabase URL/key differs between environments
- Security risk if keys are exposed in code
- Cannot use different Supabase projects for dev/staging/prod

### 2. Backend Environment Variables (CRITICAL)
**File**: `apps/app-api/main.py`

**Issue**: `SUPABASE_SERVICE_ROLE_KEY` is missing, causing backend authentication to fail.

**Required Environment Variables**:
```bash
SUPABASE_URL=https://xxdahmkfioqzgqvyabek.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here  # REQUIRED
ENVIRONMENT=production  # or development
CORS_ORIGINS=https://dev.hero.labs.pitcrewlabs.ai,http://localhost:3000
```

**Impact**:
- All backend API endpoints requiring authentication will fail
- Backend cannot verify JWT tokens
- Database operations through backend will fail

### 3. Hardcoded Supabase Edge Function URL (MEDIUM)
**File**: `apps/realtime-gateway/src/pages/SystemCheck.tsx:112`

**Issue**: Hardcoded Supabase edge function URL that may differ in production.

**Fix Required**:
```typescript
// Change from:
const response = await fetch(`https://xmeudrelqrityernpazp.supabase.co/functions/v1/${funcCheck.name}`, {

// To:
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || "https://xxdahmkfioqzgqvyabek.supabase.co";
const response = await fetch(`${supabaseUrl}/functions/v1/${funcCheck.name}`, {
```

**Impact**:
- System check page may fail in production if Supabase project differs
- Edge function calls will fail

### 4. Relative API Calls Without Base URL (MEDIUM)
**Files**: 
- `apps/realtime-gateway/src/components/admin/EnhancedUploadManager.tsx:189`

**Issue**: Some API calls use relative URLs like `/api/enhanced-context/upload/web-scrape` which may not work if API is on different domain.

**Fix Required**: Update to use `getApiUrl()` utility:
```typescript
// Change from:
const response = await fetch('/api/enhanced-context/upload/web-scrape', {

// To:
const { getApiUrl } = await import('@/utils/apiConfig');
const response = await fetch(getApiUrl('/api/enhanced-context/upload/web-scrape'), {
```

**Impact**:
- API calls may fail if frontend and backend are on different domains
- Upload features may not work in production

## ⚠️ Configuration Issues

### 5. Frontend Build Environment Variables (HIGH)
**Issue**: Frontend needs environment variables set at BUILD TIME (not runtime) for Vite.

**Required Build-Time Variables**:
```bash
# Set these BEFORE running npm run build
export VITE_SUPABASE_URL=https://xxdahmkfioqzgqvyabek.supabase.co
export VITE_SUPABASE_ANON_KEY=your_anon_key_here
# VITE_API_URL is optional - will use relative URLs if not set
```

**Impact**:
- Build will succeed but app won't work if variables are missing
- Authentication will fail
- API calls may fail

### 6. SPA Routing Configuration (HIGH)
**Issue**: Need to ensure nginx/server is configured to serve `index.html` for all routes (SPA fallback).

**Required Nginx Configuration**:
```nginx
location / {
  try_files $uri $uri/ /index.html;
}
```

**Check**: Verify `apps/realtime-gateway/nginx.conf` exists and has SPA routing configured.

**Impact**:
- Direct URLs (e.g., `/bulk-upload`) will return 404
- Browser refresh on sub-routes will fail
- Deep linking won't work

### 7. Backend CORS Configuration (MEDIUM)
**Status**: ✅ Fixed - Production domain added to default CORS origins

**Verification**: Ensure `CORS_ORIGINS` environment variable is set if using custom configuration:
```bash
CORS_ORIGINS=https://dev.hero.labs.pitcrewlabs.ai,http://localhost:3000
```

### 8. Build Output Configuration (LOW)
**File**: `apps/realtime-gateway/vite.config.ts`

**Issue**: Need to verify base path and public path are correct for deployment.

**Current**: No `base` configured (defaults to `/`)

**Impact**: 
- Assets may not load if deployed to subdirectory
- API calls may fail if base path is different

### 9. Error Handling for Network Failures (MEDIUM)
**Issue**: Need to verify error handling for:
- Network timeouts
- CORS errors
- Authentication failures
- API unavailability

**Impact**:
- Poor user experience on errors
- No feedback when services are down
- Silent failures

### 10. Health Check Endpoints (LOW)
**Status**: ✅ Backend has `/health` endpoint

**Verification**: Ensure health checks are configured in deployment:
- Load balancer health checks
- Monitoring/alerts
- Auto-scaling triggers

## 📋 Pre-Deployment Checklist

### Frontend
- [ ] Update Supabase client to use environment variables
- [ ] Fix hardcoded edge function URL in SystemCheck
- [ ] Fix relative API calls in EnhancedUploadManager
- [ ] Set `VITE_SUPABASE_URL` at build time
- [ ] Set `VITE_SUPABASE_ANON_KEY` at build time
- [ ] Verify nginx.conf has SPA routing configured
- [ ] Test build locally: `npm run build`
- [ ] Verify static assets load correctly
- [ ] Test authentication flow
- [ ] Test API calls with relative URLs

### Backend
- [ ] Set `SUPABASE_SERVICE_ROLE_KEY` environment variable
- [ ] Set `ENVIRONMENT=production` environment variable
- [ ] Set `CORS_ORIGINS` environment variable (or verify defaults)
- [ ] Test backend health endpoint: `GET /health`
- [ ] Test authentication endpoints
- [ ] Verify CORS headers in responses
- [ ] Check logs for any startup errors
- [ ] Verify database connections

### Infrastructure
- [ ] Configure nginx/server for SPA routing
- [ ] Set up SSL/HTTPS certificates
- [ ] Configure load balancer health checks
- [ ] Set up monitoring and alerts
- [ ] Configure backup and disaster recovery
- [ ] Verify domain DNS settings
- [ ] Test CDN configuration (if used)
- [ ] Verify firewall rules allow traffic

### Testing
- [ ] Test authentication in production-like environment
- [ ] Test all API endpoints
- [ ] Test file uploads
- [ ] Test error scenarios (network failures, auth failures)
- [ ] Test browser refresh on sub-routes
- [ ] Test deep linking
- [ ] Test on different browsers
- [ ] Test on mobile devices
- [ ] Load testing for API endpoints

## 🔧 Quick Fixes Script

### Fix 1: Update Supabase Client
```typescript
// apps/realtime-gateway/src/integrations/supabase/client.ts
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || "https://xxdahmkfioqzgqvyabek.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh4ZGFobWtmaW9xemdxdnlhYmVrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0MDY1MzQsImV4cCI6MjA3NTk4MjUzNH0.tbDUUFYBKUTMRPTF3HqlJ2L_sm_a9ogH2s3qP4Egz2I";
```

### Fix 2: Update SystemCheck Edge Function URL
```typescript
// apps/realtime-gateway/src/pages/SystemCheck.tsx
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || "https://xxdahmkfioqzgqvyabek.supabase.co";
const response = await fetch(`${supabaseUrl}/functions/v1/${funcCheck.name}`, {
```

### Fix 3: Update EnhancedUploadManager API Calls
```typescript
// apps/realtime-gateway/src/components/admin/EnhancedUploadManager.tsx
const { getApiUrl } = await import('@/utils/apiConfig');
const response = await fetch(getApiUrl('/api/enhanced-context/upload/web-scrape'), {
```

## 📊 Deployment Verification

After deployment, verify:
1. ✅ Frontend loads without console errors
2. ✅ Authentication works (login/logout)
3. ✅ API calls succeed (check network tab)
4. ✅ No CORS errors in console
5. ✅ Direct URLs work (e.g., `/bulk-upload`)
6. ✅ Browser refresh works on sub-routes
7. ✅ File uploads work
8. ✅ All features functional
9. ✅ Error messages are user-friendly
10. ✅ Health checks pass

## 🚨 Common Deployment Errors

### Error: "Failed to fetch"
- **Cause**: CORS configuration, network issues, API unavailable
- **Fix**: Check CORS settings, verify API is running, check network connectivity

### Error: "Authentication failed"
- **Cause**: Missing or incorrect Supabase credentials
- **Fix**: Verify `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set correctly

### Error: "404 on refresh"
- **Cause**: SPA routing not configured
- **Fix**: Configure nginx/server to serve `index.html` for all routes

### Error: "API calls to localhost"
- **Cause**: Old build with hardcoded URLs (should be fixed now)
- **Fix**: Rebuild frontend with updated code

### Error: "Backend authentication failed"
- **Cause**: Missing `SUPABASE_SERVICE_ROLE_KEY`
- **Fix**: Set backend environment variable

## 📝 Notes

- Environment variables for Vite must be set at BUILD TIME
- Backend environment variables must be set at RUNTIME
- CORS configuration must allow production domain
- SPA routing must be configured on server/nginx
- All hardcoded URLs should use utility functions
- Test in production-like environment before deploying

