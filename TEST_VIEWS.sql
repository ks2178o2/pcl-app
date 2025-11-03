-- ===========================================
-- Test All Hierarchy Views
-- ===========================================

-- TEST 1: Organization Hierarchy Summary
SELECT * FROM organization_hierarchy_v2;

-- TEST 2: Salesperson Assignments
SELECT * FROM salesperson_assignments_view
LIMIT 10;

-- TEST 3: Patient Distribution
SELECT * FROM patient_distribution_view;

-- TEST 4: Complete relationships check
SELECT 
    'Organizations' as table_name,
    COUNT(*) as total_count,
    NULL::bigint as parent_relationships
FROM organizations

UNION ALL

SELECT 
    'Regions with Organizations' as table_name,
    COUNT(*) as total_count,
    COUNT(organization_id) as parent_relationships
FROM regions

UNION ALL

SELECT 
    'Centers with Regions' as table_name,
    COUNT(*) as total_count,
    COUNT(region_id) as parent_relationships
FROM centers

UNION ALL

SELECT 
    'Patients with Centers' as table_name,
    COUNT(*) as total_count,
    COUNT(center_id) as parent_relationships
FROM patients

UNION ALL

SELECT 
    'Salespeople with Orgs' as table_name,
    COUNT(*) as total_count,
    COUNT(organization_id) as parent_relationships
FROM profiles;

-- TEST 5: Verify relationship paths work
SELECT 
    p.full_name as patient_name,
    c.name as center_name,
    r.name as region_name,
    o.name as organization_name
FROM patients p
JOIN centers c ON p.center_id = c.id
JOIN regions r ON c.region_id = r.id
JOIN organizations o ON r.organization_id = o.id
LIMIT 10;

-- TEST 6: Check user assignments work
SELECT 
    prof.salesperson_name,
    ua.center_id,
    c.name as center_name,
    r.name as region_name,
    o.name as org_name
FROM user_assignments ua
JOIN centers c ON ua.center_id = c.id
JOIN regions r ON c.region_id = r.id
JOIN organizations o ON r.organization_id = o.id
JOIN profiles prof ON prof.user_id = ua.user_id
LIMIT 10;
