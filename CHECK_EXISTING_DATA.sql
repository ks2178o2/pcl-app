-- Check existing organizations, centers, and user count
SELECT 
    o.id as org_id,
    o.name as org_name,
    COUNT(DISTINCT r.id) as regions,
    COUNT(DISTINCT c.id) as centers,
    COUNT(DISTINCT p.id) as patients,
    COUNT(DISTINCT pr.user_id) as profiles
FROM organizations o
LEFT JOIN regions r ON r.organization_id = o.id
LEFT JOIN centers c ON c.region_id = r.id
LEFT JOIN patients p ON p.center_id = c.id
LEFT JOIN profiles pr ON pr.organization_id = o.id
GROUP BY o.id, o.name
ORDER BY o.name;

-- Check existing centers and their assignments
SELECT 
    c.id,
    c.name,
    r.name as region_name,
    o.name as org_name,
    COUNT(DISTINCT ua.user_id) as assigned_users,
    COUNT(DISTINCT p.id) as patients
FROM centers c
LEFT JOIN regions r ON c.region_id = r.id
LEFT JOIN organizations o ON r.organization_id = o.id
LEFT JOIN user_assignments ua ON ua.center_id = c.id
LEFT JOIN patients p ON p.center_id = c.id
GROUP BY c.id, c.name, r.name, o.name
ORDER BY o.name, c.name;
