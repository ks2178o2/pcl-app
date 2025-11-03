-- Create comprehensive appointments for Mickey Mouse with meeting prep notes and business hours
-- Run this in Supabase SQL Editor

DO $$
DECLARE
  mickey_user_id UUID;
  mickey_org_id UUID;
  appointment_date DATE;
BEGIN
  -- Get Mickey's user_id
  SELECT id INTO mickey_user_id
  FROM auth.users
  WHERE email = 'mickey.mouse@disney.com'
  LIMIT 1;

  -- Get Mickey's organization_id from profile
  SELECT organization_id INTO mickey_org_id
  FROM profiles
  WHERE user_id = mickey_user_id
  LIMIT 1;

  IF mickey_user_id IS NULL THEN
    RAISE NOTICE '❌ Mickey Mouse user not found. Please create the user first.';
    RETURN;
  END IF;

  IF mickey_org_id IS NULL THEN
    RAISE NOTICE '❌ Mickey Mouse profile not found or missing organization_id.';
    RETURN;
  END IF;

  RAISE NOTICE '✅ Using Mickey user_id: % and org_id: %', mickey_user_id, mickey_org_id;

  -- Clear existing appointments for Mickey
  DELETE FROM appointments WHERE user_id = mickey_user_id;

  -- Create appointments for the next 9 days with business hours (9 AM - 5 PM)
  -- Using America/Los_Angeles timezone (adjust to your business timezone if needed)
  appointment_date := CURRENT_DATE; -- Today

  -- Helper function to create timezone-aware timestamps (9 AM - 5 PM business hours)
  -- Usage: biz_time(days_offset, hour, minute)
  -- Example: biz_time(0, 9, 0) = today at 9:00 AM in business timezone
  
  INSERT INTO appointments (
    user_id, 
    organization_id, 
    customer_name, 
    customer_email, 
    customer_phone,
    appointment_date, 
    duration_minutes,
    type,
    status,
    notes
  )
  VALUES
    -- Day 1 (Today) - 5 meetings
    -- All appointments are 60-90 minutes, business hours 9 AM - 5 PM, properly spaced
    (mickey_user_id, mickey_org_id, 'Donald Duck', 'donald.duck@disney.com', '(555) 111-2222', make_timestamptz(EXTRACT(YEAR FROM appointment_date)::int, EXTRACT(MONTH FROM appointment_date)::int, EXTRACT(DAY FROM appointment_date)::int, 9, 0, 0, 'America/Los_Angeles'), 75, 'Initial Consult', 'Confirmed', 'Patient interested in teeth whitening. Daughter getting married in 6 months. Budget conscious.'),
    (mickey_user_id, mickey_org_id, 'Goofy', 'goofy@disney.com', '(555) 222-3333', make_timestamptz(EXTRACT(YEAR FROM appointment_date)::int, EXTRACT(MONTH FROM appointment_date)::int, EXTRACT(DAY FROM appointment_date)::int, 10, 15, 0, 'America/Los_Angeles'), 60, 'Follow-up', 'Scheduled', 'Previous consult went well. Discussing financing options. Show promotional materials.'),
    (mickey_user_id, mickey_org_id, 'Minnie Mouse', 'minnie.mouse@disney.com', '(555) 333-4444', make_timestamptz(EXTRACT(YEAR FROM appointment_date)::int, EXTRACT(MONTH FROM appointment_date)::int, EXTRACT(DAY FROM appointment_date)::int, 11, 15, 0, 'America/Los_Angeles'), 90, 'Consultation', 'Pending', 'Referred by Donald Duck. High priority lead. Wants veneers.'),
    (mickey_user_id, mickey_org_id, 'Pluto', 'pluto@disney.com', '(555) 444-5555', make_timestamptz(EXTRACT(YEAR FROM appointment_date)::int, EXTRACT(MONTH FROM appointment_date)::int, EXTRACT(DAY FROM appointment_date)::int, 13, 15, 0, 'America/Los_Angeles'), 75, 'Initial Consult', 'Confirmed', 'Dental anxiety concerns. May need sedation options.'),
    (mickey_user_id, mickey_org_id, 'Daisy Duck', 'daisy.duck@disney.com', '(555) 555-6666', make_timestamptz(EXTRACT(YEAR FROM appointment_date)::int, EXTRACT(MONTH FROM appointment_date)::int, EXTRACT(DAY FROM appointment_date)::int, 14, 30, 0, 'America/Los_Angeles'), 60, 'Follow-up', 'Scheduled', 'Returning for second opinion. Compare packages.'),

    -- Day 2 (Tomorrow) - 4 meetings
    (mickey_user_id, mickey_org_id, 'Chip', 'chip@disney.com', '(555) 666-7777', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '1 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '1 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '1 days'))::int, 9, 0, 0, 'America/Los_Angeles'), 75, 'Initial Consult', 'Confirmed', 'Brother of Dale. Want matching treatment. Family package interest.'),
    (mickey_user_id, mickey_org_id, 'Dale', 'dale@disney.com', '(555) 777-8888', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '1 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '1 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '1 days'))::int, 10, 15, 0, 'America/Los_Angeles'), 60, 'Initial Consult', 'Pending', 'Chip will attend too. Coordinate scheduling.'),
    (mickey_user_id, mickey_org_id, 'Scrooge McDuck', 'scrooge.mcduck@disney.com', '(555) 888-9999', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '1 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '1 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '1 days'))::int, 13, 0, 0, 'America/Los_Angeles'), 90, 'Consultation', 'Scheduled', 'VIP client. Cost is not an issue. Focus on premium options.'),
    (mickey_user_id, mickey_org_id, 'Pete', 'pete@disney.com', '(555) 999-0000', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '1 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '1 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '1 days'))::int, 14, 30, 0, 'America/Los_Angeles'), 60, 'Follow-up', 'Confirmed', 'Follow up on previous quote. Timeline sensitive.'),

    -- Day 3 - 3 meetings
    (mickey_user_id, mickey_org_id, 'Clarabelle Cow', 'clarabelle.cow@disney.com', '(555) 000-1111', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '2 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '2 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '2 days'))::int, 9, 0, 0, 'America/Los_Angeles'), 90, 'Initial Consult', 'Confirmed', 'Looking for smile makeover. Professional presentation important.'),
    (mickey_user_id, mickey_org_id, 'Horace Horsecollar', 'horace@disney.com', '(555) 111-2222', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '2 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '2 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '2 days'))::int, 11, 0, 0, 'America/Los_Angeles'), 75, 'Follow-up', 'Pending', 'Discussion needed on treatment timeline. Work scheduling concerns.'),
    (mickey_user_id, mickey_org_id, 'Fifi', 'fifi@disney.com', '(555) 222-3333', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '2 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '2 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '2 days'))::int, 13, 15, 0, 'America/Los_Angeles'), 90, 'Consultation', 'Scheduled', 'Cosmetic dentistry focus. Show before/after photos.'),

    -- Day 4 - 4 meetings
    (mickey_user_id, mickey_org_id, 'Ludwig Von Drake', 'ludwig@disney.com', '(555) 333-4444', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '3 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '3 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '3 days'))::int, 9, 0, 0, 'America/Los_Angeles'), 75, 'Initial Consult', 'Confirmed', 'Research-oriented patient. Bring detailed technical literature.'),
    (mickey_user_id, mickey_org_id, 'Lampwick', 'lampwick@disney.com', '(555) 444-5555', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '3 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '3 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '3 days'))::int, 10, 15, 0, 'America/Los_Angeles'), 60, 'Consultation', 'Pending', 'Young adult. Financing will be key selling point.'),
    (mickey_user_id, mickey_org_id, 'Gideon', 'gideon@disney.com', '(555) 555-6666', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '3 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '3 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '3 days'))::int, 13, 0, 0, 'America/Los_Angeles'), 75, 'Follow-up', 'Scheduled', 'Second visit. Address concerns from initial consult.'),
    (mickey_user_id, mickey_org_id, 'J. Worthington Foulfellow', 'worthington@disney.com', '(555) 666-7777', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '3 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '3 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '3 days'))::int, 14, 15, 0, 'America/Los_Angeles'), 60, 'Initial Consult', 'Confirmed', 'Business professional. Time-sensitive decision maker.'),

    -- Day 5 - 5 meetings
    (mickey_user_id, mickey_org_id, 'Stromboli', 'stromboli@disney.com', '(555) 777-8888', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '4 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '4 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '4 days'))::int, 9, 0, 0, 'America/Los_Angeles'), 75, 'Initial Consult', 'Scheduled', 'High anxiety patient. Emphasize pain management options.'),
    (mickey_user_id, mickey_org_id, 'Monstro', 'monstro@disney.com', '(555) 888-9999', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '4 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '4 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '4 days'))::int, 10, 15, 0, 'America/Los_Angeles'), 60, 'Follow-up', 'Pending', 'Large treatment plan. Installment options required.'),
    (mickey_user_id, mickey_org_id, 'Figaro', 'figaro@disney.com', '(555) 999-0000', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '4 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '4 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '4 days'))::int, 11, 15, 0, 'America/Los_Angeles'), 75, 'Initial Consult', 'Confirmed', 'Quick decision maker. Have treatment plan ready.'),
    (mickey_user_id, mickey_org_id, 'Jiminy Cricket', 'jiminy@disney.com', '(555) 000-1111', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '4 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '4 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '4 days'))::int, 13, 0, 0, 'America/Los_Angeles'), 90, 'Consultation', 'Scheduled', 'Ethical concerns. Transparency is key.'),
    (mickey_user_id, mickey_org_id, 'Pinocchio', 'pinocchio@disney.com', '(555) 111-2222', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '4 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '4 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '4 days'))::int, 14, 30, 0, 'America/Los_Angeles'), 60, 'Follow-up', 'Confirmed', 'Father attending. Family consultation.'),

    -- Day 6 - 3 meetings
    (mickey_user_id, mickey_org_id, 'Geppetto', 'geppetto@disney.com', '(555) 222-3333', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '5 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '5 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '5 days'))::int, 9, 0, 0, 'America/Los_Angeles'), 90, 'Initial Consult', 'Confirmed', 'Age-related dental needs. Comfort focused.'),
    (mickey_user_id, mickey_org_id, 'Fairy Godmother', 'fairy.godmother@disney.com', '(555) 333-4444', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '5 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '5 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '5 days'))::int, 11, 0, 0, 'America/Los_Angeles'), 75, 'Consultation', 'Pending', 'VIP referral. Premium treatment options.'),
    (mickey_user_id, mickey_org_id, 'Mowgli', 'mowgli@disney.com', '(555) 444-5555', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '5 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '5 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '5 days'))::int, 13, 15, 0, 'America/Los_Angeles'), 75, 'Follow-up', 'Scheduled', 'Returning for final decision. Address last concerns.'),

    -- Day 7 - 4 meetings
    (mickey_user_id, mickey_org_id, 'Baloo', 'baloo@disney.com', '(555) 555-6666', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '6 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '6 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '6 days'))::int, 9, 0, 0, 'America/Los_Angeles'), 75, 'Initial Consult', 'Confirmed', 'Relaxed personality. Build rapport, no pressure.'),
    (mickey_user_id, mickey_org_id, 'Bagheera', 'bagheera@disney.com', '(555) 666-7777', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '6 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '6 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '6 days'))::int, 10, 15, 0, 'America/Los_Angeles'), 60, 'Follow-up', 'Scheduled', 'Professional evaluation. Compare options.'),
    (mickey_user_id, mickey_org_id, 'King Louie', 'king.louie@disney.com', '(555) 777-8888', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '6 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '6 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '6 days'))::int, 13, 0, 0, 'America/Los_Angeles'), 75, 'Consultation', 'Pending', 'Leadership role. Prestige matters.'),
    (mickey_user_id, mickey_org_id, 'Shere Khan', 'shere.khan@disney.com', '(555) 888-9999', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '6 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '6 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '6 days'))::int, 14, 15, 0, 'America/Los_Angeles'), 60, 'Initial Consult', 'Confirmed', 'Quick treatment preferred. Schedule flexibility needed.'),

    -- Day 8 - 5 meetings (including 2 no-shows)
    (mickey_user_id, mickey_org_id, 'Wendy Darling', 'wendy.darling@disney.com', '(555) 000-1111', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '7 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '7 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '7 days'))::int, 9, 0, 0, 'America/Los_Angeles'), 75, 'Initial Consult', 'Confirmed', 'Family consultation for multiple children.'),
    (mickey_user_id, mickey_org_id, 'Captain Hook', 'captain.hook@disney.com', '(555) 111-2222', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '7 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '7 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '7 days'))::int, 10, 15, 0, 'America/Los_Angeles'), 60, 'Follow-up', 'Scheduled', 'VIP treatment required. Showcase premium options.'),
    (mickey_user_id, mickey_org_id, 'Peter Pan', 'peter.pan@disney.com', '(555) 222-3333', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '7 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '7 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '7 days'))::int, 11, 15, 0, 'America/Los_Angeles'), 90, 'Consultation', 'No Show', 'Patient did not attend. Follow up via phone.'),
    (mickey_user_id, mickey_org_id, 'Tinker Bell', 'tinkerbell@disney.com', '(555) 333-4444', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '7 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '7 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '7 days'))::int, 13, 45, 0, 'America/Los_Angeles'), 60, 'Initial Consult', 'Pending', 'Cosmetic focused. Show transformation examples.'),
    (mickey_user_id, mickey_org_id, 'Lost Boy', 'lost.boy@disney.com', '(555) 444-5555', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '7 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '7 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '7 days'))::int, 14, 45, 0, 'America/Los_Angeles'), 60, 'Follow-up', 'No Show', 'No show. Check if still interested.'),

    -- Day 9 - 4 meetings (including 1 no-show)
    (mickey_user_id, mickey_org_id, 'Alice', 'alice@disney.com', '(555) 555-6666', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '8 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '8 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '8 days'))::int, 9, 0, 0, 'America/Los_Angeles'), 90, 'Initial Consult', 'Confirmed', 'Young professional. Busy schedule. Be efficient.'),
    (mickey_user_id, mickey_org_id, 'Mad Hatter', 'mad.hatter@disney.com', '(555) 666-7777', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '8 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '8 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '8 days'))::int, 10, 30, 0, 'America/Los_Angeles'), 75, 'Consultation', 'Pending', 'Unique concerns. Flexible approach needed.'),
    (mickey_user_id, mickey_org_id, 'Cheshire Cat', 'cheshire.cat@disney.com', '(555) 777-8888', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '8 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '8 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '8 days'))::int, 12, 45, 0, 'America/Los_Angeles'), 75, 'Follow-up', 'No Show', 'No show. Contact for rescheduling.'),
    (mickey_user_id, mickey_org_id, 'Queen of Hearts', 'queen.hearts@disney.com', '(555) 888-9999', make_timestamptz(EXTRACT(YEAR FROM (appointment_date + INTERVAL '8 days'))::int, EXTRACT(MONTH FROM (appointment_date + INTERVAL '8 days'))::int, EXTRACT(DAY FROM (appointment_date + INTERVAL '8 days'))::int, 14, 0, 0, 'America/Los_Angeles'), 60, 'Initial Consult', 'Scheduled', 'High expectations. Prepare detailed presentation.');

  RAISE NOTICE '✅ Created appointments for Mickey Mouse with business hours (9 AM - 5 PM)!';
