#!/bin/bash
# Prebuild hook for Elastic Beanstalk
# This runs BEFORE the application is deployed
# Ensures VITE_API_URL is available during frontend build

set -e

echo "=== Frontend Build Hook ==="
echo "Current directory: $(pwd)"
echo "Environment variables:"
env | grep VITE || echo "No VITE_* variables found"

# Navigate to frontend directory
if [ -d "apps/realtime-gateway" ]; then
    cd apps/realtime-gateway
    
    echo "Building frontend in: $(pwd)"
    echo "VITE_API_URL=${VITE_API_URL}"
    echo "VITE_SUPABASE_URL=${VITE_SUPABASE_URL}"
    
    # Ensure environment variables are exported
    export VITE_API_URL="${VITE_API_URL}"
    export VITE_SUPABASE_URL="${VITE_SUPABASE_URL}"
    export VITE_SUPABASE_ANON_KEY="${VITE_SUPABASE_ANON_KEY}"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing npm dependencies..."
        npm install
    fi
    
    # Build with environment variables
    echo "Building frontend..."
    npm run build
    
    echo "Frontend build complete!"
    ls -la dist/ || echo "dist/ directory not found"
else
    echo "Warning: apps/realtime-gateway directory not found"
    echo "Skipping frontend build"
fi

