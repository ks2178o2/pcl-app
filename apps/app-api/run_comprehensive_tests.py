#!/usr/bin/env python3
"""
Comprehensive Test Runner for Sales Angel Buddy
Target Coverage: 95% overall, 90% for enhanced services
"""

import subprocess
import sys
import os
from pathlib import Path


def run_tests():
    """Run comprehensive test suite with coverage reporting"""
    
    # Get the project root
    project_root = Path(__file__).parent.parent.parent
    
    # Test files to run (order matters - fix failing ones first)
    test_files = [
        # Fixed/enhanced tests (priority)
        'apps/app-api/__tests__/test_enhanced_context_management_fixed.py',
        'apps/app-api/__tests__/test_context_manager_improved.py',
        'apps/app-api/__tests__/test_audit_service_improved.py',
        'apps/app-api/__tests__/test_supabase_client_improved.py',
        
        # Existing working tests
        'apps/app-api/__tests__/test_real_database.py',
        'apps/app-api/__tests__/test_context_manager_comprehensive.py',
        'apps/app-api/__tests__/test_audit_service_comprehensive.py',
        'apps/app-api/__tests__/test_supabase_client_comprehensive.py',
    ]
    
    # Run each test file
    all_passed = True
    
    for test_file in test_files:
        test_path = project_root / test_file
        
        if not test_path.exists():
            print(f"⚠️  Skipping {test_file} - file not found")
            continue
        
        print(f"\n{'='*80}")
        print(f"Running: {test_file}")
        print(f"{'='*80}\n")
        
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', str(test_path), '-v', '--tb=short'],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            
            if result.returncode != 0:
                print(result.stderr)
                all_passed = False
        except Exception as e:
            print(f"❌ Error running {test_file}: {e}")
            all_passed = False
    
    # Generate coverage report
    print(f"\n{'='*80}")
    print("Generating Coverage Report")
    print(f"{'='*80}\n")
    
    try:
        subprocess.run([
            'python', '-m', 'pytest',
            'apps/app-api/__tests__/',
            '--cov=services',
            '--cov-report=html',
            '--cov-report=term',
            '--cov-report=json:coverage.json'
        ], cwd=project_root)
        
        print("\n✅ Coverage report generated at htmlcov/index.html")
    except Exception as e:
        print(f"❌ Error generating coverage report: {e}")
    
    return all_passed


if __name__ == '__main__':
    print("🚀 Sales Angel Buddy - Comprehensive Test Suite")
    print("=" * 80)
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        sys.exit(1)

