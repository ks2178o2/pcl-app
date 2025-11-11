#!/usr/bin/env python3
"""
Check transcription queue status
"""
import os
import sys
from pathlib import Path

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

# Get call records with "Processing..." transcript
call_records_result = supabase.table("call_records").select(
    "id, transcript, bulk_import_job_id, created_at"
).like("transcript", "Processing%").limit(10).execute()

if call_records_result.data:
    print(f"Found {len(call_records_result.data)} call records with 'Processing...' transcript:\n")
    for cr in call_records_result.data:
        print(f"  Call Record ID: {cr['id']}")
        print(f"  Transcript: {cr['transcript']}")
        print(f"  Job ID: {cr.get('bulk_import_job_id')}")
        print(f"  Created: {cr.get('created_at')}")
        
        # Check transcription_queue
        try:
            queue_result = supabase.table("transcription_queue").select("*").eq("call_record_id", cr['id']).execute()
            if queue_result.data:
                queue_item = queue_result.data[0]
                print(f"  Queue Status: {queue_item.get('status')}")
                print(f"  Queue Progress: {queue_item.get('progress')}")
                print(f"  Queue Provider: {queue_item.get('provider')}")
                print(f"  Queue Error: {queue_item.get('error')}")
            else:
                print(f"  ⚠️  No transcription_queue entry found!")
        except Exception as e:
            print(f"  ⚠️  Error checking queue: {e}")
        print()
else:
    print("No call records with 'Processing...' transcript found")

