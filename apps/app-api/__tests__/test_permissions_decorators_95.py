# apps/app-api/__tests__/test_permissions_decorators_95.py
"""
Comprehensive decorator tests to push Permissions Middleware to 95%
Target: Lines 129-148, 152-172, 176-196, 200-221, 225, 229, 233, 237, 241
"""

import pytest
import asyncio
from unittest.mock import Mock
from middleware.permissions import (
    require_role, require_org_access, require_feature_enabled,
    require_any_role, require_system_admin, require_org_admin,
    require_manager_or_higher, require_salesperson_or_higher,
    require_admin_access, UserRole, PermissionError,
    OrganizationAccessError, FeatureAccessError
)
from test_utils_permissions import SupabasePermissionMockBuilder


# Sample async function to decorate
async def sample_function(user, organization_id=None):
    return {"success": True, "data": "test"}


class TestRequireRoleDecorator:
    """Test require_role decorator - lines 129-148"""
    
    @pytest.mark.asyncio
    async def test_require_role_with_request_user_attr(self):
        """Test decorator with user in args[0].user"""
        @require_role(UserRole.MANAGER)
        async def test_func(request):
            return await sample_function(request.user)
        
        request = Mock()
        request.user = {'role': 'manager'}
        
        result = await test_func(request)
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_role_with_kwargs_user(self):
        """Test decorator with user in kwargs"""
        @require_role(UserRole.MANAGER)
        async def test_func(user):
            return await sample_function(user)
        
        user_data = {'role': 'manager'}
        result = await test_func(user=user_data)
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_role_insufficient_role_raises_error(self):
        """Test decorator raises error when role insufficient"""
        @require_role(UserRole.MANAGER)
        async def test_func(request):
            return await sample_function(request.user)
        
        request = Mock()
        request.user = {'role': 'user'}  # Lower than manager
        
        with pytest.raises(PermissionError):
            await test_func(request)
    
    @pytest.mark.asyncio
    async def test_require_role_no_user_data_raises_error(self):
        """Test decorator raises error when no user data"""
        @require_role(UserRole.MANAGER)
        async def test_func(request):
            return await sample_function(request.user)
        
        request = Mock()
        # Don't set request.user
        
        with pytest.raises(PermissionError):
            await test_func(request)


class TestRequireOrgAccessDecorator:
    """Test require_org_access decorator - lines 152-172"""
    
    @pytest.mark.asyncio
    async def test_require_org_access_with_args(self):
        """Test decorator with user and org_id in args"""
        builder = SupabasePermissionMockBuilder()
        builder.setup_organizations([{'id': 'org-123'}])
        mock_supabase = builder.get_mock_client()
        
        # Create async function with the decorator
        async def test_func(request, supabase):
            return await sample_function(request.user)
        
        decorated_func = require_org_access(check_parent=False)(test_func)
        
        request = Mock()
        request.user = {'role': 'user', 'organization_id': 'org-123'}
        request.organization_id = 'org-123'
        
        # Mock can_access_organization to return True
        import middleware.permissions
        original_can_access = middleware.permissions.can_access_organization
        middleware.permissions.can_access_organization = Mock(return_value=True)
        
        try:
            result = await decorated_func(request, mock_supabase)
            assert result.get('success') is True
        finally:
            middleware.permissions.can_access_organization = original_can_access
    
    @pytest.mark.asyncio
    async def test_require_org_access_with_kwargs(self):
        """Test decorator with user and org_id in kwargs"""
        builder = SupabasePermissionMockBuilder()
        mock_supabase = builder.get_mock_client()
        
        @require_org_access(check_parent=False)
        async def test_func(**kwargs):
            return await sample_function(kwargs['user'])
        
        with pytest.mock.patch('middleware.permissions.can_access_organization', return_value=True):
            result = await test_func(user={'role': 'user', 'organization_id': 'org-123'},
                                    organization_id='org-123')
            assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_org_access_denies_access_raises_error(self):
        """Test decorator raises error when access denied"""
        builder = SupabasePermissionMockBuilder()
        mock_supabase = builder.get_mock_client()
        
        @require_org_access(check_parent=False)
        async def test_func(request, supabase):
            return await sample_function(request.user)
        
        request = Mock()
        request.user = {'role': 'user', 'organization_id': 'org-123'}
        request.organization_id = 'org-other'
        
        with pytest.mock.patch('middleware.permissions.can_access_organization', return_value=False):
            with pytest.raises(OrganizationAccessError):
                await test_func(request, mock_supabase)


