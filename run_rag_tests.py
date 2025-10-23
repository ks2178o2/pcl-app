#!/usr/bin/env python3
"""
Comprehensive Test Runner for RAG Feature Management
Runs all tests with proper coverage reporting and parallel execution
"""

import subprocess
import sys
import os
import argparse
import json
from pathlib import Path

def run_command(command, cwd=None, capture_output=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}")
        print(f"Error: {e.stderr}")
        return None

def run_backend_tests(test_pattern=None, coverage=True, parallel=True):
    """Run backend tests with coverage"""
    print("🧪 Running Backend Tests...")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent / "apps" / "app-api"
    
    # Build test command
    test_cmd = ["python", "-m", "pytest"]
    
    if test_pattern:
        test_cmd.extend(["-k", test_pattern])
    else:
        # Run RAG-specific tests
        test_cmd.extend([
            "__tests__/test_rag_feature_management_comprehensive.py",
            "__tests__/test_rag_feature_api_endpoints.py",
            "__tests__/test_rag_feature_integration.py"
        ])
    
    if coverage:
        test_cmd.extend([
            "--cov=services",
            "--cov=api",
            "--cov=middleware",
            "--cov-report=html:htmlcov_rag",
            "--cov-report=xml:coverage_rag.xml",
            "--cov-report=json:coverage_rag.json"
        ])
    
    if parallel:
        test_cmd.extend(["-n", "auto"])
    
    test_cmd.extend(["-v", "--tb=short"])
    
    result = run_command(" ".join(test_cmd), cwd=backend_dir)
    
    if result:
        print("✅ Backend tests completed successfully")
        return True
    else:
        print("❌ Backend tests failed")
        return False

def run_frontend_tests(test_pattern=None, coverage=True):
    """Run frontend tests with coverage"""
    print("🧪 Running Frontend Tests...")
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / "apps" / "realtime-gateway"
    
    # Build test command
    test_cmd = ["npm", "run", "test"]
    
    if test_pattern:
        test_cmd.extend(["--", "--grep", test_pattern])
    
    if coverage:
        test_cmd.extend(["--", "--coverage"])
    
    result = run_command(" ".join(test_cmd), cwd=frontend_dir)
    
    if result:
        print("✅ Frontend tests completed successfully")
        return True
    else:
        print("❌ Frontend tests failed")
        return False

def generate_coverage_report():
    """Generate combined coverage report"""
    print("📊 Generating Coverage Report...")
    
    backend_dir = Path(__file__).parent / "apps" / "app-api"
    frontend_dir = Path(__file__).parent / "apps" / "realtime-gateway"
    
    # Check if coverage files exist
    backend_coverage = backend_dir / "coverage_rag.json"
    frontend_coverage = frontend_dir / "coverage" / "coverage-final.json"
    
    if backend_coverage.exists() and frontend_coverage.exists():
        print("📈 Combined coverage report available")
        print(f"   Backend: {backend_coverage}")
        print(f"   Frontend: {frontend_coverage}")
    else:
        print("⚠️  Coverage files not found")

def run_linting():
    """Run linting on both backend and frontend"""
    print("🔍 Running Linting...")
    
    backend_dir = Path(__file__).parent / "apps" / "app-api"
    frontend_dir = Path(__file__).parent / "apps" / "realtime-gateway"
    
    # Backend linting
    print("   Backend linting...")
    backend_result = run_command("python -m flake8 services api middleware", cwd=backend_dir)
    
    # Frontend linting
    print("   Frontend linting...")
    frontend_result = run_command("npm run lint", cwd=frontend_dir)
    
    if backend_result and frontend_result:
        print("✅ Linting passed")
        return True
    else:
        print("❌ Linting failed")
        return False

def run_type_checking():
    """Run type checking on both backend and frontend"""
    print("🔍 Running Type Checking...")
    
    backend_dir = Path(__file__).parent / "apps" / "app-api"
    frontend_dir = Path(__file__).parent / "apps" / "realtime-gateway"
    
    # Backend type checking
    print("   Backend type checking...")
    backend_result = run_command("python -m mypy services api middleware", cwd=backend_dir)
    
    # Frontend type checking
    print("   Frontend type checking...")
    frontend_result = run_command("npm run type-check", cwd=frontend_dir)
    
    if backend_result and frontend_result:
        print("✅ Type checking passed")
        return True
    else:
        print("❌ Type checking failed")
        return False

def main():
    parser = argparse.ArgumentParser(description="RAG Feature Management Test Runner")
    parser.add_argument("--backend-only", action="store_true", help="Run only backend tests")
    parser.add_argument("--frontend-only", action="store_true", help="Run only frontend tests")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel test execution")
    parser.add_argument("--lint", action="store_true", help="Run linting")
    parser.add_argument("--type-check", action="store_true", help="Run type checking")
    parser.add_argument("--pattern", type=str, help="Test pattern to match")
    parser.add_argument("--all", action="store_true", help="Run all tests, linting, and type checking")
    
    args = parser.parse_args()
    
    print("🚀 RAG Feature Management Test Suite")
    print("=" * 50)
    
    success = True
    
    if args.all:
        # Run everything
        success &= run_linting()
        success &= run_type_checking()
        success &= run_backend_tests(args.pattern, not args.no_coverage, not args.no_parallel)
        success &= run_frontend_tests(args.pattern, not args.no_coverage)
        generate_coverage_report()
    else:
        # Run specific tests
        if args.lint:
            success &= run_linting()
        
        if args.type_check:
            success &= run_type_checking()
        
        if not args.frontend_only:
            success &= run_backend_tests(args.pattern, not args.no_coverage, not args.no_parallel)
        
        if not args.backend_only:
            success &= run_frontend_tests(args.pattern, not args.no_coverage)
        
        if not args.no_coverage:
            generate_coverage_report()
    
    print("=" * 50)
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
