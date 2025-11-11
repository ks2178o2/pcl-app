-- Check the actual schema of user_assignments table
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'user_assignments'
ORDER BY ordinal_position;
