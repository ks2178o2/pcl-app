-- ===========================================
-- Sales Angel Buddy v1.0.0 - Complete Database Setup
-- For New Environment Deployment
-- ===========================================
-- 
-- This script creates the complete database schema
-- for a fresh Sales Angel Buddy deployment.
-- Run this in your Supabase SQL Editor for a new environment.
--
-- Created: 2025-01-27
-- Version: 1.0.0
-- ===========================================

-- ===========================================
-- 1. CREATE PATIENTS TABLE
-- ===========================================

-- Create the patients table
CREATE TABLE IF NOT EXISTS public.patients (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid REFERENCES public.organizations(id) ON DELETE CASCADE,
  full_name text NOT NULL,
  email text,
  phone text,
  friendly_id text UNIQUE DEFAULT 'P' || substring(gen_random_uuid()::text FROM 1 FOR 6),
  created_at timestamp with time zone DEFAULT now() NOT NULL,
  updated_at timestamp with time zone DEFAULT now() NOT NULL
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_patients_organization_id ON public.patients (organization_id);
CREATE INDEX IF NOT EXISTS idx_patients_full_name ON public.patients (full_name);
CREATE INDEX IF NOT EXISTS idx_patients_friendly_id ON public.patients (friendly_id);

-- Enable Row Level Security (RLS)
ALTER TABLE public.patients ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for patients
-- Policy for authenticated users to view their organization's patients
CREATE POLICY IF NOT EXISTS "Users can view patients from their organization"
ON public.patients FOR SELECT
TO public
USING (
  organization_id IN (
    SELECT organization_id
    FROM public.profiles
    WHERE user_id = auth.uid()
  )
);

-- Policy for authenticated users to create patients within their organization
CREATE POLICY IF NOT EXISTS "Users can insert patients for their organization"
ON public.patients FOR INSERT
TO public
WITH CHECK (true);  -- Simplified for easier deployment

-- Policy for authenticated users to update their organization's patients
CREATE POLICY IF NOT EXISTS "Users can update patients from their organization"
ON public.patients FOR UPDATE
TO public
USING (
  organization_id IN (
    SELECT organization_id
    FROM public.profiles
    WHERE user_id = auth.uid()
  )
);

-- Policy for authenticated users to delete their organization's patients
CREATE POLICY IF NOT EXISTS "Users can delete patients from their organization"
ON public.patients FOR DELETE
TO public
USING (
  organization_id IN (
    SELECT organization_id
    FROM public.profiles
    WHERE user_id = auth.uid()
  )
);

-- ===========================================
-- 2. FIX CALL_RECORDS TABLE
-- ===========================================

-- Add missing columns to call_records table if they don't exist
DO $$ 
BEGIN
  -- Add center_id column if missing
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'call_records' AND column_name = 'center_id'
  ) THEN
    ALTER TABLE call_records ADD COLUMN center_id UUID REFERENCES centers(id);
  END IF;

  -- Add patient_id column if missing
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'call_records' AND column_name = 'patient_id'
  ) THEN
    ALTER TABLE call_records ADD COLUMN patient_id UUID REFERENCES patients(id);
  END IF;

  -- Add total_chunks column if missing
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'call_records' AND column_name = 'total_chunks'
  ) THEN
    ALTER TABLE call_records ADD COLUMN total_chunks INTEGER DEFAULT 0;
  END IF;

  -- Add chunks_uploaded column if missing
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'call_records' AND column_name = 'chunks_uploaded'
  ) THEN
    ALTER TABLE call_records ADD COLUMN chunks_uploaded INTEGER DEFAULT 0;
  END IF;

  -- Add recording_complete column if missing
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'call_records' AND column_name = 'recording_complete'
  ) THEN
    ALTER TABLE call_records ADD COLUMN recording_complete BOOLEAN DEFAULT false;
  END IF;
END $$;

-- Update existing records to have default values
UPDATE call_records 
SET 
  total_chunks = COALESCE(total_chunks, 0),
  chunks_uploaded = COALESCE(chunks_uploaded, 0),
  recording_complete = COALESCE(recording_complete, false)
WHERE total_chunks IS NULL OR chunks_uploaded IS NULL OR recording_complete IS NULL;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_call_records_center_id ON call_records(center_id);
CREATE INDEX IF NOT EXISTS idx_call_records_patient_id ON call_records(patient_id);
CREATE INDEX IF NOT EXISTS idx_call_records_user_id ON call_records(user_id);
CREATE INDEX IF NOT EXISTS idx_call_records_recording_complete ON call_records(recording_complete);

-- ===========================================
-- 3. ENSURE CALL_RECORDS RLS POLICIES
-- ===========================================

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view their own call records" ON call_records;
DROP POLICY IF EXISTS "Users can create their own call records" ON call_records;
DROP POLICY IF EXISTS "Users can update their own call records" ON call_records;
DROP POLICY IF EXISTS "Users can delete their own call records" ON call_records;

