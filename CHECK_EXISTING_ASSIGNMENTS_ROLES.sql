-- Check if there are any existing user_assignments with roles
SELECT DISTINCT role
FROM user_assignments
WHERE role IS NOT NULL;

-- Check what roles might be used elsewhere in the app
SELECT 
    schemaname, 
    tablename, 
    column_name, 
    data_type
FROM information_schema.columns
WHERE column_name LIKE '%role%'
AND table_schema = 'public';
