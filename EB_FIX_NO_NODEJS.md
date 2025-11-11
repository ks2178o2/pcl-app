# Fix: npm command not found in Elastic Beanstalk

## Problem
The prebuild hook is running, but `npm` is not available on your EB instance. This is because you're likely using a **Python platform** which doesn't include Node.js.

**Error from logs:**
```
npm: command not found
```

## Solution: Pre-build Frontend Locally

Since Node.js isn't available on your EB instance, build the frontend locally and include the built files in your deployment.

### Step 1: Build Frontend Locally

```bash
# Set the backend API URL
export VITE_API_URL=https://dev.hero.labs.pitcrewlabs.ai:8000
export VITE_SUPABASE_URL=https://xxdahmkfioqzgqvyabek.supabase.co
export VITE_SUPABASE_ANON_KEY=your_anon_key_here

# Build the frontend
cd apps/realtime-gateway
npm install
npm run build

# Verify build output
ls -la dist/
```

### Step 2: Make Sure dist/ is in Git

The `dist/` folder should be included in your deployment. Check `.gitignore`:

```bash
# Make sure dist/ is NOT ignored
grep -E "^dist|^/dist" apps/realtime-gateway/.gitignore
```

If `dist/` is ignored, you have two options:

**Option A: Remove dist/ from .gitignore** (if you want to commit built files)
```bash
# Edit apps/realtime-gateway/.gitignore
# Remove or comment out: dist/
```

**Option B: Use .ebignore** (recommended - don't commit dist/)
Create `.ebignore` file (similar to .gitignore but for EB):
```bash
# .ebignore - files to exclude from EB deployment
# But make sure dist/ is NOT in this file
```

### Step 3: Disable Prebuild Hook

Since we're pre-building, disable the hook:

```bash
# Rename the hook so it doesn't run
mv .platform/hooks/prebuild/01_build_frontend.sh .platform/hooks/prebuild/01_build_frontend.sh.disabled
```

Or update the hook to exit gracefully if npm isn't available (already done in latest version).

### Step 4: Commit and Deploy

```bash
# Add built files (if committing them)
git add apps/realtime-gateway/dist/

# Or if using .ebignore, make sure dist/ is NOT ignored there
git add .platform/
git commit -m "Pre-build frontend locally, disable prebuild hook"
git push
```

## Alternative: Install Node.js in EB (Advanced)

If you want EB to build the frontend, you can install Node.js in the prebuild hook:

```bash
# Add to .platform/hooks/prebuild/01_build_frontend.sh
# Install Node.js if not available
if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
    yum install -y nodejs
fi
```

But this is more complex and slower. Pre-building is recommended.

## Quick Fix Steps

1. **Build locally:**
   ```bash
   export VITE_API_URL=https://dev.hero.labs.pitcrewlabs.ai:8000
   cd apps/realtime-gateway
   npm run build
   ```

2. **Disable hook:**
   ```bash
   mv .platform/hooks/prebuild/01_build_frontend.sh .platform/hooks/prebuild/01_build_frontend.sh.disabled
   ```

3. **Commit and deploy:**
   ```bash
   git add apps/realtime-gateway/dist/ .platform/
   git commit -m "Pre-build frontend, disable prebuild hook"
   git push
   ```

## Verify

After deploying, check:
- Frontend loads correctly
- Browser console shows correct API URL
- No more deployment errors

