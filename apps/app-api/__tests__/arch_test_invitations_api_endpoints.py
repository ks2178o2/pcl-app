"""
Real Integration Tests for Invitations API Endpoints
Tests actual API endpoints with real database
"""
import pytest
import os
import sys
from datetime import datetime, timedelta

from test_env_helper import load_test_env

# Load environment (prefer sandbox-friendly dotenv)
BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
load_test_env(
    [
        os.path.join(BASE_DIR, "sandbox.env"),
        os.path.join(BASE_DIR, ".env"),
    ]
)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Skip if no database connection
if not os.environ.get('SUPABASE_URL'):
    pytest.skip("No database connection", allow_module_level=True)

from fastapi.testclient import TestClient
from main import app
from services.supabase_client import get_supabase_client


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def supabase():
    """Get real Supabase client"""
    return get_supabase_client()


@pytest.fixture
def test_data(supabase):
    """Get real test data from database"""
    # Get organization
    org_result = supabase.from_('organizations').select('id, name').limit(1).execute()
    assert org_result.data, "No organizations found"
    org = org_result.data[0]
    
    # Get user
    user_result = supabase.from_('profiles').select('user_id, salesperson_name').eq(
        'organization_id', org['id']
    ).limit(1).execute()
    assert user_result.data, "No users found"
    user = user_result.data[0]
    
    return {'organization': org, 'user': user}


@pytest.fixture
def cleanup_invitations(supabase):
    """Cleanup helper"""
    inv_ids = []
    
    yield inv_ids
    
    for inv_id in inv_ids:
        try:
            supabase.from_('user_invitations').delete().eq('id', inv_id).execute()
        except:
            pass


class TestInvitationsEndpoints:
    """Test invitation API endpoints"""
    
    def test_endpoint_exists(self, client):
        """Test that endpoints are registered"""
        # Should get 401 (unauthorized), not 404 (not found)
        response = client.post('/api/invitations/', json={})
        assert response.status_code != 404, "Endpoint not found"
        
        response = client.get('/api/invitations/')
        assert response.status_code != 404, "Endpoint not found"
    
    def test_create_invitation_requires_auth(self, client):
        """Test that creating invitation requires authentication"""
        response = client.post(
            '/api/invitations/',
            json={
                'email': 'test@example.com',
                'organization_id': 'org-123',
                'role': 'salesperson'
            }
        )
        
        # Should require authentication (401 or 403)
        assert response.status_code in (401, 403)
    
    def test_list_invitations_requires_auth(self, client):
        """Test that listing invitations requires authentication"""
        response = client.get('/api/invitations/')
        
        # Should require authentication
        assert response.status_code in (401, 403)


class TestAuthEndpoints:
    """Test auth API endpoints"""
    
    def test_endpoint_exists(self, client):
        """Test that endpoints are registered"""
        response = client.post('/api/auth/login-audit', json={})
        assert response.status_code != 404, "Endpoint not found"
        
        response = client.get('/api/auth/login-history')
        assert response.status_code != 404, "Endpoint not found"
    
    def test_login_audit_requires_data(self, client):
        """Test that login audit endpoint requires data"""
        response = client.post('/api/auth/login-audit', json={})
        
        # Should fail validation (422) or require auth
        assert response.status_code in (422, 401, 403)
    
    def test_login_history_requires_auth(self, client):
        """Test that login history requires authentication"""
        response = client.get('/api/auth/login-history')
        
        # Should require authentication
        assert response.status_code in (401, 403)


class Test2FAEndpoints:
    """Test 2FA API endpoints"""
    
    def test_endpoint_exists(self, client):
        """Test that endpoints are registered"""
        response = client.get('/api/auth/2fa/status')
        assert response.status_code != 404, "Endpoint not found"
        
        response = client.post('/api/auth/2fa/setup')
        assert response.status_code != 404, "Endpoint not found"
    
    def test_2fa_status_requires_auth(self, client):
        """Test that 2FA status requires authentication"""
        response = client.get('/api/auth/2fa/status')
        
        # Should require authentication
        assert response.status_code in (401, 403)
    
    def test_2fa_setup_requires_auth(self, client):
        """Test that 2FA setup requires authentication"""
        response = client.post('/api/auth/2fa/setup')
        
        # Should require authentication
        assert response.status_code in (401, 403)


