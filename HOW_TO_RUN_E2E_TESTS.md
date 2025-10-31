# How to Run End-to-End Tests

## 🎯 Overview

There are two ways to test the database hierarchy implementation:
1. **Automated CLI tests** (quick validation)
2. **Manual UI tests** (complete workflow verification)

## 🚀 Quick Start: Automated CLI Tests

### Prerequisites
```bash
# Install dependencies if needed
pip install python-dotenv supabase pytest
```

### Run the Test
```bash
# From project root
python test_e2e_hierarchy.py
```

### What It Tests
- ✅ Organization and center data exists
- ✅ Test user setup with center assignment
- ✅ Patient creation with automatic `center_id` assignment
- ✅ Complete hierarchy chain verification (Patient → Center → Region → Org)
- ✅ Database views functionality
- ✅ RLS policies are deployed

### Output
The script will:
1. Show progress for each test step
2. Display ✅ for passed tests and ❌ for failures
3. Offer to clean up test data at the end
4. Print a summary with pass/fail counts

---

## 🎨 Complete Workflow: Manual UI Tests

For a full end-to-end test including:
- User authentication and signup
- Actual call recording
- Transcript analysis
- Follow-up plan generation

### Step 1: Check Prerequisites
```bash
# Run this SQL query in Supabase SQL Editor
cat CHECK_EXISTING_DATA.sql
```

### Step 2: Follow Detailed Guide
Open and follow: **MANUAL_E2E_TEST_INSTRUCTIONS.md**

### Step 3: Quick Validation
Use: **QUICK_START_TEST.md**

---

## 📊 Available Test Scripts

### Root Scripts (Run from project root)

**Backend Tests:**
```bash
# Run all backend Python tests
npm run test:backend

# Run with coverage
npm run test:coverage:backend

# Run specific test file
cd apps/app-api && python -m pytest __tests__/test_enhanced_context_manager_working.py -v
```

**Frontend Tests:**
```bash
# Run all frontend tests
npm run test:frontend

# Run with coverage
npm run test:coverage:frontend

# Run with watch mode
cd apps/realtime-gateway && npm run test:watch
```

**Integration Tests:**
```bash
# Run CI test suite
npm run test:ci

# Run RAG-specific tests
npm run test:rag

# Run comprehensive Python tests
python run_rag_tests.py --all
```

**Docker Tests:**
```bash
# Build and test in Docker
npm run docker:build
npm run docker:up
npm run docker:logs
```

### E2E Hierarchy Test
```bash
# Automated hierarchy validation
python test_e2e_hierarchy.py

# With cleanup
python test_e2e_hierarchy.py && echo "y"  # Auto-clean
```

---

## 🧪 Test Organization

### Backend Tests (`apps/app-api/__tests__/`)

**Service Tests:**
- `test_audit_service_working.py` - Audit service
- `test_enhanced_context_manager_working.py` - Context management
- `test_tenant_isolation_service.py` - Tenant isolation
- `test_supabase_client_working.py` - Database client

**API Tests:**
- `test_rag_features_api_client.py` - RAG features API
- `test_organization_toggles_api_client.py` - Organization toggles

**Middleware Tests:**
- `test_permissions_middleware.py` - Permission checks
- `test_validation_middleware_working.py` - Input validation

**Coverage Tests:**
- `test_*_95_coverage.py` - Target 95% coverage
- `test_*_working.py` - Working test suites

### Frontend Tests (`apps/realtime-gateway/`)

Run with Vitest:
```bash
cd apps/realtime-gateway
npm run test              # Run once
npm run test:watch        # Watch mode
npm run test:coverage     # With coverage
npm run test:integration  # Integration tests
```

---

## 🎯 Recommended Test Sequence

### For Quick Validation
```bash
1. python test_e2e_hierarchy.py       # Automated hierarchy test
2. npm run test:backend               # Backend unit tests
3. npm run test:frontend              # Frontend unit tests
```

### For Complete Testing
```bash
1. python test_e2e_hierarchy.py                    # Hierarchy validation
2. npm run test:ci                                  # Full CI suite
3. Follow MANUAL_E2E_TEST_INSTRUCTIONS.md          # Manual UI tests
4. Run QUICK_START_TEST.md                         # Verify workflows
```

### For Production Readiness
```bash
1. python test_e2e_hierarchy.py --clean           # Hierarchy + cleanup
2. npm run test:coverage                          # Full coverage report
3. npm run lint                                   # Code quality
4. docker-compose up -d                           # Docker smoke test
5. Follow MANUAL_E2E_TEST_INSTRUCTIONS.md        # Complete workflow
6. Check coverage reports in htmlcov/index.html   # Verify 95%+ coverage
```

---

## 📋 Test Coverage Goals

### Current Coverage (from last run):
- Audit Service: **96.89%**
- Context Manager: **95.93%**
- Enhanced Context Manager: **95.69%**
- Permissions Middleware: **97.83%**
- Tenant Isolation: **90.05%**
- Supabase Client: **97.70%**
- Feature Inheritance: **95.63%**
- Validation Middleware: **98.33%**
- RAG Features API: **95.63%**
- Organization Toggles API: **98.31%**

### Target: **95%+ for all modules**

---

## 🐛 Troubleshooting

### "Module not found" errors
```bash
# Install dependencies
npm install
cd apps/app-api && pip install -r requirements.txt
```

### "Supabase connection failed"
```bash
# Check environment variables
cat .env | grep SUPABASE

# Should have:
# SUPABASE_URL=your_url
# SUPABASE_SERVICE_ROLE_KEY=your_key
```

### "RLS policy error"
```bash
# Verify policies are deployed
# Run in Supabase SQL Editor:
SELECT policyname FROM pg_policies WHERE tablename = 'patients';
# Should show 4 policies
```

### "Test user not found"
```bash
# Create test user via admin UI first
# Or modify test_e2e_hierarchy.py to create user via Supabase Auth API
```

---

## 📖 Documentation

**Essential Guides:**
- `README_DATABASE_HIERARCHY.md` - Complete hierarchy documentation
- `MANUAL_E2E_TEST_INSTRUCTIONS.md` - Step-by-step UI testing
- `QUICK_START_TEST.md` - Fast validation guide

**Implementation Docs:**
- `DATABASE_MIGRATION_COMPLETE.md` - Schema changes
- `APPLICATION_UPDATES_COMPLETE.md` - Code changes
- `FINAL_IMPLEMENTATION_STATUS.md` - Current status

**SQL Scripts:**
- `CHECK_EXISTING_DATA.sql` - See current data
- `UPDATE_RLS_POLICIES_SAFE.sql` - Deploy RLS policies
- `TEST_VIEWS.sql` - Verify views

---

## ✅ Success Criteria

**Automated Tests:**
- ✅ `test_e2e_hierarchy.py` passes all steps
- ✅ All backend unit tests pass
- ✅ All frontend unit tests pass
- ✅ Coverage ≥ 95% for all modules

**Manual Tests:**
- ✅ User can signup and login
- ✅ Patient created with `center_id`
- ✅ Call recording saves with center tracking
- ✅ Analysis and follow-up generated
- ✅ RLS prevents cross-center access

**Production Ready:**
- ✅ All tests passing
- ✅ Coverage reports clean
- ✅ No linter errors
- ✅ Docker builds successfully
- ✅ Manual E2E workflow complete

---

## 🎉 You're Ready!

Choose your testing approach and start validating! The automated script is fastest for quick checks, while manual UI tests verify the complete user experience.

