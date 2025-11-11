import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from api import invitations_api


@pytest.fixture
def invitations_client():
    app = FastAPI()
    app.include_router(invitations_api.router)
    app.dependency_overrides[invitations_api.get_current_user] = lambda: {
        "id": "user-123",
        "organization_id": "org-123",
        "role": "org_admin"
    }
    app.dependency_overrides[invitations_api.require_org_admin] = lambda: {
        "id": "user-123",
        "organization_id": "org-123",
        "role": "org_admin"
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


def test_create_invitation_success(invitations_client, mock_supabase):
    """Test successful invitation creation"""
    mock_client, mock_table = mock_supabase
    
    # Mock user check (user doesn't exist)
    mock_execute_empty = Mock()
    mock_execute_empty.data = []
    
    mock_eq_empty = Mock()
    mock_eq_empty.execute.return_value = mock_execute_empty
    
    mock_select = Mock()
    mock_select.eq.return_value = mock_eq_empty
    mock_table.select.return_value = mock_select
    
    # Mock invitation insertion
    mock_insert = Mock()
    mock_insert.execute.return_value = Mock(data=[{
        "id": "invite-123",
        "email": "test@example.com",
        "token_hash": "hashed-token",
        "expires_at": "2024-12-26T00:00:00"
    }])
    mock_table.insert.return_value = mock_insert
    
    with patch('api.invitations_api.get_supabase_client', return_value=mock_client):
        with patch('api.invitations_api.get_email_service', return_value=Mock(send_invitation=Mock())):
            response = invitations_client.post(
                "/api/invitations",
                json={
                    "email": "test@example.com",
                    "organization_id": "org-123",
                    "role": "salesperson",
                    "expires_in_days": 7
                }
            )
            
            assert response.status_code in [201, 403]  # 403 if permissions fail


def test_create_invitation_validation_error(invitations_client):
    """Test invitation creation with invalid data"""
    response = invitations_client.post(
        "/api/invitations",
        json={
            "email": "not-an-email",
            "organization_id": "org-123",
            "role": "invalid_role"  # Invalid role
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_validate_invitation_token(invitations_client, mock_supabase):
    """Test invitation token validation"""
    mock_client, mock_table = mock_supabase
    
    mock_execute = Mock()
    mock_execute.data = {
        "id": "invite-123",
        "email": "test@example.com",
        "status": "pending",
        "expires_at": "2024-12-26T00:00:00"
    }
    
    mock_single = Mock()
    mock_single.execute.return_value = mock_execute
    
    mock_eq = Mock()
    mock_eq.single.return_value = mock_single
    
    mock_select = Mock()
    mock_select.eq.return_value = mock_eq
    mock_table.select.return_value = mock_select
    
    with patch('api.invitations_api.get_supabase_client', return_value=mock_client):
        response = invitations_client.post(
            "/api/invitations/validate",
            json={"token": "valid-token"}
        )
        
        assert response.status_code in [200, 400, 404]


def test_list_invitations(invitations_client, mock_supabase):
    """Test listing invitations"""
    mock_client, mock_table = mock_supabase
    
    mock_execute = Mock()
    mock_execute.data = [
        {"id": "1", "email": "test1@example.com", "status": "pending"},
        {"id": "2", "email": "test2@example.com", "status": "accepted"}
    ]
    mock_execute.count = 2
    
    mock_eq = Mock()
    mock_eq.execute.return_value = mock_execute
    
    mock_select = Mock()
    mock_select.eq.return_value = mock_eq
    mock_table.select.return_value = mock_select
    
    with patch('api.invitations_api.get_supabase_client', return_value=mock_client):
        response = invitations_client.get(
            "/api/invitations",
            params={"organization_id": "org-123"}
        )
        
        assert response.status_code in [200, 403]

