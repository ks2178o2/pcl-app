# Enhanced Admin Features - Test Scenarios

## Overview
This document outlines test scenarios for the enhanced admin features added to Sales Angel Buddy v1.0.0.

## Test Categories

### 1. RAG Feature Management
**Location:** System Admin > RAG Features Tab

#### Test Scenarios:
- [x] **RF-001**: Display RAG Feature Management tab
- [x] **RF-002**: Show feature toggles when tab is clicked
- [x] **RF-003**: Toggle individual features on/off
- [x] **RF-004**: Filter features by category (sales, manager, admin)
- [x] **RF-005**: Enable/disable multiple features at once (bulk operations)
- [x] **RF-006**: Search features by name
- [x] **RF-007**: View feature summary statistics
- [x] **RF-008**: Save changes and persist toggles
- [x] **RF-009**: Reset to default settings

**Expected Behavior:**
- All RAG features should be listed with their descriptions
- Toggle switches should reflect current state
- Changes should be saved to organization settings
- Bulk operations should work across filtered results

---

### 2. RBAC Permissions Management
**Location:** System Admin > RAG Permissions Tab

#### Test Scenarios:
- [x] **RP-001**: Display RAG Permissions tab
- [x] **RP-002**: Show role selection dropdown
- [x] **RP-003**: Display all available roles (System Admin, Org Admin, Team Leader, Sales Coach, Salesperson, Sales Doctor)
- [x] **RP-004**: Load default permissions for each role
- [x] **RP-005**: Customize permissions per feature
- [x] **RP-006**: Save permission changes
- [x] **RP-007**: Show permission summary for each role
- [x] **RP-008**: Display default vs custom permission indicators
- [x] **RP-009**: Reset to role defaults
- [x] **RP-010**: View effective permissions across roles

**Expected Behavior:**
- Default permissions should match role definitions
- Custom permissions should override defaults
- Changes should be persisted
- Summary view should show enabled/disabled counts

---

### 3. Knowledge Base Management
**Location:** System Admin > Knowledge Base Tab

#### Test Scenarios:
- [x] **KB-001**: Display Knowledge Base Management component
- [x] **KB-002**: Show Upload Manager component
- [x] **KB-003**: Display organization context
- [x] **KB-004**: Upload files (PDF, DOCX, TXT, MD, CSV)
- [x] **KB-005**: Web scraping workflow
- [x] **KB-006**: Bulk API import
- [x] **KB-007**: Manage global context items
- [x] **KB-008**: Configure tenant access levels
- [x] **KB-009**: Manage context sharing between organizations

**Expected Behavior:**
- Both components should be visible in the tab
- Organization ID should be displayed in context
- File upload should support multiple formats
- Web scraping should handle URL validation
- Bulk API should process JSON arrays

---

### 4. Enhanced System Health Checks
**Location:** System Admin > System Check Tab

#### Test Scenarios:
- [x] **SH-001**: Display System Check tab (system admins only)
- [x] **SH-002**: Run all health checks on load
- [x] **SH-003**: Check RAG-related tables:
  - RAG Features Table
  - Organization RAG Toggles
  - Global Context Items
  - Patients Table
- [x] **SH-004**: Check AI service endpoints:
  - OpenAI API
  - Deepgram API
  - AssemblyAI API
- [x] **SH-005**: Check Backend API health
- [x] **SH-006**: Check Supabase Connection
- [x] **SH-007**: Show auto-refresh toggle
- [x] **SH-008**: Enable/disable auto-refresh
- [x] **SH-009**: Display last checked timestamp
- [x] **SH-010**: Allow manual refresh on demand
- [x] **SH-011**: Auto-refresh every 60 seconds when enabled
- [x] **SH-012**: Display overall system health percentage

**Expected Behavior:**
- All checks should run automatically on page load
- RAG-specific tables should be verified
- AI services should be tested for connectivity
- Auto-refresh should work every 60 seconds
- Last checked timestamp should update on each refresh

---

### 5. System Admin Tab Integration

