#!/usr/bin/env python3
"""
Setup script for real Supabase database testing
"""

import os
import sys

def setup_supabase_credentials():
    """Interactive setup for Supabase credentials"""
    print("🔧 SUPABASE DATABASE TESTING SETUP")
    print("==================================")
    print()
    print("This script will help you set up your real Supabase credentials")
    print("for testing against your actual database.")
    print()
    
    # Get Supabase URL
    supabase_url = input("Enter your Supabase Project URL (e.g., https://abc123.supabase.co): ").strip()
    if not supabase_url.startswith('https://') or '.supabase.co' not in supabase_url:
        print("❌ Invalid Supabase URL format")
        return False
    
    # Get Service Role Key
    service_key = input("Enter your Supabase Service Role Key (starts with 'eyJ'): ").strip()
    if not service_key.startswith('eyJ'):
        print("❌ Invalid Service Role Key format")
        return False
    
    # Get Anon Key
    anon_key = input("Enter your Supabase Anon Key (starts with 'eyJ'): ").strip()
    if not anon_key.startswith('eyJ'):
        print("❌ Invalid Anon Key format")
        return False
    
    # Get OpenAI API Key (optional)
    openai_key = input("Enter your OpenAI API Key (optional, press Enter to skip): ").strip()
    
    # Create .env file
    env_content = f"""# Supabase Configuration - Real Database
SUPABASE_URL={supabase_url}
SUPABASE_SERVICE_ROLE_KEY={service_key}
SUPABASE_ANON_KEY={anon_key}

# OpenAI Configuration (for RAG features)
OPENAI_API_KEY={openai_key}

# Database Configuration
DATABASE_URL=postgresql://postgres:your-password@{supabase_url.replace('https://', '').replace('.supabase.co', '')}.supabase.co:5432/postgres

# Application Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Security Configuration
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Redis Configuration (for caching)
REDIS_URL=redis://localhost:6379

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
"""
    
    # Write .env file
    env_path = os.path.join(os.path.dirname(__file__), 'apps', 'app-api', '.env')
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print()
    print("✅ .env file created successfully!")
    print(f"📁 Location: {env_path}")
    print()
    print("🎯 NEXT STEPS:")
    print("1. Ensure your Supabase database has the required tables:")
    print("   - audit_logs")
    print("   - rag_context_items") 
    print("   - profiles")
    print()
    print("2. Run the real database tests:")
    print("   cd apps/app-api")
    print("   python -m pytest __tests__/test_real_database.py -v")
    print()
    print("🚀 You're ready to test against your real Supabase database!")
    
    return True

if __name__ == "__main__":
    setup_supabase_credentials()
