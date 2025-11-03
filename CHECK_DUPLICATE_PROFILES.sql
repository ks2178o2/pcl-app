-- Check for duplicate profiles
SELECT 
    user_id,
    COUNT(*) as profile_count,
    array_agg(id::text ORDER BY created_at) as profile_ids,
    array_agg(salesperson_name) as names,
    array_agg(organization_id::text) as org_ids
FROM profiles
GROUP BY user_id
HAVING COUNT(*) > 1
ORDER BY profile_count DESC;

-- Show all profiles
SELECT 
    id,
    user_id,
    salesperson_name,
    organization_id,
    created_at
FROM profiles
ORDER BY user_id, created_at;
