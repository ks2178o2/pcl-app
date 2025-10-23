# RAG Feature Management Test Suite

## Overview

This comprehensive test suite covers all aspects of the RAG Feature Management system, including backend services, frontend components, API endpoints, and end-to-end workflows.

## Test Structure

### Backend Tests (`apps/app-api/__tests__/`)

#### 1. Comprehensive Service Tests (`test_rag_feature_management_comprehensive.py`)
- **Permission Tests**: Role-based access control, organization access, RAG feature access
- **Feature Inheritance Tests**: Parent-child organization feature inheritance, effective features resolution
- **Enhanced Context Manager Tests**: Context sharing, approval workflows, hierarchy support
- **Tenant Isolation Tests**: Multi-tenant isolation, quota management, toggle operations
- **Error Handling Tests**: Database errors, network failures, validation errors
- **Edge Case Tests**: Empty data, missing parents, circular dependencies

#### 2. API Endpoint Tests (`test_rag_feature_api_endpoints.py`)
- **RAG Features API**: CRUD operations for global RAG feature catalog
- **Organization Toggles API**: Organization-specific feature toggles management
- **Organization Hierarchy API**: Parent-child organization management
- **Error Handling**: HTTP errors, validation failures, unauthorized access
- **Integration Tests**: Complete API workflows

#### 3. Integration Tests (`test_rag_feature_integration.py`)
- **Complete Workflows**: End-to-end feature management workflows
- **Hierarchical Organization**: Parent-child organization and feature inheritance
- **Context Sharing**: Sharing and approval workflows
- **Bulk Operations**: Bulk toggle updates and batch processing
- **Permission-Based Access**: Role-based access control workflows
- **Multi-Tenant Isolation**: Cross-tenant data isolation
- **Performance Tests**: Large datasets, concurrent operations

### Frontend Tests (`apps/realtime-gateway/src/components/rag/__tests__/`)

#### 1. Component Tests (`rag-feature-management.test.tsx`)
- **RAGFeatureSelector**: Dropdown component with search and filtering
- **RAGFeatureToggleCard**: Individual feature toggle cards
- **RAGFeatureCategorySection**: Category-based feature grouping
- **RAGFeatureManagement**: Main management panel
- **OrganizationHierarchy**: Organization tree visualization
- **SharingApprovals**: Sharing request approval interface
- **RAGFeatureErrorBoundary**: Error handling and recovery

#### 2. API Client Tests (`rag-features-api.test.ts`)
- **API Functions**: All RAG feature API client functions
- **Error Handling**: Network errors, HTTP errors, malformed responses
- **Environment Configuration**: API URL configuration
- **Request/Response**: Proper request formatting and response handling

#### 3. E2E Integration Tests (`rag-feature-e2e-integration.test.tsx`)
- **Complete Workflows**: Full user interaction workflows
- **Cross-Component Integration**: Component interaction and state management
- **Performance Tests**: Large datasets, concurrent operations
- **User Experience**: Loading states, error handling, accessibility
- **Real API Integration**: Actual API calls and responses

## Running Tests

### Quick Start

```bash
# Run all tests
./run_rag_tests.sh --all

# Run only backend tests
./run_rag_tests.sh --backend-only

# Run only frontend tests
./run_rag_tests.sh --frontend-only

# Run with specific pattern
./run_rag_tests.sh --pattern "integration"
```

### Python Test Runner

```bash
# Run comprehensive test suite
python run_rag_tests.py --all

# Run specific test pattern
python run_rag_tests.py --pattern "permission"

# Run with coverage
python run_rag_tests.py --backend-only
```

### Individual Test Execution

#### Backend Tests
```bash
cd apps/app-api
python -m pytest __tests__/test_rag_feature_management_comprehensive.py -v
python -m pytest __tests__/test_rag_feature_api_endpoints.py -v
python -m pytest __tests__/test_rag_feature_integration.py -v
```

#### Frontend Tests
```bash
cd apps/realtime-gateway
npm run test -- --coverage
npm run test -- --grep "RAGFeatureSelector"
```

## Test Coverage

### Backend Coverage Targets
- **Services**: 95%+ coverage for all RAG-related services
- **API Endpoints**: 90%+ coverage for all endpoints
- **Middleware**: 90%+ coverage for permission and validation middleware
- **Error Handling**: 100% coverage for error paths

