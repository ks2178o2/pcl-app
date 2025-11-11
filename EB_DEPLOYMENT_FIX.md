# Elastic Beanstalk Deployment Fix

## Issue: Deployment Failed

The prebuild hook might be failing. Here are solutions:

## Option 1: Make Hook Optional (Recommended First Step)

If your frontend is already pre-built, the hook might not be necessary. Let's make it optional:

The updated script now:
- ✅ Checks if node/npm is available before trying to build
- ✅ Exits gracefully if frontend directory doesn't exist
- ✅ Provides better error messages

## Option 2: Check EB Platform

What platform are you using?

1. **Go to EB Console** → Your Environment → **Configuration** → **Platform**
2. Check the platform type:
   - **Python** - May not have Node.js installed
   - **Node.js** - Should have Node.js
   - **Docker** - Uses Dockerfile

## Option 3: Pre-build Frontend Locally

If EB doesn't have Node.js or the build is failing:

1. **Build locally:**
   ```bash
   export VITE_API_URL=https://your-backend-url
   cd apps/realtime-gateway
   npm install
   npm run build
   ```

2. **Deploy the built files:**
   - Include the `dist/` folder in your deployment
   - The prebuild hook will skip if `dist/` already exists

## Option 4: Check EB Logs

1. **Go to EB Console** → Your Environment → **Logs**
2. **Request Logs** → **Last 100 Lines**
3. Look for:
   - "=== Frontend Build Hook Started ==="
   - Any error messages
   - "node command not found" or similar

## Option 5: Disable Prebuild Hook Temporarily

If you need to deploy urgently:

1. **Rename the hook:**
   ```bash
   mv .platform/hooks/prebuild/01_build_frontend.sh .platform/hooks/prebuild/01_build_frontend.sh.disabled
   ```

2. **Commit and redeploy:**
   ```bash
   git add .platform/
   git commit -m "Disable prebuild hook temporarily"
   git push
   ```

3. **Build frontend locally** and include `dist/` in deployment

## Next Steps

1. **Check EB Platform** - What platform type are you using?
2. **Check EB Logs** - What's the actual error in eb-engine.log?
3. **Share the error** - Copy the error from EB logs so we can fix it

The updated script is more defensive and should provide better error messages.

