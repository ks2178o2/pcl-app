-- ===========================================
-- Database Hierarchy Migration
-- Fix organizational relationships based on:
-- 1. Organization = Customer
-- 2. Regions belong to Organizations
-- 3. Centers belong to Regions
-- 4. Patients belong to Centers
-- 5. Salespeople can be assigned to multiple centers
-- 6. Keep networks for future use
-- ===========================================

-- ===========================================
-- STEP 1: Add organization_id to regions table
-- ===========================================

-- Add organization_id column to regions if it doesn't exist
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'regions' AND column_name = 'organization_id'
  ) THEN
    ALTER TABLE regions ADD COLUMN organization_id UUID;
    
    -- Add foreign key constraint after populating data
    ALTER TABLE regions 
    ADD CONSTRAINT regions_organization_id_fkey 
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;
    
    -- Create index for performance
    CREATE INDEX IF NOT EXISTS idx_regions_organization_id ON regions(organization_id);
    
    RAISE NOTICE '✅ Added organization_id column to regions table';
  ELSE
    RAISE NOTICE 'ℹ️ organization_id column already exists in regions table';
  END IF;
END $$;

-- ===========================================
-- STEP 2: Add center_id to patients table
-- ===========================================

-- Add center_id column to patients if it doesn't exist
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'patients' AND column_name = 'center_id'
  ) THEN
    ALTER TABLE patients ADD COLUMN center_id UUID;
    
    -- Add foreign key constraint
    ALTER TABLE patients 
    ADD CONSTRAINT patients_center_id_fkey 
    FOREIGN KEY (center_id) REFERENCES centers(id) ON DELETE SET NULL;
    
    -- Create index for performance
    CREATE INDEX IF NOT EXISTS idx_patients_center_id ON patients(center_id);
    
    RAISE NOTICE '✅ Added center_id column to patients table';
  ELSE
    RAISE NOTICE 'ℹ️ center_id column already exists in patients table';
  END IF;
END $$;

-- ===========================================
-- STEP 3: Update user_assignments constraints
-- ===========================================

-- Add check constraint to ensure user_assignments has at least one assignment
DO $$ 
DECLARE
  has_network_id BOOLEAN;
BEGIN
  -- Check if network_id column exists
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'user_assignments' AND column_name = 'network_id'
  ) INTO has_network_id;
  
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints 
    WHERE constraint_name = 'user_assignments_has_assignment_check'
  ) THEN
    IF has_network_id THEN
      -- Full constraint with network_id
      ALTER TABLE user_assignments 
      ADD CONSTRAINT user_assignments_has_assignment_check 
      CHECK (
        network_id IS NOT NULL OR 
        region_id IS NOT NULL OR 
        center_id IS NOT NULL
      );
    ELSE
      -- Constraint without network_id
      ALTER TABLE user_assignments 
      ADD CONSTRAINT user_assignments_has_assignment_check 
      CHECK (
        region_id IS NOT NULL OR 
        center_id IS NOT NULL
      );
    END IF;
    
    RAISE NOTICE '✅ Added constraint to ensure user_assignments has at least one assignment';
  ELSE
    RAISE NOTICE 'ℹ️ user_assignments constraint already exists';
  END IF;
END $$;

-- ===========================================
-- STEP 4: Add missing indexes for performance
-- ===========================================

-- Add indexes for call_records relationships
CREATE INDEX IF NOT EXISTS idx_call_records_organization_id ON call_records(organization_id);
CREATE INDEX IF NOT EXISTS idx_call_records_center_id ON call_records(center_id);
CREATE INDEX IF NOT EXISTS idx_call_records_patient_id ON call_records(patient_id);
CREATE INDEX IF NOT EXISTS idx_call_records_user_id ON call_records(user_id);

-- Add indexes for profiles
CREATE INDEX IF NOT EXISTS idx_profiles_organization_id ON profiles(organization_id);
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);

-- Add index for centers
CREATE INDEX IF NOT EXISTS idx_centers_region_id ON centers(region_id);

-- ===========================================
-- STEP 5: Create helpful views
-- ===========================================

