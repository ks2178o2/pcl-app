-- Assign all users in each organization to all centers in their organization

INSERT INTO user_assignments (user_id, center_id, role, created_at, updated_at)
SELECT DISTINCT
    p.user_id,
    c.id as center_id,
    'salesperson' as role, -- Default role for all assignments
    NOW() as created_at,
    NOW() as updated_at
FROM profiles p
JOIN organizations o ON p.organization_id = o.id
JOIN regions r ON r.organization_id = o.id
JOIN centers c ON c.region_id = r.id
WHERE NOT EXISTS (
    SELECT 1 FROM user_assignments ua
    WHERE ua.user_id = p.user_id
    AND ua.center_id = c.id
);

-- Show results
SELECT 
    COUNT(*) as total_assignments_created,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT center_id) as unique_centers
FROM user_assignments;
