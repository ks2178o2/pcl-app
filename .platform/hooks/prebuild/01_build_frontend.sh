#!/bin/bash
# Prebuild hook for Elastic Beanstalk
# This runs BEFORE the application is deployed
# Ensures VITE_API_URL is available during frontend build

set -e  # Exit on error

echo "=== Frontend Build Hook Started ==="
echo "Current directory: $(pwd)"
echo "Date: $(date)"

# Check if we're in the right location
if [ ! -f "Procfile" ]; then
    echo "Warning: Procfile not found. Current directory structure:"
    ls -la
    echo "Trying to find apps/realtime-gateway..."
fi

# Navigate to frontend directory if it exists
if [ -d "apps/realtime-gateway" ]; then
    echo "Found apps/realtime-gateway directory"
    cd apps/realtime-gateway
    
    echo "Building frontend in: $(pwd)"
    
    # Check if node/npm is available
    if ! command -v node &> /dev/null; then
        echo "ERROR: node command not found. Skipping frontend build."
        echo "Available commands:"
        which node npm || echo "node/npm not in PATH"
        exit 0  # Don't fail deployment if node isn't available
    fi
    
    echo "Node version: $(node --version)"
    echo "NPM version: $(npm --version)"
    
    # Display environment variables (without exposing secrets)
    echo "Environment variables:"
    echo "VITE_API_URL=${VITE_API_URL:0:30}..."  # Show first 30 chars only
    echo "VITE_SUPABASE_URL=${VITE_SUPABASE_URL:0:30}..."
    
    # Ensure environment variables are exported
    export VITE_API_URL="${VITE_API_URL}"
    export VITE_SUPABASE_URL="${VITE_SUPABASE_URL}"
    export VITE_SUPABASE_ANON_KEY="${VITE_SUPABASE_ANON_KEY}"
    
    # Check if node_modules exists, if not install dependencies
    if [ ! -d "node_modules" ]; then
        echo "Installing npm dependencies..."
        npm install || {
            echo "ERROR: npm install failed"
            exit 1
        }
    else
        echo "node_modules directory exists, skipping npm install"
    fi
    
    # Build with environment variables
    echo "Building frontend..."
    npm run build || {
        echo "ERROR: npm run build failed"
        exit 1
    }
    
    # Verify build output
    if [ -d "dist" ]; then
        echo "Frontend build complete! Build output:"
        ls -la dist/ | head -10
        echo "Total files in dist: $(find dist -type f | wc -l)"
    else
        echo "WARNING: dist/ directory not found after build"
        exit 1
    fi
    
    echo "=== Frontend Build Hook Completed Successfully ==="
else
    echo "WARNING: apps/realtime-gateway directory not found"
    echo "Current directory contents:"
    ls -la
    echo "Skipping frontend build - this may be expected if frontend is pre-built"
    exit 0  # Don't fail if directory doesn't exist
fi
