-- Check what RLS policies currently exist on patients table
SELECT 
    policyname,
    cmd,
    roles
FROM pg_policies
WHERE tablename = 'patients'
ORDER BY policyname;

-- Count policies
SELECT 
    COUNT(*) as total_policies,
    string_agg(policyname, ', ' ORDER BY policyname) as policy_names
FROM pg_policies
WHERE tablename = 'patients';

