# Call Classification Pipeline: call_category & call_type Usage

This document outlines how `call_category` (success/failure status) and `call_type` (granular category) are used throughout the call analysis and follow-up pipeline.

## Overview

- **call_category**: High-level status (consult_scheduled, consult_not_scheduled, other_question)
- **call_type**: Granular category (scheduling, pricing, directions, billing, complaint, transfer_to_office, general_question, reschedule, confirming_existing_appointment, cancellation)

## Pipeline Flow

### 1. Call Categorization (`call_analysis_service.py`)

**Location**: `categorize_call()`

**What it does**:
- Uses LLM (OpenAI/Gemini) or heuristic fallback to classify calls
- Returns both `call_category` and `call_type` in the result
- Stores both in `call_records` table

**Usage**:
```python
result = {
    "category": "consult_scheduled",  # call_category
    "call_type": "pricing",           # call_type
    "confidence": 0.85,
    "reasoning": "..."
}
```

**Database Update**:
- Updates `call_records.call_category`
- Updates `call_records.call_type`
- Both fields are stored together

---

### 2. Objection Detection (`call_analysis_service.py`)

**Location**: `detect_objections()`

**Current Usage**:
- Detects objections regardless of call_category or call_type
- Stores objections in `call_objections` table

**Future Enhancement**:
- Could prioritize objection types based on call_type (e.g., pricing objections more relevant for pricing calls)

---

### 3. Objection Overcome Analysis (`call_analysis_service.py`)

**Location**: `analyze_objection_overcome()`

**Current Usage**:
- Only runs for calls with `call_category == "consult_scheduled"`
- Analyzes how objections were overcome in successful calls
- Uses `call_type` context (logged but not yet used in prompts)

**Enhancement Opportunity**:
- Could tailor analysis prompts based on call_type (e.g., pricing objections overcome differently in pricing vs. scheduling calls)

---

### 4. Follow-Up Plan Generation (`call_center_followup_api.py`)

**Location**: `generate_call_center_followup_plan()`

**What it does**:
- Fetches `call_category` and `call_type` from `call_records` if not in `analysisData`
- Passes both to `_build_followup_prompt()` for personalized messaging

**Prompt Integration**:
- Includes call_type context in the LLM prompt
- Provides call_type-specific guidance:
  - **pricing**: Focus on value propositions and payment options
  - **reschedule**: Acknowledge scheduling change and offer flexibility
  - **complaint**: Prioritize addressing concerns and rebuilding trust
  - **billing**: Focus on resolving payment issues and providing clarity
  - **scheduling**: Emphasize availability and ease of booking
  - etc.

**Example Prompt Context**:
```
CALL TYPE CONTEXT:
- Call Type: Pricing
- Description: The call was about pricing, costs, or payment options
- Use this context to tailor the follow-up messaging...
```

**Frontend Integration**:
- `BulkImport.tsx` passes `call_type` in `analysisData` when generating follow-up plans

---

### 5. Bulk Import Service (`bulk_import_service.py`)

**Location**: `_wait_for_analysis_completion()`

**What it does**:
- Checks both `call_category` and `call_type` when determining if analysis is complete
- Logs both fields for better debugging
- `call_category` is required for completion check
- `call_type` is optional but preferred for better context

**Completion Criteria**:
- Valid transcript (not "Processing..." or empty)
- `call_category` must exist
- `call_type` is logged if available

---

### 6. Transcription API (`transcribe_api.py`)

**Location**: `_process_transcription_background()`

**What it does**:
- Receives `call_type` from categorization result
- Logs `call_type` when analyzing objection overcomes
- Currently logs but doesn't use in prompts (future enhancement)

**Enhancement Opportunity**:
- Could pass `call_type` to objection overcome analysis for more context-aware analysis

---

### 7. Frontend Display (`BulkImport.tsx`)

**Location**: File results display

**What it shows**:
- **Status Badge**: Shows call_category (✅ Consult Scheduled / ❌ Consult Not Scheduled)
- **Type Badge**: Shows call_type (e.g., "Pricing", "Scheduling", "Billing")
- Both displayed side-by-side for complete context

**Filtering**:
- Currently checks for both `call_category` and `call_type` when determining if results are available
- Future: Could add filter dropdowns for both fields

---

### 8. API Responses (`bulk_import_api.py`)

**Location**: `/api/bulk-import/status/{job_id}`

**What it returns**:
- Includes both `call_category` and `call_type` in call_record data
- Frontend receives both fields for display and decision-making

**Query**:
```python
call_records_result = supabase.table("call_records").select(
    "id,transcript,call_category,call_type,categorization_confidence,categorization_notes"
).in_("id", call_record_ids).execute()
```

---

## Decision Logic Summary

### When to Generate Follow-Up Plans
- **Condition**: `call_category != "consult_scheduled"`
- **Uses**: `call_type` to personalize messaging strategy

### When to Analyze Objection Overcomes
- **Condition**: `call_category == "consult_scheduled"` AND objections exist
- **Uses**: `call_type` context (logged, future: used in prompts)

### When Analysis is Complete
- **Required**: `call_category` exists
- **Preferred**: `call_type` exists
- **Also Required**: Valid transcript

### Follow-Up Plan Personalization
- **Uses**: `call_type` to tailor messaging:
  - Pricing calls → Value propositions, payment options
  - Reschedule calls → Flexibility, alternative times
  - Complaint calls → Trust rebuilding, concern addressing
  - Billing calls → Payment clarity, issue resolution
  - Scheduling calls → Availability, booking ease

---

## Future Enhancements

1. **Filtering UI**: Add dropdown filters for both call_category and call_type
2. **Analytics Dashboard**: Aggregate metrics by call_type
3. **Objection Overcome Prompts**: Use call_type in objection overcome analysis prompts
4. **Smart Routing**: Route calls to different follow-up strategies based on call_type
5. **Reporting**: Generate reports segmented by call_type

---

## Database Schema

```sql
ALTER TABLE call_records 
ADD COLUMN call_category TEXT CHECK (call_category IN ('consult_not_scheduled', 'consult_scheduled', 'other_question')),
ADD COLUMN call_type TEXT CHECK (call_type IN (
    'scheduling',
    'pricing',
    'directions',
    'billing',
    'complaint',
    'transfer_to_office',
    'general_question',
    'reschedule',
    'confirming_existing_appointment',
    'cancellation'
));
```

---

## Key Files Modified

1. `apps/app-api/services/call_analysis_service.py` - Categorization logic
2. `apps/app-api/api/call_center_followup_api.py` - Follow-up plan generation
3. `apps/app-api/api/bulk_import_api.py` - API responses
4. `apps/app-api/services/bulk_import_service.py` - Completion checking
5. `apps/app-api/api/transcribe_api.py` - Transcription pipeline
6. `apps/realtime-gateway/src/pages/BulkImport.tsx` - Frontend display

---

## Testing Checklist

- [ ] Verify both call_category and call_type are stored after categorization
- [ ] Verify follow-up plans use call_type for personalization
- [ ] Verify frontend displays both fields correctly
- [ ] Verify API responses include both fields
- [ ] Verify completion checking works with both fields
- [ ] Test with each call_type to ensure proper messaging

