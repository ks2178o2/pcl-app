#!/usr/bin/env python3
"""
Fix stuck transcripts by updating them with a timeout message or re-triggering transcription
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
from dotenv import load_dotenv

env_paths = [
    Path(__file__).parent.parent / '.env',
    Path(__file__).parent.parent.parent / '.env',
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fix_stuck_transcripts(job_id: str = None, force_update: bool = False):
    """Fix transcripts that are stuck as 'Processing...'"""
    
    # Get call records with "Processing..." transcript
    query = supabase.table("call_records").select(
        "id, transcript, bulk_import_job_id, created_at, audio_file_url"
    ).like("transcript", "Processing%")
    
    if job_id:
        query = query.eq("bulk_import_job_id", job_id)
    
    call_records_result = query.execute()
    
    if not call_records_result.data:
        print("No stuck transcripts found")
        return
    
    print(f"Found {len(call_records_result.data)} stuck transcripts\n")
    
    for cr in call_records_result.data:
        cr_id = cr['id']
        created_at = datetime.fromisoformat(cr['created_at'].replace('Z', '+00:00'))
        age = datetime.now(created_at.tzinfo) - created_at
        
        print(f"Call Record ID: {cr_id}")
        print(f"  Age: {age.total_seconds() / 60:.1f} minutes")
        print(f"  Created: {created_at}")
        
        # If older than 10 minutes, mark as timeout
        if age.total_seconds() > 600 or force_update:
            timeout_msg = "Transcription timeout - manual review required. Please check transcription service status."
            try:
                update_result = supabase.table("call_records").update({
                    "transcript": timeout_msg
                }).eq("id", cr_id).execute()
                
                if update_result.data:
                    print(f"  ✅ Updated to timeout message")
                else:
                    print(f"  ⚠️  Update returned no data")
            except Exception as e:
                print(f"  ❌ Error updating: {e}")
        else:
            print(f"  ⏳ Still within timeout window ({age.total_seconds() / 60:.1f} min < 10 min)")
        print()
    
    print(f"\n✅ Processed {len(call_records_result.data)} call records")

if __name__ == "__main__":
    import sys
    job_id = sys.argv[1] if len(sys.argv) > 1 else None
    force = "--force" in sys.argv
    
    if job_id:
        print(f"Fixing stuck transcripts for job: {job_id}\n")
    else:
        print("Fixing all stuck transcripts\n")
    
    fix_stuck_transcripts(job_id, force_update=force)

