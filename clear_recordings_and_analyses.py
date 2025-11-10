#!/usr/bin/env python3
"""
Clear all call recordings and call analyses from the database.
This script safely deletes data in the correct order to respect foreign key constraints.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
project_root = Path(__file__).parent
env_path = project_root / "apps" / "app-api" / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing SUPABASE_URL or SUPABASE_KEY in environment")
    print("   Please set these in apps/app-api/.env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def clear_recordings_and_analyses():
    """Delete all call recordings, analyses, and related data."""
    
    try:
        print("🗑️  Starting cleanup of recordings and analyses...")
        
        # Step 1: Delete call_analyses first (has foreign key to call_records)
        print("  1. Deleting call analyses...")
        analyses_result = supabase.table('call_analyses').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        analyses_count = len(analyses_result.data) if analyses_result.data else 0
        print(f"     ✓ Deleted {analyses_count} call analyses")
        
        # Step 2: Delete call_chunks (related to call_records)
        print("  2. Deleting call chunks...")
        try:
            chunks_result = supabase.table('call_chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            chunks_count = len(chunks_result.data) if chunks_result.data else 0
            print(f"     ✓ Deleted {chunks_count} call chunks")
        except Exception as e:
            print(f"     ⚠️  Could not delete chunks (table might not exist): {e}")
        
        # Step 3: Delete call_records (main recordings table)
        print("  3. Deleting call records...")
        records_result = supabase.table('call_records').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        records_count = len(records_result.data) if records_result.data else 0
        print(f"     ✓ Deleted {records_count} call records")
        
        # Step 4: Also clear transcription_queue if it exists
        print("  4. Clearing transcription queue...")
        try:
            transcription_result = supabase.table('transcription_queue').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            transcription_count = len(transcription_result.data) if transcription_result.data else 0
            print(f"     ✓ Deleted {transcription_count} transcription queue entries")
        except Exception as e:
            print(f"     ⚠️  Could not delete transcription queue (table might not exist): {e}")
        
        print("\n✅ Cleanup complete!")
        print(f"   Summary:")
        print(f"   - Call Analyses: {analyses_count}")
        print(f"   - Call Chunks: {chunks_count}")
        print(f"   - Call Records: {records_count}")
        print(f"   - Transcription Queue: {transcription_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("⚠️  WARNING: This will delete ALL call recordings and analyses from the database!")
    print("   Press Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n❌ Cancelled")
        sys.exit(0)
    
    success = clear_recordings_and_analyses()
    sys.exit(0 if success else 1)

