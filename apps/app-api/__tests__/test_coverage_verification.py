"""
Quick verification script to check current coverage status
Run this to get baseline coverage before starting 95% coverage push
"""
import subprocess
import sys

def run_coverage_check():
    """Run coverage check on key modules"""
    modules = [
        'services.context_manager',
        'services.audit_service',
        'services.tenant_isolation_service',
        'services.enhanced_context_manager',
        'services.supabase_client',
        'middleware.permissions',
        'middleware.validation',
    ]
    
    cmd = [
        sys.executable, '-m', 'pytest',
        '--cov=' + ' --cov='.join(modules),
        '--cov-report=term-missing',
        '--cov-report=json:coverage_verified.json',
        '-q'
    ]
    
    print("Running coverage verification...")
    print("Command:", ' '.join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(run_coverage_check())

