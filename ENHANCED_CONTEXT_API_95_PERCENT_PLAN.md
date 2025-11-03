# Plan: Achieve 95%+ Coverage for enhanced_context_api

## Current State
- Coverage: 26% (178 statements, 132 missing)
- Missing lines: 38, 57, 61-64, 89-90, 102-139, 148-183, 196-236, 244-274, 282-293, 306-351, 361-395, 405-441, 451-470, 479-510, 518
- Current tests: 25 tests, 2 failing

## Gap Analysis

### 1. Permission Checks (lines 38, 104-105, 108-109, 150-151, 154-155, 198-199, 246-247, 453-454, 457-458, 481-482)
- System admin vs org admin checks
- Organization-scoped permission checks
- Role-based access control

### 2. Global Context Endpoints (lines 29-64, 66-90)
- POST /global/add - success, permission denied, error handling
- GET /global/items - success, error handling

### 3. Tenant Access Management (lines 94-139, 141-183)
- POST /access/grant - success, permission denied, org admin restrictions, error handling
- POST /access/revoke - success, permission denied, org admin restrictions, error handling

### 4. Cross-Tenant Sharing (lines 187-236, 238-274, 276-293)
- POST /sharing/share - success, permission denied, error handling
- POST /sharing/approve/{sharing_id} - success, permission denied, error handling
- GET /sharing/received - success, error handling

### 5. Upload Endpoints (lines 297-351, 353-395, 397-441)
- POST /upload/file - success, error handling, metadata parsing
- POST /upload/web-scrape - success, error handling
- POST /upload/bulk - success, error handling

### 6. Quota Management (lines 445-470, 472-510)
- GET /quotas/{organization_id} - success, permission denied, error handling
- PUT /quotas/{organization_id} - success, permission denied, error handling

### 7. Error Handling (lines 61-64, 89-90, 136-139, 180-183, 233-236, 271-274, 292-293, 348-351, 392-395, 438-441, 467-470, 507-510)
- Exception handling paths
- HTTPException re-raising
- Generic exception handling

## Implementation Strategy

Similar to organization_hierarchy_api approach:
1. Create `_build_app_with_mocks` utility
2. Use dependency_overrides for get_current_user
3. Mock EnhancedContextManager methods with AsyncMock
4. Mock audit_logger with AsyncMock
5. Test all success paths
6. Test all permission denied paths
7. Test all error handling paths

## Expected Outcome
- 50+ new functional tests
- Coverage: 26% → 95%+
- All tests passing
- Estimated time: 2-3 hours

