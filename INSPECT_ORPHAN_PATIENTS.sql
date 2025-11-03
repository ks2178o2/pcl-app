-- Inspect orphan patients
SELECT 
    p.id,
    p.full_name,
    p.organization_id,
    p.center_id,
    p.created_at,
    -- Check if they have any call records
    (SELECT COUNT(*) FROM call_records cr WHERE cr.patient_id = p.id) as call_count,
    -- Get their most recent center from calls
    (SELECT cr.center_id FROM call_records cr 
     WHERE cr.patient_id = p.id 
     ORDER BY cr.created_at DESC 
     LIMIT 1) as most_recent_center_from_calls,
    -- Get center name
    c.name as current_center_name,
    -- Check if their org has any centers
    (SELECT COUNT(*) FROM centers c2 
     JOIN regions r ON c2.region_id = r.id 
     WHERE r.organization_id = p.organization_id) as org_centers_count
FROM patients p
LEFT JOIN centers c ON p.center_id = c.id
WHERE p.center_id IS NULL
ORDER BY p.created_at DESC;
