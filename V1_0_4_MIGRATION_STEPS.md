# v1.0.4 Database Migration - Step by Step

## Quick Start: Run Database Migration

### Step 1: Open Supabase SQL Editor

1. Go to: https://supabase.com/dashboard
2. Select your project (should show your project URL)
3. Click "SQL Editor" in left sidebar

### Step 2: Load the Migration File

1. In this project, open: `V1_0_4_AUTH_DATABASE_SCHEMA.sql`
2. Copy ALL contents (Ctrl+A, then Ctrl+C / Cmd+A, then Cmd+C)
3. Paste into Supabase SQL Editor

### Step 3: Execute Migration

1. Click "Run" or press Ctrl+Enter / Cmd+Enter
2. Wait for execution to complete (should show "Success" message)
3. You should see messages indicating tables, indexes, policies created

### Step 4: Verify Migration Success

Run this verification query in SQL Editor:

```sql
-- Check new tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('user_invitations', 'login_audit', 'user_devices')
ORDER BY table_name;

-- Should return 3 rows:
-- user_devices
-- user_invitations  
-- login_audit

-- Check profiles table has new columns
SELECT column_name, data_type
FROM information_schema.columns 
WHERE table_name = 'profiles' 
AND column_name IN (
    'two_factor_enabled',
    'two_factor_secret',
    'verified_devices',
    'last_login_ip',
    'last_login_at'
)
ORDER BY column_name;

-- Should return 5 rows with these columns
```

### Step 5: Verify RLS Policies

```sql
-- Check RLS is enabled on new tables
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('user_invitations', 'login_audit', 'user_devices');

-- All should show rowsecurity = true

-- Check policies exist
SELECT tablename, policyname, permissive, roles, cmd 
FROM pg_policies 
WHERE tablename IN ('user_invitations', 'login_audit', 'user_devices')
ORDER BY tablename, policyname;

-- Should show multiple policies per table
```

### Step 6: Report Back

After running the migration, tell me:
1. ✅ Did it execute successfully?
2. ✅ Any errors in the output?
3. ✅ Do the verification queries return expected results?

Then I'll run the integration tests to verify everything works!

---

## Troubleshooting

### Error: "relation already exists"
- Some tables might already exist from previous runs
- The migration uses `CREATE TABLE IF NOT EXISTS` so this is usually fine
- Check if tables have the correct structure

### Error: "permission denied"
- You need admin/service role access
- Make sure you're using the right Supabase credentials

### Error: "syntax error"
- Make sure you copied the entire file
- Don't add extra characters or comments

---

## Next Steps After Migration

Once migration succeeds:
1. I'll run integration tests ✅
2. Fix any discovered issues
3. Implement email notifications
4. Complete JWT authentication
5. Final QA and deployment

**Estimated time to full completion after migration: 20-25 hours**

