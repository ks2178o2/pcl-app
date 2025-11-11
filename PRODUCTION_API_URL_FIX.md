# Production API URL Configuration Fix

## Problem
The error `Unexpected token '<', "<!DOCTYPE "... is not valid JSON` occurs because:
- The frontend is using relative URLs (`/api/bulk-import/jobs`)
- In production, this hits the frontend server (serving static HTML) instead of the backend API
- The backend API is not accessible via relative URLs

## Solution

You have **two options**:

### Option 1: Set VITE_API_URL at Build Time (Recommended)

Set the backend API URL as an environment variable **before building** the frontend:

```bash
# For AWS deployment, set this in your build environment
export VITE_API_URL=https://api.dev.hero.labs.pitcrewlabs.ai
# OR if backend is on same domain but different port:
# export VITE_API_URL=https://dev.hero.labs.pitcrewlabs.ai:8000

# Then build
cd apps/realtime-gateway
npm run build
```

**Where to set this:**
- **AWS CodeBuild/CodePipeline**: Add as environment variable in build configuration
- **GitHub Actions**: Add as secret/environment variable
- **Local build**: Export in your shell before building
- **Docker**: Add as ARG/ENV in Dockerfile

### Option 2: Configure Reverse Proxy (If API is on same domain)

If your backend API is on the same domain (e.g., via nginx reverse proxy), configure nginx to route `/api/*` to the backend:

```nginx
server {
    listen 80;
    server_name dev.hero.labs.pitcrewlabs.ai;

    # Serve frontend static files
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Quick Fix for Current Deployment

1. **Find your backend API URL**:
   - Check your AWS deployment configuration
   - It might be something like: `https://api.dev.hero.labs.pitcrewlabs.ai` or `https://dev.hero.labs.pitcrewlabs.ai:8000`

2. **Rebuild frontend with VITE_API_URL**:
   ```bash
   export VITE_API_URL=https://your-backend-api-url-here
   cd apps/realtime-gateway
   npm run build
   ```

3. **Redeploy the frontend**

## Verification

After fixing, check the browser console:
- ✅ Should see API calls to the correct backend URL
- ✅ Should receive JSON responses, not HTML
- ✅ No more "Unexpected token '<'" errors

## Current Status

The `apiConfig.ts` utility now:
- ✅ Uses `VITE_API_URL` if set (build-time)
- ✅ Falls back to relative URLs in production (with warning)
- ✅ Defaults to `localhost:8001` in development

**Action Required**: Set `VITE_API_URL` in your production build environment.

