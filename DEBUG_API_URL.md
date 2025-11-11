# Debugging API URL Issues

## Current Error
```
Error loading jobs: SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

This means the API is returning HTML (likely the frontend's index.html) instead of JSON.

## Debug Steps

### 1. Check Browser Console
After the fix, you should see debug logs:
- `🔍 API Config Debug:` - Shows if VITE_API_URL is set
- `🌐 Fetching jobs from:` - Shows the actual URL being called
- `📡 Response status:` - Shows HTTP status code
- `📡 Response headers:` - Shows response headers

### 2. Verify VITE_API_URL Was Set at Build Time

**Important**: VITE_API_URL must be set BEFORE running `npm run build`. It's a build-time variable, not runtime.

Check your build process:
```bash
# Before building, verify it's set:
echo $VITE_API_URL

# If empty, set it:
export VITE_API_URL=https://your-backend-api-url

# Then build:
npm run build
```

### 3. Verify Backend API is Accessible

Test the backend API directly:
```bash
# Replace with your actual backend URL
curl https://your-backend-api-url/api/bulk-import/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

Should return JSON, not HTML.

### 4. Check What URL is Actually Being Called

Look in browser DevTools → Network tab:
1. Find the request to `/api/bulk-import/jobs`
2. Check the "Request URL" - what does it show?
3. Check the response - is it HTML or JSON?

### 5. Common Issues

#### Issue: VITE_API_URL not in build
**Symptom**: Console shows `VITE_API_URL: NOT SET`
**Fix**: Set environment variable before building

#### Issue: Wrong backend URL
**Symptom**: Console shows wrong URL or 404 errors
**Fix**: Verify backend URL is correct and accessible

#### Issue: CORS errors
**Symptom**: CORS policy errors in console
**Fix**: Ensure backend CORS includes your frontend domain

#### Issue: Backend not running
**Symptom**: Connection refused or timeout errors
**Fix**: Ensure backend is deployed and running

## Next Steps

1. **Check the browser console** - Look for the debug logs I added
2. **Share the console output** - Especially:
   - What does `🔍 API Config Debug` show?
   - What URL does `🌐 Fetching jobs from` show?
   - What does the Network tab show for the request?

This will help identify exactly what's wrong.

