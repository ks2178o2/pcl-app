# Deployment Steps - What We've Done

## ✅ Completed Steps

### Step 1: Build Frontend Locally ✅
- Built with `VITE_API_URL=https://dev.hero.labs.pitcrewlabs.ai:8000`
- Frontend code now has correct backend URL baked in
- Build output in `apps/realtime-gateway/dist/`

### Step 2: Include dist/ in Deployment ✅
- Force-added `dist/` folder to git (it was in .gitignore)
- Committed the built files
- Files are ready for deployment

### Step 3: Push to Repository ✅
- Pushed to `origin/main`
- Code is in your GitHub repository

## 🔄 Next Step: Deploy to AWS Elastic Beanstalk

### How to Deploy

**If EB is connected to your Git repo:**
1. EB should automatically detect the push
2. Go to EB Console → Your Environment
3. Check "Events" tab for deployment status
4. Wait for deployment to complete

**If deploying manually:**
1. Go to AWS Elastic Beanstalk Console
2. Select your environment
3. Click "Upload and Deploy"
4. Choose:
   - **Source**: "Version Label" (if using git)
   - **Or**: Upload a zip file of your code

**Using EB CLI (if installed):**
```bash
eb deploy
```

## ✅ After Deployment

1. **Check deployment status:**
   - EB Console → Your Environment → Events
   - Should see "Environment update completed successfully"

2. **Test the fix:**
   - Open your app: `https://dev.hero.labs.pitcrewlabs.ai/bulk-upload`
   - Open browser console (F12)
   - Look for: `🔍 API Config Debug:`
   - Should show: `VITE_API_URL: https://dev.hero.labs.pitcrewlabs.ai:8000`
   - Should see: `🌐 Fetching jobs from: https://dev.hero.labs.pitcrewlabs.ai:8000/api/bulk-import/jobs`
   - Should get JSON response (not HTML) ✅

3. **Verify API calls work:**
   - Check Network tab in browser
   - API requests should go to `https://dev.hero.labs.pitcrewlabs.ai:8000/api/...`
   - Should receive JSON responses

## Troubleshooting

**If deployment fails:**
- Check EB logs (we know how to do this now!)
- Look for any errors in the deployment process

**If API still doesn't work:**
- Check browser console for debug messages
- Verify `VITE_API_URL` is shown correctly
- Check Network tab to see what URL is being called

## Summary

✅ Frontend built with correct backend URL
✅ Built files committed and pushed
🔄 Ready to deploy to AWS EB
⏳ After deployment: Test and verify it works!

