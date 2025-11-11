-- Check what roles exist in user_roles table
SELECT 
    ur.user_id,
    p.salesperson_name,
    ur.role,
    ur.organization_id
FROM user_roles ur
JOIN profiles p ON ur.user_id = p.user_id
ORDER BY p.salesperson_name, ur.role
LIMIT 20;

-- Also check if role has an enum
SELECT unnest(enum_range(NULL::user_role)) as possible_roles;
