"""
Auth Integration Tests - Real Supabase Database
Tests v1.0.4 authentication features with actual database
"""
import pytest
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Set up path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Skip if environment variables not set
if not os.environ.get('SUPABASE_URL'):
    pytest.skip("SUPABASE_URL not set - skipping integration tests", allow_module_level=True)
if not os.environ.get('SUPABASE_SERVICE_ROLE_KEY'):
    pytest.skip("SUPABASE_SERVICE_ROLE_KEY not set - skipping integration tests", allow_module_level=True)

from services.supabase_client import get_supabase_client


@pytest.fixture
def supabase():
    """Get real Supabase client"""
    return get_supabase_client()


@pytest.fixture
def cleanup_invitation(supabase):
    """Cleanup helper - delete test invitation"""
    invitation_id = None
    
    yield invitation_id
    
    # Cleanup
    if invitation_id:
        try:
            supabase.from_('user_invitations').delete().eq('id', invitation_id).execute()
        except:
            pass


@pytest.fixture
def cleanup_login_audit(supabase):
    """Cleanup helper - delete test login audit"""
    audit_id = None
    
    yield audit_id
    
    # Cleanup
    if audit_id:
        try:
            supabase.from_('login_audit').delete().eq('id', audit_id).execute()
        except:
            pass


class TestInvitationsIntegration:
    """Integration tests for invitation system"""
    
    def test_create_and_list_invitation(self, supabase, cleanup_invitation):
        """Test creating an invitation and listing it"""
        # Create test invitation
        test_email = f"test_{datetime.now().timestamp()}@example.com"
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        result = supabase.from_('user_invitations').insert({
            'email': test_email,
            'organization_id': 'test-org-123',
            'role': 'salesperson',
            'token': 'test-token-hash',
            'expires_at': expires_at.isoformat(),
            'invited_by': 'test-user-123',
            'status': 'pending'
        }).execute()
        
        assert result.data is not None
        invitation_id = result.data[0]['id']
        cleanup_invitation._data['invitation_id'] = invitation_id
        
        # List invitations
        list_result = supabase.from_('user_invitations').select('*').eq('email', test_email).execute()
        
        assert len(list_result.data) == 1
        assert list_result.data[0]['email'] == test_email
        assert list_result.data[0]['status'] == 'pending'

    def test_token_validation(self, supabase, cleanup_invitation):
        """Test invitation token validation"""
        # Create test invitation
        test_email = f"test_{datetime.now().timestamp()}@example.com"
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        result = supabase.from_('user_invitations').insert({
            'email': test_email,
            'organization_id': 'test-org-123',
            'role': 'salesperson',
            'token': 'test-token-hash',
            'expires_at': expires_at.isoformat(),
            'invited_by': 'test-user-123',
            'status': 'pending'
        }).execute()
        
        invitation_id = result.data[0]['id']
        cleanup_invitation._data['invitation_id'] = invitation_id
        
        # Validate token
        validate_result = supabase.from_('user_invitations').select('*').eq('token', 'test-token-hash').single().execute()
        
        assert validate_result.data is not None
        assert validate_result.data['email'] == test_email
        assert validate_result.data['status'] == 'pending'

    def test_expired_invitation(self, supabase, cleanup_invitation):
        """Test expired invitation handling"""
        # Create expired invitation
        test_email = f"test_{datetime.now().timestamp()}@example.com"
        expired_at = datetime.utcnow() - timedelta(days=1)
        
        result = supabase.from_('user_invitations').insert({
            'email': test_email,
            'organization_id': 'test-org-123',
            'role': 'salesperson',
            'token': 'expired-token-hash',
            'expires_at': expired_at.isoformat(),
            'invited_by': 'test-user-123',
            'status': 'pending'
        }).execute()
        
        invitation_id = result.data[0]['id']
        cleanup_invitation._data['invitation_id'] = invitation_id
        
        # Check expiration
        now = datetime.utcnow()
        expired_result = supabase.from_('user_invitations').select('*').eq('token', 'expired-token-hash').single().execute()
        
        expires_at = datetime.fromisoformat(expired_result.data['expires_at'].replace('Z', '+00:00'))
        assert expires_at < now


class TestLoginAuditIntegration:
    """Integration tests for login audit system"""
    
    def test_create_login_audit(self, supabase, cleanup_login_audit):
        """Test creating a login audit entry"""
        # Create test audit entry
        result = supabase.from_('login_audit').insert({
            'user_id': 'test-user-123',
            'organization_id': 'test-org-123',
            'ip_address': '192.168.1.1',
            'user_agent': 'Test Browser',
            'login_method': 'password',
            'status': 'success'
        }).execute()
        
        assert result.data is not None
        audit_id = result.data[0]['id']
        cleanup_login_audit._data['audit_id'] = audit_id
        
        # Verify entry
        verify_result = supabase.from_('login_audit').select('*').eq('id', audit_id).single().execute()
        
        assert verify_result.data is not None
        assert verify_result.data['user_id'] == 'test-user-123'
        assert verify_result.data['status'] == 'success'

    def test_list_login_history(self, supabase, cleanup_login_audit):
        """Test retrieving login history"""
        # Create multiple audit entries
        for i in range(3):
            result = supabase.from_('login_audit').insert({
                'user_id': 'test-user-123',
                'organization_id': 'test-org-123',
                'ip_address': f'192.168.1.{i}',
                'user_agent': 'Test Browser',
                'login_method': 'password',
                'status': 'success'
            }).execute()
            
            if i == 0:
                audit_id = result.data[0]['id']
                cleanup_login_audit._data['audit_id'] = audit_id
        
        # Get history
        history = supabase.from_('login_audit').select('*').eq('user_id', 'test-user-123').order('login_at', desc=True).execute()
        
        assert len(history.data) >= 3


class Test2FAIntegration:
    """Integration tests for 2FA system"""
    
    def test_profiles_2fa_fields(self, supabase):
        """Test that profiles table has 2FA fields"""
        # Get a test profile or create one
        result = supabase.from_('profiles').select('id, two_factor_enabled, two_factor_secret').limit(1).execute()
        
        # Just verify fields exist
        if result.data and len(result.data) > 0:
            profile = result.data[0]
            assert 'two_factor_enabled' in profile or profile.get('two_factor_enabled') is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