#### Test Scenarios:
- [x] **SA-001**: Display all tabs for system admin
- [x] **SA-002**: Show system-level tabs only for system admins
- [x] **SA-003**: Hide system tabs for org admins
- [x] **SA-004**: Proper access control enforcement
- [x] **SA-005**: Tab navigation works correctly
- [x] **SA-006**: Tab state persists during navigation

**Expected Behavior:**
- System admins should see all 9 tabs
- Org admins should see 6 tabs (excluding Organizations, System Analytics, System Check)
- Access should be denied for non-admin users
- Tab switching should be smooth and responsive

---

### 6. Error Handling

#### Test Scenarios:
- [x] **EH-001**: Handle API errors gracefully in RAG Features
- [x] **EH-002**: Handle permission loading errors
- [x] **EH-003**: Handle network timeouts
- [x] **EH-004**: Show appropriate error messages
- [x] **EH-005**: Allow retry on failed operations

**Expected Behavior:**
- Errors should be displayed clearly
- Users should be able to retry failed operations
- No data loss on errors
- User experience should remain smooth

---

### 7. Access Control

#### Test Scenarios:
- [x] **AC-001**: Deny access to non-admin users
- [x] **AC-002**: Allow access for system admins
- [x] **AC-003**: Allow access for org admins
- [x] **AC-004**: Show appropriate access denied message
- [x] **AC-005**: Display user roles in security info

**Expected Behavior:**
- Non-admin users should see "Access Denied" message
- System admins should have full access
- Org admins should have limited access
- Security info should show user roles

---

## Running the Tests

### Prerequisites
```bash
# Install dependencies
npm install

# Run all tests
npm test

# Run specific test file
npm test admin-features.test.tsx

# Run with coverage
npm test -- --coverage
```

### Test Files
1. `apps/realtime-gateway/src/__tests__/admin-features.test.tsx`
   - Comprehensive tests for all admin features
   - 70+ test scenarios
   
2. `apps/realtime-gateway/src/__tests__/system-check-autorefresh.test.tsx`
   - Auto-refresh functionality tests
   - Periodic health check tests

---

## Manual Testing Checklist

### Setup
- [ ] Start backend API (`python main.py`)
- [ ] Start frontend (`npm run dev`)
- [ ] Login as system admin user

### RAG Feature Management
- [ ] Navigate to System Admin > RAG Features
- [ ] Verify all features are listed
- [ ] Toggle a feature on/off
- [ ] Use category filter
- [ ] Use search functionality
- [ ] Test bulk enable/disable
- [ ] Save changes
- [ ] Verify changes persisted

### RBAC Permissions
- [ ] Navigate to System Admin > RAG Permissions
- [ ] Select "Salesperson" role
- [ ] Verify default permissions loaded
- [ ] Modify a permission
- [ ] Save changes
- [ ] Select another role
- [ ] Verify defaults differ by role

### Knowledge Base
- [ ] Navigate to System Admin > Knowledge Base
- [ ] Verify both components visible
- [ ] Test file upload
- [ ] Test web scraping
- [ ] Test bulk API import
- [ ] Verify organization context

### System Health Checks
- [ ] Navigate to System Admin > System Check
- [ ] Verify all checks run
- [ ] Check RAG tables listed
- [ ] Check AI services listed
- [ ] Toggle auto-refresh
- [ ] Wait 60 seconds (or use manual refresh)
- [ ] Verify timestamp updates

---

## Test Results Summary

### Coverage
- **Total Test Scenarios:** 70+
- **Test Categories:** 7
- **Expected Pass Rate:** 100%
- **Critical Paths:** All covered

### Known Issues
None at this time.

### Future Enhancements
- E2E tests with Playwright
- Integration tests with real backend
- Performance tests for bulk operations
- Load tests for auto-refresh

---

## Notes

1. **Auto-refresh interval:** 60 seconds (configurable)
2. **Default permissions:** Defined per role in `ROLE_DEFAULTS`
3. **Access control:** Role-based, enforced at hook level
4. **Error handling:** Graceful degradation with retry options

