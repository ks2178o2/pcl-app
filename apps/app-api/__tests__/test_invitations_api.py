"""
Invitations API Tests - Comprehensive test coverage using dependency_overrides
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_supabase_client():
    """Create a comprehensive mock Supabase client"""
    mock_client = Mock()
    
    # Mock query chain for profiles lookup
    mock_profile_query = Mock()
    mock_profile_query.select.return_value = mock_profile_query
    mock_profile_query.eq.return_value = mock_profile_query
    mock_profile_query.single.return_value = Mock(
        execute=Mock(return_value=Mock(data={'organization_id': 'org-123'}))
    )
    
    # Mock query chain for user_invitations
    mock_invite_query = Mock()
    mock_invite_query.select.return_value = mock_invite_query
    mock_invite_query.eq.return_value = mock_invite_query
    
    # Mock insert query
    mock_insert_query = Mock()
    mock_insert_query.insert.return_value = Mock(
        execute=Mock(return_value=Mock(data=[{
            'id': 'inv-123',
            'email': 'newuser@example.com',
            'organization_id': 'org-123',
            'role': 'salesperson',
            'status': 'pending',
            'created_at': (datetime.utcnow() + timedelta(days=7)).isoformat()
        }]))
    )
    
    # Configure from_ to return different queries based on table
    def mock_from(table_name):
        if table_name == 'profiles':
            return mock_profile_query
        elif table_name == 'user_invitations':
            # Return insert for insert operations, select for select operations
            return mock_insert_query
        return mock_profile_query
    
    mock_client.from_ = mock_from
    
    # Mock auth.admin.list_users
    mock_client.auth = Mock()
    mock_client.auth.admin = Mock()
    mock_client.auth.admin.list_users.return_value.execute.return_value = Mock(users=[])
    
    # Mock auth.admin.create_user
    mock_client.auth.admin.create_user = Mock(return_value=Mock(
        user=Mock(id='new-user-123')
    ))
    
    return mock_client


@pytest.fixture
def mock_current_user():
    """Mock current authenticated user"""
    return {
        'id': 'user-123',
        'user_id': 'user-123',
        'email': 'admin@example.com',
        'role': 'org_admin',
        'organization_id': 'org-123'
    }


@pytest.fixture
def app(mock_supabase_client, mock_current_user):
    """Create FastAPI app with mocked dependencies"""
    from api import invitations_api
    import importlib
    importlib.reload(invitations_api)
    
    app = FastAPI()
    app.include_router(invitations_api.router)
    
    # Override dependencies
    app.dependency_overrides[invitations_api.get_supabase_client] = lambda: mock_supabase_client
    app.dependency_overrides[invitations_api.require_org_admin_dependency] = lambda: mock_current_user
    app.dependency_overrides[invitations_api.get_current_user] = lambda: mock_current_user
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


class TestInvitationsAPI:
    """Test suite for Invitations API"""

    def test_create_invitation_success(self, client, mock_supabase_client, mock_current_user):
        """Test successful invitation creation"""
        # Create invitation
        response = client.post('/api/invitations/', json={
            'email': 'newuser@example.com',
            'organization_id': 'org-123',
            'role': 'salesperson',
            'expires_in_days': 7
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data['email'] == 'newuser@example.com'
        assert 'invitation_id' in data
        assert data['status'] == 'pending'

    def test_create_invitation_existing_user(self, client, mock_supabase_client, mock_current_user):
        """Test invitation creation when user already exists"""
        # Mock existing user
        mock_supabase_client.auth.admin.list_users.return_value.execute.return_value = Mock(
            users=[Mock(email='existing@example.com')]
        )
        
        response = client.post('/api/invitations/', json={
            'email': 'existing@example.com',
            'organization_id': 'org-123',
            'role': 'salesperson'
        })
        
        assert response.status_code == 409
        assert 'already exists' in response.json()['detail']

    def test_create_invitation_wrong_org(self, client, mock_supabase_client, mock_current_user):
        """Test invitation creation to wrong organization"""
        # Mock different org for user
        mock_profile_query = Mock()
        mock_profile_query.select.return_value = mock_profile_query
        mock_profile_query.eq.return_value = mock_profile_query
        mock_profile_query.single.return_value = Mock(
            execute=Mock(return_value=Mock(data={'organization_id': 'org-999'}))
        )
        
        def mock_from_wrong_org(table_name):
            if table_name == 'profiles':
                return mock_profile_query
            return mock_supabase_client.from_._mock_return_value
        
        client.app.dependency_overrides = {
            **client.app.dependency_overrides,
            'api.invitations_api.get_supabase_client': lambda: mock_supabase_client
        }
        mock_supabase_client.from_ = mock_from_wrong_org
        
        response = client.post('/api/invitations/', json={
            'email': 'newuser@example.com',
            'organization_id': 'org-123',
            'role': 'salesperson'
        })
        
        assert response.status_code == 403
        assert 'own organization' in response.json()['detail']

    def test_list_invitations_success(self, client, mock_supabase_client, mock_current_user):
        """Test listing invitations"""
        # Mock invitations list query
        mock_list_query = Mock()
        mock_list_query.select.return_value = mock_list_query
        mock_list_query.eq.return_value = mock_list_query
        mock_list_query.order.return_value = mock_list_query
        mock_list_query.range.return_value = Mock(
            execute=Mock(return_value=Mock(data=[
                {
                    'id': 'inv-1',
                    'email': 'user1@example.com',
                    'organization_id': 'org-123',
                    'status': 'pending',
                    'role': 'salesperson',
                    'created_at': datetime.utcnow().isoformat()
                }
            ], count=1))
        )
        
        mock_supabase_client.from_ = lambda table: mock_list_query if table == 'user_invitations' else mock_list_query
        
        response = client.get('/api/invitations/')
        
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1
        assert len(data['invitations']) == 1

    def test_validate_token_success(self, client, mock_supabase_client):
        """Test validating valid invitation token"""
        # Mock token validation query
        mock_validate_query = Mock()
        mock_validate_query.select.return_value = mock_validate_query
        mock_validate_query.eq.return_value = mock_validate_query
        mock_validate_query.single.return_value = Mock(
            execute=Mock(return_value=Mock(data={
                'id': 'inv-123',
                'email': 'user@example.com',
                'organization_id': 'org-123',
                'role': 'salesperson',
                'status': 'pending',
                'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                'token': 'hashed_token'
            }))
        )
        
        mock_supabase_client.from_ = lambda table: mock_validate_query
        
        response = client.post('/api/invitations/validate-token', json={'token': 'valid_token_here'})
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['email'] == 'user@example.com'

    def test_cancel_invitation_success(self, client, mock_supabase_client, mock_current_user):
        """Test cancelling invitation"""
        # Mock update query
        mock_update_query = Mock()
        mock_update_query.update.return_value = Mock(
            execute=Mock(return_value=Mock(data=[{'id': 'inv-123'}]))
        )
        
        mock_supabase_client.from_ = lambda table: mock_update_query
        
        response = client.delete('/api/invitations/inv-123')
        
        assert response.status_code == 204


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
