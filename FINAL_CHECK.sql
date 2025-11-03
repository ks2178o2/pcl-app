-- Quick check after cleanup
SELECT 
    ua.user_id,
    p.salesperson_name,
    COUNT(*) as total_assignments,
    COUNT(DISTINCT ua.center_id) as distinct_centers,
    string_agg(c.name, ', ') as centers
FROM user_assignments ua
LEFT JOIN profiles p ON ua.user_id = p.user_id
LEFT JOIN centers c ON ua.center_id = c.id
WHERE ua.center_id IS NOT NULL
GROUP BY ua.user_id, p.salesperson_name
ORDER BY salesperson_name;

-- Check for any remaining duplicates
SELECT 
    user_id,
    center_id,
    COUNT(*) as count
FROM user_assignments
WHERE center_id IS NOT NULL
GROUP BY user_id, center_id
HAVING COUNT(*) > 1;
