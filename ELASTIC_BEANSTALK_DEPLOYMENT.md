# Elastic Beanstalk Deployment Guide

## Setting VITE_API_URL for Elastic Beanstalk

For Elastic Beanstalk deployments, `VITE_API_URL` must be set **before** the frontend build runs. Here are three methods:

## Method 1: Elastic Beanstalk Console (Recommended)

1. Go to AWS Elastic Beanstalk Console
2. Select your environment
3. Go to **Configuration** → **Software** → **Environment properties**
4. Add these environment variables:
   ```
   VITE_API_URL = https://your-backend-api-url-here
   VITE_SUPABASE_URL = https://xxdahmkfioqzgqvyabek.supabase.co
   VITE_SUPABASE_ANON_KEY = your_supabase_anon_key_here
   ```
5. Click **Apply**
6. Redeploy your application

## Method 2: Using .ebextensions Config File

I've created `.ebextensions/01-environment.config` which sets environment variables.

**Important**: Update the values in `.ebextensions/01-environment.config`:
- Replace `https://your-backend-api-url-here` with your actual backend API URL
- Replace `your_supabase_anon_key_here` with your actual Supabase anon key
- Replace `your_service_role_key_here` with your Supabase service role key

Then deploy:
```bash
eb deploy
# or
git aws.push
```

## Method 3: Using EB CLI

```bash
eb setenv VITE_API_URL=https://your-backend-api-url-here \
          VITE_SUPABASE_URL=https://xxdahmkfioqzgqvyabek.supabase.co \
          VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here

eb deploy
```

## Finding Your Backend API URL

Your backend API URL depends on your Elastic Beanstalk setup:

1. **If backend is on same EB environment**: 
   - Check your EB environment URL (e.g., `https://your-app.elasticbeanstalk.com`)
   - Backend might be at: `https://your-app.elasticbeanstalk.com:8000`
   - Or if using a load balancer: `https://api.your-domain.com`

2. **If backend is separate**:
   - Check your backend EB environment URL
   - Or check your API Gateway/ALB URL

3. **Check your Procfile**:
   - Your `Procfile` shows: `web: gunicorn ... --bind :8000`
   - This means backend runs on port 8000
   - If frontend and backend are on same EB environment, you might need a reverse proxy

## Verifying the Fix

After deploying:

1. **Check browser console** - Look for:
   - `🔍 API Config Debug:` - Should show `VITE_API_URL: https://your-backend-url`
   - `✅ Using VITE_API_URL:` - Should show your backend URL
   - `🌐 Fetching jobs from:` - Should show full backend URL, not relative

2. **Check Network tab**:
   - API requests should go to your backend URL
   - Should receive JSON responses, not HTML

## Troubleshooting

### Issue: Still seeing relative URLs
**Solution**: Environment variable wasn't set before build. Check:
- EB console shows the variable is set
- Build logs show the variable during build
- Rebuild/redeploy after setting variables

### Issue: Backend not accessible
**Solution**: 
- Verify backend is running: `curl https://your-backend-url/health`
- Check CORS settings in backend
- Verify security groups allow traffic

### Issue: CORS errors
**Solution**: Ensure backend `CORS_ORIGINS` includes your frontend domain:
```python
CORS_ORIGINS=https://dev.hero.labs.pitcrewlabs.ai,http://localhost:3000
```

## Next Steps

1. **Update `.ebextensions/01-environment.config`** with your actual values
2. **Set environment variables in EB Console** (Method 1 - easiest)
3. **Redeploy** your application
4. **Check browser console** for the debug logs
5. **Verify API calls work**

## Important Notes

- **VITE_API_URL is build-time**: Must be set before `npm run build` runs
- **Environment variables in EB**: Available during deployment/build process
- **Backend URL**: Make sure it's accessible from the frontend domain
- **CORS**: Backend must allow requests from frontend domain

