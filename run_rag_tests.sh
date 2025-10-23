#!/bin/bash
# RAG Feature Management Test Suite Runner
# Comprehensive test execution with coverage and reporting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="apps/app-api"
FRONTEND_DIR="apps/realtime-gateway"
COVERAGE_THRESHOLD=80

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run backend tests
run_backend_tests() {
    print_status "Running Backend Tests..."
    
    cd "$BACKEND_DIR"
    
    # Install dependencies if needed
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # Install test dependencies
    pip install -q pytest pytest-cov pytest-xdist flake8 mypy
    
    # Run tests with coverage
    print_status "Executing backend test suite..."
    python -m pytest \
        __tests__/test_rag_feature_management_comprehensive.py \
        __tests__/test_rag_feature_api_endpoints.py \
        __tests__/test_rag_feature_integration.py \
        --cov=services \
        --cov=api \
        --cov=middleware \
        --cov-report=html:htmlcov_rag \
        --cov-report=xml:coverage_rag.xml \
        --cov-report=json:coverage_rag.json \
        --cov-report=term-missing \
        --cov-fail-under=$COVERAGE_THRESHOLD \
        -n auto \
        -v \
        --tb=short
    
    if [ $? -eq 0 ]; then
        print_success "Backend tests passed"
    else
        print_error "Backend tests failed"
        return 1
    fi
    
    deactivate
    cd - > /dev/null
}

# Function to run frontend tests
run_frontend_tests() {
    print_status "Running Frontend Tests..."
    
    cd "$FRONTEND_DIR"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_status "Installing frontend dependencies..."
        npm install
    fi
    
    # Run tests with coverage
    print_status "Executing frontend test suite..."
    npm run test -- --coverage --reporter=verbose
    
    if [ $? -eq 0 ]; then
        print_success "Frontend tests passed"
    else
        print_error "Frontend tests failed"
        return 1
    fi
    
    cd - > /dev/null
}

# Function to run linting
run_linting() {
    print_status "Running Linting..."
    
    # Backend linting
    print_status "Backend linting..."
    cd "$BACKEND_DIR"
    source venv/bin/activate 2>/dev/null || true
    python -m flake8 services api middleware --max-line-length=100 --ignore=E203,W503
    if [ $? -eq 0 ]; then
        print_success "Backend linting passed"
    else
        print_error "Backend linting failed"
        return 1
    fi
    deactivate 2>/dev/null || true
    cd - > /dev/null
    
    # Frontend linting
    print_status "Frontend linting..."
    cd "$FRONTEND_DIR"
    npm run lint
    if [ $? -eq 0 ]; then
        print_success "Frontend linting passed"
    else
        print_error "Frontend linting failed"
        return 1
    fi
    cd - > /dev/null
}

# Function to run type checking
run_type_checking() {
    print_status "Running Type Checking..."
    
    # Backend type checking
    print_status "Backend type checking..."
    cd "$BACKEND_DIR"
    source venv/bin/activate 2>/dev/null || true
    python -m mypy services api middleware --ignore-missing-imports
    if [ $? -eq 0 ]; then
        print_success "Backend type checking passed"
    else
        print_warning "Backend type checking had issues (continuing...)"
    fi
    deactivate 2>/dev/null || true
    cd - > /dev/null
    
    # Frontend type checking
    print_status "Frontend type checking..."
    cd "$FRONTEND_DIR"
    npm run type-check
    if [ $? -eq 0 ]; then
        print_success "Frontend type checking passed"
    else
        print_error "Frontend type checking failed"
        return 1
    fi
    cd - > /dev/null
}

# Function to generate coverage report
generate_coverage_report() {
    print_status "Generating Coverage Report..."
    
    # Check if coverage files exist
    if [ -f "$BACKEND_DIR/coverage_rag.json" ] && [ -f "$FRONTEND_DIR/coverage/coverage-final.json" ]; then
        print_success "Coverage reports generated:"
        echo "  Backend: $BACKEND_DIR/htmlcov_rag/index.html"
        echo "  Frontend: $FRONTEND_DIR/coverage/lcov-report/index.html"
    else
        print_warning "Coverage files not found"
    fi
}

# Function to run specific test pattern
run_test_pattern() {
    local pattern="$1"
    print_status "Running tests matching pattern: $pattern"
    
    # Backend pattern tests
    cd "$BACKEND_DIR"
    source venv/bin/activate 2>/dev/null || true
    python -m pytest -k "$pattern" -v
    deactivate 2>/dev/null || true
    cd - > /dev/null
    
    # Frontend pattern tests
    cd "$FRONTEND_DIR"
    npm run test -- --grep "$pattern"
    cd - > /dev/null
}

# Function to show help
show_help() {
    echo "RAG Feature Management Test Suite Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --backend-only     Run only backend tests"
    echo "  --frontend-only    Run only frontend tests"
    echo "  --no-coverage      Skip coverage reporting"
    echo "  --lint             Run linting"
    echo "  --type-check       Run type checking"
    echo "  --pattern PATTERN  Run tests matching pattern"
    echo "  --all              Run all tests, linting, and type checking"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --all                    # Run everything"
    echo "  $0 --backend-only           # Run only backend tests"
    echo "  $0 --pattern 'integration'  # Run integration tests"
    echo "  $0 --lint --type-check      # Run linting and type checking"
}

# Main execution
main() {
    echo "🚀 RAG Feature Management Test Suite"
    echo "=================================================="
    
    # Check prerequisites
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    if ! command_exists node; then
        print_error "Node.js is required but not installed"
        exit 1
    fi
    
    if ! command_exists npm; then
        print_error "npm is required but not installed"
        exit 1
    fi
    
    # Parse arguments
    BACKEND_ONLY=false
    FRONTEND_ONLY=false
    NO_COVERAGE=false
    RUN_LINT=false
    RUN_TYPE_CHECK=false
    RUN_ALL=false
    TEST_PATTERN=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend-only)
                BACKEND_ONLY=true
                shift
                ;;
            --frontend-only)
                FRONTEND_ONLY=true
                shift
                ;;
            --no-coverage)
                NO_COVERAGE=true
                shift
                ;;
            --lint)
                RUN_LINT=true
                shift
                ;;
            --type-check)
                RUN_TYPE_CHECK=true
                shift
                ;;
            --pattern)
                TEST_PATTERN="$2"
                shift 2
                ;;
            --all)
                RUN_ALL=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Execute based on options
    if [ "$RUN_ALL" = true ]; then
        run_linting
        run_type_checking
        run_backend_tests
        run_frontend_tests
        generate_coverage_report
    else
        if [ "$RUN_LINT" = true ]; then
            run_linting
        fi
        
        if [ "$RUN_TYPE_CHECK" = true ]; then
            run_type_checking
        fi
        
        if [ "$FRONTEND_ONLY" = false ]; then
            run_backend_tests
        fi
        
        if [ "$BACKEND_ONLY" = false ]; then
            run_frontend_tests
        fi
        
        if [ "$NO_COVERAGE" = false ]; then
            generate_coverage_report
        fi
        
        if [ -n "$TEST_PATTERN" ]; then
            run_test_pattern "$TEST_PATTERN"
        fi
    fi
    
    echo "=================================================="
    print_success "Test suite completed!"
}

# Run main function
main "$@"
