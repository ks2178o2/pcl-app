-- ===========================================
-- Update RLS Policies for Center-Based Hierarchy
-- ===========================================
-- 
-- This script updates Row Level Security policies to use the new
-- center_id hierarchy instead of organization_id for patient access.
-- 
-- Migration Date: 2025
-- Version: 2.0
-- ===========================================

-- ===========================================
-- 1. UPDATE PATIENTS RLS POLICIES
-- ===========================================

-- Drop existing organization-based policies
DROP POLICY IF EXISTS "Users can view patients from their organization" ON patients;
DROP POLICY IF EXISTS "Users can insert patients for their organization" ON patients;
DROP POLICY IF EXISTS "Users can update patients from their organization" ON patients;
DROP POLICY IF EXISTS "Users can delete patients from their organization" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to view patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to create patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to update patients" ON patients;
DROP POLICY IF EXISTS "Allow authenticated users to delete patients" ON patients;

-- New policy: Users can view patients from their assigned centers
-- Users with center assignments can see patients assigned to those centers
-- Users without assignments can see all patients in their organization (fallback)
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

-- New policy: Users can insert patients to their assigned centers
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

-- New policy: Users can update patients from their assigned centers
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

-- New policy: Users can delete patients from their assigned centers
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
-- 2. ADD INDEXES FOR PERFORMANCE
-- ===========================================

-- Add index on center_id for faster RLS policy checks
CREATE INDEX IF NOT EXISTS idx_patients_center_id 
ON patients(center_id) 
WHERE center_id IS NOT NULL;

-- ===========================================
-- 3. VERIFY POLICIES
-- ===========================================

-- Show all policies on patients table
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
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

