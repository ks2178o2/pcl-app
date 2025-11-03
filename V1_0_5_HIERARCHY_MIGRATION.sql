-- Migration to restructure from 4-level to 3-level hierarchy: Organization → Region → Center
-- This migration also fixes the RLS recursion issues
-- Updated: 2025-01-07 for v1.0.5

-- Step 1: Drop the problematic RLS policies that cause recursion
DROP POLICY IF EXISTS "Leaders and coaches can view assignments in their scope" ON public.user_assignments;
DROP POLICY IF EXISTS "Users can view accessible regions" ON public.regions;
-- Only drop networks policy if networks table exists
DO $$ 
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'networks' AND table_schema = 'public') THEN
    DROP POLICY IF EXISTS "Users can view accessible networks" ON public.networks;
  END IF;
END $$;

-- Step 2: Add organization_id to profiles table if it doesn't exist
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'profiles' AND column_name = 'organization_id') THEN
    ALTER TABLE public.profiles ADD COLUMN organization_id UUID REFERENCES public.organizations(id);
  END IF;
END $$;

-- Step 3: Migrate existing networks to be regions under a default organization
INSERT INTO public.organizations (id, name) 
VALUES ('00000000-0000-0000-0000-000000000001', 'Default Organization')
ON CONFLICT (id) DO NOTHING;

-- Step 4: Prepare regions table for migration
-- Add organization_id column and remove network_id constraints (only if they exist)
ALTER TABLE public.regions ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE;

-- Only modify network_id column if it exists
DO $$ 
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'regions' AND column_name = 'network_id' AND table_schema = 'public') THEN
    ALTER TABLE public.regions DROP CONSTRAINT IF EXISTS regions_network_id_fkey;
    ALTER TABLE public.regions ALTER COLUMN network_id DROP NOT NULL;
  END IF;
END $$;

-- Step 5: Convert existing networks to regions under the default organization (only if networks table exists)
DO $$ 
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'networks' AND table_schema = 'public') THEN
    INSERT INTO public.regions (id, organization_id, name, created_at, updated_at)
    SELECT 
      id, 
      '00000000-0000-0000-0000-000000000001'::UUID as organization_id,
      name || ' (Migrated Network)' as name,
      created_at,
      updated_at
    FROM public.networks
    ON CONFLICT (id) DO NOTHING;
  END IF;
END $$;

-- Step 6: Clean up old network references from regions (only if network_id column exists)
DO $$ 
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'regions' AND column_name = 'network_id' AND table_schema = 'public') THEN
    ALTER TABLE public.regions DROP COLUMN network_id CASCADE;
  END IF;
END $$;

-- Update existing regions to point to the default organization if they don't have organization_id
UPDATE public.regions 
SET organization_id = '00000000-0000-0000-0000-000000000001'::UUID 
WHERE organization_id IS NULL;

-- Make organization_id NOT NULL
ALTER TABLE public.regions ALTER COLUMN organization_id SET NOT NULL;

-- Step 7: Update user_assignments to remove network references and add organization_id (only if network_id exists)
DO $$ 
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_assignments' AND column_name = 'network_id' AND table_schema = 'public') THEN
    ALTER TABLE public.user_assignments DROP COLUMN network_id CASCADE;
  END IF;
END $$;
ALTER TABLE public.user_assignments ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES public.organizations(id);

-- Set organization_id for existing assignments
UPDATE public.user_assignments ua
SET organization_id = '00000000-0000-0000-0000-000000000001'::UUID
WHERE organization_id IS NULL;

-- Step 7: Update the constraint
ALTER TABLE public.user_assignments DROP CONSTRAINT IF EXISTS check_assignment_level;
ALTER TABLE public.user_assignments ADD CONSTRAINT check_assignment_level CHECK (
  (center_id IS NOT NULL) OR 
  (region_id IS NOT NULL) OR 
  (organization_id IS NOT NULL)
);

-- Step 8: Drop the networks table (no longer needed)
DROP TABLE IF EXISTS public.networks CASCADE;

-- Step 9: Update the get_user_accessible_centers function
CREATE OR REPLACE FUNCTION public.get_user_accessible_centers(_user_id UUID)
RETURNS TABLE(center_id UUID)
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT DISTINCT c.id as center_id
  FROM public.centers c
  JOIN public.regions r ON c.region_id = r.id
  LEFT JOIN public.user_assignments ua ON ua.user_id = _user_id
  LEFT JOIN public.profiles p ON p.id = _user_id
  WHERE 
    ua.center_id = c.id OR
    ua.region_id = r.id OR
    ua.organization_id = r.organization_id OR
    p.organization_id = r.organization_id OR
    public.has_role(_user_id, 'leader');
$$;

