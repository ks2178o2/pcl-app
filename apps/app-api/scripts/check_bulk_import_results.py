#!/usr/bin/env python3
"""
Script to check bulk import results in the database
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
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

def check_job_results(job_id: str = None):
    """Check results for a specific job or all jobs"""
    
    if job_id:
        jobs_result = supabase.table("bulk_import_jobs").select("*").eq("id", job_id).execute()
        jobs = jobs_result.data if jobs_result.data else []
    else:
        jobs_result = supabase.table("bulk_import_jobs").select("*").order("created_at", desc=True).limit(5).execute()
        jobs = jobs_result.data if jobs_result.data else []
    
    if not jobs:
        print("No jobs found")
        return
    
    for job in jobs:
        print(f"\n{'='*80}")
        print(f"Job ID: {job['id']}")
        print(f"Customer: {job.get('customer_name')}")
        print(f"Status: {job.get('status')}")
        print(f"Total Files: {job.get('total_files')}, Processed: {job.get('processed_files')}, Failed: {job.get('failed_files')}")
        
        # Get files for this job
        files_result = supabase.table("bulk_import_files").select("*").eq("job_id", job['id']).execute()
        files = files_result.data if files_result.data else []
        
        print(f"\nFiles ({len(files)}):")
        for file in files:
            call_record_id = file.get('call_record_id')
            print(f"\n  File: {file.get('file_name')}")
            print(f"    Status: {file.get('status')}")
            print(f"    Call Record ID: {call_record_id}")
            
            if call_record_id:
                # Check call_record
                call_result = supabase.table("call_records").select(
                    "id, transcript, call_category, categorization_confidence, categorization_notes"
                ).eq("id", call_record_id).execute()
                
                if call_result.data:
                    call_record = call_result.data[0]
                    transcript = call_record.get('transcript', '')
                    transcript_len = len(transcript) if transcript else 0
                    
                    print(f"    Transcript Length: {transcript_len} chars")
                    print(f"    Transcript Preview: {transcript[:100] if transcript else 'None'}...")
                    print(f"    Category: {call_record.get('call_category')}")
                    print(f"    Confidence: {call_record.get('categorization_confidence')}")
                    
                    # Check objections
                    objections_result = supabase.table("call_objections").select("*").eq("call_record_id", call_record_id).execute()
                    objections = objections_result.data if objections_result.data else []
                    print(f"    Objections: {len(objections)}")
                    
                    # Check overcomes
                    if objections:
                        objection_ids = [obj['id'] for obj in objections if obj.get('id')]
                        if objection_ids:
                            try:
                                overcomes_result = supabase.table("objection_overcome_details").select("*").in_("objection_id", objection_ids).execute()
                                overcomes = overcomes_result.data if overcomes_result.data else []
                                print(f"    Objection Overcomes: {len(overcomes)}")
                            except Exception as e:
                                print(f"    Error fetching overcomes: {e}")
                else:
                    print(f"    ❌ Call record not found!")
        
        print(f"\n{'='*80}")

if __name__ == "__main__":
    import sys
    job_id = sys.argv[1] if len(sys.argv) > 1 else None
    check_job_results(job_id)

