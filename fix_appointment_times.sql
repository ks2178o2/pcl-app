-- Fix appointment times that were stored incorrectly
-- This script updates appointments to be stored correctly in UTC based on their intended Pacific time

DO $$
DECLARE
  mickey_user_id UUID;
  updated_count INTEGER;
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

  RAISE NOTICE '✅ Fixing appointments for user: %', mickey_user_id;

  -- Update appointments to correct UTC times
  -- The appointments should be at business hours (9 AM - 5 PM Pacific)
  -- But they were stored as if those times were UTC
  -- We need to subtract 8 hours (PST offset) or 7 hours (PDT offset) from the stored time
  
  -- First, let's see what we have
  RAISE NOTICE 'Current appointments (checking first 5):';
  
  -- Update each appointment based on its intended Pacific time
  -- If appointment_date is around 09:00 UTC, it should be 17:00 UTC (9 AM Pacific)
  -- If appointment_date is around 10:15 UTC, it should be 18:15 UTC (10:15 AM Pacific)
  -- etc.
  
  -- For November 2025, Pacific time is PST (UTC-8)
  -- The appointments were stored as if 9 AM Pacific = 9 AM UTC (wrong!)
  -- They should be stored as 9 AM Pacific = 17:00 UTC (5 PM UTC)
  -- So we add 8 hours to convert from incorrectly stored UTC to correct UTC
  
  -- Update appointments that were stored incorrectly
  -- These are appointments where the UTC hour is between 9-17 (should have been 17-01 next day)
  UPDATE appointments
  SET appointment_date = (
    -- Recreate the timestamp correctly using make_timestamptz with Pacific timezone
    make_timestamptz(
      EXTRACT(YEAR FROM appointment_date)::int,
      EXTRACT(MONTH FROM appointment_date)::int,
      EXTRACT(DAY FROM appointment_date)::int,
      EXTRACT(HOUR FROM appointment_date)::int,  -- This hour should be Pacific time
      EXTRACT(MINUTE FROM appointment_date)::int,
      0,
      'America/Los_Angeles'
    )
  )
  WHERE user_id = mickey_user_id
    AND appointment_date >= '2025-11-01 00:00:00+00'
    AND appointment_date < '2025-12-01 00:00:00+00'
    -- Only fix appointments that look like they were stored incorrectly (between 9 AM and 5 PM UTC)
    AND EXTRACT(HOUR FROM appointment_date AT TIME ZONE 'UTC') BETWEEN 9 AND 17;
  
  GET DIAGNOSTICS updated_count = ROW_COUNT;
  RAISE NOTICE '✅ Updated % appointments', updated_count;

  -- Show sample of fixed appointments
  RAISE NOTICE 'Sample of fixed appointments:';
  FOR rec IN 
    SELECT 
      customer_name,
      appointment_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/Los_Angeles' as pacific_time,
      appointment_date as utc_time
    FROM appointments
    WHERE user_id = mickey_user_id
    ORDER BY appointment_date
    LIMIT 5
  LOOP
    RAISE NOTICE '  %: % (UTC: %)', rec.customer_name, rec.pacific_time, rec.utc_time;
  END LOOP;

END $$;

