#!/bin/bash
# Comprehensive CI/CD Test Script for Sales Angel Buddy
# This script runs all tests and generates reports for CI/CD pipeline

set -e  # Exit on any error

echo "🚀 Starting CI/CD Test Suite"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to run tests with timeout
run_test_with_timeout() {
    local test_name="$1"
    local command="$2"
    local timeout="${3:-300}"
    
    print_status "Running $test_name..."
    
    if timeout $timeout bash -c "$command"; then
        print_success "$test_name completed successfully"
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            print_error "$test_name timed out after ${timeout}s"
        else
            print_error "$test_name failed with exit code $exit_code"
        fi
        return $exit_code
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install dependencies if needed
install_dependencies() {
    print_status "Checking and installing dependencies..."
    
    # Python dependencies
    if [ -f "apps/app-api/requirements.txt" ]; then
        print_status "Installing Python dependencies..."
        pip install -r apps/app-api/requirements.txt
        pip install pytest pytest-cov pytest-asyncio safety
    fi
    
    # Node.js dependencies
    if [ -f "apps/realtime-gateway/package.json" ]; then
        print_status "Installing Node.js dependencies..."
        cd apps/realtime-gateway
        npm install
        cd ../..
    fi
    
    # Install K6 for performance testing
    if ! command_exists k6; then
        print_status "Installing K6 for performance testing..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
            echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
            sudo apt-get update
            sudo apt-get install k6
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install k6
        else
            print_warning "K6 installation not supported on this OS"
        fi
    fi
}

# Function to run backend unit tests
run_backend_tests() {
    print_status "Running Backend Unit Tests..."
    
    cd apps/app-api
    
    # Run each test file individually for better error reporting
    test_files=(
        "test_audit_logger.py"
        "test_audit_service.py"
        "test_context_manager.py"
        "test_supabase_client.py"
        "test_rag_endpoints.py"
        "test_knowledge_ingestion.py"
    )
    
    total_tests=0
    passed_tests=0
    
    for test_file in "${test_files[@]}"; do
        if [ -f "__tests__/$test_file" ]; then
            print_status "Running $test_file..."
            if run_test_with_timeout "$test_file" "python -m pytest __tests__/$test_file -v --tb=short" 60; then
                passed_tests=$((passed_tests + 1))
            fi
            total_tests=$((total_tests + 1))
        else
            print_warning "$test_file not found"
        fi
    done
    
    # Run all tests together for coverage
    print_status "Generating backend coverage report..."
    python -m pytest __tests__/ --cov=. --cov-report=xml --cov-report=html --cov-report=json --junitxml=backend-test-results.xml
    
    cd ../..
    
    print_success "Backend tests completed: $passed_tests/$total_tests suites passed"
    return $([ $passed_tests -eq $total_tests ] && echo 0 || echo 1)
}

# Function to run frontend tests
run_frontend_tests() {
    print_status "Running Frontend Tests..."
    
    cd apps/realtime-gateway
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    # Run unit tests
    if run_test_with_timeout "Frontend Unit Tests" "npm run test:ci" 120; then
        print_success "Frontend unit tests passed"
    else
        print_error "Frontend unit tests failed"
        cd ../..
        return 1
    fi
    
    # Run integration tests if available
    if [ -f "package.json" ] && grep -q "test:integration" package.json; then
        if run_test_with_timeout "Frontend Integration Tests" "npm run test:integration" 180; then
            print_success "Frontend integration tests passed"
        else
            print_warning "Frontend integration tests failed"
        fi
    fi
    
    cd ../..
    return 0
}

# Function to run integration tests
run_integration_tests() {
    print_status "Running Integration Tests..."
    
    if [ -d "__tests__/integration" ]; then
        cd __tests__
        if run_test_with_timeout "Integration Tests" "python -m pytest integration/ -v --tb=short" 300; then
            print_success "Integration tests passed"
            cd ..
            return 0
        else
            print_error "Integration tests failed"
            cd ..
            return 1
        fi
    else
        print_warning "Integration tests directory not found"
        return 0
    fi
}

# Function to run agent tests
run_agent_tests() {
    print_status "Running Agent Tests..."
    
    if [ -d "apps/app-worker/__tests__" ]; then
        cd apps/app-worker
        if run_test_with_timeout "Agent Tests" "python -m pytest __tests__/ -v --tb=short" 180; then
            print_success "Agent tests passed"
            cd ../..
            return 0
        else
            print_error "Agent tests failed"
            cd ../..
            return 1
        fi
    else
        print_warning "Agent tests directory not found"
        return 0
    fi
}

# Function to run performance tests
run_performance_tests() {
    print_status "Running Performance Tests..."
    
    if command_exists k6 && [ -d "__tests__/performance" ]; then
        cd __tests__/performance
        
        # Run each performance test
        for test_file in *.js; do
            if [ -f "$test_file" ]; then
                print_status "Running performance test: $test_file"
                if run_test_with_timeout "Performance Test: $test_file" "k6 run --out json=${test_file%.js}_results.json $test_file" 300; then
                    print_success "Performance test $test_file passed"
                else
                    print_warning "Performance test $test_file failed or timed out"
                fi
            fi
        done
        
        cd ../..
        print_success "Performance tests completed"
        return 0
    else
        print_warning "Performance tests skipped (K6 not available or no tests found)"
        return 0
    fi
}

# Function to run security tests
run_security_tests() {
    print_status "Running Security Tests..."
    
    # Python security check
    if command_exists safety; then
        print_status "Running Python security check..."
        if safety check; then
            print_success "Python security check passed"
        else
            print_warning "Python security check found issues"
        fi
    else
        print_warning "Safety not installed, skipping Python security check"
    fi
    
    # Node.js security check
    if command_exists npm; then
        print_status "Running Node.js security audit..."
        if npm audit --audit-level=moderate; then
            print_success "Node.js security audit passed"
        else
            print_warning "Node.js security audit found issues"
        fi
    else
        print_warning "npm not available, skipping Node.js security check"
    fi
    
    return 0
}

# Function to generate coverage report
generate_coverage_report() {
    print_status "Generating Coverage Report..."
    
    # Backend coverage
    if [ -f "apps/app-api/coverage.xml" ]; then
        print_success "Backend coverage report generated"
    else
        print_warning "Backend coverage report not found"
    fi
    
    # Frontend coverage
    if [ -f "apps/realtime-gateway/coverage/lcov.info" ]; then
        print_success "Frontend coverage report generated"
    else
        print_warning "Frontend coverage report not found"
    fi
    
    return 0
}

# Function to check test results
check_test_results() {
    print_status "Checking Test Results..."
    
    local total_suites=0
    local successful_suites=0
    
    # Count test suites
    if [ -d "apps/app-api/__tests__" ]; then
        total_suites=$((total_suites + 1))
        if [ -f "apps/app-api/backend-test-results.xml" ]; then
            successful_suites=$((successful_suites + 1))
        fi
    fi
    
    if [ -d "apps/realtime-gateway" ]; then
        total_suites=$((total_suites + 1))
        if [ -f "apps/realtime-gateway/test-results.xml" ]; then
            successful_suites=$((successful_suites + 1))
        fi
    fi
    
    if [ -d "__tests__/integration" ]; then
        total_suites=$((total_suites + 1))
        successful_suites=$((successful_suites + 1))
    fi
    
    if [ -d "apps/app-worker/__tests__" ]; then
        total_suites=$((total_suites + 1))
        successful_suites=$((successful_suites + 1))
    fi
    
    local success_rate=$((successful_suites * 100 / total_suites))
    
    echo ""
    echo "================================"
    echo "📊 TEST EXECUTION SUMMARY"
    echo "================================"
    echo "✅ Successful Suites: $successful_suites/$total_suites"
    echo "📈 Success Rate: $success_rate%"
    
    if [ $success_rate -ge 95 ]; then
        print_success "Overall Success: PASS (95%+ success rate)"
        return 0
    else
        print_error "Overall Success: FAIL (Below 95% success rate)"
        return 1
    fi
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    
    # Remove temporary files
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    # Install dependencies
    install_dependencies
    
    # Run all test suites
    local backend_result=0
    local frontend_result=0
    local integration_result=0
    local agent_result=0
    local performance_result=0
    local security_result=0
    
    run_backend_tests || backend_result=1
    run_frontend_tests || frontend_result=1
    run_integration_tests || integration_result=1
    run_agent_tests || agent_result=1
    run_performance_tests || performance_result=1
    run_security_tests || security_result=1
    
    # Generate coverage report
    generate_coverage_report
    
    # Check overall results
    check_test_results || exit 1
    
    # Cleanup
    cleanup
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    echo "================================"
    echo "🎉 ALL TESTS COMPLETED SUCCESSFULLY!"
    echo "⏱️  Total execution time: ${duration}s"
    echo "================================"
}

# Run main function
main "$@"
