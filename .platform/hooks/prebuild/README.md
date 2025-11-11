# Elastic Beanstalk Prebuild Hooks

These hooks run during the deployment process BEFORE your application starts.

## How It Works

1. `.platform/hooks/prebuild/01_build_frontend.sh` runs during deployment
2. It reads environment variables from EB configuration
3. Builds the frontend with those variables baked in
4. The built files are then deployed

## Making the Script Executable

After adding these files, make sure they're executable:

```bash
chmod +x .platform/hooks/prebuild/01_build_frontend.sh
git add .platform/
git commit -m "Add EB prebuild hook for frontend"
```

## Verifying It Works

After deploying, check the EB logs:
1. Go to Elastic Beanstalk Console
2. Select your environment
3. Go to **Logs** → **Request Logs** → **Last 100 Lines**
4. Look for "=== Frontend Build Hook ===" messages
5. Verify it shows your VITE_API_URL value

