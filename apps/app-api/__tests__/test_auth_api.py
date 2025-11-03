"""
Auth API Tests - Login audit and JWT management
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from api.auth_api import router as auth_router
    AUTH_MODULE_AVAILABLE = True
except ImportError as e:
    AUTH_MODULE_AVAILABLE = False
    pytest.skip(f"Auth API module not available: {e}", allow_module_level=True)


@pytest.fixture
def app():
    """Create FastAPI app with routers"""
    app = FastAPI()
    app.include_router(auth_router)
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
        'email': 'user@example.com',
        'role': 'salesperson'
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
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.execute.return_value = Mock(data=[], count=0)
    mock_client.from_.return_value = mock_query
    
    # Mock auth methods
    mock_client.auth = Mock()
    mock_client.auth.refresh_session = Mock()
    mock_client.auth.sign_out = Mock()
    
    return mock_client


class TestAuthAPI:
    """Test suite for Auth API"""

    @patch('api.auth_api.get_supabase_client')
    def test_log_login_attempt_success(self, mock_get_client, client, mock_supabase_client):
        """Test logging successful login attempt"""
        mock_get_client.return_value = mock_supabase_client
        
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{
            'id': 'audit-123',
            'user_id': 'user-123',
            'login_at': datetime.utcnow().isoformat(),
            'status': 'success'
        }])
        
        response = client.post('/api/auth/login-audit', json={
            'user_id': 'user-123',
            'organization_id': 'org-123',
            'ip_address': '192.168.1.1',
            'user_agent': 'Test Browser',
            'login_method': 'password',
            'status': 'success'
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert data['audit_id'] == 'audit-123'

    @patch('api.auth_api.get_supabase_client')
    def test_get_login_history_success(self, mock_get_client, client, mock_supabase_client, mock_current_user):
        """Test getting login history"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock get_current_user
        import api.auth_api
        api.auth_api.get_current_user = lambda: mock_current_user
        
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[
            {
                'id': 'log-1',
                'user_id': 'user-123',
                'ip_address': '192.168.1.1',
                'login_method': 'password',
                'status': 'success',
                'login_at': datetime.utcnow().isoformat()
            },
            {
                'id': 'log-2',
                'user_id': 'user-123',
                'ip_address': '192.168.1.2',
                'login_method': 'oauth_google',
                'status': 'success',
                'login_at': datetime.utcnow().isoformat()
            }
        ])
        
        # Mock count query
        mock_client_copy = Mock()
        mock_client_copy.from_.return_value.select.return_value.eq.return_value.execute.return_value = Mock(count=2)
        mock_supabase_client.__copy__ = lambda: mock_client_copy
        
        # Need to patch execute to return different results for count vs data
        def mock_execute():
            result = Mock()
            result.data = [
                {
                    'id': 'log-1',
                    'user_id': 'user-123',
                    'ip_address': '192.168.1.1',
                    'login_method': 'password',
                    'status': 'success',
                    'login_at': datetime.utcnow().isoformat()
                }
            ]
            result.count = 2
            return result
        
        mock_query.execute = mock_execute
        
        response = client.get('/api/auth/login-history', headers={'Authorization': 'Bearer fake-token'})
        
        assert response.status_code == 200
        data = response.json()
        assert 'logins' in data
        assert 'total' in data

    @patch('api.auth_api.get_supabase_client')
    def test_refresh_token_success(self, mock_get_client, client, mock_supabase_client):
        """Test refreshing JWT token"""
        mock_get_client.return_value = mock_supabase_client
        
        mock_session = Mock()
        mock_session.session = Mock()
        mock_session.session.access_token = 'new_access_token'
        mock_session.session.refresh_token = 'new_refresh_token'
        mock_session.session.expires_in = 3600
        
        mock_supabase_client.auth.refresh_session.return_value = mock_session
        
        response = client.post('/api/auth/refresh', json={
            'refresh_token': 'valid_refresh_token'
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['access_token'] == 'new_access_token'
        assert data['refresh_token'] == 'new_refresh_token'
        assert data['expires_in'] == 3600

    @patch('api.auth_api.get_supabase_client')
    def test_refresh_token_invalid(self, mock_get_client, client, mock_supabase_client):
        """Test refreshing with invalid token"""
        mock_get_client.return_value = mock_supabase_client
        
        mock_session = Mock()
        mock_session.session = None
        
        mock_supabase_client.auth.refresh_session.return_value = mock_session
        
        response = client.post('/api/auth/refresh', json={
            'refresh_token': 'invalid_token'
        })
        
        assert response.status_code == 401
        assert 'Invalid' in response.json()['detail']

    @patch('api.auth_api.get_supabase_client')
    def test_revoke_token_success(self, mock_get_client, client, mock_supabase_client):
        """Test revoking JWT token"""
        mock_get_client.return_value = mock_supabase_client
        
        mock_supabase_client.auth.sign_out.return_value = None
        
        response = client.post('/api/auth/revoke', json={
            'token': 'token_to_revoke'
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

    @patch('api.auth_api.get_supabase_client')
    def test_get_current_user_info(self, mock_get_client, client, mock_supabase_client, mock_current_user):
        """Test getting current user info"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock get_current_user
        import api.auth_api
        api.auth_api.get_current_user = lambda: mock_current_user
        
        response = client.get('/api/auth/me', headers={'Authorization': 'Bearer fake-token'})
        
        assert response.status_code == 200
        data = response.json()
        assert data['user_id'] == 'user-123'
        assert data['email'] == 'user@example.com'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

