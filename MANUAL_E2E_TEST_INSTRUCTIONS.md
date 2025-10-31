# Manual End-to-End Test Instructions

## 🎯 Objective

Test the complete workflow from new user signup → patient creation → call recording → analysis → follow-up plan with the new center-based hierarchy.

## ✅ Pre-Flight Checks

Before starting, verify:
1. ✅ Database migration complete
2. ✅ RLS policies deployed (4 policies active)
3. ✅ Application code deployed
4. ✅ Supabase Edge Functions running

Run this first:
```sql
-- Verify system is ready
SELECT COUNT(*) as organization_count FROM organizations;
SELECT COUNT(*) as center_count FROM centers;
SELECT COUNT(*) as policy_count FROM pg_policies WHERE tablename = 'patients';

-- Should see: 5 orgs, 3 centers, 4 policies
```

## 🚀 Test Execution

### Step 1: Create Test User (Admin Interface)

**Location**: Admin → User Management

**Actions**:
1. Open admin panel
2. Navigate to "User Management" or "Create User"
3. Fill in:
   - **Email**: `test-salesperson@example.com`
   - **Password**: `Test123!@#`
   - **Name**: `Test Salesperson`
   - **Organization**: Select "Sales Pro Corp"
   - **Roles**: Check "salesperson"
   - **Centers**: Check "Sales Center A" (or any center)
4. Click "Create User"
5. ✅ Verify success message

**Verify in Database**:
```sql
SELECT 
    u.email,
    p.salesperson_name,
    ua.center_id,
    c.name as center_name
FROM auth.users u
LEFT JOIN profiles p ON p.user_id = u.id
LEFT JOIN user_assignments ua ON ua.user_id = u.id
LEFT JOIN centers c ON ua.center_id = c.id
WHERE u.email = 'test-salesperson@example.com';
```

**Expected Result**:
- ✅ User exists in `auth.users`
- ✅ Profile exists with `organization_id` set
- ✅ User assignment exists with `center_id` set
- ✅ Center matches selected center from UI

---

### Step 2: Log In as Test User

**Actions**:
1. Log out of admin account
2. Log in with:
   - Email: `test-salesperson@example.com`
   - Password: `Test123!@#`
3. ✅ Verify login successful
4. ✅ Verify you see only "Sales Center A" (or your assigned center)

**Expected Behavior**:
- No center selection modal (1 center assignment)
- Dashboard loads successfully
- No error messages

---

### Step 3: Create Test Patient

**Location**: Main Dashboard → Patient Selection

**Actions**:
1. Click "+ New Patient" or search for patient
2. Fill in patient details:
   - **Name**: "Dr. Sarah Williams"
   - **Email**: "sarah.williams@email.com" (optional)
   - **Phone**: "555-1234" (optional)
3. Click "Create"
4. ✅ Verify success message
5. ✅ Verify patient appears in list

**Verify in Database**:
```sql
SELECT 
    p.id,
    p.full_name,
    p.center_id,
    c.name as center_name,
    p.created_at
FROM patients p
LEFT JOIN centers c ON p.center_id = c.id
WHERE p.full_name = 'Dr. Sarah Williams';
```

**Expected Result**:
- ✅ `center_id` is **NOT NULL**
- ✅ `center_id` matches user's assigned center
- ✅ Patient visible in UI list

---

### Step 4: Start Call Recording

**Location**: Main Dashboard → Professional Recording Tab

**Actions**:
1. Select patient "Dr. Sarah Williams"
2. Verify center is auto-selected
3. Click "Start Recording" or start microphone
4. Record for 10-15 seconds
5. Stop recording
6. ✅ Verify recording saved
7. ✅ Check dashboard for new call record

**Verify in Database**:
```sql
SELECT 
    cr.id,
    cr.customer_name,
    cr.center_id,
    cr.patient_id,
    cr.recording_complete,
    cr.transcript,
    c.name as center_name
FROM call_records cr
LEFT JOIN centers c ON cr.center_id = c.id
WHERE cr.customer_name = 'Dr. Sarah Williams'
ORDER BY cr.created_at DESC
LIMIT 1;
```

**Expected Result**:
- ✅ `center_id` is **NOT NULL** and matches patient's center
- ✅ `patient_id` references the patient we created
- ✅ `recording_complete` is `true`
- ✅ Audio file uploaded to storage

---

### Step 5: Wait for Transcription & Analysis

**Actions**:
1. Wait 30-60 seconds for transcription to complete
2. Refresh page or check call records
3. ✅ Verify transcript appears
4. Click on the call record to view details
5. ✅ Verify analysis is generating or complete

**Verify in Database**:
```sql
-- Check transcription
SELECT 
    cr.id,
    cr.transcript,
    LENGTH(cr.transcript) as transcript_length,
    cr.transcript NOT LIKE '%Transcribing%' as transcription_complete
FROM call_records cr
WHERE cr.customer_name = 'Dr. Sarah Williams'
ORDER BY cr.created_at DESC
LIMIT 1;

-- Check analysis
SELECT 
    ca.id,
    ca.call_record_id,
    ca.summary,
    ca.model_used,
    ca.customer_personality,
    ca.created_at
FROM call_analysis ca
WHERE ca.call_record_id IN (
    SELECT id FROM call_records 
    WHERE customer_name = 'Dr. Sarah Williams'
    ORDER BY created_at DESC LIMIT 1
);
```

**Expected Result**:
- ✅ Transcript is not blank or "Transcribing..."
- ✅ Analysis exists with summary and insights
- ✅ Personality analysis populated

---

### Step 6: Generate Follow-Up Plan

**Location**: Call Analysis Page → Follow-Up Plan Section

