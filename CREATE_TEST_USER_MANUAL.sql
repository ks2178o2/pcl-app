-- ===========================================
-- Manual Test: Create Complete Test User Journey
-- ===========================================
-- This simulates the happy path using SQL directly
-- Note: This is for testing. Actual app flow uses UI + Supabase Auth
-- ===========================================

-- STEP 1: Check existing organizations to use for testing
SELECT 
    id,
    name,
    business_type
FROM organizations
ORDER BY name;

-- STEP 2: Check existing centers we can assign to
SELECT 
    c.id,
    c.name as center_name,
    r.name as region_name,
    o.name as org_name,
    COUNT(DISTINCT p.id) as patients,
    COUNT(DISTINCT ua.user_id) as users
FROM centers c
LEFT JOIN regions r ON c.region_id = r.id
LEFT JOIN organizations o ON r.organization_id = o.id
LEFT JOIN patients p ON p.center_id = c.id
LEFT JOIN user_assignments ua ON ua.center_id = c.id
GROUP BY c.id, c.name, r.name, o.name
ORDER BY o.name, c.name;

-- Use the output from above to note:
-- Organization ID: _________________
-- Center ID: _________________

