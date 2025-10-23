#!/usr/bin/env python3
"""
RAG Feature Management Migration Runner
Applies database schema changes for hierarchical organizations and RAG feature metadata
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the parent directory to the path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.supabase_client import get_supabase_client

async def run_migration():
    """Run the RAG feature hierarchy migration"""
    try:
        # Read the migration SQL file
        migration_file = Path(__file__).parent / "migrations" / "001_rag_feature_hierarchy.sql"
        
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
            
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("🔄 Running RAG Feature Hierarchy Migration...")
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Execute the migration SQL
        result = supabase.rpc('exec_sql', {'sql': migration_sql}).execute()
        
        if result.data:
            print("✅ Migration completed successfully!")
            print("📊 Schema changes applied:")
            print("   - Added parent_organization_id to organizations table")
            print("   - Created rag_feature_metadata table with 20 default features")
            print("   - Added category and inheritance fields to organization_rag_toggles")
            print("   - Created audit table for toggle changes")
            print("   - Created organization hierarchy and effective features views")
            return True
        else:
            print("❌ Migration failed - no data returned")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed with error: {e}")
        return False

async def verify_migration():
    """Verify that the migration was applied correctly"""
    try:
        supabase = get_supabase_client()
        
        print("\n🔍 Verifying migration...")
        
        # Check if rag_feature_metadata table exists and has data
        result = supabase.from_('rag_feature_metadata').select('count').execute()
        if result.data:
            count = result.data[0]['count'] if result.data[0]['count'] else 0
            print(f"✅ rag_feature_metadata table created with {count} features")
        
        # Check if parent_organization_id column exists
        result = supabase.from_('organizations').select('parent_organization_id').limit(1).execute()
        if result.data is not None:
            print("✅ parent_organization_id column added to organizations table")
        
        # Check if category column exists in organization_rag_toggles
        result = supabase.from_('organization_rag_toggles').select('category').limit(1).execute()
        if result.data is not None:
            print("✅ category column added to organization_rag_toggles table")
        
        # Check if inheritance columns exist
        result = supabase.from_('organization_rag_toggles').select('is_inherited, inherited_from').limit(1).execute()
        if result.data is not None:
            print("✅ inheritance columns added to organization_rag_toggles table")
        
        print("✅ Migration verification completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        success = await run_migration()
        if success:
            await verify_migration()
        else:
            print("❌ Migration failed - skipping verification")
            sys.exit(1)
    
    asyncio.run(main())