END $$;

-- Create call records and analyses for follow-up patients to populate motivation/objections/history
DO $$
DECLARE
  mickey_user_id UUID;
  mickey_org_id UUID;
BEGIN
  -- Get Mickey's user_id
  SELECT id INTO mickey_user_id
  FROM auth.users
  WHERE email = 'mickey.mouse@disney.com'
  LIMIT 1;

  SELECT organization_id INTO mickey_org_id
  FROM profiles
  WHERE user_id = mickey_user_id
  LIMIT 1;

  -- Create call records for patients who have Follow-up appointments
  INSERT INTO call_records (
    user_id,
    organization_id,
    customer_name,
    start_time,
    end_time,
    recording_complete,
    transcript
  )
  SELECT 
    mickey_user_id,
    mickey_org_id,
    customer_name,
    appointment_date - INTERVAL '7 days', -- Call was 1 week before appointment
    appointment_date - INTERVAL '7 days' + INTERVAL '30 minutes',
    true,
    'Initial consultation call with ' || customer_name || '. Discussed treatment options and concerns.'
  FROM appointments
  WHERE user_id = mickey_user_id 
    AND type = 'Follow-up'
    AND NOT EXISTS (
      SELECT 1 FROM call_records 
      WHERE user_id = mickey_user_id AND customer_name = appointments.customer_name
    );

  -- Create call analyses for the follow-up patients with realistic motivations and objections
  INSERT INTO call_analyses (
    call_record_id,
    user_id,
    analysis_type,
    provider,
    analysis_data
  )
  SELECT 
    cr.id,
    mickey_user_id,
    'standard',
    'openai',
    jsonb_build_object(
      'customerPersonality', jsonb_build_object(
        'motivationCategory', 
        CASE 
          WHEN a.customer_name = 'Goofy' THEN 'health-driven'
          WHEN a.customer_name = 'Daisy Duck' THEN 'cost-conscious'
          WHEN a.customer_name = 'Horace Horsecollar' THEN 'schedule-flexible'
          WHEN a.customer_name = 'Gideon' THEN 'quality-focused'
          WHEN a.customer_name = 'Monstro' THEN 'price-sensitive'
          WHEN a.customer_name = 'Pinocchio' THEN 'family-oriented'
          WHEN a.customer_name = 'Bagheera' THEN 'quality-focused'
          WHEN a.customer_name = 'Captain Hook' THEN 'premium-oriented'
          WHEN a.customer_name = 'Lost Boy' THEN 'budget-conscious'
          ELSE 'service-quality'
        END,
        'communicationStyle', jsonb_build_object(
          'decisionSpeed', 'moderate',
          'informationDepth', 'detailed',
          'preferredTone', 'friendly'
        )
      ),
      'objections', 
      jsonb_build_array(
        jsonb_build_object(
          'text',
          CASE 
            WHEN a.customer_name = 'Goofy' THEN 'Concerned about financing options and monthly payments'
            WHEN a.customer_name = 'Daisy Duck' THEN 'Wants to compare prices across providers'
            WHEN a.customer_name = 'Horace Horsecollar' THEN 'Unsure about treatment timeline compatibility with work'
            WHEN a.customer_name = 'Gideon' THEN 'Questioning long-term durability of treatment'
            WHEN a.customer_name = 'Monstro' THEN 'Price is main concern, needs installment plan'
            WHEN a.customer_name = 'Pinocchio' THEN 'Needs to discuss with family before decision'
            WHEN a.customer_name = 'Bagheera' THEN 'Comparing multiple treatment options'
            WHEN a.customer_name = 'Captain Hook' THEN 'Concerned about treatment duration'
            WHEN a.customer_name = 'Lost Boy' THEN 'Budget constraints, looking for discounts'
            ELSE 'General concerns about treatment process'
          END,
          'type',
          CASE 
            WHEN a.customer_name IN ('Goofy', 'Monstro', 'Lost Boy') THEN 'cost'
            WHEN a.customer_name = 'Horace Horsecollar' THEN 'timing'
            WHEN a.customer_name = 'Gideon' THEN 'provider-trust'
            WHEN a.customer_name = 'Pinocchio' THEN 'decision-support'
            ELSE 'general'
          END
        )
      )
    )
  FROM call_records cr
  INNER JOIN appointments a ON cr.customer_name = a.customer_name
  WHERE cr.user_id = mickey_user_id
    AND a.user_id = mickey_user_id
    AND a.type = 'Follow-up'
    AND NOT EXISTS (
      SELECT 1 FROM call_analyses WHERE call_record_id = cr.id
    );

  RAISE NOTICE '✅ Created call records and analyses for follow-up patients!';
END $$;

-- Show success message
SELECT 
  'Mickey Mouse appointments created successfully! 🎉' as status,
  COUNT(*) as total_appointments,
  COUNT(DISTINCT DATE(appointment_date)) as days_with_appointments
FROM appointments
WHERE user_id = (SELECT id FROM auth.users WHERE email = 'mickey.mouse@disney.com');
