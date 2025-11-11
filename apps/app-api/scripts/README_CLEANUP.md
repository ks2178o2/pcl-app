# Bulk Import Cleanup Scripts

This directory contains scripts to clean up bulk import test data from Supabase.

## Option 1: Python Script (Recommended)

The Python script will:
- Delete all bulk import jobs from the database
- Delete all associated files, call records, objections, and overcome details
- List and optionally delete storage buckets created for bulk imports

### Usage:

```bash
cd /Users/krupasrinivas/pcl-product/apps/app-api
source venv/bin/activate
python scripts/cleanup_bulk_import.py
```

The script will:
1. Show you what will be deleted
2. Ask for confirmation before deleting storage buckets
3. Clean up everything in the correct order (respecting foreign key constraints)

## Option 2: SQL Script

Run the SQL script directly in Supabase SQL Editor:

1. Go to your Supabase Dashboard
2. Navigate to SQL Editor
3. Copy and paste the contents of `migrations/cleanup_bulk_import.sql`
4. Run it

**Note:** SQL script only cleans database tables. Storage buckets must be deleted manually or using the Python script.

## What Gets Deleted

### Database Tables:
- `bulk_import_jobs` - All bulk import job records
- `bulk_import_files` - All file records from bulk imports
- `call_records` - Call records created from bulk imports (only those with `bulk_import_job_id`)
- `call_objections` - Objections detected for bulk import calls
- `objection_overcome_details` - Objection overcome analysis for bulk import calls

### Storage Buckets:
- All buckets starting with `customer-` (created for bulk imports)
- All buckets ending with `-analysis` (analysis sub-buckets)

## Important Notes

⚠️ **This will delete ALL bulk import data permanently!**

- Make sure you want to delete everything before running
- The Python script asks for confirmation before deleting buckets
- Database deletions happen immediately (no confirmation)
- Storage bucket deletion is optional and requires confirmation

## Troubleshooting

If you get errors about missing API keys:
- Make sure `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_SERVICE_KEY` is set in your environment
- The script needs the service role key to delete storage buckets

If storage bucket deletion fails:
- You can manually delete buckets in the Supabase Dashboard
- Go to Storage → Buckets and delete buckets starting with `customer-` or ending with `-analysis`

