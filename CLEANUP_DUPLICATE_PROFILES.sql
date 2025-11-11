-- Remove duplicate profiles, keeping only the most recent one per user_id
DELETE FROM profiles p
WHERE p.id NOT IN (
    SELECT DISTINCT ON (user_id) id
    FROM profiles
    ORDER BY user_id, created_at DESC
);

-- Verify no duplicates remain
SELECT 
    user_id,
    COUNT(*) as profile_count
FROM profiles
GROUP BY user_id
HAVING COUNT(*) > 1;
-- Should return 0 rows

-- Show final profiles
SELECT 
    id,
    user_id,
    salesperson_name,
    organization_id
FROM profiles
ORDER BY user_id;
