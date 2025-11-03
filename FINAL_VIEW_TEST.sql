-- Test all views now that data is populated

-- TEST 1: Organization Hierarchy
SELECT * FROM organization_hierarchy_v2;

-- TEST 2: Salesperson Assignments (should have no duplicates now)
SELECT * FROM salesperson_assignments_view;

-- TEST 3: Patient Distribution
SELECT * FROM patient_distribution_view;

-- TEST 4: Verify no duplicates
SELECT 
    user_id,
    center_id,
    COUNT(*) as count
FROM user_assignments
GROUP BY user_id, center_id
HAVING COUNT(*) > 1;
-- Should return 0 rows
