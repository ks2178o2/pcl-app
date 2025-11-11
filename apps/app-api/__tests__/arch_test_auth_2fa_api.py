"""
2FA API Tests - Comprehensive test coverage
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from api.auth_2fa_api import router as auth_2fa_router
    AUTH_2FA_MODULE_AVAILABLE = True
except ImportError as e:
    AUTH_2FA_MODULE_AVAILABLE = False
    pytest.skip(f"Auth 2FA API module not available: {e}", allow_module_level=True)


@pytest.fixture
def app():
    """Create FastAPI app with routers"""
    app = FastAPI()
    app.include_router(auth_2fa_router)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock current authenticated user"""
    return {
        'user_id': 'user-123',
        'email': 'user@example.com'
    }


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    mock_client = Mock()
    mock_query = Mock()
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.insert.return_value = mock_query
    mock_query.update.return_value = mock_query
    mock_query.delete.return_value = mock_query
    mock_query.single.return_value = mock_query
    mock_query.execute.return_value = Mock(data=[], count=0)
    mock_client.from_.return_value = mock_query
    return mock_client


class TestAuth2FAAPI:
    """Test suite for 2FA API"""

    @patch('api.auth_2fa_api.get_supabase_client')
    def test_setup_2fa_success(self, mock_get_client, client, mock_supabase_client, mock_current_user):
        """Test successful 2FA setup"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock get_current_user
        import api.auth_2fa_api
        api.auth_2fa_api.get_current_user = lambda: mock_current_user
        
        # Mock profile check - 2FA not enabled
        mock_query = mock_supabase_client.from_.return_value
        mock_query.single.return_value.execute.return_value = Mock(data={
            'two_factor_enabled': False
        })
        
        # Mock update operations
        mock_query.execute.return_value = Mock(data=[{'id': 'user-123'}])
        
        response = client.post('/api/auth/2fa/setup', headers={'Authorization': 'Bearer fake-token'})
        
        assert response.status_code == 200
        data = response.json()
        assert 'qr_code' in data
        assert 'secret' in data
        assert 'backup_codes' in data
        assert len(data['backup_codes']) == 10

    @patch('api.auth_2fa_api.get_supabase_client')
    def test_setup_2fa_already_enabled(self, mock_get_client, client, mock_supabase_client, mock_current_user):
        """Test setup when 2FA already enabled"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock get_current_user
        import api.auth_2fa_api
        api.auth_2fa_api.get_current_user = lambda: mock_current_user
        
        # Mock profile check - 2FA enabled
        mock_query = mock_supabase_client.from_.return_value
        mock_query.single.return_value.execute.return_value = Mock(data={
            'two_factor_enabled': True
        })
        
        response = client.post('/api/auth/2fa/setup', headers={'Authorization': 'Bearer fake-token'})
        
        assert response.status_code == 400
        assert 'already enabled' in response.json()['detail']

    @patch('api.auth_2fa_api.get_supabase_client')
    def test_verify_2fa_code_success(self, mock_get_client, client, mock_supabase_client, mock_current_user):
        """Test verifying 2FA code"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock get_current_user
        import api.auth_2fa_api
        api.auth_2fa_api.get_current_user = lambda: mock_current_user
        
        # Mock profile with secret
        mock_query = mock_supabase_client.from_.return_value
        mock_query.single.return_value.execute.return_value = Mock(data={
            'two_factor_secret': 'JBSWY3DPEHPK3PXP'
        })
        
        # Mock pyotp verify
        with patch('api.auth_2fa_api.verify_totp_code', return_value=True):
            response = client.post('/api/auth/2fa/verify', 
                json={'code': '123456'},
                headers={'Authorization': 'Bearer fake-token'})
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True

    @patch('api.auth_2fa_api.get_supabase_client')
    def test_verify_2fa_code_invalid(self, mock_get_client, client, mock_supabase_client, mock_current_user):
        """Test verifying invalid 2FA code"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock get_current_user
        import api.auth_2fa_api
        api.auth_2fa_api.get_current_user = lambda: mock_current_user
        
        # Mock profile with secret
        mock_query = mock_supabase_client.from_.return_value
        mock_query.single.return_value.execute.return_value = Mock(data={
            'two_factor_secret': 'JBSWY3DPEHPK3PXP'
        })
        
        # Mock pyotp verify
        with patch('api.auth_2fa_api.verify_totp_code', return_value=False):
            response = client.post('/api/auth/2fa/verify',
                json={'code': '000000'},
                headers={'Authorization': 'Bearer fake-token'})
            
            assert response.status_code == 401
            assert 'Invalid' in response.json()['detail']

    @patch('api.auth_2fa_api.get_supabase_client')
    def test_enable_2fa_success(self, mock_get_client, client, mock_supabase_client, mock_current_user):
        """Test enabling 2FA"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock get_current_user
        import api.auth_2fa_api
        api.auth_2fa_api.get_current_user = lambda: mock_current_user
        
        # Mock profile with secret
        mock_query = mock_supabase_client.from_.return_value
        mock_query.single.return_value.execute.return_value = Mock(data={
            'two_factor_secret': 'JBSWY3DPEHPK3PXP'
        })
        mock_query.update.return_value.execute.return_value = Mock(data=[{'id': 'user-123'}])
        
        # Mock pyotp verify
        with patch('api.auth_2fa_api.verify_totp_code', return_value=True):
            response = client.post('/api/auth/2fa/enable',
                json={'code': '123456'},
                headers={'Authorization': 'Bearer fake-token'})
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True

    @patch('api.auth_2fa_api.get_supabase_client')
    def test_disable_2fa_success(self, mock_get_client, client, mock_supabase_client, mock_current_user):
        """Test disabling 2FA"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock get_current_user
        import api.auth_2fa_api
        api.auth_2fa_api.get_current_user = lambda: mock_current_user
        
        # Mock profile with 2FA enabled
        mock_query = mock_supabase_client.from_.return_value
        mock_query.single.return_value.execute.return_value = Mock(data={
            'two_factor_enabled': True,
            'two_factor_secret': 'JBSWY3DPEHPK3PXP'
        })
        mock_query.update.return_value.execute.return_value = Mock(data=[{'id': 'user-123'}])
        
        # Mock pyotp verify
        with patch('api.auth_2fa_api.verify_totp_code', return_value=True):
            response = client.post('/api/auth/2fa/disable',
                json={'password': 'testpass'},
                headers={'Authorization': 'Bearer fake-token'})
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True

    @patch('api.auth_2fa_api.get_supabase_client')
    def test_list_devices_success(self, mock_get_client, client, mock_supabase_client, mock_current_user):
        """Test listing devices"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock get_current_user
        import api.auth_2fa_api
        api.auth_2fa_api.get_current_user = lambda: mock_current_user
        
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[
            {
                'id': 'dev-1',
                'user_id': 'user-123',
                'device_name': 'iPhone 14',
                'device_id': 'fingerprint-123',
                'is_primary': True,
                'last_used_at': '2025-10-31T12:00:00Z'
            },
            {
                'id': 'dev-2',
                'user_id': 'user-123',
                'device_name': 'MacBook Pro',
                'device_id': 'fingerprint-456',
                'is_primary': False,
                'last_used_at': '2025-10-30T12:00:00Z'
            }
        ])
        
        response = client.get('/api/auth/2fa/devices', headers={'Authorization': 'Bearer fake-token'})
        
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        assert len(data['devices']) == 2
        assert 'two_factor_code_hash' not in data['devices'][0]  # Should be removed

    @patch('api.auth_2fa_api.get_supabase_client')
    def test_remove_device_success(self, mock_get_client, client, mock_supabase_client, mock_current_user):
        """Test removing device"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock get_current_user
        import api.auth_2fa_api
        api.auth_2fa_api.get_current_user = lambda: mock_current_user
        
        mock_query = mock_supabase_client.from_.return_value
        mock_query.delete.return_value.execute.return_value = Mock(data=[{'id': 'dev-1'}])
        
        response = client.delete('/api/auth/2fa/devices/dev-1', headers={'Authorization': 'Bearer fake-token'})
        
        assert response.status_code == 204

    @patch('api.auth_2fa_api.get_supabase_client')
    def test_get_2fa_status_enabled(self, mock_get_client, client, mock_supabase_client, mock_current_user):
        """Test getting 2FA status when enabled"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock get_current_user
        import api.auth_2fa_api
        api.auth_2fa_api.get_current_user = lambda: mock_current_user
        
        mock_query = mock_supabase_client.from_.return_value
        mock_query.single.return_value.execute.return_value = Mock(data={
            'two_factor_enabled': True
        })
        
        response = client.get('/api/auth/2fa/status', headers={'Authorization': 'Bearer fake-token'})
        
        assert response.status_code == 200
        data = response.json()
        assert data['enabled'] is True
        assert data['setup_required'] is False

    @patch('api.auth_2fa_api.get_supabase_client')
    def test_get_2fa_status_disabled(self, mock_get_client, client, mock_supabase_client, mock_current_user):
        """Test getting 2FA status when disabled"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock get_current_user
        import api.auth_2fa_api
        api.auth_2fa_api.get_current_user = lambda: mock_current_user
        
        mock_query = mock_supabase_client.from_.return_value
        mock_query.single.return_value.execute.return_value = Mock(data={
            'two_factor_enabled': False
        })
        
        response = client.get('/api/auth/2fa/status', headers={'Authorization': 'Bearer fake-token'})
        
        assert response.status_code == 200
        data = response.json()
        assert data['enabled'] is False
        assert data['setup_required'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

