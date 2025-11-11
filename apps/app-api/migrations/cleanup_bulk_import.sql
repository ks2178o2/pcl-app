-- Cleanup script for bulk import test data
-- Run this in Supabase SQL Editor to clean up all test data

-- WARNING: This will delete ALL bulk import data
-- Make sure you want to delete everything before running!

BEGIN;

-- Delete objection overcome details for bulk import calls
DELETE FROM objection_overcome_details
WHERE call_record_id IN (
    SELECT id FROM call_records WHERE bulk_import_job_id IS NOT NULL
);

-- Delete call objections for bulk import calls
DELETE FROM call_objections
WHERE call_record_id IN (
    SELECT id FROM call_records WHERE bulk_import_job_id IS NOT NULL
);

-- Delete call records associated with bulk imports
DELETE FROM call_records
WHERE bulk_import_job_id IS NOT NULL;

-- Delete bulk import files
DELETE FROM bulk_import_files;

-- Delete bulk import jobs
DELETE FROM bulk_import_jobs;

-- Optional: Reset sequences if you want to start IDs from 1
-- ALTER SEQUENCE bulk_import_jobs_id_seq RESTART WITH 1;
-- ALTER SEQUENCE bulk_import_files_id_seq RESTART WITH 1;

COMMIT;

-- Note: Storage buckets must be deleted manually via Supabase Dashboard
-- or using the Python cleanup script (cleanup_bulk_import.py)

