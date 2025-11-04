-- Cleanup script: Delete all calls and related data for Donald Duck and Goofy
-- Tables touched: call_records, call_chunks, call_analyses
-- Run inside a transaction. Review the preview query before executing deletes.

BEGIN;

-- 1) Preview: shows all calls for these customers
SELECT 
  id,
  customer_name,
  audio_file_url,
  created_at,
  transcript
FROM call_records
WHERE customer_name ILIKE 'Donald Duck' 
   OR customer_name ILIKE 'Goofy'
ORDER BY customer_name, created_at DESC;

-- 2) Delete related data for all calls matching these customers
WITH to_delete AS (
  SELECT id FROM call_records
  WHERE customer_name ILIKE 'Donald Duck' 
     OR customer_name ILIKE 'Goofy'
),
deleted_chunks AS (
  DELETE FROM call_chunks cc
  USING to_delete td
  WHERE cc.call_record_id = td.id
  RETURNING cc.call_record_id
),
deleted_analyses AS (
  DELETE FROM call_analyses ca
  USING to_delete td
  WHERE ca.call_record_id = td.id
  RETURNING ca.call_record_id
)
DELETE FROM call_records cr
USING to_delete td
WHERE cr.id = td.id;

-- Note: After running this SQL, you'll need to manually delete the storage files
-- Use the storage cleanup script or Supabase Storage UI

COMMIT;

-- Verify deletion (run after COMMIT)
-- SELECT COUNT(*) as remaining_calls
-- FROM call_records
-- WHERE customer_name ILIKE 'Donald Duck' 
--    OR customer_name ILIKE 'Goofy';