-- View: Organization hierarchy with regions and centers
CREATE OR REPLACE VIEW organization_hierarchy_v2 AS
SELECT 
    o.id as organization_id,
    o.name as organization_name,
    o.business_type,
    COUNT(DISTINCT r.id) as total_regions,
    COUNT(DISTINCT c.id) as total_centers,
    COUNT(DISTINCT p.id) as total_patients,
    COUNT(DISTINCT prof.user_id) as total_salespeople
FROM organizations o
LEFT JOIN regions r ON r.organization_id = o.id
LEFT JOIN centers c ON c.region_id = r.id
LEFT JOIN patients p ON p.center_id = c.id
LEFT JOIN profiles prof ON prof.organization_id = o.id
GROUP BY o.id, o.name, o.business_type;

COMMENT ON VIEW organization_hierarchy_v2 IS 'Complete organization hierarchy with counts of regions, centers, patients, and salespeople';

-- View: Salesperson assignments across organization
CREATE OR REPLACE VIEW salesperson_assignments_view AS
SELECT 
    p.user_id,
    p.id as profile_id,
    p.salesperson_name,
    o.id as organization_id,
    o.name as organization_name,
    ua.id as assignment_id,
    ua.center_id,
    c.name as center_name,
    r.name as region_name,
    o2.name as organization_name_from_center
FROM profiles p
LEFT JOIN organizations o ON p.organization_id = o.id
LEFT JOIN user_assignments ua ON ua.user_id = p.user_id
LEFT JOIN centers c ON ua.center_id = c.id
LEFT JOIN regions r ON c.region_id = r.id
LEFT JOIN organizations o2 ON r.organization_id = o2.id
WHERE ua.center_id IS NOT NULL;

COMMENT ON VIEW salesperson_assignments_view IS 'View of all salesperson center assignments with full context';

-- View: Patient distribution across organization
CREATE OR REPLACE VIEW patient_distribution_view AS
SELECT 
    o.id as organization_id,
    o.name as organization_name,
    r.id as region_id,
    r.name as region_name,
    c.id as center_id,
    c.name as center_name,
    COUNT(p.id) as patient_count,
    COUNT(DISTINCT cr.user_id) as salesperson_count_with_calls
FROM organizations o
JOIN regions r ON r.organization_id = o.id
JOIN centers c ON c.region_id = r.id
LEFT JOIN patients p ON p.center_id = c.id
LEFT JOIN call_records cr ON cr.patient_id = p.id
GROUP BY o.id, o.name, r.id, r.name, c.id, c.name
ORDER BY o.name, r.name, c.name;

COMMENT ON VIEW patient_distribution_view IS 'Distribution of patients across organization hierarchy with activity metrics';

-- ===========================================
-- STEP 6: Data migration helpers (if needed)
-- ===========================================

-- Function to migrate existing patient data to centers based on most recent call
CREATE OR REPLACE FUNCTION migrate_patients_to_centers()
RETURNS JSONB AS $$
DECLARE
    migrated_count INTEGER := 0;
    patient_record RECORD;