-- Step 10: Drop existing policies before creating new ones to avoid conflicts
DROP POLICY IF EXISTS "Users can view regions in their organization or system admins see all" ON public.regions;
DROP POLICY IF EXISTS "Users can view centers in their organization or system admins see all" ON public.centers;
DROP POLICY IF EXISTS "Users can view assignments in their organization or system admins see all" ON public.user_assignments;
DROP POLICY IF EXISTS "System admins can view all organizations" ON public.organizations;
DROP POLICY IF EXISTS "Users can view their own organization" ON public.organizations;
DROP POLICY IF EXISTS "System admins can create regions" ON public.regions;
DROP POLICY IF EXISTS "System admins can update regions" ON public.regions;
DROP POLICY IF EXISTS "System admins can create centers" ON public.centers;
DROP POLICY IF EXISTS "System admins can update centers" ON public.centers;
DROP POLICY IF EXISTS "System admins can create user assignments" ON public.user_assignments;
DROP POLICY IF EXISTS "System admins can update user assignments" ON public.user_assignments;
DROP POLICY IF EXISTS "System admins can create organizations" ON public.organizations;
DROP POLICY IF EXISTS "System admins can update organizations" ON public.organizations;

-- Step 11: Create new organization-based RLS policies (non-recursive)
CREATE POLICY "Users can view regions in their organization or system admins see all" ON public.regions
FOR SELECT USING (
  public.has_role(auth.uid(), 'system_admin') OR
  organization_id IN (
    SELECT p.organization_id 
    FROM public.profiles p 
    WHERE p.id = auth.uid() AND p.organization_id IS NOT NULL
  ) OR
  public.has_role(auth.uid(), 'leader')
);

CREATE POLICY "Users can view centers in their organization or system admins see all" ON public.centers
FOR SELECT USING (
  public.has_role(auth.uid(), 'system_admin') OR
  region_id IN (
    SELECT r.id 
    FROM public.regions r
    JOIN public.profiles p ON p.organization_id = r.organization_id
    WHERE p.id = auth.uid()
  ) OR
  id IN (SELECT center_id FROM public.get_user_accessible_centers(auth.uid()))
);

CREATE POLICY "Users can view assignments in their organization or system admins see all" ON public.user_assignments
FOR SELECT USING (
  public.has_role(auth.uid(), 'system_admin') OR
  user_id = auth.uid() OR
  public.has_role(auth.uid(), 'leader') OR
  (public.has_role(auth.uid(), 'coach') AND 
   organization_id IN (
     SELECT p.organization_id 
     FROM public.profiles p 
     WHERE p.id = auth.uid()
   ))
);

-- Add organization policies for system admins
CREATE POLICY "System admins can view all organizations" ON public.organizations
FOR SELECT USING (public.has_role(auth.uid(), 'system_admin'));

CREATE POLICY "Users can view their own organization" ON public.organizations
FOR SELECT USING (
  id IN (
    SELECT p.organization_id 
    FROM public.profiles p 
    WHERE p.id = auth.uid() AND p.organization_id IS NOT NULL
  )
);

-- Step 12: Add INSERT/UPDATE policies for organizational data
CREATE POLICY "System admins can create regions" ON public.regions
FOR INSERT WITH CHECK (public.has_role(auth.uid(), 'system_admin'));

CREATE POLICY "System admins can update regions" ON public.regions
FOR UPDATE USING (public.has_role(auth.uid(), 'system_admin'));

CREATE POLICY "System admins can create centers" ON public.centers
FOR INSERT WITH CHECK (public.has_role(auth.uid(), 'system_admin'));

CREATE POLICY "System admins can update centers" ON public.centers
FOR UPDATE USING (public.has_role(auth.uid(), 'system_admin'));

CREATE POLICY "System admins can create user assignments" ON public.user_assignments
FOR INSERT WITH CHECK (public.has_role(auth.uid(), 'system_admin'));

CREATE POLICY "System admins can update user assignments" ON public.user_assignments
FOR UPDATE USING (public.has_role(auth.uid(), 'system_admin'));

CREATE POLICY "System admins can create organizations" ON public.organizations
FOR INSERT WITH CHECK (public.has_role(auth.uid(), 'system_admin'));

CREATE POLICY "System admins can update organizations" ON public.organizations
FOR UPDATE USING (public.has_role(auth.uid(), 'system_admin'));

-- Step 13: Add missing system_admin role if it doesn't exist
ALTER TYPE public.user_role ADD VALUE IF NOT EXISTS 'system_admin';

-- Step 14: Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_regions_organization_id ON public.regions(organization_id);
CREATE INDEX IF NOT EXISTS idx_centers_region_id ON public.centers(region_id);
CREATE INDEX IF NOT EXISTS idx_user_assignments_organization_id ON public.user_assignments(organization_id);
CREATE INDEX IF NOT EXISTS idx_profiles_organization_id ON public.profiles(organization_id);

-- Step 15: Verification and completion message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ v1.0.5 Hierarchy Migration Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE '  - Networks table dropped';
    RAISE NOTICE '  - Regions now belong directly to Organizations';
    RAISE NOTICE '  - RLS recursion issues fixed';
    RAISE NOTICE '  - Organization-based access control enabled';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Verify the migration with: SELECT * FROM organization_hierarchy_v2;';
    RAISE NOTICE '2. Test region and center creation';
    RAISE NOTICE '3. Test user assignments';
    RAISE NOTICE '4. Regenerate Supabase TypeScript types';
    RAISE NOTICE '';
END $$;

