-- Verification queries for call_type migration
-- Run these to confirm the migration was successful

-- 1. Check if call_type column exists
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'call_records' 
AND column_name = 'call_type';

-- 2. Check if indexes were created
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'call_records' 
AND indexname IN (
    'idx_call_records_call_type',
    'idx_call_records_category_type',
    'idx_call_records_type_created'
)
ORDER BY indexname;

-- 3. Check column constraints (should show the CHECK constraint)
SELECT 
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'call_records'::regclass
AND conname LIKE '%call_type%';

-- 4. Check column comments
SELECT 
    col_description('call_records'::regclass, ordinal_position) AS column_comment
FROM information_schema.columns
WHERE table_name = 'call_records'
AND column_name = 'call_type';

-- 5. Sample query to test the new column (should return 0 or more rows)
SELECT 
    COUNT(*) as total_records,
    COUNT(call_type) as records_with_call_type,
    COUNT(*) - COUNT(call_type) as records_without_call_type
FROM call_records;

-- 6. Show call_type distribution (if any records have it)
SELECT 
    call_type,
    COUNT(*) as count
FROM call_records
WHERE call_type IS NOT NULL
GROUP BY call_type
ORDER BY count DESC;