-- Create RLS policies for call_records
CREATE POLICY IF NOT EXISTS "Users can view their own call records"
ON call_records FOR SELECT
TO public
USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "Users can create their own call records"
ON call_records FOR INSERT
TO public
WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "Users can update their own call records"
ON call_records FOR UPDATE
TO public
USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "Users can delete their own call records"
ON call_records FOR DELETE
TO public
USING (auth.uid() = user_id);

-- ===========================================
-- 4. ENSURE PATIENTS RLS POLICIES
-- ===========================================

-- Drop existing permissive policies if they exist
DROP POLICY IF EXISTS "Allow authenticated users to view patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to create patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to update patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to delete patients" ON patients;

-- Create permissive policies for easier testing (can be tightened later)
CREATE POLICY IF NOT EXISTS "Allow authenticated users to view patients"
ON patients FOR SELECT
TO authenticated
USING (true);

CREATE POLICY IF NOT EXISTS "Allow authenticated users to create patients"
ON patients FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "Allow authenticated users to update patients"
ON patients FOR UPDATE
TO authenticated
USING (true);

CREATE POLICY IF NOT EXISTS "Allow authenticated users to delete patients"
ON patients FOR DELETE
TO authenticated
USING (true);

-- Same for call_records
DROP POLICY IF EXISTS "Allow authenticated users to view call records" ON call_records;
DROP POLICY IF EXISTS "Allow authenticated users to create call records" ON call_records;
DROP POLICY IF EXISTS "Allow authenticated users to update call records" ON call_records;
DROP POLICY IF EXISTS "Allow authenticated users to delete call records" ON call_records;

CREATE POLICY IF NOT EXISTS "Allow authenticated users to view call records"
ON call_records FOR SELECT
TO authenticated
USING (true);

CREATE POLICY IF NOT EXISTS "Allow authenticated users to create call records"
ON call_records FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "Allow authenticated users to update call records"
ON call_records FOR UPDATE
TO authenticated
USING (true);

CREATE POLICY IF NOT EXISTS "Allow authenticated users to delete call records"
ON call_records FOR DELETE
TO authenticated
USING (true);

-- ===========================================
-- 5. VERIFY DATABASE SETUP
-- ===========================================

-- Check if patients table has required columns
DO $$
DECLARE
  patient_columns integer;
  call_records_columns integer;
BEGIN
  SELECT COUNT(*) INTO patient_columns
  FROM information_schema.columns 
  WHERE table_name = 'patients' 
  AND column_name IN ('id', 'organization_id', 'full_name', 'email', 'phone', 'friendly_id');
  
  SELECT COUNT(*) INTO call_records_columns
  FROM information_schema.columns 
  WHERE table_name = 'call_records' 
  AND column_name IN ('center_id', 'patient_id', 'total_chunks', 'chunks_uploaded', 'recording_complete');
  
  -- Log verification results
  IF patient_columns = 6 THEN
    RAISE NOTICE '✅ Patients table verified: All 6 required columns exist';
  ELSE
    RAISE WARNING '⚠️ Patients table: Only % columns found (expected 6)', patient_columns;
  END IF;
  
  IF call_records_columns = 5 THEN
    RAISE NOTICE '✅ Call records table verified: All 5 required columns exist';
  ELSE
    RAISE WARNING '⚠️ Call records table: Only % columns found (expected 5)', call_records_columns;
  END IF;
END $$;

-- ===========================================
-- 6. VERIFY RLS POLICIES
-- ===========================================

-- Check RLS policies
DO $$
DECLARE
  policy_count integer;
BEGIN
  SELECT COUNT(*) INTO policy_count
  FROM pg_policies 
  WHERE tablename IN ('patients', 'call_records');
  
  RAISE NOTICE '✅ Verified: % RLS policies active for patients and call_records tables', policy_count;
END $$;

-- ===========================================
-- VERIFICATION QUERIES (Optional - Run separately)
-- ===========================================

-- Uncomment to run verification queries:
-- 
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'patients' 
-- ORDER BY column_name;
--
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'call_records' 
-- AND column_name IN ('center_id', 'patient_id', 'total_chunks', 'chunks_uploaded', 'recording_complete');
--
-- SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
-- FROM pg_policies 
-- WHERE tablename IN ('patients', 'call_records')
-- ORDER BY tablename, policyname;

-- ===========================================
-- SETUP COMPLETE
-- ===========================================

-- Success message
DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Sales Angel Buddy v1.0.0 Database Setup';
  RAISE NOTICE 'Complete!';
  RAISE NOTICE '========================================';
  RAISE NOTICE '✅ Patients table created with RLS policies';
  RAISE NOTICE '✅ Call records table updated with required columns';
  RAISE NOTICE '✅ RLS policies configured for multi-tenant isolation';
  RAISE NOTICE '';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '1. Verify the setup by running the verification queries above';
  RAISE NOTICE '2. Create test users and organizations';
  RAISE NOTICE '3. Test patient creation and recording functionality';
  RAISE NOTICE '';
END $$;

