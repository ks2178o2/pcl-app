-- ===========================================
-- Clean up duplicate user_assignments
-- ===========================================

-- Strategy: Keep only the most recent assignment per user_id + center_id
DELETE FROM user_assignments ua
WHERE ua.id NOT IN (
    SELECT DISTINCT ON (user_id, center_id) id
    FROM user_assignments
    WHERE center_id IS NOT NULL
    ORDER BY user_id, center_id, created_at DESC
)
AND ua.center_id IS NOT NULL;

-- Also clean up duplicate assignments for regions
DELETE FROM user_assignments ua
WHERE ua.id NOT IN (
    SELECT DISTINCT ON (user_id, region_id) id
    FROM user_assignments
    WHERE region_id IS NOT NULL
    ORDER BY user_id, region_id, created_at DESC
)
AND ua.region_id IS NOT NULL;

-- Verify no duplicates remain
SELECT 
    user_id,
    center_id,
    region_id,
    COUNT(*) as count
FROM user_assignments
GROUP BY user_id, center_id, region_id
HAVING COUNT(*) > 1;
-- Should return 0 rows

-- Show final count
SELECT 
    COUNT(*) as total_assignments,
    COUNT(DISTINCT user_id) as users_with_assignments
FROM user_assignments;
