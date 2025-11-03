"""
Quick script to check if v1.0.4 tables exist in the database
"""
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

from services.supabase_client import get_supabase_client

def check_tables():
    supabase = get_supabase_client()
    
    # Check for v1.0.4 tables
    tables_to_check = [
        'user_invitations',
        'login_audit', 
        'user_devices'
    ]
    
    print("Checking v1.0.4 tables...")
    
    for table in tables_to_check:
        try:
            # Try to select from table
            result = supabase.from_(table).select('id').limit(1).execute()
            print(f"✅ {table}: EXISTS")
        except Exception as e:
            print(f"❌ {table}: NOT FOUND - {str(e)[:100]}")
    
    # Check profiles table for 2FA columns
    try:
        result = supabase.from_('profiles').select('id, two_factor_enabled, two_factor_secret').limit(1).execute()
        if result.data:
            profile = result.data[0]
            if 'two_factor_enabled' in profile:
                print("✅ profiles.two_factor_enabled: EXISTS")
            if 'two_factor_secret' in profile:
                print("✅ profiles.two_factor_secret: EXISTS")
            else:
                print("⚠️  profiles 2FA columns: MISSING")
    except Exception as e:
        print(f"⚠️  Could not check profiles table: {str(e)[:100]}")

if __name__ == '__main__':
    check_tables()

