-- Check what appointments exist and their dates
DO $$
DECLARE
  mickey_user_id UUID;
  rec RECORD;
BEGIN
  -- Get Mickey's user_id
  SELECT id INTO mickey_user_id
  FROM auth.users
  WHERE email = 'mickey.mouse@disney.com'
  LIMIT 1;

  IF mickey_user_id IS NULL THEN
    RAISE NOTICE '❌ Mickey Mouse user not found.';
    RETURN;
  END IF;

  RAISE NOTICE '✅ Checking appointments for user: %', mickey_user_id;
  RAISE NOTICE '';
  RAISE NOTICE 'All appointments:';
  RAISE NOTICE '================================================================================';
  
  FOR rec IN 
    SELECT 
      customer_name,
      appointment_date,
      appointment_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/Los_Angeles' as pacific_time,
      DATE(appointment_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/Los_Angeles') as pacific_date
    FROM appointments
    WHERE user_id = mickey_user_id
    ORDER BY appointment_date
    LIMIT 20
  LOOP
    RAISE NOTICE '  %: UTC=% | Pacific=% | Date=%', 
      rec.customer_name, 
      rec.appointment_date, 
      rec.pacific_time,
      rec.pacific_date;
  END LOOP;
  
  RAISE NOTICE '';
  RAISE NOTICE 'Appointments for Nov 3, 2025 (Pacific):';
  RAISE NOTICE '================================================================================';
  
  FOR rec IN 
    SELECT 
      customer_name,
      appointment_date,
      appointment_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/Los_Angeles' as pacific_time
    FROM appointments
    WHERE user_id = mickey_user_id
      AND DATE(appointment_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/Los_Angeles') = '2025-11-03'
    ORDER BY appointment_date
  LOOP
    RAISE NOTICE '  %: UTC=% | Pacific=%', 
      rec.customer_name, 
      rec.appointment_date, 
      rec.pacific_time;
  END LOOP;

END $$;

