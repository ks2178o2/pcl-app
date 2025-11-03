-- Check for duplicate user_assignments entries
SELECT 
    user_id,
    center_id,
    COUNT(*) as assignment_count,
    array_agg(id::text ORDER BY created_at) as assignment_ids
FROM user_assignments
WHERE center_id IS NOT NULL
GROUP BY user_id, center_id
HAVING COUNT(*) > 1
ORDER BY assignment_count DESC;

-- Check total assignments by user
SELECT 
    ua.user_id,
    p.salesperson_name,
    COUNT(*) as total_assignments,
    COUNT(DISTINCT ua.center_id) as distinct_centers
FROM user_assignments ua
LEFT JOIN profiles p ON ua.user_id = p.user_id
WHERE ua.center_id IS NOT NULL
GROUP BY ua.user_id, p.salesperson_name
ORDER BY total_assignments DESC;
