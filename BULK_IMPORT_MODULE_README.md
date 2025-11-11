# Bulk Audio Import Module

## Overview

The Bulk Audio Import Module allows users to import and analyze multiple audio files from a web source for a customer. It automatically:

1. Creates a Supabase storage bucket for the customer
2. Discovers audio files from a provided web URL
3. Converts files to supported formats (WAV, MP3, M4A, WebM, OGG up to 500MB)
4. Uploads files to customer-specific storage
5. Triggers the call analysis pipeline
6. Categorizes calls (consult not scheduled, consult scheduled, other question)
7. Detects objections and misgivings
8. Analyzes how objections were overcome for scheduled consults

## Architecture

### Backend Components

- **`apps/app-api/api/bulk_import_api.py`**: FastAPI router with endpoints for:
  - `POST /api/bulk-import/start`: Start a new bulk import job
  - `GET /api/bulk-import/status/{job_id}`: Get job status and progress
  - `GET /api/bulk-import/jobs`: List all import jobs for the user

- **`apps/app-api/services/bulk_import_service.py`**: Core service handling:
  - Audio file discovery from web URLs
  - File downloading and conversion
  - Storage bucket creation
  - Integration with transcription and analysis pipeline

- **`apps/app-api/services/call_analysis_service.py`**: LLM-based analysis service for:
  - Call categorization (OpenAI/Gemini)
  - Objection detection
  - Objection overcome analysis

### Database Schema

Migration file: `apps/app-api/migrations/002_bulk_import_schema.sql`

**New Tables:**
- `bulk_import_jobs`: Tracks import jobs
- `bulk_import_files`: Tracks individual files in a job
- `call_objections`: Stores detected objections
- `objection_overcome_details`: Stores how objections were overcome

**Extended Tables:**
- `call_records`: Added fields for bulk import job ID, call category, categorization confidence

### Frontend Components

- **`apps/realtime-gateway/src/pages/BulkImport.tsx`**: React page with:
  - Form to start new imports (customer name, source URL, LLM provider)
  - Real-time job status tracking
  - Job history with progress indicators
  - File-level status details

**Route:** `/bulk-import`

## Setup Instructions

### 1. Run Database Migration

```sql
-- Run the migration file in Supabase SQL Editor
\i apps/app-api/migrations/002_bulk_import_schema.sql
```

Or execute the SQL file directly in your Supabase dashboard.

### 2. Install Python Dependencies

```bash
cd apps/app-api
pip install -r requirements.txt
```

The module requires `aiohttp` for async HTTP requests, which is already in `requirements.txt`.

### 3. Environment Variables

The module uses the existing environment variables from your `.env` file:

```env
OPENAI_API_KEY=your_openai_key  # Already configured in your .env
GOOGLE_API_KEY=your_google_key  # Or GOOGLE_SERVICES_API_KEY - already configured
SUPABASE_URL=your_supabase_url  # Already configured
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key  # Already configured
```

**Note:** The module supports multiple env var names for Google/Gemini:
- `GEMINI_API_KEY`
- `GOOGLE_API_KEY`
- `GOOGLE_SERVICES_API_KEY`
- `GOOGLE_APPLICATION_CREDENTIALS`

Since your `.env` file already contains `OPENAI_API_KEY` and Google services API key, the module should work out of the box without additional configuration!

### 4. Start the Backend

The bulk import API is automatically registered when the FastAPI app starts. No additional configuration needed.

### 5. Access the Frontend

Navigate to `/bulk-import` in your React application.

## Usage

### Starting a Bulk Import

1. Go to `/bulk-import` page
2. Enter:
   - **Customer Name**: Will be used to create storage bucket
   - **Source URL**: Web link containing audio files
   - **LLM Provider**: Choose OpenAI or Gemini for analysis
3. Click "Start Bulk Import"

### Source URL Formats Supported

The module can discover audio files from:
- Direct file links (e.g., `https://example.com/audio.mp3`)
- HTML pages with links to audio files
- JSON APIs returning file URLs
- Directory listings

### Supported Audio Formats

