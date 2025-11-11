-- Complete cleanup workflow

-- STEP 1: Clean duplicate user_assignments
DELETE FROM user_assignments ua
WHERE ua.id NOT IN (
    SELECT DISTINCT ON (user_id, center_id) id
    FROM user_assignments
    WHERE center_id IS NOT NULL
    ORDER BY user_id, center_id, created_at DESC
);

DELETE FROM user_assignments ua
WHERE ua.id NOT IN (
    SELECT DISTINCT ON (user_id, region_id) id
    FROM user_assignments
    WHERE region_id IS NOT NULL
    ORDER BY user_id, region_id, created_at DESC
);

-- STEP 2: Clean duplicate profiles
DELETE FROM profiles p
WHERE p.id NOT IN (
    SELECT DISTINCT ON (user_id) id
    FROM profiles
    ORDER BY user_id, created_at DESC
);

-- STEP 3: Verify
SELECT 
    'user_assignments' as table_name,
    COUNT(*) as total,
    COUNT(DISTINCT user_id) as distinct_users
FROM user_assignments

UNION ALL

SELECT 
    'profiles' as table_name,
    COUNT(*) as total,
    COUNT(DISTINCT user_id) as distinct_users
FROM profiles;
