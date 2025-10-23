#!/usr/bin/env python3
"""
Comprehensive Test Runner for Sales Angel Buddy
Runs all test suites and generates coverage reports for CI/CD
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime


class TestRunner:
    """Comprehensive test runner for the entire application"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_success": True,
            "test_suites": {},
            "coverage": {},
            "performance": {},
            "summary": {}
        }
    
    def run_command(self, command, cwd=None, timeout=300):
        """Run a command and return the result"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.root_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def run_backend_unit_tests(self):
        """Run backend unit tests"""
        print("🧪 Running Backend Unit Tests...")
        
        test_suites = [
            "test_audit_logger.py",
            "test_audit_service.py", 
            "test_context_manager.py",
            "test_supabase_client.py",
            "test_rag_endpoints.py",
            "test_knowledge_ingestion.py"
        ]
        
        suite_results = {}
        total_tests = 0
        passed_tests = 0
        
        for test_file in test_suites:
            test_path = self.root_dir / "apps" / "app-api" / "__tests__" / test_file
            if test_path.exists():
                print(f"  Running {test_file}...")
                result = self.run_command(
                    f"python -m pytest {test_path} -v --tb=short",
                    cwd=self.root_dir / "apps" / "app-api"
                )
                
                suite_results[test_file] = {
                    "success": result["success"],
                    "output": result["stdout"],
                    "error": result["stderr"]
                }
                
                if result["success"]:
                    # Extract test count from output
                    lines = result["stdout"].split('\n')
                    for line in lines:
                        if "passed" in line and "failed" in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == "passed":
                                    passed_tests += int(parts[i-1])
                                elif part == "failed":
                                    total_tests += int(parts[i-1])
                            break
                else:
                    print(f"    ❌ {test_file} failed")
            else:
                print(f"    ⚠️  {test_file} not found")
        
        self.results["test_suites"]["backend_unit"] = {
            "success": all(suite["success"] for suite in suite_results.values()),
            "suites": suite_results,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "coverage": 0  # Will be calculated separately
        }
        
        return suite_results
    
    def run_frontend_tests(self):
        """Run frontend tests"""
        print("🧪 Running Frontend Tests...")
        
        frontend_dir = self.root_dir / "apps" / "realtime-gateway"
        
        # Check if vitest is available
        result = self.run_command("npm list vitest", cwd=frontend_dir)
        if not result["success"]:
            print("  Installing frontend test dependencies...")
            install_result = self.run_command("npm install", cwd=frontend_dir)
            if not install_result["success"]:
                print("    ❌ Failed to install frontend dependencies")
                return {"success": False}
        
        # Run frontend tests
        test_result = self.run_command("npm run test:ci", cwd=frontend_dir)
        
        self.results["test_suites"]["frontend"] = {
            "success": test_result["success"],
            "output": test_result["stdout"],
            "error": test_result["stderr"]
        }
        
        return test_result
    
    def run_integration_tests(self):
        """Run integration tests"""
        print("🧪 Running Integration Tests...")
        
        integration_dir = self.root_dir / "__tests__"
        
        if not integration_dir.exists():
            print("  ⚠️  Integration tests directory not found")
            return {"success": False}
        
        result = self.run_command(
            "python -m pytest integration/ -v --tb=short",
            cwd=integration_dir
        )
        
        self.results["test_suites"]["integration"] = {
            "success": result["success"],
            "output": result["stdout"],
            "error": result["stderr"]
        }
        
        return result
    
    def run_agent_tests(self):
        """Run agent tests"""
        print("🧪 Running Agent Tests...")
        
        agent_dir = self.root_dir / "apps" / "app-worker"
        
        if not agent_dir.exists():
            print("  ⚠️  Agent tests directory not found")
            return {"success": False}
        
        result = self.run_command(
            "python -m pytest __tests__/ -v --tb=short",
            cwd=agent_dir
        )
        
        self.results["test_suites"]["agents"] = {
            "success": result["success"],
            "output": result["stdout"],
            "error": result["stderr"]
        }
        
        return result
    
    def run_performance_tests(self):
        """Run performance tests"""
        print("🧪 Running Performance Tests...")
        
        # Check if K6 is available
        k6_result = self.run_command("k6 version")
        if not k6_result["success"]:
            print("  ⚠️  K6 not available, skipping performance tests")
            self.results["test_suites"]["performance"] = {
                "success": False,
                "error": "K6 not installed"
            }
            return {"success": False}
        
        performance_dir = self.root_dir / "__tests__" / "performance"
        
        if not performance_dir.exists():
            print("  ⚠️  Performance tests directory not found")
            return {"success": False}
        
        # Run K6 performance tests
        test_files = list(performance_dir.glob("*.js"))
        performance_results = {}
        
        for test_file in test_files:
            print(f"  Running {test_file.name}...")
            result = self.run_command(
                f"k6 run --out json={test_file.stem}_results.json {test_file}",
                cwd=performance_dir
            )
            
            performance_results[test_file.name] = {
                "success": result["success"],
                "output": result["stdout"],
                "error": result["stderr"]
            }
        
        self.results["test_suites"]["performance"] = {
            "success": all(r["success"] for r in performance_results.values()),
            "tests": performance_results
        }
        
        return performance_results
    
    def generate_coverage_report(self):
        """Generate comprehensive coverage report"""
        print("📊 Generating Coverage Report...")
        
        coverage_results = {}
        
        # Backend coverage
        backend_dir = self.root_dir / "apps" / "app-api"
        backend_result = self.run_command(
            "python -m pytest __tests__/ --cov=. --cov-report=html --cov-report=xml --cov-report=json",
            cwd=backend_dir
        )
        
        coverage_results["backend"] = {
            "success": backend_result["success"],
            "output": backend_result["stdout"]
        }
        
        # Frontend coverage
        frontend_dir = self.root_dir / "apps" / "realtime-gateway"
        frontend_result = self.run_command(
            "npm run test:coverage",
            cwd=frontend_dir
        )
        
        coverage_results["frontend"] = {
            "success": frontend_result["success"],
            "output": frontend_result["stdout"]
        }
        
        self.results["coverage"] = coverage_results
        return coverage_results
    
    def run_security_tests(self):
        """Run security tests"""
        print("🔒 Running Security Tests...")
        
        security_results = {}
        
        # Python security check
        python_result = self.run_command("pip install safety && safety check")
        security_results["python"] = {
            "success": python_result["success"],
            "output": python_result["stdout"]
        }
        
        # Node.js security check
        node_result = self.run_command("npm audit --audit-level=moderate")
        security_results["nodejs"] = {
            "success": node_result["success"],
            "output": node_result["stdout"]
        }
        
        self.results["test_suites"]["security"] = {
            "success": all(r["success"] for r in security_results.values()),
            "checks": security_results
        }
        
        return security_results
    
    def generate_summary(self):
        """Generate test summary"""
        print("📋 Generating Test Summary...")
        
        total_suites = len(self.results["test_suites"])
        successful_suites = sum(1 for suite in self.results["test_suites"].values() if suite["success"])
        
        self.results["summary"] = {
            "total_test_suites": total_suites,
            "successful_suites": successful_suites,
            "success_rate": (successful_suites / total_suites * 100) if total_suites > 0 else 0,
            "overall_success": successful_suites == total_suites,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results["overall_success"] = self.results["summary"]["overall_success"]
        
        return self.results["summary"]
    
    def save_results(self):
        """Save test results to file"""
        results_file = self.root_dir / "test-results.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 Test results saved to {results_file}")
    
    def print_summary(self):
        """Print test summary"""
        summary = self.results["summary"]
        
        print("\n" + "="*60)
        print("📊 TEST EXECUTION SUMMARY")
        print("="*60)
        
        print(f"✅ Successful Suites: {summary['successful_suites']}/{summary['total_test_suites']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"🎯 Overall Success: {'✅ PASS' if summary['overall_success'] else '❌ FAIL'}")
        
        print("\n📋 Test Suite Results:")
        for suite_name, suite_result in self.results["test_suites"].items():
            status = "✅ PASS" if suite_result["success"] else "❌ FAIL"
            print(f"  {status} {suite_name}")
        
        print(f"\n⏰ Completed at: {summary['timestamp']}")
        
        if not summary["overall_success"]:
            print("\n❌ Some test suites failed. Check the detailed results above.")
            sys.exit(1)
        else:
            print("\n🎉 All tests passed! Ready for deployment.")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive Test Suite")
        print("="*60)
        
        start_time = time.time()
        
        # Run all test suites
        self.run_backend_unit_tests()
        self.run_frontend_tests()
        self.run_integration_tests()
        self.run_agent_tests()
        self.run_performance_tests()
        self.run_security_tests()
        
        # Generate reports
        self.generate_coverage_report()
        
        # Generate summary
        self.generate_summary()
        
        # Save results
        self.save_results()
        
        # Print summary
        self.print_summary()
        
        end_time = time.time()
        print(f"\n⏱️  Total execution time: {end_time - start_time:.2f} seconds")


def main():
    """Main entry point"""
    runner = TestRunner()
    runner.run_all_tests()


if __name__ == "__main__":
    main()
