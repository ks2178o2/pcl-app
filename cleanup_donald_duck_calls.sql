-- Cleanup script: keep only the most recent call for Donald Duck
-- Tables touched: call_records, call_chunks, call_analyses
-- Run inside a transaction. Review the preview query before executing deletes.

BEGIN;

-- 1) Preview: shows Donald Duck calls with newest first and row numbers
WITH ranked AS (
  SELECT
    id,
    customer_name,
    created_at,
    ROW_NUMBER() OVER (PARTITION BY customer_name ORDER BY created_at DESC) AS rn
  FROM call_records
  WHERE customer_name ILIKE 'Donald Duck'
)
SELECT id, customer_name, created_at, rn
FROM ranked
ORDER BY created_at DESC;

-- 2) Delete dependents for all but the most recent call
WITH ranked AS (
  SELECT
    id,
    ROW_NUMBER() OVER (PARTITION BY customer_name ORDER BY created_at DESC) AS rn
  FROM call_records
  WHERE customer_name ILIKE 'Donald Duck'
),
to_delete AS (
  SELECT id FROM ranked WHERE rn > 1
),
del_chunks AS (
  DELETE FROM call_chunks cc
  USING to_delete td
  WHERE cc.call_record_id = td.id
  RETURNING cc.call_record_id
),
del_analyses AS (
  DELETE FROM call_analyses ca
  USING to_delete td
  WHERE ca.call_record_id = td.id
  RETURNING ca.call_record_id
)
DELETE FROM call_records cr
USING to_delete td
WHERE cr.id = td.id;

COMMIT;

-- Note: If you also want to remove associated audio files from storage,
-- use your storage API (e.g., Supabase Storage) to delete objects whose
-- paths are referenced by the deleted call_records.audio_file_url.

