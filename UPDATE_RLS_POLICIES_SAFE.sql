-- ===========================================
-- Update RLS Policies for Center-Based Hierarchy (Safe Version)
-- ===========================================
-- This version checks for existing policies before creating
-- 
-- Migration Date: 2025
-- Version: 2.1 (Safe)
-- ===========================================

-- ===========================================
-- 1. DROP ALL EXISTING POLICIES FIRST
-- ===========================================

-- Drop ALL existing policies on patients table
DROP POLICY IF EXISTS "Users can view patients from their organization" ON patients;
DROP POLICY IF EXISTS "Users can insert patients for their organization" ON patients;
DROP POLICY IF EXISTS "Users can update patients from their organization" ON patients;
DROP POLICY IF EXISTS "Users can delete patients from their organization" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to view patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to create patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to update patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to delete patients" ON patients;
DROP POLICY IF EXISTS "Users can view patients from assigned centers" ON patients;
DROP POLICY IF EXISTS "Users can insert patients to assigned centers" ON patients;
DROP POLICY IF EXISTS "Users can update patients from assigned centers" ON patients;
DROP POLICY IF EXISTS "Users can delete patients from assigned centers" ON patients;

-- ===========================================
-- 2. CREATE NEW POLICIES
-- ===========================================

-- Policy 1: SELECT (View)
CREATE POLICY "Users can view patients from assigned centers"
ON patients FOR SELECT
TO authenticated
USING (
  -- User has access if they have a center assignment and patient belongs to that center
  center_id IN (
    SELECT center_id 
    FROM user_assignments 
    WHERE user_id = auth.uid() 
    AND center_id IS NOT NULL
  )
  -- OR user has no center assignments (fallback: see all org patients)
  OR NOT EXISTS (
    SELECT 1 FROM user_assignments 
    WHERE user_id = auth.uid() 
    AND center_id IS NOT NULL
  )
  -- AND organization matches (safety check)
  AND organization_id IN (
    SELECT organization_id 
    FROM profiles 
    WHERE user_id = auth.uid()
  )
);

-- Policy 2: INSERT (Create)
CREATE POLICY "Users can insert patients to assigned centers"
ON patients FOR INSERT
TO authenticated
WITH CHECK (
  -- User can insert if patient is assigned to a center they have access to
  center_id IN (
    SELECT center_id 
    FROM user_assignments 
    WHERE user_id = auth.uid() 
    AND center_id IS NOT NULL
  )
  -- OR user has no center assignments (fallback: insert anywhere in org)
  OR NOT EXISTS (
    SELECT 1 FROM user_assignments 
    WHERE user_id = auth.uid() 
    AND center_id IS NOT NULL
  )
);

-- Policy 3: UPDATE (Edit)
CREATE POLICY "Users can update patients from assigned centers"
ON patients FOR UPDATE
TO authenticated
USING (
  -- User has access if they have a center assignment and patient belongs to that center
  center_id IN (
    SELECT center_id 
    FROM user_assignments 
    WHERE user_id = auth.uid() 
    AND center_id IS NOT NULL
  )
  -- OR user has no center assignments (fallback: see all org patients)
  OR NOT EXISTS (
    SELECT 1 FROM user_assignments 
    WHERE user_id = auth.uid() 
    AND center_id IS NOT NULL
  )
  -- AND organization matches (safety check)
  AND organization_id IN (
    SELECT organization_id 
    FROM profiles 
    WHERE user_id = auth.uid()
  )
);

-- Policy 4: DELETE (Remove)
CREATE POLICY "Users can delete patients from assigned centers"
ON patients FOR DELETE
TO authenticated
USING (
  -- User has access if they have a center assignment and patient belongs to that center
  center_id IN (
    SELECT center_id 
    FROM user_assignments 
    WHERE user_id = auth.uid() 
    AND center_id IS NOT NULL
  )
  -- OR user has no center assignments (fallback: see all org patients)
  OR NOT EXISTS (
    SELECT 1 FROM user_assignments 
    WHERE user_id = auth.uid() 
    AND center_id IS NOT NULL
  )
  -- AND organization matches (safety check)
  AND organization_id IN (
    SELECT organization_id 
    FROM profiles 
    WHERE user_id = auth.uid()
  )
);

-- ===========================================
-- 3. ADD INDEXES FOR PERFORMANCE
-- ===========================================

CREATE INDEX IF NOT EXISTS idx_patients_center_id 
ON patients(center_id) 
WHERE center_id IS NOT NULL;

-- ===========================================
-- 4. VERIFY POLICIES
-- ===========================================

SELECT 
    policyname,
    cmd
FROM pg_policies
WHERE tablename = 'patients'
ORDER BY policyname;

-- ===========================================
-- VERIFICATION COMPLETE
-- ===========================================

DO $$ 
BEGIN
    RAISE NOTICE '✅ RLS policies updated for center-based hierarchy!';
    RAISE NOTICE '📋 Users now see patients based on their center assignments';
    RAISE NOTICE '🔄 Users without center assignments see all patients in their organization (fallback)';
END $$;

