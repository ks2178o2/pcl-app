-- Fix call_chunks table schema
-- This migration creates the table if it doesn't exist and adds missing columns

-- Create call_chunks table if it doesn't exist
CREATE TABLE IF NOT EXISTS call_chunks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  call_record_id UUID NOT NULL REFERENCES call_records(id) ON DELETE CASCADE,
  chunk_number INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  file_path TEXT NOT NULL DEFAULT '',
  duration_seconds NUMERIC(10, 2) DEFAULT 0,
  file_size BIGINT DEFAULT 0,
  upload_status TEXT DEFAULT 'pending',
  uploaded_at TIMESTAMP WITH TIME ZONE,
  UNIQUE(call_record_id, chunk_number)
);

-- Add file_path column if it doesn't exist (for existing tables)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'call_chunks' AND column_name = 'file_path'
  ) THEN
    ALTER TABLE call_chunks ADD COLUMN file_path TEXT DEFAULT '';
    -- Update any existing NULL values
    UPDATE call_chunks SET file_path = '' WHERE file_path IS NULL;
    -- Now make it NOT NULL
    ALTER TABLE call_chunks ALTER COLUMN file_path SET NOT NULL;
  END IF;
END $$;

-- Add duration_seconds column if it doesn't exist
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'call_chunks' AND column_name = 'duration_seconds'
  ) THEN
    ALTER TABLE call_chunks ADD COLUMN duration_seconds NUMERIC(10, 2) DEFAULT 0;
  END IF;
END $$;

-- Add file_size column if it doesn't exist
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'call_chunks' AND column_name = 'file_size'
  ) THEN
    ALTER TABLE call_chunks ADD COLUMN file_size BIGINT DEFAULT 0;
  END IF;
END $$;

-- Add upload_status column if it doesn't exist
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'call_chunks' AND column_name = 'upload_status'
  ) THEN
    ALTER TABLE call_chunks ADD COLUMN upload_status TEXT DEFAULT 'pending';
  END IF;
END $$;

-- Add uploaded_at column if it doesn't exist
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'call_chunks' AND column_name = 'uploaded_at'
  ) THEN
    ALTER TABLE call_chunks ADD COLUMN uploaded_at TIMESTAMP WITH TIME ZONE;
  END IF;
END $$;

-- Update existing records to have default values
UPDATE call_chunks 
SET 
  duration_seconds = COALESCE(duration_seconds, 0),
  file_size = COALESCE(file_size, 0),
  upload_status = COALESCE(upload_status, 'pending')
WHERE duration_seconds IS NULL OR file_size IS NULL OR upload_status IS NULL;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_call_chunks_call_record_id ON call_chunks(call_record_id);
CREATE INDEX IF NOT EXISTS idx_call_chunks_upload_status ON call_chunks(upload_status);
CREATE INDEX IF NOT EXISTS idx_call_chunks_call_record_upload_status ON call_chunks(call_record_id, upload_status);

-- Enable RLS if not already enabled
ALTER TABLE call_chunks ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for call_chunks
-- Allow users to read chunks for call records they have access to
DROP POLICY IF EXISTS "Users can view chunks for their call records" ON call_chunks;
CREATE POLICY "Users can view chunks for their call records" ON call_chunks
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM call_records cr
      WHERE cr.id = call_chunks.call_record_id
      AND cr.user_id = auth.uid()
    )
  );

-- Allow users to insert chunks for their call records
DROP POLICY IF EXISTS "Users can insert chunks for their call records" ON call_chunks;
CREATE POLICY "Users can insert chunks for their call records" ON call_chunks
  FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM call_records cr
      WHERE cr.id = call_chunks.call_record_id
      AND cr.user_id = auth.uid()
    )
  );

-- Allow users to update chunks for their call records
DROP POLICY IF EXISTS "Users can update chunks for their call records" ON call_chunks;
CREATE POLICY "Users can update chunks for their call records" ON call_chunks
  FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM call_records cr
      WHERE cr.id = call_chunks.call_record_id
      AND cr.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM call_records cr
      WHERE cr.id = call_chunks.call_record_id
      AND cr.user_id = auth.uid()
    )
  );