BEGIN
    -- For each patient, find their most recent call center and assign them to it
    FOR patient_record IN 
        SELECT DISTINCT ON (p.id) 
            p.id as patient_id,
            cr.center_id
        FROM patients p
        JOIN call_records cr ON cr.patient_id = p.id
        WHERE p.center_id IS NULL
        ORDER BY p.id, cr.created_at DESC
    LOOP
        IF patient_record.center_id IS NOT NULL THEN
            UPDATE patients 
            SET center_id = patient_record.center_id 
            WHERE id = patient_record.patient_id;
            migrated_count := migrated_count + 1;
        END IF;
    END LOOP;
    
    RETURN jsonb_build_object(
        'success', true,
        'migrated_patients', migrated_count,
        'message', 'Migration completed'
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION migrate_patients_to_centers() IS 'Helper function to migrate existing patient data to centers based on call history';

-- Function to migrate existing region data to organizations
CREATE OR REPLACE FUNCTION migrate_regions_to_organizations()
RETURNS JSONB AS $$
DECLARE
    migrated_count INTEGER := 0;
    region_record RECORD;
BEGIN
    -- For each region without organization_id, try to find it through centers and users
    FOR region_record IN 
        SELECT DISTINCT ON (r.id)
            r.id as region_id,
            p.organization_id
        FROM regions r
        JOIN centers c ON c.region_id = r.id
        JOIN profiles p ON TRUE  -- Cross join
        WHERE r.organization_id IS NULL
        AND EXISTS (
            -- Find if any user from this org has assignments in centers from this region
            SELECT 1 
            FROM user_assignments ua
            WHERE ua.center_id IN (SELECT id FROM centers WHERE region_id = r.id)
            AND ua.user_id IN (SELECT user_id FROM profiles WHERE organization_id = p.organization_id)
        )
        ORDER BY r.id, p.organization_id
    LOOP
        IF region_record.organization_id IS NOT NULL THEN
            UPDATE regions 
            SET organization_id = region_record.organization_id 
            WHERE id = region_record.region_id;
            migrated_count := migrated_count + 1;
        END IF;
    END LOOP;
    
    RETURN jsonb_build_object(
        'success', true,
        'migrated_regions', migrated_count,
        'message', 'Migration completed'
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION migrate_regions_to_organizations() IS 'Helper function to migrate existing region data to organizations based on user assignments';

-- ===========================================
-- STEP 7: Verification queries
-- ===========================================

-- Verification query to check the hierarchy
DO $$
DECLARE
    orphaned_regions INTEGER;
    orphaned_patients INTEGER;
    missing_center_patients INTEGER;
    multi_center_salespeople INTEGER;
BEGIN
    -- Check for orphaned regions (regions without organization_id)
    SELECT COUNT(*) INTO orphaned_regions
    FROM regions
    WHERE organization_id IS NULL;
    
    IF orphaned_regions > 0 THEN
        RAISE WARNING '⚠️ Found % regions without organization_id', orphaned_regions;
    ELSE
        RAISE NOTICE '✅ All regions have organization_id';
    END IF;
    
    -- Check for patients without centers
    SELECT COUNT(*) INTO missing_center_patients
    FROM patients
    WHERE center_id IS NULL;
    
    IF missing_center_patients > 0 THEN
        RAISE WARNING '⚠️ Found % patients without center_id', missing_center_patients;
        RAISE NOTICE '💡 You can run: SELECT migrate_patients_to_centers(); to migrate existing data';
    ELSE
        RAISE NOTICE '✅ All patients have center_id';
    END IF;
    
    -- Check for salespeople assigned to multiple centers
    SELECT COUNT(DISTINCT user_id) INTO multi_center_salespeople
    FROM user_assignments
    WHERE center_id IS NOT NULL
    GROUP BY user_id
    HAVING COUNT(*) > 1;
    
    RAISE NOTICE 'ℹ️ Found % salespeople assigned to multiple centers (expected)', multi_center_salespeople;
    
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ Hierarchy migration completed!';
    RAISE NOTICE '========================================';
END $$;

-- ===========================================
-- STEP 8: Summary report
-- ===========================================

-- Display summary of current state
SELECT 
    'Database Hierarchy Summary' as report_section,
    (SELECT COUNT(*) FROM organizations) as total_organizations,
    (SELECT COUNT(*) FROM regions) as total_regions,
    (SELECT COUNT(*) FROM regions WHERE organization_id IS NOT NULL) as regions_with_organization,
    (SELECT COUNT(*) FROM centers) as total_centers,
    (SELECT COUNT(*) FROM patients) as total_patients,
    (SELECT COUNT(*) FROM patients WHERE center_id IS NOT NULL) as patients_with_center,
    (SELECT COUNT(*) FROM profiles) as total_salespeople,
    (SELECT COUNT(DISTINCT user_id) FROM user_assignments WHERE center_id IS NOT NULL) as salespeople_assigned_to_centers;

-- ===========================================
-- STEP 9: Final completion message
-- ===========================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Review the verification queries above';
    RAISE NOTICE '2. Run SELECT migrate_regions_to_organizations(); if regions need migration';
    RAISE NOTICE '3. Run SELECT migrate_patients_to_centers(); if patients need migration';
    RAISE NOTICE '4. Manually fill in any remaining NULL values';
    RAISE NOTICE '5. Test the views: SELECT * FROM organization_hierarchy_v2;';
    RAISE NOTICE '';
END $$;

