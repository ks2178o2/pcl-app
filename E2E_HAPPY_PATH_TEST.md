# End-to-End Happy Path Test Plan

## 🎯 Test Scenario

**Goal**: Test the complete user journey from signup to follow-up plan generation with the new center-based hierarchy.

## 📋 Test Steps

### Phase 1: Create Test User ✅

**Action**: Use admin interface to create a new salesperson user

**Prerequisites**:
- Logged in as system admin
- Select existing organization (e.g., "Sales Pro Corp")
- Select center for assignment

**Expected Result**:
- User created in `auth.users`
- Profile created in `profiles` table
- User role added to `user_roles` table
- User assignment added to `user_assignments` table with `center_id`
- User can log in

**Verification Query**:
```sql
-- Check new user
SELECT 
    u.id as user_id,
    u.email,
    p.salesperson_name,
    p.organization_id,
    o.name as org_name,
    ua.center_id,
    c.name as center_name
FROM auth.users u
LEFT JOIN profiles p ON p.user_id = u.id
LEFT JOIN organizations o ON p.organization_id = o.id
LEFT JOIN user_assignments ua ON ua.user_id = u.id
LEFT JOIN centers c ON ua.center_id = c.id
WHERE u.email = 'test-salesperson@example.com';
```

### Phase 2: Patient Creation ✅

**Action**: Log in as new salesperson and create a test patient

**Expected Behavior**:
- Center automatically selected (user has 1 center assignment)
- Patient created with `center_id` populated
- Patient visible in patient list

**Verification Query**:
```sql
-- Check patient was created with center_id
SELECT 
    p.id,
    p.full_name,
    p.center_id,
    c.name as center_name,
    r.name as region_name,
    o.name as org_name
FROM patients p
LEFT JOIN centers c ON p.center_id = c.id
LEFT JOIN regions r ON c.region_id = r.id
LEFT JOIN organizations o ON r.organization_id = o.id
ORDER BY p.created_at DESC
LIMIT 5;
```

### Phase 3: Start Call Recording ✅

**Action**: Start a consultation recording with the new patient

**Expected Behavior**:
- Recording starts successfully
- Call record created in `call_records` table
- `center_id` and `patient_id` populated
- Audio uploads to storage

**Verification Query**:
```sql
-- Check call record
SELECT 
    cr.id,
    cr.customer_name,
    cr.center_id,
    c.name as center_name,
    cr.patient_id,
    cr.recording_complete,
    cr.transcript
FROM call_records cr
LEFT JOIN centers c ON cr.center_id = c.id
ORDER BY cr.created_at DESC
LIMIT 5;
```

### Phase 4: Transcript Analysis ✅

**Action**: Wait for transcription and analysis to complete

**Expected Behavior**:
- Transcript generated
- Call analysis created
- Stored in `call_analysis` table

**Verification Query**:
```sql
-- Check analysis
SELECT 
    id,
    call_record_id,
    summary,
    model_used,
    created_at
FROM call_analysis
ORDER BY created_at DESC
LIMIT 5;
```

### Phase 5: Follow-Up Plan Generation ✅

**Action**: Generate follow-up plan from analysis

**Expected Behavior**:
- Follow-up plan created
- Messages generated
- Stored in `follow_up_plans` and `follow_up_messages` tables

**Verification Query**:
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
GROUP BY fup.id
ORDER BY fup.created_at DESC
LIMIT 5;
```

### Phase 6: RLS Verification ✅

**Action**: Verify center-based access control

**Test Cases**:
1. **User can see their patients**: ✅
   - Query: Select all patients
   - Expected: Only see patients from assigned center

2. **User can see their calls**: ✅
   - Query: Select all call records
   - Expected: Only see calls from their center

3. **Cross-center access blocked**: ✅
   - Create second user in different center
   - Try to see first user's patients
   - Expected: RLS blocks access

**Verification Queries**:
```sql
-- Check RLS is working
-- Run as user with specific center assignment
SET role authenticated;
SET local "user.jwt.claims" = '{"sub":"<USER_ID>"}';

-- Try to select patients (should only see their center's patients)
SELECT COUNT(*) as visible_patients, 
       COUNT(DISTINCT center_id) as centers
FROM patients;

-- Check user's assignments
SELECT center_id, c.name 
FROM user_assignments ua
JOIN centers c ON ua.center_id = c.id
WHERE user_id = auth.uid();

-- Reset
RESET role;
```

## 🔍 Complete Data Flow Verification

```sql
-- Complete journey verification
WITH journey AS (
    SELECT 
        u.email as user_email,
        p.salesperson_name,
        o.name as organization,
        c.name as center,
        pat.full_name as patient_name,
        cr.id as call_id,
        cr.customer_name,
        ca.summary as analysis_summary,
        fup.next_action as followup_action
    FROM auth.users u
    LEFT JOIN profiles p ON p.user_id = u.id
    LEFT JOIN organizations o ON p.organization_id = o.id
    LEFT JOIN user_assignments ua ON ua.user_id = u.id
    LEFT JOIN centers c ON ua.center_id = c.id
    LEFT JOIN patients pat ON pat.center_id = c.id
    LEFT JOIN call_records cr ON cr.patient_id = pat.id
    LEFT JOIN call_analysis ca ON ca.call_record_id = cr.id
    LEFT JOIN follow_up_plans fup ON fup.call_record_id = cr.id
    WHERE u.email = 'test-salesperson@example.com'
)
SELECT * FROM journey;
```

## 📊 Success Criteria

✅ **User Management**:
- User created with center assignment
- Profile, role, and assignment records all present

✅ **Patient Management**:
- Patient created with `center_id` populated
- Patient visible to user due to RLS policies
- No orphan patients

✅ **Call Recording**:
- Call record created with `center_id` and `patient_id`
- Audio uploaded to storage
- Transcription completes successfully

✅ **Analysis**:
- Call analysis generated from transcript
- Analysis stored in database
- All analysis fields populated

✅ **Follow-Up**:
- Follow-up plan generated
- Messages created
- Ready for customer outreach

✅ **Security**:
- RLS policies enforcing center-based access
- Users can only see their center's data
- No cross-tenant data leakage

## 🐛 Common Issues to Watch For

**Issue**: Patient not created with `center_id`
- **Cause**: `activeCenter` not set in center session
- **Fix**: Ensure user has center assignment

**Issue**: User can't see patients
- **Cause**: RLS policy not applied correctly
- **Fix**: Check `user_assignments` table has correct records

**Issue**: Call analysis not generating
- **Cause**: Transcript not complete or LLM error
- **Fix**: Check transcript in `call_records`, verify LLM API keys

**Issue**: Follow-up plan generation fails
- **Cause**: Edge function not deployed or error
- **Fix**: Check Supabase Edge Functions status

## 📝 Test Execution

**Manual Testing**:
1. Use admin UI to create test user
2. Log in as test user
3. Create patient through UI
4. Start recording through UI
5. Wait for analysis and follow-up generation
6. Verify data through SQL queries

**Automated Testing**:
- Create test script to simulate full flow
- Run verification queries
- Check for expected data patterns
- Validate RLS policies working correctly

---

**Ready to Execute**: Use this guide to test the complete workflow!

