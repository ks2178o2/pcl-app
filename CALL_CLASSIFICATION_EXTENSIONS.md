# Call Classification Extensions: Where Else to Use call_category & call_type

This document outlines additional areas where `call_category` and `call_type` should be integrated for maximum value.

## Priority Areas

### 1. **Search & Filtering** (High Priority)
**Location**: `apps/realtime-gateway/src/pages/CallsSearch.tsx`

**What to Add**:
- Filter dropdown for `call_category` (Consult Scheduled / Not Scheduled / Other)
- Filter dropdown for `call_type` (Scheduling, Pricing, Billing, etc.)
- Multi-select capability for call_type
- Filter persistence in sessionStorage

**Implementation**:
```typescript
const [filterCallCategory, setFilterCallCategory] = useState<string>('all');
const [filterCallType, setFilterCallType] = useState<string[]>([]);

// In applyFilters():
if (filterCallCategory !== 'all') {
  filtered = filtered.filter(call => call.call_category === filterCallCategory);
}
if (filterCallType.length > 0) {
  filtered = filtered.filter(call => 
    call.call_type && filterCallType.includes(call.call_type)
  );
}
```

**Impact**: Users can quickly find calls by type (e.g., "Show me all billing complaints")

---

### 2. **Analytics & Reporting** (High Priority)
**Location**: `apps/realtime-gateway/src/components/EnterpriseReports.tsx`

**What to Add**:
- Breakdown by `call_type` (pie chart or bar chart)
- Success rate by `call_type` (consult_scheduled % per type)
- Average quality score by `call_type`
- Trend analysis by `call_type` over time
- Conversion funnel by `call_type`

**Metrics to Calculate**:
```typescript
// Call type distribution
const callTypeBreakdown = callRecords.reduce((acc, record) => {
  const type = record.call_type || 'unknown';
  acc[type] = (acc[type] || 0) + 1;
  return acc;
}, {});

// Success rate by type
const successByType = callRecords.reduce((acc, record) => {
  const type = record.call_type || 'unknown';
  if (!acc[type]) {
    acc[type] = { total: 0, scheduled: 0 };
  }
  acc[type].total++;
  if (record.call_category === 'consult_scheduled') {
    acc[type].scheduled++;
  }
  return acc;
}, {});
```

**Impact**: Understand which call types convert best, identify problem areas

---

### 3. **Dashboard Metrics** (Medium Priority)
**Location**: `apps/realtime-gateway/src/hooks/useDashboardMetrics.ts`

**What to Add**:
- Breakdown of calls by `call_type` in dashboard
- Success rate by `call_type`
- Most common `call_type` this week/month
- Trend of `call_type` distribution

**Implementation**:
```typescript
interface DashboardMetrics {
  // ... existing fields
  callTypeBreakdown: Record<string, number>;
  callTypeSuccessRates: Record<string, number>;
  topCallTypes: Array<{ type: string; count: number; successRate: number }>;
}
```

**Impact**: Quick visibility into call type trends on dashboard

---

### 4. **Leaderboard** (Medium Priority)
**Location**: `apps/realtime-gateway/src/pages/Leaderboard.tsx`

**What to Add**:
- Filter leaderboard by `call_type`
- Show success rate by `call_type` per salesperson
- Rank by performance in specific call types (e.g., "Best at handling pricing calls")

**Impact**: Identify specialists and training opportunities

---

### 5. **API Endpoints for Statistics** (High Priority)
**Location**: `apps/app-api/api/` (new file: `call_statistics_api.py`)

**What to Create**:
```python
@router.get("/statistics/call-types")
async def get_call_type_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics aggregated by call_type:
    - Count by call_type
    - Success rate by call_type
    - Average quality score by call_type
    - Trend over time by call_type
    """
```

**Impact**: Enable frontend to fetch aggregated statistics efficiently

---

### 6. **Export Functionality** (Medium Priority)
**Location**: Any export/CSV generation code

**What to Add**:
- Include `call_category` and `call_type` columns in CSV exports
- Group exports by `call_type`
- Filter exports by `call_category` and `call_type`

**Impact**: Better data analysis in Excel/Sheets

---

### 7. **Call Records Hook** (Medium Priority)
**Location**: `apps/realtime-gateway/src/hooks/useCallRecords.ts`

**What to Add**:
- Support filtering by `call_category` and `call_type` in `loadCalls()`
- Add filter parameters to hook interface

**Implementation**:
```typescript
const loadCalls = async (
  limit?: number,
  filters?: {
    call_category?: string;
    call_type?: string[];
  }
) => {
  let query = supabase.from('call_records').select('*');
  
  if (filters?.call_category) {
    query = query.eq('call_category', filters.call_category);
  }
  if (filters?.call_type && filters.call_type.length > 0) {
    query = query.in('call_type', filters.call_type);
  }
  // ...
};
```

