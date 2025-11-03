-- Assign all 5 orphan patients to Sales Center A
UPDATE patients 
SET center_id = '922b1622-9235-4780-9fc0-e253f7b80f22'
WHERE id IN (
    '55ece5bf-5288-4758-bef6-9ed13953976f', -- Bob Johnson
    '4df033af-d646-4729-ace4-e41449617d7e', -- Jane Smith
    'f4c21a29-fd2d-4f8e-915f-fce6273742eb', -- John Doe
    '50a26265-0837-4210-8035-debe8bc7271c', -- Test Patient 1
    '57b2c731-61ff-4696-b1aa-1fc77ca28081'  -- Test Patient 2
);

-- Verify the fix
SELECT 
    p.full_name,
    p.center_id,
    c.name as center_name,
    CASE WHEN p.center_id IS NOT NULL THEN '✅ Assigned' ELSE '❌ Orphan' END as status
FROM patients p
LEFT JOIN centers c ON p.center_id = c.id
WHERE p.id IN (
    '55ece5bf-5288-4758-bef6-9ed13953976f',
    '4df033af-d646-4729-ace4-e41449617d7e',
    'f4c21a29-fd2d-4f8e-915f-fce6273742eb',
    '50a26265-0837-4210-8035-debe8bc7271c',
    '57b2c731-61ff-4696-b1aa-1fc77ca28081'
);

-- Final check - should return 0 orphans
SELECT COUNT(*) as remaining_orphans
FROM patients
WHERE center_id IS NULL;
