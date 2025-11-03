-- Check current RLS policies on patients table
SELECT 
    policyname,
    cmd,
    roles,
    qual,
    with_check
FROM pg_policies
WHERE tablename = 'patients'
ORDER BY policyname;

-- Check if policies exist
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ Policies exist'
        ELSE '❌ No policies found'
    END as status,
    COUNT(*) as policy_count
FROM pg_policies
WHERE tablename = 'patients';