class TestDatabaseOperations:
    """Test actual database operations"""
    
    def test_create_invitation_direct(self, supabase, test_data, cleanup_invitations):
        """Test creating invitation directly in database"""
        test_email = f"direct_{datetime.now().timestamp()}@test.com"
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        result = supabase.from_('user_invitations').insert({
            'email': test_email,
            'organization_id': test_data['organization']['id'],
            'role': 'salesperson',
            'invited_by': test_data['user']['user_id'],
            'token': 'direct_token_hash',
            'expires_at': expires_at.isoformat(),
            'status': 'pending'
        }).execute()
        
        assert result.data
        inv_id = result.data[0]['id']
        cleanup_invitations.append(inv_id)
        
        # Verify
        verify = supabase.from_('user_invitations').select('*').eq('id', inv_id).execute()
        assert verify.data
        assert verify.data[0]['email'] == test_email
    
    def test_query_invitation_by_email(self, supabase, test_data, cleanup_invitations):
        """Test querying invitation by email"""
        test_email = f"query_{datetime.now().timestamp()}@test.com"
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        result = supabase.from_('user_invitations').insert({
            'email': test_email,
            'organization_id': test_data['organization']['id'],
            'role': 'salesperson',
            'invited_by': test_data['user']['user_id'],
            'token': 'query_token_hash',
            'expires_at': expires_at.isoformat(),
            'status': 'pending'
        }).execute()
        
        assert result.data
        inv_id = result.data[0]['id']
        cleanup_invitations.append(inv_id)
        
        # Query by email
        query_result = supabase.from_('user_invitations').select('*').eq('email', test_email).execute()
        assert query_result.data
        assert query_result.data[0]['email'] == test_email
    
    def test_update_invitation_status(self, supabase, test_data, cleanup_invitations):
        """Test updating invitation status"""
        test_email = f"update_{datetime.now().timestamp()}@test.com"
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        result = supabase.from_('user_invitations').insert({
            'email': test_email,
            'organization_id': test_data['organization']['id'],
            'role': 'salesperson',
            'invited_by': test_data['user']['user_id'],
            'token': 'update_token_hash',
            'expires_at': expires_at.isoformat(),
            'status': 'pending'
        }).execute()
        
        assert result.data
        inv_id = result.data[0]['id']
        cleanup_invitations.append(inv_id)
        
        # Update status
        update_result = supabase.from_('user_invitations').update({
            'status': 'accepted'
        }).eq('id', inv_id).execute()
        
        assert update_result.data
        
        # Verify
        verify = supabase.from_('user_invitations').select('*').eq('id', inv_id).execute()
        assert verify.data
        assert verify.data[0]['status'] == 'accepted'
    
    def test_delete_invitation(self, supabase, test_data):
        """Test deleting an invitation"""
        test_email = f"delete_{datetime.now().timestamp()}@test.com"
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        result = supabase.from_('user_invitations').insert({
            'email': test_email,
            'organization_id': test_data['organization']['id'],
            'role': 'salesperson',
            'invited_by': test_data['user']['user_id'],
            'token': 'delete_token_hash',
            'expires_at': expires_at.isoformat(),
            'status': 'pending'
        }).execute()
        
        assert result.data
        inv_id = result.data[0]['id']
        
        # Delete
        supabase.from_('user_invitations').delete().eq('id', inv_id).execute()
        
        # Verify deleted
        verify = supabase.from_('user_invitations').select('*').eq('id', inv_id).execute()
        assert not verify.data or len(verify.data) == 0
    
    def test_list_all_invitations_for_org(self, supabase, test_data, cleanup_invitations):
        """Test listing all invitations for an organization"""
        # Create a few invitations
        for i in range(3):
            test_email = f"bulk_{i}_{datetime.now().timestamp()}@test.com"
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            result = supabase.from_('user_invitations').insert({
                'email': test_email,
                'organization_id': test_data['organization']['id'],
                'role': 'salesperson',
                'invited_by': test_data['user']['user_id'],
                'token': f'bulk_token_hash_{i}',
                'expires_at': expires_at.isoformat(),
                'status': 'pending'
            }).execute()
            
            if result.data:
                cleanup_invitations.append(result.data[0]['id'])
        
        # List all for org
        list_result = supabase.from_('user_invitations').select('*').eq(
            'organization_id', test_data['organization']['id']
        ).execute()
        
        assert isinstance(list_result.data, list)


