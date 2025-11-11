# Quick Frontend Testing Guide

## Step-by-Step Testing (No SQL Required)

### 🎯 **Step 1: Test CallsSearch Page** (Easiest to see results)

1. **Navigate to:** `/calls-search` or click "Search Call Records" in navigation
2. **What to look for:**
   - In the filter section, you should see two new dropdowns:
     - **"Call Status"** dropdown (All Statuses, ✅ Consult Scheduled, ❌ Consult Not Scheduled, ❓ Other Question)
     - **"Call Type"** dropdown (All Types, Scheduling, Pricing, Billing, etc.)
   - In the results table, you should see two new columns:
     - **"Status"** column with colored badges
     - **"Type"** column with call type badges

3. **Test the filters:**
   - Select a call status → Results should filter
   - Select a call type → Results should filter
   - If you see calls with `-` badges, those calls don't have `call_type` yet (that's normal for old calls)

**✅ Success:** You can see and use the filters, and the table shows Status and Type columns.

---

### 🎯 **Step 2: Test Bulk Import Page** (Best for seeing call_type statistics)

1. **Navigate to:** `/bulk-import` or "Call center recordings analysis"
2. **If you have a completed job:**
   - Look for the job status card
   - Scroll down past the progress bars
   - Find the **"Call Type Statistics"** section (it's expandable, click to open)
   - You should see a breakdown by call type with counts and success rates

3. **If you don't have a job yet:**
   - Create a new bulk import job
   - Wait for it to complete processing
   - Then check the Call Type Statistics section

**✅ Success:** You see call type statistics with counts and success rates.

---

### 🎯 **Step 3: Test Enterprise Reports** (Best for visualizations)

**Note:** Requires leader/coach/admin role

1. **Navigate to:** `/enterprise-reports` or find "Enterprise Reports" in navigation
2. **Look for the tabs:**
   - You should see a new tab: **"Call Type Analysis"**
3. **Click on "Call Type Analysis" tab:**
   - You should see:
     - **Call Status Breakdown** section with 3 cards and a pie chart
     - **Call Type Breakdown** section with a bar chart and detailed table
     - Table showing: Call Type, Total Calls, Scheduled, Not Scheduled, Success Rate, Avg Quality

**✅ Success:** You see charts and tables with call type data.

---

### 🎯 **Step 4: Test Leaderboard** (If you have access)

1. **Navigate to:** `/leaderboard`
2. **Look at the top right:**
   - You should see a **"Filter by Call Type"** dropdown
3. **Test the filter:**
   - Select different call types
   - The leaderboard should update to show only calls of that type

**✅ Success:** Filter works and leaderboard updates.

---

## 🚨 **If You Don't See Data:**

### Quick Check: Do you have calls with `call_type`?

The easiest way to check without SQL:

1. Go to **CallsSearch** page
2. Look at the table - if all calls show `-` in the Type column, you need to:
   - **Option A:** Process new calls (bulk import or record new calls)
   - **Option B:** Re-analyze existing calls (use the retranscribe button)

### To Get Test Data:

1. **Bulk Import (Recommended):**
   - Go to Bulk Import page
   - Upload some audio files or provide a Google Drive URL
   - Wait for processing
   - New calls will automatically get `call_type` populated

2. **Re-analyze Existing Calls:**
   - Go to CallsSearch page
   - Find a call that has a transcript
   - Click the retranscribe/analyze button
   - The call will be re-analyzed and get a `call_type`

---

## 🎨 **What You Should See:**

### CallsSearch Page:
```
┌─────────────────────────────────────────┐
│ Search & Filter                         │
├─────────────────────────────────────────┤
│ [Patient Name Search]                   │
│ [Call Status ▼] [Call Type ▼]          │  ← NEW FILTERS
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Call Records                            │
├─────────────────────────────────────────┤
│ Customer | Date | Duration | Status | Type | ... │  ← NEW COLUMNS
│ John Doe | ...  | 5:23    | ✅ Scheduled | Scheduling | ... │
└─────────────────────────────────────────┘
```

### Bulk Import Page:
```
┌─────────────────────────────────────────┐
│ Job Status                             │
├─────────────────────────────────────────┤
│ ... progress bars ...                  │
│                                         │
│ ▼ Call Type Statistics (3 types)       │  ← NEW SECTION
│   Scheduling: 5 total, 3 scheduled    │
│   Pricing: 2 total, 0 scheduled       │
│   Billing: 1 total, 1 scheduled       │
└─────────────────────────────────────────┘
```

### Enterprise Reports:
```
┌─────────────────────────────────────────┐
│ [Salespeople] [Trends] [Centers] [Call Type Analysis] │  ← NEW TAB
└─────────────────────────────────────────┘

Call Status Breakdown:
[✅ 15] [❌ 8] [❓ 2]  + Pie Chart

Call Type Breakdown:
Bar Chart + Table with success rates
```

---

## 🔍 **Troubleshooting:**

### Issue: Filters don't show up
- **Check:** Hard refresh the page (Ctrl+Shift+R or Cmd+Shift+R)
- **Check:** Make sure you're logged in
- **Check:** Browser console for errors (F12)

### Issue: All calls show "-" in Type column
- **This is normal** for calls that were processed before the migration
- **Solution:** Process new calls or re-analyze existing ones

### Issue: Enterprise Reports tab missing
- **Check:** You need leader/coach/admin role
- **Check:** You have call records with `call_analyses`

### Issue: Call Type Statistics section empty
- **Check:** Job has completed files
- **Check:** Files have been analyzed (have `call_record` with `call_type`)

---

## ✅ **Quick Success Checklist:**

- [ ] CallsSearch page shows Status and Type filters
- [ ] CallsSearch table shows Status and Type columns
- [ ] Filters work when selecting options
- [ ] Bulk Import shows Call Type Statistics (if you have a completed job)
- [ ] Enterprise Reports has "Call Type Analysis" tab (if you have permissions)
- [ ] Leaderboard has Call Type filter (if you have access)

---

## 🎯 **Fastest Test Path:**

1. **Go to CallsSearch** → Check if filters and columns appear (30 seconds)
2. **If you have bulk import data** → Check Call Type Statistics (1 minute)
3. **If you have leader access** → Check Enterprise Reports tab (1 minute)

That's it! No SQL needed. Just navigate to the pages and look for the new UI elements.

