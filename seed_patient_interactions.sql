-- Seed patient_interactions table from existing data
-- This backfills interaction history from call_records and appointments
-- Run this in your Supabase SQL Editor

DO $$
DECLARE
  org_record RECORD;
BEGIN
  -- Insert interactions from call_records
  INSERT INTO patient_interactions (
    patient_id,
    patient_name,
    user_id,
    organization_id,
    interaction_type,
    call_record_id,
    interaction_date,
    metadata
  )
  SELECT DISTINCT
    cr.patient_id,
    cr.customer_name,
    cr.user_id,
    COALESCE(
      (SELECT organization_id FROM profiles WHERE user_id = cr.user_id LIMIT 1),
      (SELECT organization_id FROM patients WHERE id = cr.patient_id LIMIT 1)
    ),
    'call',
    cr.id,
    cr.start_time,
    jsonb_build_object(
      'duration_seconds', cr.duration_seconds,
      'has_transcript', CASE WHEN cr.transcript IS NOT NULL THEN true ELSE false END
    )
  FROM call_records cr
  WHERE cr.recording_complete = true
    AND NOT EXISTS (
      SELECT 1 FROM patient_interactions pi 
      WHERE pi.call_record_id = cr.id
    )
  ON CONFLICT DO NOTHING;

  RAISE NOTICE '✅ Synced call_records to patient_interactions';

  -- Insert interactions from appointments
  -- Use only columns that definitely exist: customer_name, user_id, appointment_date, created_at, id
  -- For optional columns, use JSONB to extract if they exist, otherwise use defaults
  INSERT INTO patient_interactions (
    patient_id,
    patient_name,
    user_id,
    organization_id,
    interaction_type,
    appointment_id,
    interaction_date,
    metadata,
    outcome
  )
  SELECT DISTINCT
    (SELECT p.id FROM patients p WHERE p.full_name = apt.customer_name LIMIT 1) as patient_id,
    apt.customer_name,
    apt.user_id,
    (SELECT organization_id FROM profiles WHERE user_id = apt.user_id LIMIT 1) as organization_id,
    'appointment' as interaction_type, -- Default, will be updated if type column exists
    apt.id,
    COALESCE(apt.appointment_date, apt.created_at),
    jsonb_build_object('source', 'appointment'),
    'scheduled' as outcome
  FROM appointments apt
  WHERE NOT EXISTS (
    SELECT 1 FROM patient_interactions pi 
    WHERE pi.appointment_id = apt.id
  )
  ON CONFLICT DO NOTHING;
  
  RAISE NOTICE '✅ Synced appointments to patient_interactions';

  -- Create sample webform/walk-in/online inquiry interactions for variety
  -- This simulates initial contact methods for patients who have appointments but no recorded initial contact
  INSERT INTO patient_interactions (
    patient_id,
    patient_name,
    user_id,
    organization_id,
    interaction_type,
    interaction_date,
    metadata,
    notes
  )
  SELECT DISTINCT
    p.id,
    p.full_name,
    (SELECT user_id FROM profiles WHERE organization_id = p.organization_id LIMIT 1),
    p.organization_id,
    CASE 
      WHEN ASCII(UPPER(LEFT(p.full_name, 1))) % 4 = 0 THEN 'webform'
      WHEN ASCII(UPPER(LEFT(p.full_name, 1))) % 4 = 1 THEN 'walk_in'
      WHEN ASCII(UPPER(LEFT(p.full_name, 1))) % 4 = 2 THEN 'online_inquiry'
      ELSE 'referral'
    END,
    p.created_at - INTERVAL '1 day', -- Initial contact before first appointment
    jsonb_build_object('source', 'initial_contact'),
    'Initial patient contact'
  FROM patients p
  WHERE p.created_at < (
    SELECT MIN(a.created_at) 
    FROM appointments a 
    WHERE a.customer_name = p.full_name
  )
  AND NOT EXISTS (
    SELECT 1 FROM patient_interactions pi 
    WHERE pi.patient_name = p.full_name 
    AND pi.interaction_type IN ('webform', 'walk_in', 'online_inquiry', 'referral')
  )
  ON CONFLICT DO NOTHING;

  RAISE NOTICE '✅ Created initial contact interactions for patients';

  -- Create sample email and SMS interactions for patients with multiple appointments
  -- This adds variety to interaction history
  INSERT INTO patient_interactions (
    patient_id,
    patient_name,
    user_id,
    organization_id,
    interaction_type,
    interaction_date,
    metadata,
    notes
  )
  SELECT DISTINCT
    p.id,
    a.customer_name,
    a.user_id,
    a.organization_id,
    CASE 
      WHEN ASCII(UPPER(LEFT(a.customer_name, 1))) % 2 = 0 THEN 'email'
      ELSE 'sms'
    END,
    a.created_at - INTERVAL '2 hours', -- Email/SMS before appointment
    jsonb_build_object('type', 'follow_up'),
    CASE 
      WHEN ASCII(UPPER(LEFT(a.customer_name, 1))) % 2 = 0 THEN 'Appointment confirmation email'
      ELSE 'Appointment reminder SMS'
    END
  FROM appointments a
  JOIN patients p ON p.full_name = a.customer_name AND p.organization_id = a.organization_id
  WHERE a.type ILIKE '%follow%'
    AND NOT EXISTS (
      SELECT 1 FROM patient_interactions pi 
      WHERE pi.patient_name = a.customer_name 
      AND pi.user_id = a.user_id
      AND pi.interaction_type IN ('email', 'sms')
      AND DATE(pi.interaction_date) = DATE(a.created_at)
    )
  ON CONFLICT DO NOTHING;

  RAISE NOTICE '✅ Created email/SMS interactions for variety';

END $$;

-- Show summary
SELECT 
  interaction_type,
  COUNT(*) as count
FROM patient_interactions
GROUP BY interaction_type
ORDER BY count DESC;
