-- Strategy: Create user_assignments based on which centers users have interacted with
-- via call_records

-- Create assignments from call history
INSERT INTO user_assignments (user_id, center_id, created_at, updated_at)
SELECT DISTINCT
    cr.user_id,
    cr.center_id,
    NOW() as created_at,
    NOW() as updated_at
FROM call_records cr
WHERE cr.center_id IS NOT NULL
AND cr.user_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM user_assignments ua 
    WHERE ua.user_id = cr.user_id 
    AND ua.center_id = cr.center_id
);

-- Verify the inserts
SELECT 
    'After inserting from call_records' as step,
    COUNT(*) as total_assignments,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT center_id) as unique_centers
FROM user_assignments;
