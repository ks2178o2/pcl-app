# Frontend Testing Guide for call_type Functionality

## Prerequisites

Before testing, ensure you have:
1. ✅ Database migration completed (`call_type` column exists)
2. ✅ Backend API running and accessible
3. ✅ Frontend application running
4. ✅ At least some call records with `call_type` populated

## Testing Checklist

### 1. **CallsSearch Page** (`/calls-search`)

#### Test Filters:
1. Navigate to the Calls Search page
2. Look for the filter section with:
   - **Call Status** dropdown (consult_scheduled, consult_not_scheduled, other_question)
   - **Call Type** dropdown (scheduling, pricing, billing, etc.)
3. Test filtering:
   - Select a call status → Should filter results
   - Select a call type → Should filter results
   - Combine filters → Should apply both filters
   - Clear filters → Should show all calls

#### Test Table Display:
1. Check if the table shows:
   - **Status** column with badges (✅ Scheduled, ❌ Not Scheduled)
   - **Type** column with call type badges
2. Verify badges are correctly styled and display the call type

#### Test Export:
1. Apply some filters
2. Click "Export CSV"
3. Verify the CSV includes:
   - `Call Status` column
   - `Call Type` column
   - Properly formatted values

**Expected Result:** Filters work, table displays call_type, export includes both fields.

---

### 2. **Enterprise Reports** (`/enterprise-reports`)

#### Test Call Type Analysis Tab:
1. Navigate to Enterprise Reports (requires leader/coach/admin role)
2. Look for the **"Call Type Analysis"** tab
3. Click on it
4. Verify you see:
   - **Call Status Breakdown** section with:
     - 3 cards showing counts (Scheduled, Not Scheduled, Other Question)
     - Pie chart showing distribution
   - **Call Type Breakdown** section with:
     - Bar chart showing calls by type
     - Table with columns:
       - Call Type
       - Total Calls
       - Scheduled
       - Not Scheduled
       - Success Rate
       - Avg Quality

**Expected Result:** Charts and tables display correctly with call_type data.

---

### 3. **Bulk Import Page** (`/bulk-import`)

#### Test Call Type Statistics:
1. Navigate to Bulk Import page
2. Start a new import job or view an existing completed job
3. Look for the job status card
4. Scroll down to find **"Call Type Statistics"** section (expandable)
5. Click to expand
6. Verify you see:
   - List of call types with counts
   - Scheduled vs Not Scheduled counts
   - Success rates per type

**Expected Result:** Statistics section shows call_type breakdown for imported files.

---

### 4. **Leaderboard Page** (`/leaderboard`)

#### Test Call Type Filter:
1. Navigate to Leaderboard page
2. Look for the **"Filter by Call Type"** dropdown in the header
3. Test filtering:
   - Select "All Types" → Shows all calls
   - Select a specific type (e.g., "Pricing") → Shows only that type
   - Verify leaderboard updates with filtered data
   - Check that success rates are calculated correctly

**Expected Result:** Filter works, leaderboard updates based on selected call_type.

---

### 5. **Dashboard Metrics** (if using useDashboardMetrics hook)

#### Test Call Type Breakdown:
1. Check any dashboard that uses `useDashboardMetrics` hook
2. Verify the metrics object includes:
   - `callTypeBreakdown` array
   - `topCallType` string
3. Check if these are displayed in the UI

**Expected Result:** Dashboard shows call type insights.

---

### 6. **API Endpoint Testing** (Direct API Call)

#### Test `/api/call-statistics/call-types`:
1. Open browser DevTools → Network tab
2. Navigate to a page that might call this endpoint
3. Or manually test with curl:

```bash
# Get your auth token first
curl -X GET "http://localhost:8001/api/call-statistics/call-types" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

4. Or test with date filters:

```bash
curl -X GET "http://localhost:8001/api/call-statistics/call-types?start_date=2024-01-01&end_date=2024-12-31" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**Expected Result:** API returns JSON with call_type breakdown and statistics.

---

## Creating Test Data

### Option 1: Use Bulk Import
1. Go to Bulk Import page
2. Upload audio files or provide Google Drive URL
3. Wait for processing to complete
4. New calls will have `call_type` automatically populated

### Option 2: Check Existing Calls
1. Run this SQL query to see if any calls have `call_type`:

```sql
SELECT 
    id,
    call_category,
    call_type,
    created_at
FROM call_records
WHERE call_type IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;
```

### Option 3: Update Existing Calls (for testing)
If you need to manually set `call_type` for testing:

```sql
-- Update a few test records
UPDATE call_records
SET call_type = 'scheduling'
WHERE call_category = 'consult_scheduled'
AND call_type IS NULL
LIMIT 5;

UPDATE call_records
SET call_type = 'pricing'
WHERE call_category = 'consult_not_scheduled'
AND call_type IS NULL
LIMIT 5;

UPDATE call_records
SET call_type = 'billing'
WHERE call_category = 'consult_not_scheduled'
AND call_type IS NULL
LIMIT 3;
```

---

## Troubleshooting

### Issue: Filters don't work
- **Check:** Are there calls with `call_type` populated?
- **Check:** Browser console for JavaScript errors
- **Check:** Network tab for API errors

### Issue: No data in Enterprise Reports
- **Check:** Do you have the right permissions (leader/coach/admin)?
- **Check:** Are there call records with `call_analyses`?
- **Check:** Do calls have `call_type` populated?

### Issue: API returns empty data
- **Check:** Backend logs for errors
- **Check:** Authentication token is valid
- **Check:** Database has calls with `call_type`

### Issue: Call Type Statistics not showing in Bulk Import
- **Check:** Job has completed files
- **Check:** Files have `call_record` with `call_type`
- **Check:** Expand the "Call Type Statistics" section

---

## Quick Test Script

Run this in your browser console on the CallsSearch page:

```javascript
// Test if call_type is being loaded
const testCallType = async () => {
  const { data } = await supabase
    .from('call_records')
    .select('call_type, call_category')
    .not('call_type', 'is', null)
    .limit(5);
  
  console.log('Calls with call_type:', data);
  return data;
};

testCallType();
```

---

## Expected UI Elements

### CallsSearch:
- ✅ Filter dropdowns for Call Status and Call Type
- ✅ Status and Type columns in table
- ✅ Badges showing call_type values
- ✅ Export CSV includes both fields

### EnterpriseReports:
- ✅ "Call Type Analysis" tab
- ✅ Pie chart for call status
- ✅ Bar chart for call types
- ✅ Table with success rates

### BulkImport:
- ✅ "Call Type Statistics" expandable section
- ✅ Breakdown by type with counts
- ✅ Success rates per type

### Leaderboard:
- ✅ "Filter by Call Type" dropdown
- ✅ Leaderboard updates based on filter

---

## Next Steps After Testing

1. ✅ Verify all features work as expected
2. ✅ Test with real data from bulk imports
3. ✅ Verify API endpoint returns correct data
4. ✅ Check performance with large datasets
5. ✅ Test edge cases (null values, missing data)

---

## Need Help?

If something doesn't work:
1. Check browser console for errors
2. Check network tab for failed API calls
3. Check backend logs for errors
4. Verify database has data with `call_type`
5. Verify you're logged in with proper permissions

