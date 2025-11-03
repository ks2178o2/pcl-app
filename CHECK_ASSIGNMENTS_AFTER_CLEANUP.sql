-- Check if any user_assignments still exist
SELECT COUNT(*) as total_assignments FROM user_assignments;

-- Check if any users have assignments
SELECT 
    p.user_id,
    p.salesperson_name,
    p.organization_id,
    (SELECT COUNT(*) FROM user_assignments WHERE user_id = p.user_id) as assignment_count
FROM profiles p
WHERE (SELECT COUNT(*) FROM user_assignments WHERE user_id = p.user_id) > 0;
