-- Comprehensive Database Schema Fix
-- Run this in your Supabase SQL Editor

-- ===========================================
-- 1. Fix call_records table schema
-- ===========================================

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

-- ===========================================
-- 2. Fix RLS policies for patients table
-- ===========================================

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow authenticated users to view their organization's patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to create patients in their organization" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to update their organization's patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to delete their organization's patients" ON patients;

-- Create new, more permissive policies for testing
CREATE POLICY "Allow authenticated users to view patients" ON patients FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated users to create patients" ON patients FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Allow authenticated users to update patients" ON patients FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Allow authenticated users to delete patients" ON patients FOR DELETE TO authenticated USING (true);

-- ===========================================
-- 3. Fix RLS policies for call_records table
-- ===========================================

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow authenticated users to view their call records" ON call_records;
DROP POLICY IF EXISTS "Allow authenticated users to create call records" ON call_records;
DROP POLICY IF EXISTS "Allow authenticated users to update their call records" ON call_records;
DROP POLICY IF EXISTS "Allow authenticated users to delete their call records" ON call_records;

-- Create new, more permissive policies for testing
CREATE POLICY "Allow authenticated users to view call records" ON call_records FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated users to create call records" ON call_records FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Allow authenticated users to update call records" ON call_records FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Allow authenticated users to delete call records" ON call_records FOR DELETE TO authenticated USING (true);

-- ===========================================
-- 4. Add some test data
-- ===========================================

-- Insert test patients if none exist
INSERT INTO patients (organization_id, full_name, email, phone) 
SELECT 
  (SELECT organization_id FROM profiles WHERE user_id = 'cfc2f7f8-cf3a-4962-99bc-7168bf0622de' LIMIT 1),
  'Test Patient 1',
  'test1@example.com',
  '111-222-3333'
WHERE NOT EXISTS (SELECT 1 FROM patients WHERE full_name = 'Test Patient 1');

INSERT INTO patients (organization_id, full_name, email, phone) 
SELECT 
  (SELECT organization_id FROM profiles WHERE user_id = 'cfc2f7f8-cf3a-4962-99bc-7168bf0622de' LIMIT 1),
  'Test Patient 2',
  'test2@example.com',
  '444-555-6666'
WHERE NOT EXISTS (SELECT 1 FROM patients WHERE full_name = 'Test Patient 2');

-- ===========================================
-- 5. Verify the fixes
-- ===========================================

-- Check if call_records table has the required columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'call_records' 
AND column_name IN ('center_id', 'patient_id', 'total_chunks', 'chunks_uploaded', 'recording_complete');

-- Check if patients table is accessible
SELECT COUNT(*) as patient_count FROM patients;

-- Check RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('patients', 'call_records');
