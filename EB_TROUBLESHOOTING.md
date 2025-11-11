# Elastic Beanstalk Troubleshooting Guide

## Issue: VITE_API_URL Not Working After Setting in EB Console

### Step 1: Verify Environment Variable is Set

1. Go to EB Console → Your Environment → **Configuration** → **Software**
2. Scroll to **Environment properties**
3. Verify `VITE_API_URL` is listed and has the correct value
4. If not set, add it and click **Apply**

### Step 2: Check Build Logs

After redeploying, check the build logs:

1. EB Console → Your Environment → **Logs** → **Request Logs**
2. Look for build output
3. Search for "VITE_API_URL" in the logs
4. Verify it shows your backend URL

### Step 3: Verify Build Process

**Question**: Are you deploying pre-built files or is EB building during deployment?

**If deploying pre-built files:**
- You need to build locally with `VITE_API_URL` set
- Then deploy the built `dist/` folder
- The `.platform/hooks/prebuild/` script won't run

**If EB is building:**
- The `.platform/hooks/prebuild/01_build_frontend.sh` script should run
- Check logs for "=== Frontend Build Hook ==="

### Step 4: Check Browser Console

After deploying, open your app and check browser console:

1. Look for `🔍 API Config Debug:` message
2. Check what `VITE_API_URL` shows:
   - ✅ If it shows your backend URL → Good!
   - ❌ If it shows "NOT SET" → Build didn't include it

### Step 5: Force Rebuild

If the variable is set but not working:

1. **Option A**: Create a `.env.production` file in `apps/realtime-gateway/`:
   ```bash
   VITE_API_URL=https://your-backend-url
   VITE_SUPABASE_URL=https://xxdahmkfioqzgqvyabek.supabase.co
   VITE_SUPABASE_ANON_KEY=your_key_here
   ```

2. **Option B**: Build locally and deploy pre-built files:
   ```bash
   export VITE_API_URL=https://your-backend-url
   cd apps/realtime-gateway
   npm run build
   # Then deploy the dist/ folder
   ```

### Step 6: Check EB Platform Version

Different EB platforms handle builds differently:

- **Python platform**: May need custom build scripts
- **Node.js platform**: Should run npm scripts automatically
- **Docker platform**: Uses Dockerfile

Check your platform in: **Configuration** → **Platform**

## Common Issues

### Issue: Environment Variable Not Available During Build
**Solution**: Use `.platform/hooks/prebuild/` scripts (already created)

### Issue: Build Happens Before Environment Variables Load
**Solution**: The prebuild hook should handle this, but verify in logs

### Issue: Wrong Backend URL
**Solution**: Double-check the URL in EB console matches your actual backend

### Issue: CORS Errors
**Solution**: Ensure backend `CORS_ORIGINS` includes your frontend domain

## Next Steps

1. **Check EB logs** after next deployment
2. **Look for the build hook output** in logs
3. **Check browser console** for debug messages
4. **Share the logs** if still not working

## Quick Test

To test if the build hook works:

1. Deploy with the new `.platform/hooks/prebuild/` files
2. Check logs for "=== Frontend Build Hook ==="
3. Verify it shows your VITE_API_URL value
4. Check browser console for debug output

