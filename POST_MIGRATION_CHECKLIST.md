# Post-Migration Checklist

## ✅ Migration Complete! Next Steps:

### STEP 1: Verify the Migration
Run these queries in your Supabase SQL Editor:

```sql
-- Check if all regions have organization_id
SELECT 
    COUNT(*) as total_regions,
    COUNT(organization_id) as regions_with_org,
    COUNT(*) - COUNT(organization_id) as orphaned_regions
FROM regions;

-- Check if all patients have center_id
SELECT 
    COUNT(*) as total_patients,
    COUNT(center_id) as patients_with_center,
    COUNT(*) - COUNT(center_id) as orphaned_patients
FROM patients;

-- Check overall hierarchy
SELECT * FROM organization_hierarchy_v2;
```

### STEP 2: Migrate Existing Data (if needed)

**A) If you have regions without organization_id:**
```sql
SELECT migrate_regions_to_organizations();
```

**B) If you have patients without center_id:**
```sql
SELECT migrate_patients_to_centers();
```

### STEP 3: Manually Fix Orphans (if any)

If the helper functions didn't catch everything, manually update:

```sql
-- Assign specific regions to organizations
UPDATE regions 
SET organization_id = 'your-org-uuid-here'
WHERE id = 'region-uuid-here' AND organization_id IS NULL;

-- Assign specific patients to centers
UPDATE patients 
SET center_id = 'center-uuid-here'
WHERE id = 'patient-uuid-here' AND center_id IS NULL;
```

### STEP 4: Test the New Relationships

```sql
-- Test: Get all centers for an organization
SELECT c.*, r.name as region_name 
FROM centers c
JOIN regions r ON c.region_id = r.id
WHERE r.organization_id = 'your-org-uuid';

-- Test: Get all patients for a center
SELECT p.* 
FROM patients p
WHERE p.center_id = 'your-center-uuid';

-- Test: Get a salesperson's accessible centers
SELECT * FROM salesperson_assignments_view
WHERE organization_id = 'your-org-uuid';

-- Test: See patient distribution
SELECT * FROM patient_distribution_view;
```

### STEP 5: Update Application Code

Now update your application to use these new relationships:

**Frontend (TypeScript):**
- Update patient forms to include center selection
- Update region management to link to organizations
- Update user assignment interfaces

**Backend (Python):**
- Update API endpoints to filter by organization hierarchy
- Update RLS policies if needed
- Update services to use new relationships

### STEP 6: Create Any Missing Centers

If patients exist but centers don't, you may need to:

```sql
-- Example: Create a center
INSERT INTO centers (region_id, name, address)
VALUES (
    (SELECT id FROM regions WHERE organization_id = 'org-uuid' LIMIT 1),
    'Main Center',
    '123 Main St'
);
```

## 🎯 Priority Actions

1. ✅ Migration ran successfully
2. ⏳ Verify data integrity (run STEP 1 queries)
3. ⏳ Migrate orphaned data (run STEP 2 functions)
4. ⏳ Manually fix any remaining orphans
5. ⏳ Test queries (run STEP 4 queries)
6. ⏳ Update application code

## 📊 Key Relationships Now Working

- ✅ Organizations → Regions
- ✅ Regions → Centers  
- ✅ Centers → Patients
- ✅ Salespeople → Multiple Centers via user_assignments

All foreign keys are now properly set up with indexes!