### Frontend Coverage Targets
- **Components**: 90%+ coverage for all RAG components
- **Hooks**: 95%+ coverage for custom hooks
- **API Client**: 95%+ coverage for API functions
- **Integration**: 85%+ coverage for E2E workflows

## Test Data and Mocking

### Backend Mocking
- **Supabase Client**: Comprehensive mocking with chained query builders
- **Database Responses**: Realistic data structures and error conditions
- **External APIs**: Mocked external service calls
- **Authentication**: Mocked user roles and permissions

### Frontend Mocking
- **API Client**: Mocked API responses and error conditions
- **UI Components**: Mocked Radix UI components
- **Hooks**: Mocked authentication and user role hooks
- **Icons**: Mocked Lucide React icons

## Test Categories

### Unit Tests
- Individual function and method testing
- Component isolation testing
- Service method testing
- Utility function testing

### Integration Tests
- Service-to-service integration
- API endpoint integration
- Component-to-component integration
- Database integration

### End-to-End Tests
- Complete user workflows
- Cross-system integration
- Real API interactions
- Performance testing

## Continuous Integration

### GitHub Actions
```yaml
name: RAG Feature Management Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Backend Tests
        run: ./run_rag_tests.sh --backend-only
      - name: Run Frontend Tests
        run: ./run_rag_tests.sh --frontend-only
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Debugging Tests

### Backend Debugging
```bash
# Run with debug output
python -m pytest -v -s --tb=long

# Run specific test with debugging
python -m pytest __tests__/test_rag_feature_management_comprehensive.py::TestRAGFeatureManagement::test_complete_feature_inheritance_workflow -v -s

# Run with coverage and debugging
python -m pytest --cov=services --cov-report=html -v -s
```

### Frontend Debugging
```bash
# Run with debug output
npm run test -- --reporter=verbose

# Run specific test file
npm run test -- src/components/rag/__tests__/rag-feature-management.test.tsx

# Run with coverage and debugging
npm run test -- --coverage --reporter=verbose
```

## Performance Testing

### Backend Performance
- **Large Datasets**: Tests with 100+ RAG features
- **Concurrent Operations**: Multiple simultaneous API calls
- **Database Performance**: Query optimization testing
- **Memory Usage**: Memory leak detection

### Frontend Performance
- **Large Component Trees**: Tests with 100+ feature cards
- **Search Performance**: Real-time search with large datasets
- **Rendering Performance**: Component render optimization
- **Bundle Size**: Code splitting and optimization

## Test Maintenance

### Adding New Tests
1. **Backend**: Add tests to appropriate test file in `__tests__/`
2. **Frontend**: Add tests to appropriate test file in `__tests__/`
3. **Update Coverage**: Ensure new code is covered by tests
4. **Update Documentation**: Document new test cases

### Test Data Management
- **Mock Data**: Keep mock data realistic and up-to-date
- **Test Fixtures**: Use consistent test fixtures across tests
- **Data Cleanup**: Ensure tests clean up after themselves
- **Isolation**: Tests should not depend on each other

## Troubleshooting

### Common Issues

#### Backend Test Issues
- **Import Errors**: Check Python path and module imports
- **Database Errors**: Verify Supabase client mocking
- **Permission Errors**: Check role and organization mocking
- **Async Issues**: Ensure proper async/await usage

#### Frontend Test Issues
- **Component Rendering**: Check component mocking and props
- **Hook Errors**: Verify hook mocking and dependencies
- **API Errors**: Check API client mocking
- **Timing Issues**: Use proper waitFor and async handling

### Getting Help
- **Test Logs**: Check test output for detailed error messages
- **Coverage Reports**: Review coverage reports for missing tests
- **Documentation**: Refer to component and API documentation
- **Examples**: Look at existing test patterns and examples

## Best Practices

### Test Writing
- **Descriptive Names**: Use clear, descriptive test names
- **Single Responsibility**: Each test should test one thing
- **Arrange-Act-Assert**: Follow AAA pattern for test structure
- **Mock External Dependencies**: Isolate units under test

### Test Organization
- **Group Related Tests**: Use describe blocks for related tests
- **Consistent Structure**: Follow consistent test file structure
- **Clear Setup/Teardown**: Proper test setup and cleanup
- **Meaningful Assertions**: Use specific, meaningful assertions

### Maintenance
- **Regular Updates**: Keep tests updated with code changes
- **Refactoring**: Refactor tests when refactoring code
- **Performance**: Monitor test execution time
- **Coverage**: Maintain high test coverage