**Impact**: Reusable filtering across components

---

### 8. **Smart Routing & Assignment** (Future Enhancement)
**Location**: New service or extension to existing routing

**What to Add**:
- Route calls to specialized agents based on `call_type`
  - Pricing calls → Finance-trained agents
  - Complaint calls → Customer service specialists
  - Scheduling calls → General sales team
- Auto-assign follow-up tasks based on `call_type`

**Impact**: Better customer experience, higher conversion rates

---

### 9. **Quality Scoring Adjustments** (Future Enhancement)
**Location**: Quality scoring algorithms

**What to Add**:
- Different quality criteria based on `call_type`
  - Pricing calls: Focus on value communication
  - Complaint calls: Focus on empathy and resolution
  - Scheduling calls: Focus on efficiency and clarity
- Weighted scoring by `call_type`

**Impact**: More accurate quality assessments

---

### 10. **Notification & Alerts** (Future Enhancement)
**Location**: Notification system

**What to Add**:
- Alert managers when high volume of specific `call_type` (e.g., complaints)
- Notify when `call_type` success rate drops below threshold
- Daily/weekly summaries by `call_type`

**Impact**: Proactive issue identification

---

### 11. **Bulk Import UI Enhancements** (Low Priority)
**Location**: `apps/realtime-gateway/src/pages/BulkImport.tsx`

**What to Add**:
- Summary statistics by `call_type` in job status
- Filter files by `call_type` in the file list
- Group files by `call_type` for easier review

**Impact**: Better bulk import workflow

---

### 12. **Call Analysis Page** (Low Priority)
**Location**: `apps/realtime-gateway/src/pages/CallAnalysis.tsx`

**What to Add**:
- Display `call_type` prominently in call header
- Show related calls of same `call_type`
- Suggest actions based on `call_type`

**Impact**: Better context for individual call review

---

## Implementation Priority

### Phase 1 (Immediate Value)
1. ✅ Follow-up plan generation (DONE)
2. ✅ Bulk import pipeline (DONE)
3. 🔄 Search & Filtering (CallsSearch)
4. 🔄 Analytics & Reporting (EnterpriseReports)
5. 🔄 API Statistics Endpoint

### Phase 2 (Enhanced Insights)
6. Dashboard Metrics breakdown
7. Leaderboard filtering
8. Export functionality
9. Call Records hook filtering

### Phase 3 (Advanced Features)
10. Smart routing
11. Quality scoring adjustments
12. Notifications & alerts
13. UI enhancements

---

## Database Considerations

### Indexes Needed
```sql
-- Already exists
CREATE INDEX idx_call_records_call_category ON call_records(call_category);
CREATE INDEX idx_call_records_call_type ON call_records(call_type);

-- Composite index for common queries
CREATE INDEX idx_call_records_category_type ON call_records(call_category, call_type);

-- For time-based analytics
CREATE INDEX idx_call_records_type_created ON call_records(call_type, created_at);
```

### Query Patterns
```sql
-- Count by call_type
SELECT call_type, COUNT(*) 
FROM call_records 
WHERE user_id = ? 
GROUP BY call_type;

-- Success rate by call_type
SELECT 
  call_type,
  COUNT(*) as total,
  SUM(CASE WHEN call_category = 'consult_scheduled' THEN 1 ELSE 0 END) as scheduled,
  ROUND(100.0 * SUM(CASE WHEN call_category = 'consult_scheduled' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM call_records
WHERE user_id = ?
GROUP BY call_type;
```

---

## Testing Checklist

- [ ] Filter by call_category in CallsSearch
- [ ] Filter by call_type in CallsSearch
- [ ] Aggregate statistics by call_type in EnterpriseReports
- [ ] Dashboard shows call_type breakdown
- [ ] API statistics endpoint returns correct data
- [ ] Export includes both fields
- [ ] Leaderboard filters by call_type
- [ ] useCallRecords hook supports filtering
- [ ] Performance is acceptable with new indexes

---

## Key Files to Modify

1. `apps/realtime-gateway/src/pages/CallsSearch.tsx` - Add filters
2. `apps/realtime-gateway/src/components/EnterpriseReports.tsx` - Add breakdowns
3. `apps/realtime-gateway/src/hooks/useDashboardMetrics.ts` - Add call_type metrics
4. `apps/realtime-gateway/src/hooks/useCallRecords.ts` - Add filtering
5. `apps/realtime-gateway/src/pages/Leaderboard.tsx` - Add call_type filtering
6. `apps/app-api/api/call_statistics_api.py` - NEW FILE - Statistics endpoint
7. Export/CSV generation code - Include both fields

---

## Success Metrics

- Users can filter calls by type in < 2 clicks
- Reports show call_type breakdowns automatically
- Dashboard provides call_type insights at a glance
- API responses include call_type statistics
- Export files include both classification fields

