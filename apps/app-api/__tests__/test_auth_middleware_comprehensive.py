"""
Comprehensive tests for Authentication Middleware
Target: 0% → 95% coverage
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from middleware.auth import (
    get_current_user, require_org_admin, require_system_admin, verify_org_access
)


class TestGetCurrentUser:
    """Test get_current_user function"""
    
    @pytest.fixture
    def mock_credentials(self):
        """Create mock credentials"""
        creds = Mock(spec=HTTPAuthorizationCredentials)
        creds.credentials = "test-token"
        return creds
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Create mock Supabase client"""
        mock_client = Mock()
        mock_auth = Mock()
        mock_client.auth = mock_auth
        return mock_client, mock_auth
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_credentials, mock_supabase_client):
        """Test successful authentication"""
        mock_client, mock_auth = mock_supabase_client
        
        # Mock auth.get_user
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_auth_response = Mock()
        mock_auth_response.user = mock_user
        mock_auth.get_user.return_value = mock_auth_response
        
        # Mock profile query
        profile_result = Mock()
        profile_result.data = [{
            'organization_id': 'org-123',
            'salesperson_name': 'John Doe',
            'created_at': '2024-01-01T00:00:00'
        }]
        
        # Mock role query
        role_result = Mock()
        role_result.data = [{'role': 'salesperson'}]
        
        # Mock assignments query
        assignments_result = Mock()
        assignments_result.data = [{'center_id': 'center-1'}, {'center_id': 'center-2'}]
        
        # Setup table mock chain
        def table_side_effect(table_name):
            mock_table = Mock()
            mock_select = Mock()
            mock_eq = Mock()
            mock_order = Mock()
            mock_limit = Mock()
            
            if table_name == "profiles":
                mock_limit.execute = Mock(return_value=profile_result)
                mock_order.limit = Mock(return_value=mock_limit)
                mock_eq.order = Mock(return_value=mock_order)
                mock_select.eq = Mock(return_value=mock_eq)
            elif table_name == "user_roles":
                mock_limit.execute = Mock(return_value=role_result)
                mock_eq.limit = Mock(return_value=mock_limit)
                mock_select.eq = Mock(return_value=mock_eq)
            elif table_name == "user_assignments":
                mock_eq.execute = Mock(return_value=assignments_result)
                mock_select.eq = Mock(return_value=mock_eq)
            
            mock_table.select = Mock(return_value=mock_select)
            return mock_table
        
        mock_client.table = Mock(side_effect=table_side_effect)
        
        with patch('middleware.auth.get_supabase_client', return_value=mock_client):
            user = await get_current_user(mock_credentials)
            
            assert user['user_id'] == "user-123"
            assert user['email'] == "test@example.com"
            assert user['role'] == "salesperson"
            assert user['organization_id'] == "org-123"
            assert user['center_ids'] == ['center-1', 'center-2']
            assert user['full_name'] == 'John Doe'
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_supabase_client(self, mock_credentials):
        """Test when Supabase client is None"""
        with patch('middleware.auth.get_supabase_client', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials)
            
            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "Authentication service unavailable" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_credentials, mock_supabase_client):
        """Test with invalid token"""
        mock_client, mock_auth = mock_supabase_client
        
        # Mock auth.get_user returns None user
        mock_auth_response = Mock()
        mock_auth_response.user = None
        mock_auth.get_user.return_value = mock_auth_response
        
        with patch('middleware.auth.get_supabase_client', return_value=mock_client):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid authentication credentials" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_profile(self, mock_credentials, mock_supabase_client):
        """Test when user has no profile"""
        mock_client, mock_auth = mock_supabase_client
        
        # Mock auth.get_user
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_auth_response = Mock()
        mock_auth_response.user = mock_user
        mock_auth.get_user.return_value = mock_auth_response
        
        # Mock empty profile
        profile_result = Mock()
        profile_result.data = []
        
        # Mock role query
        role_result = Mock()
        role_result.data = [{'role': 'salesperson'}]
        
        # Mock empty assignments
        assignments_result = Mock()
        assignments_result.data = []
        
        def table_side_effect(table_name):
            mock_table = Mock()
            mock_select = Mock()
            mock_eq = Mock()
            mock_order = Mock()
            mock_limit = Mock()
            
            if table_name == "profiles":
                mock_limit.execute = Mock(return_value=profile_result)
                mock_order.limit = Mock(return_value=mock_limit)
                mock_eq.order = Mock(return_value=mock_order)
                mock_select.eq = Mock(return_value=mock_eq)
            elif table_name == "user_roles":
                mock_limit.execute = Mock(return_value=role_result)
                mock_eq.limit = Mock(return_value=mock_limit)
                mock_select.eq = Mock(return_value=mock_eq)
            elif table_name == "user_assignments":
                mock_eq.execute = Mock(return_value=assignments_result)
                mock_select.eq = Mock(return_value=mock_eq)
            
            mock_table.select = Mock(return_value=mock_select)
            return mock_table
        
        mock_client.table = Mock(side_effect=table_side_effect)
        
        with patch('middleware.auth.get_supabase_client', return_value=mock_client):
            user = await get_current_user(mock_credentials)
            
            assert user['user_id'] == "user-123"
            assert user['organization_id'] is None
            assert user['center_ids'] == []
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_role(self, mock_credentials, mock_supabase_client):
        """Test when user has no role (defaults to salesperson)"""
        mock_client, mock_auth = mock_supabase_client
        
        # Mock auth.get_user
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_auth_response = Mock()
        mock_auth_response.user = mock_user
        mock_auth.get_user.return_value = mock_auth_response
        
        # Mock profile
        profile_result = Mock()
        profile_result.data = [{'organization_id': 'org-123'}]
        
        # Mock empty role
        role_result = Mock()
        role_result.data = []
        
        # Mock empty assignments
        assignments_result = Mock()
        assignments_result.data = []
        
        def table_side_effect(table_name):
            mock_table = Mock()
            mock_select = Mock()
            mock_eq = Mock()
            mock_order = Mock()
            mock_limit = Mock()
            
            if table_name == "profiles":
                mock_limit.execute = Mock(return_value=profile_result)
                mock_order.limit = Mock(return_value=mock_limit)
                mock_eq.order = Mock(return_value=mock_order)
                mock_select.eq = Mock(return_value=mock_eq)
            elif table_name == "user_roles":
                mock_limit.execute = Mock(return_value=role_result)
                mock_eq.limit = Mock(return_value=mock_limit)
                mock_select.eq = Mock(return_value=mock_eq)
            elif table_name == "user_assignments":
                mock_eq.execute = Mock(return_value=assignments_result)
                mock_select.eq = Mock(return_value=mock_eq)
            
            mock_table.select = Mock(return_value=mock_select)
            return mock_table
        
        mock_client.table = Mock(side_effect=table_side_effect)
        
        with patch('middleware.auth.get_supabase_client', return_value=mock_client):
            user = await get_current_user(mock_credentials)
            
            assert user['role'] == 'salesperson'  # Default role
    
    @pytest.mark.asyncio
    async def test_get_current_user_exception(self, mock_credentials, mock_supabase_client):
        """Test exception handling"""
        mock_client, mock_auth = mock_supabase_client
        
        # Mock exception
        mock_auth.get_user.side_effect = Exception("Database error")
        
        with patch('middleware.auth.get_supabase_client', return_value=mock_client):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestRequireOrgAdmin:
    """Test require_org_admin function"""
    
    @pytest.mark.asyncio
    async def test_require_org_admin_success_org_admin(self):
        """Test with org_admin role"""
        mock_user = {'role': 'org_admin', 'user_id': 'user-123'}
        result = await require_org_admin(mock_user)
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_require_org_admin_success_system_admin(self):
        """Test with system_admin role"""
        mock_user = {'role': 'system_admin', 'user_id': 'user-123'}
        result = await require_org_admin(mock_user)
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_require_org_admin_failure(self):
        """Test with insufficient role"""
        mock_user = {'role': 'salesperson', 'user_id': 'user-123'}
        with pytest.raises(HTTPException) as exc_info:
            await require_org_admin(mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Org admin access required" in str(exc_info.value.detail)


class TestRequireSystemAdmin:
    """Test require_system_admin function"""
    
    @pytest.mark.asyncio
    async def test_require_system_admin_success(self):
        """Test with system_admin role"""
        mock_user = {'role': 'system_admin', 'user_id': 'user-123'}
        result = await require_system_admin(mock_user)
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_require_system_admin_failure(self):
        """Test with insufficient role"""
        mock_user = {'role': 'org_admin', 'user_id': 'user-123'}
        with pytest.raises(HTTPException) as exc_info:
            await require_system_admin(mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "System admin access required" in str(exc_info.value.detail)


class TestVerifyOrgAccess:
    """Test verify_org_access function"""
    
    @pytest.mark.asyncio
    async def test_verify_org_access_same_org(self):
        """Test with matching organization_id"""
        mock_user = {'role': 'salesperson', 'organization_id': 'org-123'}
        result = await verify_org_access('org-123', mock_user)
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_verify_org_access_system_admin(self):
        """Test with system_admin (can access any org)"""
        mock_user = {'role': 'system_admin', 'organization_id': 'org-1'}
        result = await verify_org_access('org-999', mock_user)
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_verify_org_access_denied(self):
        """Test with different organization_id"""
        mock_user = {'role': 'salesperson', 'organization_id': 'org-123'}
        with pytest.raises(HTTPException) as exc_info:
            await verify_org_access('org-999', mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Access denied" in str(exc_info.value.detail)

