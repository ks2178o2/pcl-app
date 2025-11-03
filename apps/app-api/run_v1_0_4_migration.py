"""
Execute v1.0.4 database migration
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import Supabase client
sys.path.insert(0, os.path.dirname(__file__))
from services.supabase_client import get_supabase_client

def run_migration():
    """Read and execute the SQL migration file"""
    # Read SQL file
    sql_file = Path(__file__).parent.parent / 'V1_0_4_AUTH_DATABASE_SCHEMA.sql'
    
    if not sql_file.exists():
        print(f"❌ Migration file not found: {sql_file}")
        return False
    
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    # Split into individual statements (simple approach)
    # Remove comments and split by semicolon
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        line = line.strip()
        # Skip empty lines and comments
        if not line or line.startswith('--'):
            continue
        current_statement.append(line)
        
        if line.endswith(';'):
            statements.append(' '.join(current_statement))
            current_statement = []
    
    # Execute via Supabase
    supabase = get_supabase_client()
    
    print(f"Executing {len(statements)} SQL statements...")
    
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements, 1):
        if not statement.strip():
            continue
        
        try:
            # Supabase doesn't have direct SQL execution in the Python client
            # We'll need to use the REST API or rpc functions
            # For now, just track what we're attempting
            print(f"  [{i}/{len(statements)}] Executing statement...")
            # Note: This won't actually execute via the Python client
            # We need to use the Supabase REST API or connect via psycopg2
            success_count += 1
        except Exception as e:
            print(f"  ❌ Error in statement {i}: {e}")
            error_count += 1
    
    print(f"\nResults: {success_count} successful, {error_count} errors")
    print("\n⚠️  Note: Supabase Python client doesn't support direct SQL execution")
    print("   Please run this migration in the Supabase SQL Editor instead.")
    
    return error_count == 0


if __name__ == '__main__':
    print("=" * 70)
    print("v1.0.4 Database Migration")
    print("=" * 70)
    print("\n⚠️  This script cannot execute SQL directly.")
    print("   Please run V1_0_4_AUTH_DATABASE_SCHEMA.sql in Supabase SQL Editor.")
    print("\nAlternative: Would you like me to create a migration guide?")
    print("=" * 70)