- WAV
- MP3
- M4A
- WebM
- OGG
- FLAC

**Size Limit:** 500MB per file

### Processing Pipeline

1. **Discovery**: Finds all audio files at the source URL
2. **Download**: Downloads each file
3. **Conversion**: Ensures format compatibility (validation only - actual conversion requires ffmpeg)
4. **Upload**: Uploads to customer-specific Supabase bucket
5. **Transcription**: Triggers Deepgram/AssemblyAI transcription
6. **Categorization**: Uses LLM to categorize calls
7. **Objection Detection**: Identifies objections in transcripts
8. **Objection Overcome Analysis**: For scheduled consults, analyzes how objections were overcome
9. **Storage**: Saves analysis results to `{customer-name}-analysis` bucket

### Call Categories

- **consult_not_scheduled**: Call ended without scheduling
- **consult_scheduled**: Appointment was scheduled
- **other_question**: General inquiry, not scheduling-related

### Objection Types

- safety-risk
- cost-value
- timing
- social-concerns
- provider-trust
- results-skepticism
- other

## API Endpoints

### POST /api/bulk-import/start

Start a new bulk import job.

**Request:**
```json
{
  "customer_name": "Acme Corp",
  "source_url": "https://example.com/audio-files",
  "provider": "openai"
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "uuid",
  "customer_name": "Acme Corp",
  "storage_bucket_name": "customer-acme-corp",
  "message": "Bulk import job started for Acme Corp"
}
```

### GET /api/bulk-import/status/{job_id}

Get status of a bulk import job.

**Query Parameters:**
- `include_files` (optional): Include file details in response

**Response:**
```json
{
  "job_id": "uuid",
  "status": "analyzing",
  "customer_name": "Acme Corp",
  "total_files": 10,
  "processed_files": 7,
  "failed_files": 1,
  "progress_percentage": 70.0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z",
  "files": [...]
}
```

### GET /api/bulk-import/jobs

List all bulk import jobs for the current user.

**Query Parameters:**
- `limit` (optional, default: 50)
- `offset` (optional, default: 0)

## Storage Structure

For customer "Acme Corp":

```
customer-acme-corp/
  └── {user_id}/
      └── {job_id}/
          ├── file1.mp3
          ├── file2.wav
          └── ...

customer-acme-corp-analysis/
  └── {user_id}/
      └── {call_record_id}/
          └── analysis.json
```

## Limitations & Future Improvements

1. **Audio Conversion**: Currently validates formats but doesn't convert. Add ffmpeg integration for actual conversion.

2. **Web Scraping**: Basic HTML/JSON parsing. Could be enhanced with:
   - BeautifulSoup for better HTML parsing
   - Support for authenticated URLs
   - S3/GCS bucket direct access

3. **Background Processing**: Uses threading for transcription. Consider:
   - Celery/RQ for proper task queues
   - Webhook support for async processing
   - Better error recovery

4. **Gemini Integration**: Placeholder exists but needs `google-generativeai` package implementation.

5. **File Size**: 500MB limit per file. Consider chunking for larger files.

## Troubleshooting

### Job Stuck in "discovering" Status

- Check source URL is accessible
- Verify URL contains audio files
- Check logs for discovery errors

### Transcription Timeout

- Large files may take longer than 5 minutes
- Consider increasing timeout in `bulk_import_service.py`
- Check transcription provider status

### Storage Bucket Creation Fails

- Verify Supabase service role key has storage admin permissions
- Check bucket name doesn't conflict with existing buckets
- Bucket names are sanitized (alphanumeric, hyphens, underscores only)

## Security Considerations

- All storage buckets are private (not public)
- RLS policies ensure users can only access their own jobs
- Service role key required for bucket creation (backend only)
- Signed URLs used for temporary file access (1 hour expiry)

## Testing

Run the migration SQL file in a test environment first to verify schema changes.

Test with a small set of files initially to verify the pipeline works end-to-end.

## Support

For issues or questions, check:
- Backend logs: `apps/app-api/logs/`
- Frontend console: Browser DevTools
- Supabase logs: Dashboard > Logs

