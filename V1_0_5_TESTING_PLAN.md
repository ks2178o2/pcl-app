# V1.0.5 Testing Plan

**Date:** January 7, 2025  
**Status:** Ready to Execute  
**Priority:** 🔴 Critical

---

## Overview

Comprehensive testing plan for all v1.0.5 integrations before production deployment.

---

## 🎯 Testing Scope

### Integration Testing
1. Chunked Recording Service
2. Audio Re-encoding Service
3. Failed Uploads Banner
4. useFailedUploadCount Hook

### Database Testing
5. Hierarchy Migration (Staging)
6. RLS Policy Verification
7. Data Integrity Checks

---

## 📋 Test Execution Plan

### Phase 1: Browser Testing (Day 1-2)
**Priority:** 🔴 High  
**Duration:** 4-6 hours

#### 1.1 Chunked Recording Tests

**Test 1.1.1: Basic Recording**
- [ ] Start recording
- [ ] Speak for 30 seconds
- [ ] Stop recording
- [ ] Verify recording saved
- [ ] Check transcription triggers
- **Expected:** Recording completes, transcription starts

**Test 1.1.2: Crash Recovery**
- [ ] Start recording
- [ ] Speak for 15 seconds
- [ ] Close browser tab
- [ ] Reopen browser
- [ ] Navigate to recording page
- [ ] Verify recovery dialog appears
- [ ] Complete recording
- [ ] Verify full audio captured
- **Expected:** Recovery dialog, complete audio preserved

**Test 1.1.3: Background Upload**
- [ ] Start recording
- [ ] Speak for 30 seconds
- [ ] Switch to another tab
- [ ] Wait 1 minute
- [ ] Return to recording tab
- [ ] Verify upload progress advanced
- [ ] Verify no errors
- **Expected:** Upload continues, progress updates

**Test 1.1.4: Pause/Resume**
- [ ] Start recording
- [ ] Speak for 10 seconds
- [ ] Pause recording
- [ ] Resume recording
- [ ] Speak for 10 more seconds
- [ ] Stop recording
- [ ] Verify complete audio
- **Expected:** Both segments captured

**Test 1.1.5: Multi-Chunk Recording**
- [ ] Start recording
- [ ] Speak for 6+ minutes (crosses 5-min chunk boundary)
- [ ] Stop recording
- [ ] Verify multiple chunks created
- [ ] Verify all chunks uploaded
- [ ] Verify transcription successful
- **Expected:** Multiple chunks, all uploaded, single transcript

**Test 1.1.6: Audio Level Monitoring**
- [ ] Start recording
- [ ] Speak quietly, then loudly
- [ ] Verify audio level meter responds
- [ ] Stop recording
- **Expected:** Meter reflects audio level changes

---

#### 1.2 Audio Re-encoding Tests

**Test 1.2.1: Fast-Path Validation**
- [ ] Record 30-second call
- [ ] Check console for "Direct concatenation validated"
- [ ] Verify transcription successful
- **Expected:** Fast-path used, transcription works

**Test 1.2.2: Fallback Re-encoding**
- [ ] Create malformed audio manually (for testing)
- [ ] Attempt transcription
- [ ] Verify fallback to re-encoding
- [ ] Check console for "Starting fallback re-encoding"
- **Expected:** Fallback triggered, audio fixed

**Test 1.2.3: Performance**
- [ ] Record 5-minute call
- [ ] Time re-encoding duration
- [ ] Verify transcription completes
- **Expected:** Re-encoding < 30 seconds, transcript accurate

**Test 1.2.4: Quality Preservation**
- [ ] Record high-quality audio
- [ ] Compare original vs re-encoded
- [ ] Verify no quality degradation
- **Expected:** Quality maintained

---

#### 1.3 Failed Uploads Banner Tests

**Test 1.3.1: Display**
- [ ] Create failed upload (force error)
- [ ] Navigate to recordings page
- [ ] Verify banner appears
- [ ] Check correct count displayed
- **Expected:** Banner visible with correct count

**Test 1.3.2: Retry Functionality**
- [ ] Trigger failed upload
- [ ] Click retry button
- [ ] Verify upload re-attempted
- [ ] Check success toast
- [ ] Verify banner disappears
- **Expected:** Retry succeeds, banner hides