**Actions**:
1. Navigate to Call Analysis page for the new call
2. Scroll to "Follow-Up Plan" section
3. Click "Generate Follow-Up Plan"
4. Wait for generation to complete
5. ✅ Verify plan appears with recommendations

**Verify in Database**:
```sql
-- Check follow-up plan
SELECT 
    fup.id,
    fup.call_record_id,
    fup.strategy_type,
    fup.recommended_timing,
    fup.priority_score,
    fup.customer_urgency,
    fup.next_action,
    COUNT(fum.id) as message_count
FROM follow_up_plans fup
LEFT JOIN follow_up_messages fum ON fum.follow_up_plan_id = fup.id
WHERE fup.call_record_id IN (
    SELECT id FROM call_records 
    WHERE customer_name = 'Dr. Sarah Williams'
    ORDER BY created_at DESC LIMIT 1
)
GROUP BY fup.id
ORDER BY fup.created_at DESC
LIMIT 1;

-- Check messages
SELECT 
    fum.id,
    fum.channel_type,
    fum.message_content,
    fum.priority
FROM follow_up_messages fum
JOIN follow_up_plans fup ON fum.follow_up_plan_id = fup.id
WHERE fup.call_record_id IN (
    SELECT id FROM call_records 
    WHERE customer_name = 'Dr. Sarah Williams'
    ORDER BY created_at DESC LIMIT 1
)
ORDER BY fum.priority DESC;
```

**Expected Result**:
- ✅ Follow-up plan exists
- ✅ Plan has strategy type and timing
- ✅ Multiple messages generated (email, SMS)
- ✅ Messages are personalized and relevant

---

### Step 7: Verify RLS Security

**Actions**:
1. Create **second test user** in **different center**
2. Log in as second user
3. Try to search for "Dr. Sarah Williams"
4. ✅ Verify patient is **NOT visible**

**SQL Verification**:
```sql
-- Check what first test user can see
-- (Run this in Supabase SQL Editor AS the test user)
SET local "request.jwt.claims" = '{"sub":"<FIRST_USER_ID>"}';
SELECT COUNT(*) as visible_patients, COUNT(DISTINCT center_id) as centers FROM patients;
-- Should see: 1 patient (Dr. Sarah Williams)

-- Check what second user can see  
SET local "request.jwt.claims" = '{"sub":"<SECOND_USER_ID>"}';
SELECT COUNT(*) as visible_patients, COUNT(DISTINCT center_id) as centers FROM patients;
-- Should see: 0 patients (different center)
```

**Expected Result**:
- ✅ First user sees their center's patients only
- ✅ Second user sees different patients or none
- ✅ No cross-center data leakage

---

## 📊 Complete Journey Verification

Run this to see the entire data flow:

```sql
-- Complete journey check
SELECT 
    'User' as step,
    u.email as data_point,
    ua.center_id as center_id,
    c.name as center_name
FROM auth.users u
LEFT JOIN user_assignments ua ON ua.user_id = u.id
LEFT JOIN centers c ON ua.center_id = c.id
WHERE u.email = 'test-salesperson@example.com'

UNION ALL

SELECT 
    'Patient' as step,
    p.full_name as data_point,
    p.center_id as center_id,
    c.name as center_name
FROM patients p
LEFT JOIN centers c ON p.center_id = c.id
WHERE p.full_name = 'Dr. Sarah Williams'

UNION ALL

SELECT 
    'Call Record' as step,
    cr.customer_name as data_point,
    cr.center_id as center_id,
    c.name as center_name
FROM call_records cr
LEFT JOIN centers c ON cr.center_id = c.id
WHERE cr.customer_name = 'Dr. Sarah Williams'
ORDER BY step, data_point;
```

## ✅ Success Checklist

Mark off as you complete:

**Setup**:
- [ ] Database migration complete
- [ ] RLS policies deployed (4 active)
- [ ] Application code updated
- [ ] Edge functions running

**User Creation**:
- [ ] Test user created via admin UI
- [ ] Profile created correctly
- [ ] Center assignment created
- [ ] User can log in

**Patient Management**:
- [ ] Patient created successfully
- [ ] `center_id` populated automatically
- [ ] Patient visible in UI
- [ ] RLS filtering working

**Call Recording**:
- [ ] Recording starts successfully
- [ ] Call record created with all IDs
- [ ] Audio uploaded to storage
- [ ] Transcript generated

**Analysis**:
- [ ] Analysis generated from transcript
- [ ] All analysis fields populated
- [ ] Insights are relevant
- [ ] Stored in database correctly

**Follow-Up**:
- [ ] Plan generated successfully
- [ ] Messages created
- [ ] Recommendations personalized
- [ ] Ready for outreach

**Security**:
- [ ] RLS enforcing center isolation
- [ ] Cross-center access blocked
- [ ] No data leakage
- [ ] Policies working correctly

---

## 🐛 Troubleshooting

### Issue: Patient not creating

**Check**:
```sql
-- Verify center assignment exists
SELECT * FROM user_assignments WHERE user_id IN (
    SELECT id FROM auth.users WHERE email = 'test-salesperson@example.com'
);
```

### Issue: Can't see patients after creation

**Check**:
```sql
-- Verify RLS policies
SELECT policyname FROM pg_policies WHERE tablename = 'patients';

-- Should see 4 policies
```

### Issue: Call analysis not generating

**Check**:
```sql
-- Check if transcript exists
SELECT id, transcript, LENGTH(transcript) 
FROM call_records 
WHERE customer_name = 'Dr. Sarah Williams'
ORDER BY created_at DESC LIMIT 1;

-- If transcript is complete, check edge function logs in Supabase
```

---

**Ready to test!** Follow these steps in order and verify each phase before moving to the next.

