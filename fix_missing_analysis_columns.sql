-- Fix missing columns based on audit results
-- Run this in Supabase SQL Editor

-- 1. call_records: Add missing columns
ALTER TABLE call_records
  ADD COLUMN IF NOT EXISTS diarization_segments jsonb,
  ADD COLUMN IF NOT EXISTS speaker_mapping jsonb,
  ADD COLUMN IF NOT EXISTS status text,
  ADD COLUMN IF NOT EXISTS vendor_insights jsonb,
  ADD COLUMN IF NOT EXISTS salesperson_name text;

-- 2. call_chunks: Add missing columns
ALTER TABLE call_chunks
  ADD COLUMN IF NOT EXISTS chunk_number integer,
  ADD COLUMN IF NOT EXISTS chunk_size integer,
  ADD COLUMN IF NOT EXISTS status text,
  ADD COLUMN IF NOT EXISTS uploaded_at timestamp with time zone;

-- 3. follow_up_plans: Add missing columns
ALTER TABLE follow_up_plans
  ADD COLUMN IF NOT EXISTS customer_name text,
  ADD COLUMN IF NOT EXISTS follow_up_type text,
  ADD COLUMN IF NOT EXISTS salesperson_name text,
  ADD COLUMN IF NOT EXISTS scheduled_date timestamp with time zone;

-- 4. Ensure provider column exists and is nullable (for call_analyses)
ALTER TABLE call_analyses
  ADD COLUMN IF NOT EXISTS provider text;

-- Make provider nullable (remove NOT NULL constraint if it exists)
DO $$
BEGIN
  -- Check if column has NOT NULL constraint and remove it
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'call_analyses'
      AND column_name = 'provider'
      AND is_nullable = 'NO'
  ) THEN
    ALTER TABLE call_analyses ALTER COLUMN provider DROP NOT NULL;
  END IF;
  
  -- Set default if not already set
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'call_analyses'
      AND column_name = 'provider'
      AND column_default IS NOT NULL
  ) THEN
    ALTER TABLE call_analyses ALTER COLUMN provider SET DEFAULT 'gemini';
  END IF;
END$$;

-- 5. Reload PostgREST schema cache (critical!)
SELECT pg_notify('pgrst', 'reload schema');

-- 6. Verify columns were added
SELECT 
  table_name,
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns
WHERE table_name IN ('call_records', 'call_analyses', 'call_chunks', 'follow_up_plans')
  AND column_name IN (
    'diarization_segments', 'speaker_mapping', 'status', 'vendor_insights', 'salesperson_name',
    'chunk_number', 'chunk_size', 'uploaded_at',
    'customer_name', 'follow_up_type', 'scheduled_date',
    'provider'
  )
ORDER BY table_name, column_name;