**Test 1.3.3: Delete Functionality**
- [ ] Trigger failed upload
- [ ] Click delete button
- [ ] Verify upload removed
- [ ] Check success toast
- [ ] Verify banner disappears
- **Expected:** Delete succeeds, banner hides

---

#### 1.4 useFailedUploadCount Hook Tests

**Test 1.4.1: Count Accuracy**
- [ ] Create 3 failed uploads
- [ ] Check hook returns count: 3
- [ ] Delete 1 upload
- [ ] Check hook returns count: 2
- **Expected:** Count accurate

**Test 1.4.2: Efficiency**
- [ ] Monitor network requests
- [ ] Check failed uploads count
- [ ] Verify count-only query (no data payload)
- **Expected:** Minimal data transfer

**Test 1.4.3: Auto-Refresh**
- [ ] Check initial count
- [ ] Trigger failed upload
- [ ] Verify count updates automatically
- **Expected:** Auto-refresh works

---

### Phase 2: Database Migration Testing (Day 3-4)
**Priority:** 🔴 High  
**Duration:** 8-10 hours

#### 2.1 Pre-Migration Checks

**Test 2.1.1: Database Backup**
- [ ] Create full backup of production
- [ ] Verify backup integrity
- [ ] Test restore process
- **Expected:** Backup successful, restore works

**Test 2.1.2: Current State Audit**
- [ ] Count organizations
- [ ] Count regions
- [ ] Count centers
- [ ] Count networks (should exist)
- [ ] Document current structure
- **Expected:** Baseline established

---

#### 2.2 Staging Environment Testing

**Test 2.2.1: Migration Application**
- [ ] Apply `V1_0_5_HIERARCHY_MIGRATION.sql` to staging
- [ ] Monitor for errors
- [ ] Verify all steps complete
- [ ] Check logs for warnings
- **Expected:** Migration successful, no errors

**Test 2.2.2: Networks Table Removal**
- [ ] Verify networks table dropped
- [ ] Check no orphaned references
- [ ] Verify regions have organization_id
- **Expected:** Clean transition

**Test 2.2.3: Data Integrity**
- [ ] Compare record counts (before vs after)
- [ ] Verify no data loss
- [ ] Check foreign key relationships
- [ ] Verify constraints intact
- **Expected:** Zero data loss, relationships valid

**Test 2.2.4: RLS Policy Verification**
- [ ] Test system_admin access
- [ ] Test org_admin access
- [ ] Test user access
- [ ] Verify multi-tenant isolation
- [ ] Check no recursion errors
- **Expected:** All policies work, no errors

**Test 2.2.5: Function Verification**
- [ ] Test `get_user_accessible_centers()`
- [ ] Verify performance
- [ ] Check correct results
- **Expected:** Function works, fast

**Test 2.2.6: Index Verification**
- [ ] Check indexes created
- [ ] Verify query performance
- [ ] Compare before/after
- **Expected:** Indexes help, queries fast

---

#### 2.3 Application Integration Testing

**Test 2.3.1: TypeScript Compilation**
- [ ] Regenerate Supabase types
- [ ] Check for type errors
- [ ] Fix any issues
- [ ] Verify clean compile
- **Expected:** Zero type errors

**Test 2.3.2: Frontend Tests**
- [ ] Test region creation
- [ ] Test center creation
- [ ] Test user assignment
- [ ] Verify UI renders correctly
- **Expected:** All features work

**Test 2.3.3: Backend Tests**
- [ ] Run all API tests
- [ ] Verify hierarchy operations
- [ ] Check RLS enforcement
- **Expected:** Tests pass

---

### Phase 3: End-to-End Testing (Day 5)
**Priority:** 🟡 Medium  
**Duration:** 4-6 hours

#### 3.1 Complete User Workflows

**Test 3.1.1: Full Recording Workflow**
- [ ] Login as user
- [ ] Start recording
- [ ] Speak for 60 seconds
- [ ] Stop recording
- [ ] Wait for transcription
- [ ] View analysis
- [ ] Verify all data present
- **Expected:** Complete workflow succeeds

