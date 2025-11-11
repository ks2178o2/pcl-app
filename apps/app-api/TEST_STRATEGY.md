# Backend Test Strategy

## Test Types and When to Use Them

### 1. Unit Tests (Mocked) ✅
**Files:** `test_*_modern.py` (most test files)

**Purpose:**
- Fast execution (< 1 second per test)
- No external dependencies
- Test logic in isolation
- CI/CD friendly (no credentials needed)

**When to Use:**
- Testing business logic
- Testing error handling
- Testing validation
- Fast feedback during development
- CI/CD pipelines without database access

**Example:** `test_database_integration_modern.py` (mocked Supabase)

---

### 2. Integration Tests (Real Database) ✅ **PREFERRED**
**Files:** `test_database_integration_real.py`, `test_real_database.py`

**Purpose:**
- Test actual database operations
- Validate RLS policies
- Test database constraints
- Test query performance
- Catch schema mismatches

**When to Use:**
- Testing database operations
- Validating RLS policies
- Testing constraints and foreign keys
- Performance testing
- End-to-end integration testing
- Pre-deployment validation

**Requirements:**
- `SUPABASE_URL` in `.env.test` file (preferred) or `.env` file (automatically loaded)
- `SUPABASE_SERVICE_ROLE_KEY` in `.env.test` file (preferred) or `.env` file (automatically loaded)

**Note:** Tests prioritize `.env.test` over `.env` to ensure they use test database credentials, not production.

**Example:** `test_database_integration_real.py` (real Supabase)

---

## Why Real Database Tests Are Better for Integration

### Advantages of Real Database Tests:

1. **RLS Policy Validation**
   - Tests actual Row Level Security policies
   - Catches RLS misconfigurations
   - Validates user access patterns

2. **Database Constraint Testing**
   - Tests unique constraints
   - Tests foreign key relationships
   - Tests NOT NULL constraints
   - Tests check constraints

3. **Schema Validation**
   - Catches schema mismatches early
   - Validates column types
   - Tests migrations

4. **Query Performance**
   - Tests actual query performance
   - Identifies slow queries
   - Validates indexes

5. **End-to-End Integration**
   - Tests complete data flow
   - Validates transaction behavior
   - Tests rollback scenarios

### When Mocked Tests Are Still Useful:

1. **Fast Unit Testing**
   - Test business logic quickly
   - No database setup needed
   - Fast CI/CD feedback

2. **Error Handling**
   - Test error scenarios
   - Test edge cases
   - Test validation logic

3. **Development Speed**
   - Quick feedback during development
   - No database dependency
   - Easy to run locally

---

## Recommended Test Structure

```
__tests__/
├── test_*_modern.py          # Unit tests (mocked) - Fast, isolated
├── test_database_integration_real.py  # Integration tests (real DB) - Comprehensive
└── test_real_database.py    # Legacy real DB tests
```

---

## Running Tests

### Unit Tests (Mocked):
```bash
# Fast, no credentials needed
pytest __tests__/test_*_modern.py
```

### Integration Tests (Real Database):
```bash
# Credentials are automatically loaded from .env.test (preferred) or .env file
# Tests use .env.test to point to test database, not production
pytest __tests__/test_database_integration_real.py -v
```

### All Tests:
```bash
# Runs both unit and integration tests
pytest __tests__/ -v
```

---

## Test Coverage Strategy

1. **Unit Tests (Mocked):** 95%+ coverage
   - Fast feedback
   - Test all code paths
   - Test error handling

2. **Integration Tests (Real DB):** Critical paths
   - Database operations
   - RLS policies
   - Constraints
   - Performance

3. **E2E Tests:** User flows
   - Complete workflows
   - API endpoints
   - Authentication flows

---

## Best Practices

1. **Use Real Database Tests for Integration**
   - When you have credentials, use them
   - Test actual database behavior
   - Validate RLS and constraints

2. **Use Mocked Tests for Unit Testing**
   - Fast feedback during development
   - Test business logic in isolation
   - CI/CD without database access

3. **Clean Up Test Data**
   - Use unique test IDs (timestamps)
   - Clean up after tests
   - Use test fixtures for isolation

4. **Test Isolation**
   - Each test should be independent
   - Use unique identifiers
   - Don't rely on test execution order

---

## Migration Plan

1. ✅ **Keep mocked tests** for unit testing
2. ✅ **Enhance real database tests** for integration
3. ✅ **Use real tests** when credentials are available
4. ✅ **Use mocked tests** for fast CI/CD feedback

---

## Summary

**For Integration Testing:** Use real Supabase credentials when available
- Better validation of RLS policies
- Tests actual database constraints
- Validates schema and migrations
- Tests query performance

**For Unit Testing:** Use mocked Supabase
- Fast execution
- No external dependencies
- CI/CD friendly
- Quick development feedback

**Both have their place, but real database tests are essential for integration testing!**