class TestRequireFeatureEnabledDecorator:
    """Test require_feature_enabled decorator - lines 176-196"""
    
    @pytest.mark.asyncio
    async def test_require_feature_enabled_allows_access(self):
        """Test decorator allows access when feature enabled"""
        builder = SupabasePermissionMockBuilder()
        builder.setup_toggles([{'organization_id': 'org-123', 'rag_feature': 'sales_intelligence', 'enabled': True}])
        mock_supabase = builder.get_mock_client()
        
        @require_feature_enabled('sales_intelligence')
        async def test_func(request, supabase):
            return await sample_function(request.user)
        
        request = Mock()
        request.user = {'role': 'user', 'organization_id': 'org-123'}
        request.organization_id = 'org-123'
        
        # Mock can_access_rag_feature to return True
        with pytest.mock.patch('middleware.permissions.can_access_rag_feature', return_value=True):
            result = await test_func(request, mock_supabase)
            assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_feature_enabled_denies_access_raises_error(self):
        """Test decorator raises error when feature access denied"""
        builder = SupabasePermissionMockBuilder()
        mock_supabase = builder.get_mock_client()
        
        @require_feature_enabled('sales_intelligence')
        async def test_func(request, supabase):
            return await sample_function(request.user)
        
        request = Mock()
        request.user = {'role': 'user', 'organization_id': 'org-123'}
        request.organization_id = 'org-123'
        
        with pytest.mock.patch('middleware.permissions.can_access_rag_feature', return_value=False):
            with pytest.raises(FeatureAccessError):
                await test_func(request, mock_supabase)


class TestRequireAnyRoleDecorator:
    """Test require_any_role decorator - lines 200-221"""
    
    @pytest.mark.asyncio
    async def test_require_any_role_matches_one_role(self):
        """Test decorator passes when user has one of required roles"""
        @require_any_role([UserRole.MANAGER, UserRole.ORG_ADMIN])
        async def test_func(request):
            return await sample_function(request.user)
        
        request = Mock()
        request.user = {'role': 'manager'}  # One of the required roles
        
        result = await test_func(request)
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_any_role_no_match_raises_error(self):
        """Test decorator raises error when no required roles match"""
        @require_any_role([UserRole.MANAGER, UserRole.ORG_ADMIN])
        async def test_func(request):
            return await sample_function(request.user)
        
        request = Mock()
        request.user = {'role': 'user'}  # Not in required roles
        
        with pytest.raises(PermissionError):
            await test_func(request)


class TestConvenienceDecorators:
    """Test convenience decorators - lines 225, 229, 233, 237, 241"""
    
    @pytest.mark.asyncio
    async def test_require_system_admin_decorator(self):
        """Test require_system_admin convenience decorator"""
        @require_system_admin
        async def test_func(request):
            return await sample_function(request.user)
        
        request = Mock()
        request.user = {'role': 'system_admin'}
        
        result = await test_func(request)
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_org_admin_decorator(self):
        """Test require_org_admin convenience decorator"""
        @require_org_admin
        async def test_func(request):
            return await sample_function(request.user)
        
        request = Mock()
        request.user = {'role': 'org_admin'}
        
        result = await test_func(request)
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_manager_or_higher_decorator(self):
        """Test require_manager_or_higher convenience decorator"""
        @require_manager_or_higher
        async def test_func(request):
            return await sample_function(request.user)
        
        request = Mock()
        request.user = {'role': 'org_admin'}  # Higher than manager
        
        result = await test_func(request)
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_salesperson_or_higher_decorator(self):
        """Test require_salesperson_or_higher convenience decorator"""
        @require_salesperson_or_higher
        async def test_func(request):
            return await sample_function(request.user)
        
        request = Mock()
        request.user = {'role': 'manager'}  # Higher than salesperson
        
        result = await test_func(request)
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_admin_access_decorator(self):
        """Test require_admin_access convenience decorator"""
        @require_admin_access
        async def test_func(request):
            return await sample_function(request.user)
        
        request = Mock()
        request.user = {'role': 'org_admin'}  # One of admin roles
        
        result = await test_func(request)
        assert result.get('success') is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=middleware.permissions', '--cov-report=html'])

