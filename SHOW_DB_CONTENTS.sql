-- ===========================================
-- Complete Database Contents Viewer
-- ===========================================
-- Shows all tables and their current data
-- Run this in Supabase SQL Editor
-- ===========================================

-- ===========================================
-- 1. ORGANIZATIONS
-- ===========================================
SELECT 'ORGANIZATIONS' as table_name;
SELECT 
    id,
    name,
    business_type,
    created_at,
    updated_at
FROM organizations
ORDER BY name;

-- ===========================================
-- 2. REGIONS
-- ===========================================
SELECT 'REGIONS' as table_name;
SELECT 
    r.id,
    r.name,
    r.organization_id,
    o.name as organization_name,
    r.created_at
FROM regions r
LEFT JOIN organizations o ON r.organization_id = o.id
ORDER BY o.name, r.name;

-- ===========================================
-- 3. CENTERS
-- ===========================================
SELECT 'CENTERS' as table_name;
SELECT 
    c.id,
    c.name,
    c.region_id,
    r.name as region_name,
    r.organization_id,
    o.name as organization_name,
    c.created_at
FROM centers c
LEFT JOIN regions r ON c.region_id = r.id
LEFT JOIN organizations o ON r.organization_id = o.id
ORDER BY o.name, r.name, c.name;

-- ===========================================
-- 4. PATIENTS (with hierarchy)
-- ===========================================
SELECT 'PATIENTS' as table_name;
SELECT 
    p.id,
    p.full_name,
    p.email,
    p.phone,
    p.center_id,
    c.name as center_name,
    r.name as region_name,
    o.name as organization_name,
    p.friendly_id,
    p.created_at
FROM patients p
LEFT JOIN centers c ON p.center_id = c.id
LEFT JOIN regions r ON c.region_id = r.id
LEFT JOIN organizations o ON r.organization_id = o.id
ORDER BY o.name, c.name, p.full_name;

-- ===========================================
-- 5. PROFILES (users)
-- ===========================================
SELECT 'PROFILES' as table_name;
SELECT 
    p.id,
    p.user_id,
    p.salesperson_name,
    p.organization_id,
    o.name as organization_name,
    p.created_at,
    p.updated_at
FROM profiles p
LEFT JOIN organizations o ON p.organization_id = o.id
ORDER BY p.salesperson_name;

-- ===========================================
-- 6. USER ASSIGNMENTS
-- ===========================================
SELECT 'USER_ASSIGNMENTS' as table_name;
SELECT 
    ua.id,
    ua.user_id,
    p.salesperson_name,
    ua.center_id,
    c.name as center_name,
    ua.region_id,
    r.name as region_name,
    o.name as organization_name,
    ua.role,
    ua.is_active,
    ua.created_at
FROM user_assignments ua
LEFT JOIN profiles p ON ua.user_id = p.user_id
LEFT JOIN centers c ON ua.center_id = c.id
LEFT JOIN regions r ON ua.region_id = r.id
LEFT JOIN organizations o ON r.organization_id = o.id OR (ua.organization_id IS NOT NULL AND ua.organization_id = o.id)
ORDER BY p.salesperson_name, c.name;

-- ===========================================
-- 7. USER ROLES
-- ===========================================
SELECT 'USER_ROLES' as table_name;
SELECT 
    ur.id,
    ur.user_id,
    p.salesperson_name,
    ur.role,
    ur.organization_id,
    o.name as organization_name,
    ur.is_active,
    ur.created_at
FROM user_roles ur
LEFT JOIN profiles p ON ur.user_id = p.user_id
LEFT JOIN organizations o ON ur.organization_id = o.id
ORDER BY p.salesperson_name, ur.role;

-- ===========================================
-- 8. CALL RECORDS (recent)
-- ===========================================
SELECT 'CALL_RECORDS (recent 10)' as table_name;
SELECT 
    cr.id,
    cr.customer_name,
    cr.center_id,
    c.name as center_name,
    cr.patient_id,
    p.full_name as patient_name,
    cr.salesperson_name,
    cr.status,
    cr.recording_complete,
    cr.created_at
FROM call_records cr
LEFT JOIN centers c ON cr.center_id = c.id
LEFT JOIN patients p ON cr.patient_id = p.id
ORDER BY cr.created_at DESC
LIMIT 10;

-- ===========================================
-- 9. SUMMARY COUNTS
-- ===========================================
SELECT 'SUMMARY' as table_name;
SELECT 
    'Organizations' as entity,
    COUNT(*) as count
FROM organizations
UNION ALL
SELECT 
    'Regions',
    COUNT(*)
FROM regions
UNION ALL
SELECT 
    'Centers',
    COUNT(*)
FROM centers
UNION ALL
SELECT 
    'Patients',
    COUNT(*)
FROM patients
UNION ALL
SELECT 
    'Profiles (Users)',
    COUNT(*)
FROM profiles
UNION ALL
SELECT 
    'User Assignments',
    COUNT(*)
FROM user_assignments
UNION ALL
SELECT 
    'User Roles',
    COUNT(*)
FROM user_roles
UNION ALL
SELECT 
    'Call Records',
    COUNT(*)
FROM call_records
ORDER BY entity;

-- ===========================================
-- 10. HIERARCHY SUMMARY BY ORGANIZATION
-- ===========================================
SELECT 'HIERARCHY_SUMMARY' as table_name;
SELECT 
    o.name as organization,
    COUNT(DISTINCT r.id) as regions,
    COUNT(DISTINCT c.id) as centers,
    COUNT(DISTINCT p.id) as patients,
    COUNT(DISTINCT pr.user_id) as users,
    COUNT(DISTINCT ua.user_id) as assigned_users
FROM organizations o
LEFT JOIN regions r ON r.organization_id = o.id
LEFT JOIN centers c ON c.region_id = r.id
LEFT JOIN patients p ON p.center_id = c.id
LEFT JOIN profiles pr ON pr.organization_id = o.id
LEFT JOIN user_assignments ua ON ua.center_id = c.id OR ua.region_id = r.id
GROUP BY o.id, o.name
ORDER BY o.name;

-- ===========================================
-- 11. RLS POLICIES STATUS
-- ===========================================
SELECT 'RLS_POLICIES' as table_name;
SELECT 
    schemaname,
    tablename,
    policyname,
    roles,
    cmd as operation
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('patients', 'centers', 'regions', 'organizations', 'user_assignments', 'call_records')
ORDER BY tablename, policyname;

-- ===========================================
-- DONE
-- ===========================================
SELECT 'END' as status;

