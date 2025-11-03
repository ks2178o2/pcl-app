-- Fix orphan patients by assigning them to a center

-- Strategy 1: Assign to center from most recent call record
UPDATE patients p
SET center_id = (
    SELECT cr.center_id 
    FROM call_records cr 
    WHERE cr.patient_id = p.id 
    AND cr.center_id IS NOT NULL
    ORDER BY cr.created_at DESC 
    LIMIT 1
)
WHERE p.center_id IS NULL
AND EXISTS (
    SELECT 1 FROM call_records cr 
    WHERE cr.patient_id = p.id 
    AND cr.center_id IS NOT NULL
);

-- Check how many were fixed
SELECT COUNT(*) as fixed_from_call_records
FROM patients
WHERE center_id IS NOT NULL 
AND id IN (
    SELECT id FROM patients WHERE center_id WAS NULL
);

-- Strategy 2: Assign to first available center in their organization
UPDATE patients p
SET center_id = (
    SELECT c.id 
    FROM centers c
    JOIN regions r ON c.region_id = r.id
    WHERE r.organization_id = p.organization_id
    ORDER BY c.created_at ASC
    LIMIT 1
)
WHERE p.center_id IS NULL
AND EXISTS (
    SELECT 1 FROM centers c
    JOIN regions r ON c.region_id = r.id
    WHERE r.organization_id = p.organization_id
);

-- Strategy 3: If no centers exist, show which patients still need manual assignment
SELECT 
    p.id,
    p.full_name,
    p.organization_id,
    o.name as org_name,
    (SELECT COUNT(*) FROM centers c 
     JOIN regions r ON c.region_id = r.id 
     WHERE r.organization_id = p.organization_id) as centers_count
FROM patients p
LEFT JOIN organizations o ON p.organization_id = o.id
WHERE p.center_id IS NULL;

-- Final check
SELECT 
    COUNT(*) as remaining_orphans,
    COUNT(*) FILTER (WHERE EXISTS (
        SELECT 1 FROM call_records cr 
        WHERE cr.patient_id = patients.id 
        AND cr.center_id IS NOT NULL
    )) as patients_with_call_history
FROM patients
WHERE center_id IS NULL;
