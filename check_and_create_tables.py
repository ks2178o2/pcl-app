#!/usr/bin/env python3
"""
Script to check existing tables in Supabase and create missing ones for testing
"""

import os
import asyncio
from supabase import create_client, Client

# Set up environment variables
# These should be set in your environment or CI/CD pipeline
# Example: export SUPABASE_URL="your_supabase_url"
# Example: export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"

# Check if environment variables are set
if not os.environ.get('SUPABASE_URL'):
    print("❌ SUPABASE_URL environment variable not set")
    print("Please set it with: export SUPABASE_URL='your_supabase_url'")
    exit(1)

if not os.environ.get('SUPABASE_SERVICE_ROLE_KEY'):
    print("❌ SUPABASE_SERVICE_ROLE_KEY environment variable not set")
    print("Please set it with: export SUPABASE_SERVICE_ROLE_KEY='your_service_role_key'")
    exit(1)

def get_supabase_client() -> Client:
    """Get Supabase client"""
    url = os.environ['SUPABASE_URL']
    key = os.environ['SUPABASE_SERVICE_ROLE_KEY']
    return create_client(url, key)

async def check_existing_tables():
    """Check what tables exist in the database"""
    supabase = get_supabase_client()
    
    print("🔍 Checking existing tables in your Supabase database...")
    print("=" * 60)
    
    # Try to query each table to see if it exists
    tables_to_check = [
        'audit_logs',
        'rag_context_items', 
        'organizations',
        'rag_feature_metadata',
        'organization_rag_toggles',
        'global_context_items',
        'tenant_context_access',
        'context_sharing',
        'organization_context_quotas',
        'context_upload_logs',
        'tenant_isolation_policies',
        'cross_tenant_permissions',
        'quota_usage_logs',
        'isolation_violation_logs'
    ]
    
    existing_tables = []
    missing_tables = []
    
    for table in tables_to_check:
        try:
            # Try to query the table with a limit to see if it exists
            result = supabase.from_(table).select('*').limit(1).execute()
            existing_tables.append(table)
            print(f"✅ {table} - EXISTS")
        except Exception as e:
            missing_tables.append(table)
            print(f"❌ {table} - MISSING ({str(e)[:50]}...)")
    
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY:")
    print(f"✅ Existing tables: {len(existing_tables)}")
    print(f"❌ Missing tables: {len(missing_tables)}")
    
    if missing_tables:
        print(f"\n🔧 Missing tables: {', '.join(missing_tables)}")
        print("\n💡 To create missing tables, run:")
        print("   python setup_supabase.py")
        print("   # or")
        print("   psql -d your_database -f enhanced_rag_context_schema.sql")
        print("   psql -d your_database -f tenant_isolation_schema.sql")
    else:
        print("\n🎉 All required tables exist!")
    
    return existing_tables, missing_tables

async def create_sample_data():
    """Create sample data for testing"""
    supabase = get_supabase_client()
    
    print("\n🔧 Creating sample data for testing...")
    print("=" * 60)
    
    try:
        # Create sample organization
        org_data = {
            'id': 'test-org-123',
            'name': 'Test Organization',
            'description': 'Test organization for development',
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        result = supabase.from_('organizations').upsert(org_data).execute()
        print("✅ Created test organization")
        
        # Create sample RAG feature metadata
        rag_feature_data = {
            'rag_feature': 'test_feature',
            'feature_name': 'Test Feature',
            'description': 'Test RAG feature for development',
            'category': 'test',
            'is_active': True,
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        result = supabase.from_('rag_feature_metadata').upsert(rag_feature_data).execute()
        print("✅ Created test RAG feature metadata")
        
        # Create sample organization RAG toggle
        toggle_data = {
            'organization_id': 'test-org-123',
            'rag_feature': 'test_feature',
            'enabled': True,
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        result = supabase.from_('organization_rag_toggles').upsert(toggle_data).execute()
        print("✅ Created test organization RAG toggle")
        
        print("\n🎉 Sample data created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")

async def main():
    """Main function"""
    print("🏁 PitCrew Labs - Database Setup Checker")
    print("=" * 60)
    
    # Check existing tables
    existing_tables, missing_tables = await check_existing_tables()
    
    # Create sample data if all tables exist
    if not missing_tables:
        await create_sample_data()
    
    print("\n" + "=" * 60)
    print("✅ Database setup check complete!")

if __name__ == "__main__":
    asyncio.run(main())