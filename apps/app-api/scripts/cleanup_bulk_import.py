#!/usr/bin/env python3
"""
Cleanup script for bulk import test data
Removes all bulk import jobs, files, call records, and storage buckets
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.supabase_client import get_supabase_client
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_database_tables(supabase):
    """Delete all bulk import related data from database tables"""
    logger.info("Starting database cleanup...")
    
    try:
        # Get all bulk import jobs to find associated buckets
        jobs_result = supabase.table("bulk_import_jobs").select("id, storage_bucket_name").execute()
        job_ids = [job["id"] for job in jobs_result.data] if jobs_result.data else []
        bucket_names = [job["storage_bucket_name"] for job in jobs_result.data] if jobs_result.data else []
        
        # Also get analysis buckets (format: {bucket_name}-analysis)
        analysis_bucket_names = [f"{name}-analysis" for name in bucket_names]
        all_bucket_names = bucket_names + analysis_bucket_names
        
        logger.info(f"Found {len(job_ids)} bulk import jobs")
        logger.info(f"Found {len(set(bucket_names))} storage buckets to clean")
        
        if job_ids:
            # Delete in order (respecting foreign key constraints)
            # 1. Get call record IDs first
            logger.info("Finding call records from bulk imports...")
            call_records_result = supabase.table("call_records").select("id").in_(
                "bulk_import_job_id", job_ids
            ).execute()
            call_record_ids = [cr["id"] for cr in call_records_result.data] if call_records_result.data else []
            
            # 2. Delete objection overcome details
            if call_record_ids:
                logger.info("Deleting objection overcome details...")
                for cr_id in call_record_ids:
                    try:
                        supabase.table("objection_overcome_details").delete().eq("call_record_id", cr_id).execute()
                    except Exception as e:
                        logger.debug(f"Error deleting objection overcome for call {cr_id}: {e}")
            
            # 3. Delete call objections
            if call_record_ids:
                logger.info("Deleting call objections...")
                for cr_id in call_record_ids:
                    try:
                        supabase.table("call_objections").delete().eq("call_record_id", cr_id).execute()
                    except Exception as e:
                        logger.debug(f"Error deleting objections for call {cr_id}: {e}")
            
            # 4. Delete call records associated with bulk imports
            if call_record_ids:
                logger.info("Deleting call records from bulk imports...")
                for cr_id in call_record_ids:
                    try:
                        supabase.table("call_records").delete().eq("id", cr_id).execute()
                    except Exception as e:
                        logger.debug(f"Error deleting call record {cr_id}: {e}")
                logger.info(f"Deleted {len(call_record_ids)} call records")
            
            # 5. Delete bulk import files
            logger.info("Deleting bulk import files...")
            for job_id in job_ids:
                try:
                    supabase.table("bulk_import_files").delete().eq("job_id", job_id).execute()
                except Exception as e:
                    logger.debug(f"Error deleting files for job {job_id}: {e}")
            
            # 6. Delete bulk import jobs
            logger.info("Deleting bulk import jobs...")
            for job_id in job_ids:
                try:
                    supabase.table("bulk_import_jobs").delete().eq("id", job_id).execute()
                except Exception as e:
                    logger.debug(f"Error deleting job {job_id}: {e}")
            
            logger.info(f"✅ Deleted {len(job_ids)} bulk import jobs and associated data")
        else:
            logger.info("No bulk import jobs found to delete")
        
        return all_bucket_names
        
    except Exception as e:
        logger.error(f"Error cleaning database: {e}", exc_info=True)
        return []


def list_storage_buckets(supabase):
    """List all storage buckets"""
    try:
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets] if buckets else []
        logger.info(f"Found {len(bucket_names)} storage buckets: {', '.join(bucket_names)}")
        return bucket_names
    except Exception as e:
        logger.error(f"Error listing buckets: {e}")
        return []


def delete_storage_bucket(supabase, bucket_name):
    """Delete a storage bucket and all its contents"""
    try:
        # First, try to delete all files in the bucket
        try:
            files = supabase.storage.from_(bucket_name).list()
            if files:
                file_paths = [f["name"] for f in files]
                logger.info(f"Deleting {len(file_paths)} files from bucket {bucket_name}...")
                supabase.storage.from_(bucket_name).remove(file_paths)
        except Exception as e:
            logger.warning(f"Could not list/delete files in bucket {bucket_name}: {e}")
        
        # Delete the bucket using REST API (Supabase Python client has issues)
        supabase_url = os.getenv('SUPABASE_URL', 'https://xxdahmkfioqzgqvyabek.supabase.co')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_key:
            logger.error("SUPABASE_SERVICE_ROLE_KEY not set, cannot delete buckets via API")
            return False
        
        api_url = f"{supabase_url}/storage/v1/bucket/{bucket_name}"
        headers = {
            "Authorization": f"Bearer {supabase_key}",
            "apikey": supabase_key
        }
        
        with httpx.Client() as client:
            response = client.delete(api_url, headers=headers, timeout=10.0)
            if response.status_code in [200, 204]:
                logger.info(f"✅ Deleted storage bucket: {bucket_name}")
                return True
            elif response.status_code == 404:
                logger.info(f"Bucket {bucket_name} does not exist (already deleted)")
                return True
            else:
                logger.warning(f"Failed to delete bucket {bucket_name}: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error deleting bucket {bucket_name}: {e}")
        return False


def cleanup_storage_buckets(supabase, bucket_names):
    """Delete storage buckets associated with bulk imports"""
    if not bucket_names:
        logger.info("No storage buckets to delete")
        return
    
    logger.info(f"Cleaning up {len(bucket_names)} storage buckets...")
    
    deleted = 0
    failed = 0
    
    for bucket_name in bucket_names:
        if delete_storage_bucket(supabase, bucket_name):
            deleted += 1
        else:
            failed += 1
    
    logger.info(f"✅ Deleted {deleted} buckets, {failed} failed")


def main():
    """Main cleanup function"""
    logger.info("=" * 60)
    logger.info("Bulk Import Cleanup Script")
    logger.info("=" * 60)
    
    supabase = get_supabase_client()
    if not supabase:
        logger.error("❌ Failed to connect to Supabase. Check your credentials.")
        sys.exit(1)
    
    # Clean up database tables first
    bucket_names = cleanup_database_tables(supabase)
    
    # List all buckets
    all_buckets = list_storage_buckets(supabase)
    
    # Filter to only customer buckets (those starting with "customer-")
    customer_buckets = [b for b in all_buckets if b.startswith("customer-") or b.endswith("-analysis")]
    
    # Combine with buckets from database
    buckets_to_delete = list(set(bucket_names + customer_buckets))
    
    if buckets_to_delete:
        logger.info(f"\nBuckets to delete: {', '.join(buckets_to_delete)}")
        response = input("\nDelete these storage buckets? (yes/no): ").strip().lower()
        if response == 'yes':
            cleanup_storage_buckets(supabase, buckets_to_delete)
        else:
            logger.info("Skipping bucket deletion")
    else:
        logger.info("No bulk import buckets found to delete")
    
    logger.info("\n✅ Cleanup complete!")


if __name__ == "__main__":
    main()