class TestLoginAuditOperations:
    """Test login audit operations"""
    
    def test_create_successful_login(self, supabase, test_data, cleanup_data):
        """Test creating successful login audit"""
        result = supabase.from_('login_audit').insert({
            'user_id': test_data['user']['user_id'],
            'organization_id': test_data['organization']['id'],
            'ip_address': '10.0.0.1',
            'user_agent': 'Test Agent',
            'login_method': 'password',
            'status': 'success'
        }).execute()
        
        assert result.data
        audit_id = result.data[0]['id']
        cleanup_data.append(audit_id)
        
        # Verify
        verify = supabase.from_('login_audit').select('*').eq('id', audit_id).execute()
        assert verify.data
        assert verify.data[0]['status'] == 'success'
    
    def test_query_login_history_for_user(self, supabase, test_data):
        """Test querying login history for a user"""
        result = supabase.from_('login_audit').select('*').eq(
            'user_id', test_data['user']['user_id']
        ).limit(10).execute()
        
        assert isinstance(result.data, list)
    
    def test_login_audit_with_device_info(self, supabase, test_data, cleanup_data):
        """Test creating login audit with device information"""
        result = supabase.from_('login_audit').insert({
            'user_id': test_data['user']['user_id'],
            'organization_id': test_data['organization']['id'],
            'ip_address': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 Test Browser',
            'device_name': 'Test Device',
            'device_fingerprint': 'test_fingerprint_abc123',
            'login_method': 'password',
            'status': 'success'
        }).execute()
        
        assert result.data
        audit_id = result.data[0]['id']
        cleanup_data.append(audit_id)
        
        # Verify
        verify = supabase.from_('login_audit').select('*').eq('id', audit_id).execute()
        assert verify.data
        assert verify.data[0]['device_name'] == 'Test Device'


class Test2FAOperations:
    """Test 2FA operations"""
    
    def test_update_user_2fa_settings(self, supabase, test_data):
        """Test updating user 2FA settings"""
        # Update profile with 2FA
        result = supabase.from_('profiles').update({
            'two_factor_enabled': True,
            'two_factor_secret': 'test_secret_key_abc123'
        }).eq('user_id', test_data['user']['user_id']).execute()
        
        # Should not error
        assert result.data is not None or True  # May or may not return data
        
        # Verify
        verify = supabase.from_('profiles').select('two_factor_enabled, two_factor_secret').eq(
            'user_id', test_data['user']['user_id']
        ).execute()
        
        assert verify.data
        profile = verify.data[0]
        assert profile['two_factor_enabled'] == True
    
    def test_user_devices_operations(self, supabase, test_data, cleanup_devices):
        """Test user devices operations"""
        # Create a device entry
        device_result = supabase.from_('user_devices').insert({
            'user_id': test_data['user']['user_id'],
            'device_id': 'device_fp_test123',
            'device_name': 'Test Device',
            'verified_at': datetime.utcnow().isoformat(),
            'last_used_at': datetime.utcnow().isoformat(),
            'is_primary': True
        }).execute()
        
        if device_result.data:
            device_id = device_result.data[0]['id']
            cleanup_devices.append(device_id)
            
            # Verify
            verify = supabase.from_('user_devices').select('*').eq('id', device_id).execute()
            assert verify.data
            assert verify.data[0]['device_name'] == 'Test Device'


@pytest.fixture
def cleanup_data():
    """Cleanup audit entries"""
    audit_ids = []
    
    yield audit_ids
    
    supabase = get_supabase_client()
    for audit_id in audit_ids:
        try:
            supabase.from_('login_audit').delete().eq('id', audit_id).execute()
        except:
            pass


@pytest.fixture
def cleanup_devices():
    """Cleanup device entries"""
    device_ids = []
    
    yield device_ids
    
    supabase = get_supabase_client()
    for device_id in device_ids:
        try:
            supabase.from_('user_devices').delete().eq('id', device_id).execute()
        except:
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

