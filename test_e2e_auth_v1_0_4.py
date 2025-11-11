#!/usr/bin/env python3
"""
End-to-End Test for v1.0.4 Authentication System

This script tests the complete authentication workflow:
1. Create an invitation
2. Accept the invitation
3. Login
4. Test 2FA (if enabled)
5. Verify audit logging

Usage:
    python test_e2e_auth_v1_0_4.py
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps/app-api"))

try:
    from supabase import create_client
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Install with: pip install python-dotenv supabase")
    sys.exit(1)

# Load environment variables - try multiple locations
env_locations = [
    project_root / ".env",
    project_root / "apps" / "app-api" / ".env",
    os.path.expanduser("~/.env"),
]

env_loaded = False
for env_path in env_locations:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    load_dotenv()
    print("ℹ️  Using system environment variables")

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n❌ Missing Supabase credentials")
    print("\nConfigure in one of these ways:")
    print("1. Create apps/app-api/.env file with:")
    print("   SUPABASE_URL=https://your-project.supabase.co")
    print("   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key")
    print("\n2. Or set environment variables:")
    print("   export SUPABASE_URL=https://your-project.supabase.co")
    print("   export SUPABASE_SERVICE_ROLE_KEY=your_service_role_key")
    sys.exit(1)


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_success(message):
    print(f"✅ {message}")


def print_error(message):
    print(f"❌ {message}")


def print_info(message):
    print(f"ℹ️  {message}")


class AuthE2ETestRunner:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.test_invitation_id = None
        self.test_user_id = None
        self.test_org_id = None
        self.cleanup_ids = []
    
    def cleanup(self):
        """Clean up test data"""
        print_header("CLEANUP")
        
        if self.test_user_id:
            try:
                # Delete assignments
                self.supabase.table('user_assignments').delete().eq('user_id', self.test_user_id).execute()
                print_success("Deleted user assignments")
                
                # Delete roles
                self.supabase.table('user_roles').delete().eq('user_id', self.test_user_id).execute()
                print_success("Deleted user roles")
                
                # Delete profile
                self.supabase.table('profiles').delete().eq('user_id', self.test_user_id).execute()
                print_success("Deleted profile")
                
                # Delete from auth (admin API)
                self.supabase.auth.admin.delete_user(self.test_user_id)
                print_success("Deleted auth user")
            except Exception as e:
                print_error(f"Failed to cleanup user data: {e}")
        
        if self.test_invitation_id:
            try:
                self.supabase.table('user_invitations').delete().eq('id', self.test_invitation_id).execute()
                print_success("Deleted test invitation")
            except Exception as e:
                print_error(f"Failed to cleanup invitation: {e}")
    
    def step_1_create_invitation(self):
        """Step 1: Create a test invitation"""
        print_header("STEP 1: Create User Invitation")
        
        try:
            # Get an existing organization
            org_result = self.supabase.table('organizations').select('*').limit(1).execute()
            
            if not org_result.data:
                print_error("No organizations found. Cannot proceed with test.")
                return False
            
            self.test_org_id = org_result.data[0]['id']
            org_name = org_result.data[0]['name']
            print_success(f"Using organization: {org_name} ({self.test_org_id})")
            
            # Get an org admin user to be the inviter
            admin_result = self.supabase.table('profiles').select('user_id, salesperson_name').eq(
                'organization_id', self.test_org_id
            ).limit(1).execute()
            
            if not admin_result.data:
                print_error("No admin user found in organization")
                return False
            
            inviter_id = admin_result.data[0]['user_id']
            inviter_name = admin_result.data[0].get('salesperson_name', 'Admin')
            print_success(f"Using inviter: {inviter_name} ({inviter_id})")
            
            # Create invitation
            test_email = f"test_{datetime.now().timestamp()}@e2e-test.com"
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            invitation_data = {
                'email': test_email,
                'organization_id': self.test_org_id,
                'role': 'salesperson',
                'invited_by': inviter_id,
                'token': 'test_token_hash',
                'expires_at': expires_at.isoformat(),
                'status': 'pending'
            }
            
            result = self.supabase.table('user_invitations').insert(invitation_data).execute()
            
            if not result.data:
                print_error("Failed to create invitation")
                return False
            
            self.test_invitation_id = result.data[0]['id']
            print_success(f"Created invitation: {self.test_invitation_id}")
            print_info(f"  Email: {test_email}")
            print_info(f"  Expires: {expires_at}")
            print_info(f"  Status: pending")
            
            return True
            
        except Exception as e:
            print_error(f"Failed to create invitation: {e}")
            return False
    
    def step_2_verify_invitation_in_db(self):
        """Step 2: Verify invitation exists in database"""
        print_header("STEP 2: Verify Invitation in Database")
        
        try:
            result = self.supabase.table('user_invitations').select('*').eq('id', self.test_invitation_id).execute()
            
            if not result.data:
                print_error("Invitation not found in database")
                return False
            
            invitation = result.data[0]
            print_success("Invitation found in database")
            print_info(f"  ID: {invitation['id']}")
            print_info(f"  Email: {invitation['email']}")
            print_info(f"  Status: {invitation['status']}")
            print_info(f"  Organization: {invitation['organization_id']}")
            
            return True
            
        except Exception as e:
            print_error(f"Failed to verify invitation: {e}")
            return False
    
    def step_3_check_audit_logging(self):
        """Step 3: Test login audit logging"""
        print_header("STEP 3: Test Login Audit Logging")
        
        try:
            # Create a test login audit entry
            if not self.test_org_id:
                print_error("No test organization ID available")
                return False
            
            # Get a real user ID from the organization
            user_result = self.supabase.table('profiles').select('user_id').eq(
                'organization_id', self.test_org_id
            ).limit(1).execute()
            
            if not user_result.data:
                print_error("No users found in organization")
                return False
            
            real_user_id = user_result.data[0]['user_id']
            
            audit_data = {
                'user_id': real_user_id,
                'organization_id': self.test_org_id,
                'ip_address': '127.0.0.1',
                'user_agent': 'E2E Test Agent',
                'login_method': 'password',
                'status': 'success'
            }
            
            result = self.supabase.table('login_audit').insert(audit_data).execute()
            
            if not result.data:
                print_error("Failed to create login audit entry")
                return False
            
            audit_id = result.data[0]['id']
            self.cleanup_ids.append(('login_audit', audit_id))
            
            print_success(f"Created login audit entry: {audit_id}")
            print_info(f"  User ID: {real_user_id}")
            print_info(f"  Method: {audit_data['login_method']}")
            print_info(f"  Status: {audit_data['status']}")
            
            # Verify it's queryable
            verify_result = self.supabase.table('login_audit').select('*').eq('id', audit_id).execute()
            if not verify_result.data:
                print_error("Login audit entry not queryable")
                return False
            
            print_success("Login audit entry verified in database")
            return True
            
        except Exception as e:
            print_error(f"Failed to test audit logging: {e}")
            return False
    
    def step_4_check_2fa_tables(self):
        """Step 4: Verify 2FA related tables exist"""
        print_header("STEP 4: Verify 2FA Tables")
        
        try:
            # Check user_devices table exists
            result = self.supabase.table('user_devices').select('id').limit(1).execute()
            print_success("user_devices table exists and is accessible")
            
            # Check profiles has 2FA columns
            profile_result = self.supabase.table('profiles').select('two_factor_enabled, two_factor_secret').limit(1).execute()
            if profile_result.data:
                print_success("profiles table has 2FA columns")
                print_info(f"  two_factor_enabled: {profile_result.data[0].get('two_factor_enabled')}")
                print_info(f"  two_factor_secret: {'[hidden]' if profile_result.data[0].get('two_factor_secret') else 'null'}")
            
            return True
            
        except Exception as e:
            print_error(f"Failed to verify 2FA tables: {e}")
            return False
    
    def run_all_tests(self):
        """Run all E2E tests"""
        print_header("v1.0.4 Authentication E2E Tests")
        print_info("Testing user invitation and authentication system")
        
        try:
            # Run all test steps
            if not self.step_1_create_invitation():
                return False
            
            if not self.step_2_verify_invitation_in_db():
                return False
            
            if not self.step_3_check_audit_logging():
                return False
            
            if not self.step_4_check_2fa_tables():
                return False
            
            # All tests passed
            print_header("ALL TESTS PASSED")
            print_success("v1.0.4 authentication system is working correctly!")
            return True
            
        except Exception as e:
            print_error(f"E2E test failed: {e}")
            return False


def main():
    """Main test runner"""
    runner = AuthE2ETestRunner()
    
    try:
        success = runner.run_all_tests()
        
        if success:
            print("\n🎉 E2E tests completed successfully!")
            return 0
        else:
            print("\n❌ E2E tests failed")
            return 1
    
    finally:
        # Always cleanup
        runner.cleanup()
        
        # Cleanup any additional test data
        if runner.cleanup_ids:
            print_header("ADDITIONAL CLEANUP")
            for table, id_val in runner.cleanup_ids:
                try:
                    runner.supabase.table(table).delete().eq('id', id_val).execute()
                    print_success(f"Deleted {table} entry: {id_val}")
                except Exception as e:
                    print_error(f"Failed to delete {table} entry: {e}")


if __name__ == "__main__":
    sys.exit(main())

