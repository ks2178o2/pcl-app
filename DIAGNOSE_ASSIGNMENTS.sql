-- Check if we accidentally deleted everything
-- First, see if there's any backup or audit

SELECT 
    COUNT(*) as total_assignments,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT center_id) as unique_centers,
    COUNT(DISTINCT region_id) as unique_regions
FROM user_assignments;

-- Check profiles with their organizations
SELECT 
    p.user_id,
    p.salesperson_name,
    p.organization_id,
    o.name as org_name
FROM profiles p
LEFT JOIN organizations o ON p.organization_id = o.id
ORDER BY p.salesperson_name
LIMIT 20;

-- Check what centers exist
SELECT 
    c.id,
    c.name,
    c.region_id,
    r.name as region_name,
    o.name as org_name
FROM centers c
JOIN regions r ON c.region_id = r.id
JOIN organizations o ON r.organization_id = o.id
ORDER BY o.name, r.name, c.name;
