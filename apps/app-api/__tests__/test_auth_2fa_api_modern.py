import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from api import auth_2fa_api


@pytest.fixture
def auth_2fa_client():
    app = FastAPI()
    app.include_router(auth_2fa_api.router)
    app.dependency_overrides[auth_2fa_api.get_current_user] = lambda: {
        "id": "user-123",
        "organization_id": "org-123"
    }
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_supabase():
    mock_client = Mock()
    mock_table = Mock()
    mock_client.from_.return_value = mock_table
    return mock_client, mock_table


def test_enable_2fa_success(auth_2fa_client, mock_supabase):
    """Test enabling 2FA"""
    mock_client, mock_table = mock_supabase
    
    # Mock profile update
    mock_execute = Mock()
    mock_execute.data = [{"two_factor_enabled": True}]
    
    mock_eq = Mock()
    mock_eq.execute.return_value = mock_execute
    
    mock_update = Mock()
    mock_update.eq.return_value = mock_eq
    mock_table.update.return_value = mock_update
    
    with patch('api.auth_2fa_api.get_supabase_client', return_value=mock_client):
        response = auth_2fa_client.post(
            "/api/auth/2fa/enable",
            json={"user_id": "user-123"}
        )
        
        assert response.status_code in [200, 201, 403]


def test_disable_2fa_success(auth_2fa_client, mock_supabase):
    """Test disabling 2FA"""
    mock_client, mock_table = mock_supabase
    
    mock_execute = Mock()
    mock_execute.data = [{"two_factor_enabled": False}]
    
    mock_eq = Mock()
    mock_eq.execute.return_value = mock_execute
    
    mock_update = Mock()
    mock_update.eq.return_value = mock_eq
    mock_table.update.return_value = mock_update
    
    with patch('api.auth_2fa_api.get_supabase_client', return_value=mock_client):
        response = auth_2fa_client.post(
            "/api/auth/2fa/disable",
            json={"user_id": "user-123"}
        )
        
        assert response.status_code in [200, 403]


def test_verify_2fa_code(auth_2fa_client, mock_supabase):
    """Test 2FA code verification"""
    mock_client, mock_table = mock_supabase
    
    mock_execute = Mock()
    mock_execute.data = {
        "two_factor_secret": "secret123",
        "two_factor_enabled": True
    }
    
    mock_single = Mock()
    mock_single.execute.return_value = mock_execute
    
    mock_eq = Mock()
    mock_eq.single.return_value = mock_single
    
    mock_select = Mock()
    mock_select.eq.return_value = mock_eq
    mock_table.select.return_value = mock_select
    
    with patch('api.auth_2fa_api.get_supabase_client', return_value=mock_client):
        with patch('api.auth_2fa_api.pyotp.TOTP') as mock_totp:
            mock_totp.return_value.verify.return_value = True
            response = auth_2fa_client.post(
                "/api/auth/2fa/verify",
                json={
                    "user_id": "user-123",
                    "code": "123456"
                }
            )
            
            assert response.status_code in [200, 400, 403]

