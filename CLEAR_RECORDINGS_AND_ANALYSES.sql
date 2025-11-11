-- Clear all call recordings and call analyses from the database
-- Run this in your Supabase SQL Editor
-- WARNING: This will delete ALL recordings and analyses!

BEGIN;

-- Step 1: Delete call_analyses first (has foreign key to call_records)
DELETE FROM call_analyses;

-- Step 2: Delete call_chunks (related to call_records)
DELETE FROM call_chunks;

-- Step 3: Delete call_records (main recordings table)
DELETE FROM call_records;

-- Step 4: Clear transcription_queue if it exists
DELETE FROM transcription_queue;

COMMIT;

-- Note: This does NOT delete the audio files from storage.
-- If you want to delete storage files too, you'll need to:
-- 1. Query the audio_file_url or storage_path from call_records before deletion
-- 2. Use Supabase Storage API to delete those files
-- Or use the Supabase dashboard to manually clean up storage buckets.

