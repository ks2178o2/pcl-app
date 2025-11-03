-- Fix call_records table schema
-- Run this in your Supabase SQL Editor

-- Add missing columns to call_records table
ALTER TABLE call_records 
ADD COLUMN IF NOT EXISTS center_id UUID REFERENCES centers(id),
ADD COLUMN IF NOT EXISTS patient_id UUID REFERENCES patients(id),
ADD COLUMN IF NOT EXISTS total_chunks INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS chunks_uploaded INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recording_complete BOOLEAN DEFAULT false;

-- Update existing records to have default values
UPDATE call_records 
SET 
  total_chunks = 0,
  chunks_uploaded = 0,
  recording_complete = false
WHERE total_chunks IS NULL OR chunks_uploaded IS NULL OR recording_complete IS NULL;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_call_records_center_id ON call_records(center_id);
CREATE INDEX IF NOT EXISTS idx_call_records_patient_id ON call_records(patient_id);
CREATE INDEX IF NOT EXISTS idx_call_records_user_id ON call_records(user_id);
CREATE INDEX IF NOT EXISTS idx_call_records_recording_complete ON call_records(recording_complete);
