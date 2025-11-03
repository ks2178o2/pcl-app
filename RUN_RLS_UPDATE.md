# How to Run RLS Policy Update

## Quick Instructions

1. **Open Supabase Dashboard**
   - Go to your Supabase project dashboard
   - Navigate to SQL Editor

2. **Copy the SQL Script**
   - Open `UPDATE_RLS_POLICIES_FOR_CENTER_HIERARCHY.sql`
   - Copy the entire contents

3. **Paste and Execute**
   - Paste into Supabase SQL Editor
   - Click "Run" or press Cmd/Ctrl + Enter

4. **Verify Success**
   - Check for any errors in the output
   - Run the verification query at the bottom of the script

## What This Script Does

✅ Drops old organization-based policies (8 policies)
✅ Creates new center-based policies (4 policies)
✅ Adds performance index on `center_id`
✅ Verifies policies were created correctly

## Expected Output

You should see:
- ✅ Success messages from RAISE NOTICE
- ✅ Policy verification query results showing 4 new policies
- ✅ No errors

## Rollback (If Needed)

If you need to revert, the old policies were organization-based. You can recreate them from:
- `create_patients_table.sql` or
- `COMPLETE_DATABASE_SETUP.sql`

## Verification Query

After running, verify with:
```sql
SELECT policyname, cmd 
FROM pg_policies 
WHERE tablename = 'patients' 
ORDER BY policyname;
```

Expected policies:
- Users can view patients from assigned centers
- Users can insert patients to assigned centers
- Users can update patients from assigned centers
- Users can delete patients from assigned centers

