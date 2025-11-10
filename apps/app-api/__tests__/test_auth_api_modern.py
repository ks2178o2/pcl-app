import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from api import auth_api


@pytest.fixture
def auth_client():
    app = FastAPI()
    app.include_router(auth_api.router)
    app.dependency_overrides[auth_api.get_current_user] = lambda: {"id": "user-123", "organization_id": "org-123"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_supabase():
    mock_client = Mock()
    mock_table = Mock()
    mock_client.from_.return_value = mock_table
    return mock_client, mock_table


def test_log_login_attempt_success(auth_client, mock_supabase):
    """Test successful login audit logging"""
    mock_client, mock_table = mock_supabase
    
    mock_insert = Mock()
    mock_insert.execute.return_value = Mock(data=[{"id": "audit-123"}])
    mock_table.insert.return_value = mock_insert
    
    mock_update = Mock()
    mock_update.eq.return_value = Mock(execute=Mock())
    mock_table.update.return_value = mock_update
    
    with patch('api.auth_api.get_supabase_client', return_value=mock_client):
        response = auth_client.post(
            "/api/auth/login-audit",
            json={
                "user_id": "user-123",
                "organization_id": "org-123",
                "login_method": "password",
                "status": "success",
                "ip_address": "127.0.0.1",
                "user_agent": "test-agent"
            }
        )
        
        assert response.status_code == 201
        assert response.json()["success"] is True
        assert "audit_id" in response.json()


def test_log_login_attempt_validation_error(auth_client):
    """Test login audit with invalid data"""
    response = auth_client.post(
        "/api/auth/login-audit",
        json={
            "user_id": "user-123",
            "login_method": "invalid_method",  # Invalid
            "status": "success"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_get_login_history_success(auth_client, mock_supabase):
    """Test retrieving login history"""
    mock_client, mock_table = mock_supabase
    
    mock_limit = Mock()
    mock_limit.execute.return_value = Mock(
        data=[
            {"id": "1", "user_id": "user-123", "login_at": "2024-01-01T00:00:00"},
            {"id": "2", "user_id": "user-123", "login_at": "2024-01-02T00:00:00"}
        ],
        count=2
    )
    
    mock_order = Mock()
    mock_order.limit.return_value = mock_limit
    
    mock_eq = Mock()
    mock_eq.order.return_value = mock_order
    
    mock_select = Mock()
    mock_select.eq.return_value = mock_eq
    mock_table.select.return_value = mock_select
    
    with patch('api.auth_api.get_supabase_client', return_value=mock_client):
        response = auth_client.get(
            "/api/auth/login-history",
            params={"user_id": "user-123", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["logins"]) == 2


def test_get_login_history_no_user(auth_client):
    """Test login history without user_id"""
    response = auth_client.get("/api/auth/login-history")
    assert response.status_code == 422  # Missing required parameter

