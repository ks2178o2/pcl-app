# Quick Start Test Guide

## 🚀 Fastest Way to Test Everything

### Prerequisites
- ✅ RLS policies deployed
- ✅ You're logged in as admin
- ✅ Your database has at least 1 organization and 1 center

### Quick 5-Step Test

**Step 1**: Check what's available
```sql
-- Run this first
SELECT * FROM CHECK_EXISTING_DATA.sql;
```

**Step 2**: Use Admin UI to create test user
- Email: `e2e-test@example.com`
- Password: `Test123!@#`
- Name: `E2E Test User`
- Org: Pick any organization
- Role: `salesperson`
- Center: Pick any center

**Step 3**: Log in as test user
- Verify you see only your assigned center
- No center selection popup

**Step 4**: Create a patient
- Name: "Test Patient E2E"
- Verify it auto-assigns to your center

**Step 5**: Start a recording
- Select the test patient
- Record for 10 seconds
- Stop and verify it saved

### Verification Query

Run this to see everything connected:
```sql
SELECT 
    u.email,
    p.salesperson_name,
    c.name as center_assigned,
    pat.full_name as patient_name,
    pat.center_id = ua.center_id as center_match,
    cr.customer_name,
    cr.center_id = ua.center_id as call_center_match
FROM auth.users u
LEFT JOIN profiles p ON p.user_id = u.id
LEFT JOIN user_assignments ua ON ua.user_id = u.id
LEFT JOIN centers c ON ua.center_id = c.id
LEFT JOIN patients pat ON pat.center_id = c.id
LEFT JOIN call_records cr ON cr.patient_id = pat.id
WHERE u.email = 'e2e-test@example.com';
```

### ✅ Success Indicators

- `center_match` = true (patient in user's center)
- `call_center_match` = true (call in user's center)
- All JOINs return data (no NULLs in the chain)

**If all checks pass, your center hierarchy is working perfectly! 🎉**

