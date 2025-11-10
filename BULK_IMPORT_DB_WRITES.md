# Bulk Import Pipeline - Database Writes & Timing Analysis

## Database Write Locations

### 1. **Job Creation** (`bulk_import_api.py`)
- **Table**: `bulk_import_jobs`
- **When**: Immediately when user starts import
- **Fields**: `id`, `user_id`, `customer_name`, `source_url`, `storage_bucket_name`, `status` (default: 'pending')

### 2. **File Discovery** (`bulk_import_service.py` line ~60-90)
- **Table**: `bulk_import_files`
- **When**: After discovering audio files from source URL
- **Fields**: `job_id`, `file_name`, `original_url`, `status` (default: 'pending')

### 3. **File Upload** (`bulk_import_service.py` line ~810-832)
- **Table**: `bulk_import_files` (UPDATE)
- **When**: After successful upload to Supabase storage
- **Fields Updated**: `storage_path`, `file_size`, `file_format`, `status` → 'transcribing'
- **Table**: `call_records` (INSERT)
- **When**: Immediately after upload
- **Fields**: `id`, `user_id`, `customer_name`, `audio_file_url`, `transcript` (initial: 'Transcribing audio...')
- **Table**: `bulk_import_files` (UPDATE)
- **When**: After call_record creation
- **Fields Updated**: `call_record_id`, `status` → 'analyzing'

### 4. **Transcription** (`transcribe_api.py` line ~333)
- **Table**: `call_records` (UPDATE)
- **When**: When transcription service completes (ASYNCHRONOUS - background thread)
- **Fields Updated**: `transcript` (final text), `transcription_provider`, `diarization_segments`, `diarization_confidence`

### 5. **Call Categorization** (`call_analysis_service.py` line ~61-65)
- **Table**: `call_records` (UPDATE)
- **When**: After transcript is available
- **Fields Updated**: `call_category`, `categorization_confidence`, `categorization_notes`
- **Table**: `bulk_import_files` (UPDATE)
- **When**: After categorization completes
- **Fields Updated**: `status` → 'categorized'

### 6. **Objection Detection** (`call_analysis_service.py` line ~103-110)
- **Table**: `call_objections` (INSERT - multiple rows)
- **When**: After categorization completes
- **Fields**: `call_record_id`, `objection_type`, `objection_text`, `transcript_segment`, `confidence`

### 7. **Objection Overcome Analysis** (`call_analysis_service.py` line ~149-156)
- **Table**: `objection_overcome_details` (INSERT - multiple rows)
- **When**: Only if `call_category == 'consult_scheduled'` AND objections exist
- **Fields**: `call_record_id`, `objection_id`, `overcome_method`, `transcript_quote`, `confidence`

### 8. **Analysis Storage** (`bulk_import_service.py` line ~1159-1163)
- **Storage**: Supabase Storage (not DB)
- **Bucket**: `{bucket_name}-analysis`
- **When**: After all analysis completes
- **File**: JSON file with analysis summary

### 9. **Final Status** (`bulk_import_service.py` line ~1170)
- **Table**: `bulk_import_files` (UPDATE)
- **When**: After ALL analysis steps complete
- **Fields Updated**: `status` → 'completed'

## Why Loading Takes Time After "Completed"

### The Problem:
Even though the file status shows `completed`, loading the analysis results (transcript, categorization, objections, overcomes) can take additional time. Here's why:

### Root Causes:

1. **Sequential DB Writes**
   - All writes are synchronous (`.execute()` blocks until commit)
   - But there's a delay between each write:
     - Categorization write → Wait → Objection detection write → Wait → Overcome analysis write → Wait → Status update
   - Each LLM API call takes 2-5 seconds, plus DB write time

2. **Query Timing in Status Endpoint** (`bulk_import_api.py` line ~260-298)
   - When frontend calls `/api/bulk-import/status/{job_id}?include_files=true`, it:
     1. Fetches `bulk_import_files` (fast)
     2. For each file, queries `call_records` (can be slow if many files)
     3. For each call_record, queries `call_objections` (another query per file)
     4. For each objection, queries `objection_overcome_details` (yet another query per objection)
   - **Total queries**: 1 + N + N + M (where N = files, M = objections)
   - If you have 10 files with 3 objections each = 1 + 10 + 10 + 30 = **51 queries**

3. **Supabase Read Consistency**
   - Supabase may have read replicas with slight lag
   - Even though writes are committed, reads might hit a replica that's 100-500ms behind

4. **No Error Logging for Failed Nested Queries**
   - The status endpoint catches exceptions silently (line ~291, 295)
   - If a query fails, it just logs `debug` and continues
   - Frontend shows "loading" because it's waiting for data that failed to load

5. **Missing Data Handling**
   - The code checks `if call_result.data` but doesn't handle partial data
   - If `call_objections` query fails, objections array is empty but no error is shown

## Recommendations:

### Immediate Fixes:
1. **Add explicit error logging** in status endpoint for failed nested queries
2. **Add retry logic** for Supabase queries (handle transient failures)
3. **Batch queries** where possible (use `.in_()` for fetching multiple call_records at once)
4. **Add caching** for recently fetched data (avoid re-querying same data)

### Performance Improvements:
1. **Use Supabase RPC functions** to fetch all nested data in a single query
2. **Add database indexes** on foreign keys (`call_record_id`, `objection_id`)
3. **Implement pagination** for files in status endpoint (fetch in batches)
4. **Use database views** to join related tables instead of multiple queries

### Better Status Tracking:
1. **Add intermediate status fields** in `bulk_import_files`:
   - `transcription_completed_at`
   - `categorization_completed_at`
   - `objections_completed_at`
   - `overcomes_completed_at`
2. **Only mark as 'completed'** when ALL nested queries succeed
3. **Store analysis summary** in `bulk_import_files` table (JSONB) to avoid nested queries