**Test 3.1.2: Multi-User Scenario**
- [ ] Login as org_admin
- [ ] Create region
- [ ] Create center
- [ ] Assign user to center
- [ ] Login as assigned user
- [ ] Verify correct access
- [ ] Start recording
- [ ] Verify data scoped correctly
- **Expected:** Multi-tenant isolation works

**Test 3.1.3: Error Recovery**
- [ ] Simulate network failure
- [ ] Verify retry mechanism
- [ ] Simulate server error
- [ ] Verify graceful degradation
- [ ] Simulate storage full
- [ ] Verify user notification
- **Expected:** Graceful error handling

---

### Phase 4: Performance Testing (Day 6)
**Priority:** 🟡 Medium  
**Duration:** 4-6 hours

#### 4.1 Load Testing

**Test 4.1.1: Concurrent Recordings**
- [ ] 10 concurrent recordings
- [ ] Monitor system load
- [ ] Verify all complete
- **Expected:** Handles load, all succeed

**Test 4.1.2: Re-encoding Performance**
- [ ] Test 10-minute recording
- [ ] Measure encoding time
- [ ] Check memory usage
- [ ] Verify quality
- **Expected:** Performance acceptable

**Test 4.1.3: Query Performance**
- [ ] Test hierarchy queries
- [ ] Measure response times
- [ ] Compare before/after
- **Expected:** No degradation

---

## 🚨 Regression Testing

### Existing Features
- [ ] Verify existing recordings still work
- [ ] Check existing transcriptions intact
- [ ] Verify user assignments preserved
- [ ] Test existing RAG features
- [ ] Verify analytics unchanged
- **Expected:** No regressions

---

## 📊 Test Results Template

### Test Execution Log
```
Test ID: 1.1.1
Name: Basic Recording
Status: PASSED
Duration: 45s
Browser: Chrome 120
Notes: Successful

Test ID: 1.1.2
Name: Crash Recovery
Status: PASSED
Duration: 2m
Browser: Chrome 120
Notes: Recovery dialog appeared correctly

Test ID: 2.2.1
Name: Migration Application
Status: PASSED
Duration: 30s
Environment: Staging
Notes: No errors, clean migration
```

---

## ✅ Success Criteria

### Phase 1: Browser Testing
- ✅ All recording tests pass
- ✅ All re-encoding tests pass
- ✅ All banner tests pass
- ✅ All hook tests pass
- ✅ Zero console errors
- ✅ Zero runtime errors

### Phase 2: Migration Testing
- ✅ Migration completes successfully
- ✅ Zero data loss
- ✅ All policies work
- ✅ All functions work
- ✅ Performance acceptable
- ✅ No regressions

### Phase 3: End-to-End
- ✅ All workflows complete
- ✅ Multi-tenant isolation works
- ✅ Error handling graceful
- ✅ User experience smooth

### Phase 4: Performance
- ✅ Load testing passes
- ✅ No performance degradation
- ✅ Resource usage acceptable

---

## 🚨 Rollback Criteria

Execute rollback if:
- ❌ Data loss detected
- ❌ Critical feature broken
- ❌ Performance > 2x worse
- ❌ Security breach detected
- ❌ User-facing errors

---

## 📝 Test Documentation

### Deliverables
1. ✅ Test execution log
2. ✅ Bug reports (if any)
3. ✅ Performance benchmarks
4. ✅ Rollback procedures
5. ✅ Sign-off document

---

## 👥 Assignments

### Testers
- Primary: TBD
- Secondary: TBD
- Reviewer: TBD

### Responsibilities
- Tester 1: Browser tests
- Tester 2: Migration tests
- Tester 3: E2E tests
- Tester 4: Performance tests

---

## 📅 Timeline

| Phase | Duration | Days | Status |
|-------|----------|------|--------|
| Phase 1: Browser | 4-6 hrs | Days 1-2 | ⚠️ Pending |
| Phase 2: Migration | 8-10 hrs | Days 3-4 | ⚠️ Pending |
| Phase 3: E2E | 4-6 hrs | Day 5 | ⚠️ Pending |
| Phase 4: Performance | 4-6 hrs | Day 6 | ⚠️ Pending |
| **Total** | **20-28 hrs** | **6 days** | **Not Started** |

---

**Status:** Ready to Execute  
**Next Action:** Begin Phase 1 Browser Testing  
**Estimated Completion:** 6 business days

