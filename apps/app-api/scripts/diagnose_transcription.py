#!/usr/bin/env python3
"""
Diagnose transcription issues by checking:
1. API keys availability
2. Signed URL generation
3. Transcription queue status
4. Recent transcription errors
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
from dotenv import load_dotenv
import requests

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
DEEPGRAM_KEY = os.getenv("DEEPGRAM_API_KEY")
ASSEMBLYAI_KEY = os.getenv("ASSEMBLY_AI_API_KEY") or os.getenv("ASSEMBLYAI_API_KEY")

print("=" * 80)
print("TRANSCRIPTION DIAGNOSTICS")
print("=" * 80)

# Check API keys
print("\n1. API Keys:")
print(f"   DEEPGRAM_API_KEY: {'✅ SET' if DEEPGRAM_KEY else '❌ NOT SET'}")
print(f"   ASSEMBLY_AI_API_KEY: {'✅ SET' if ASSEMBLYAI_KEY else '❌ NOT SET'}")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n❌ Missing Supabase credentials - cannot continue")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Check recent call records with transcription issues
print("\n2. Recent Call Records with Transcription Issues:")
call_records_result = supabase.table("call_records").select(
    "id, transcript, created_at, audio_file_url"
).order("created_at", desc=True).limit(5).execute()

if call_records_result.data:
    for cr in call_records_result.data:
        print(f"\n   Call Record ID: {cr['id']}")
        transcript = cr.get('transcript', 'None')
        print(f"   Transcript: {transcript[:50] if transcript else 'None'}...")
        print(f"   Created: {cr.get('created_at')}")
        
        # Try to get signed URL
        if cr.get('audio_file_url'):
            try:
                # Extract bucket and path from audio_file_url
                # Format: bucket_name/path/to/file
                url_parts = cr['audio_file_url'].split('/', 1)
                if len(url_parts) == 2:
                    bucket = url_parts[0]
                    path = url_parts[1]
                    
                    # Try to create signed URL
                    signed_url_result = supabase.storage.from_(bucket).create_signed_url(path, 3600)
                    
                    if isinstance(signed_url_result, dict) and signed_url_result.get('signedURL'):
                        signed_url = signed_url_result['signedURL']
                        print(f"   ✅ Signed URL generated (length: {len(signed_url)})")
                        
                        # Test if URL is accessible
                        try:
                            response = requests.head(signed_url, timeout=5)
                            if response.status_code == 200:
                                print(f"   ✅ Signed URL is accessible (status: {response.status_code})")
                            else:
                                print(f"   ⚠️  Signed URL returned status: {response.status_code}")
                        except Exception as e:
                            print(f"   ❌ Signed URL not accessible: {e}")
                    else:
                        print(f"   ⚠️  Could not generate signed URL")
                else:
                    print(f"   ⚠️  Invalid audio_file_url format: {cr['audio_file_url']}")
            except Exception as e:
                print(f"   ❌ Error checking signed URL: {e}")
        else:
            print(f"   ⚠️  No audio_file_url")
else:
    print("   No call records found")

# Check transcription queue
print("\n3. Transcription Queue Status:")
try:
    queue_result = supabase.table("transcription_queue").select("*").order("created_at", desc=True).limit(5).execute()
    if queue_result.data:
        print(f"   Found {len(queue_result.data)} recent queue entries:")
        for item in queue_result.data:
            print(f"\n   Queue ID: {item.get('id')}")
            print(f"   Status: {item.get('status')}")
            print(f"   Progress: {item.get('progress')}")
            print(f"   Provider: {item.get('provider')}")
            print(f"   Error: {item.get('error', 'None')}")
    else:
        print("   No transcription queue entries found")
except Exception as e:
    print(f"   ⚠️  Error checking transcription queue: {e}")
    print(f"   (This might be expected if the table doesn't exist or has different schema)")

# Test API connectivity
print("\n4. API Connectivity:")
if DEEPGRAM_KEY:
    try:
        # Test Deepgram API
        headers = {'Authorization': f'Token {DEEPGRAM_KEY}'}
        response = requests.get('https://api.deepgram.com/v1/projects', headers=headers, timeout=10)
        if response.status_code == 200:
            print("   ✅ Deepgram API: Connected")
        else:
            print(f"   ⚠️  Deepgram API: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Deepgram API: {e}")

if ASSEMBLYAI_KEY:
    try:
        # Test AssemblyAI API
        headers = {'authorization': ASSEMBLYAI_KEY}
        response = requests.get('https://api.assemblyai.com/v2/account', headers=headers, timeout=10)
        if response.status_code == 200:
            print("   ✅ AssemblyAI API: Connected")
        else:
            print(f"   ⚠️  AssemblyAI API: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ AssemblyAI API: {e}")

print("\n" + "=" * 80)

