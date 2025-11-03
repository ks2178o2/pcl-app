# apps/app-api/__tests__/test_permissions_decorators_integration.py
"""
Integration-style tests for decorators to reach 95% coverage
Lines: 129-148, 152-172, 176-196, 200-221
"""

import pytest
from unittest.mock import Mock
import asyncio
from middleware.permissions import (
    require_role, require_org_access, require_feature_enabled,
    require_any_role, UserRole, PermissionError,
    OrganizationAccessError, FeatureAccessError
)


# Test async functions to decorate
async def test_async_func(user=None, organization_id=None):
    return {"success": True, "message": "executed"}


async def test_async_func_kwargs(**kwargs):
    return {"success": True, "message": "executed with kwargs"}


class TestRequireRoleDecoratorIntegration:
    """Test require_role decorator integration - lines 129-148"""
    
    @pytest.mark.asyncio
    async def test_decorator_with_valid_role(self):
        """Test decorator allows execution with valid role"""
        decorated = require_role(UserRole.MANAGER)(test_async_func)
        
        # Create mock request with user attribute
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'manager'}
        
        request = MockRequest()
        result = await decorated(request)
        
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_decorator_with_invalid_role_raises_error(self):
        """Test decorator raises error with invalid role - line 140-145"""
        decorated = require_role(UserRole.MANAGER)(test_async_func)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'user'}  # Too low
        
        request = MockRequest()
        
        with pytest.raises(PermissionError) as exc:
            await decorated(request)
        
        assert "does not meet" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_decorator_with_user_in_kwargs(self):
        """Test decorator with user in kwargs - line 135"""
        decorated = require_role(UserRole.USER)(test_async_func)
        
        result = await decorated(user={'role': 'user'})
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_decorator_no_user_data_raises_error(self):
        """Test decorator raises error when no user data - line 138"""
        decorated = require_role(UserRole.MANAGER)(test_async_func)
        
        request = Mock()  # No user attribute
        request.user = None
        
        with pytest.raises(PermissionError) as exc:
            await decorated(request)
        
        assert "User data not found" in str(exc.value)


class TestRequireOrgAccessDecoratorIntegration:
    """Test require_org_access decorator - lines 152-172"""
    
    @pytest.mark.asyncio
    async def test_decorator_allows_access(self):
        """Test decorator allows access when permission granted - line 165"""
        decorated = require_org_access(check_parent=False)(test_async_func)
        
        # Mock can_access_organization
        import middleware.permissions
        original_func = middleware.permissions.can_access_organization
        
        def mock_can_access(user_data, org_id, supabase, check_parent=False):
            return user_data.get('organization_id') == org_id
        
        middleware.permissions.can_access_organization = mock_can_access
        
        try:
            class MockRequest:
                def __init__(self):
                    self.user = {'role': 'user', 'organization_id': 'org-123'}
                    self.organization_id = 'org-123'
            
            request = MockRequest()
            result = await decorated(request)
            
            assert result.get('success') is True
        finally:
            middleware.permissions.can_access_organization = original_func
    
    @pytest.mark.asyncio
    async def test_decorator_denies_access_raises_error(self):
        """Test decorator raises error when access denied - line 165-168"""
        decorated = require_org_access(check_parent=False)(test_async_func)
        
        import middleware.permissions
        original_func = middleware.permissions.can_access_organization
        
        def mock_can_access(user_data, org_id, supabase, check_parent=False):
            return False
        
        middleware.permissions.can_access_organization = mock_can_access
        
        try:
            class MockRequest:
                def __init__(self):
                    self.user = {'role': 'user', 'organization_id': 'org-123'}
                    self.organization_id = 'org-other'
            
            request = MockRequest()
            
            with pytest.raises(OrganizationAccessError):
                await decorated(request)
        finally:
            middleware.permissions.can_access_organization = original_func
    
    @pytest.mark.asyncio
    async def test_decorator_with_kwargs(self):
        """Test decorator with user and org_id in kwargs - line 159-161"""
        decorated = require_org_access(check_parent=False)(test_async_func_kwargs)
        
        import middleware.permissions
        original_func = middleware.permissions.can_access_organization
        
        def mock_can_access(user_data, org_id, supabase, check_parent=False):
            return True
        
        middleware.permissions.can_access_organization = mock_can_access
        
        try:
            result = await decorated(user={'role': 'user', 'organization_id': 'org-123'},
                                   organization_id='org-123')
            
            assert result.get('success') is True
        finally:
            middleware.permissions.can_access_organization = original_func


class TestRequireFeatureEnabledDecoratorIntegration:
    """Test require_feature_enabled decorator - lines 176-196"""
    
    @pytest.mark.asyncio
    async def test_decorator_allows_access_when_enabled(self):
        """Test decorator allows access when feature enabled - line 189"""
        decorated = require_feature_enabled('sales_intelligence')(test_async_func)
        
        import middleware.permissions
        original_func = middleware.permissions.can_access_rag_feature
        
        def mock_can_access(user_data, feature_name, org_id, supabase):
            return True
        
        middleware.permissions.can_access_rag_feature = mock_can_access
        
        try:
            class MockRequest:
                def __init__(self):
                    self.user = {'role': 'user', 'organization_id': 'org-123'}
                    self.organization_id = 'org-123'
            
            request = MockRequest()
            result = await decorated(request)
            
            assert result.get('success') is True
        finally:
            middleware.permissions.can_access_rag_feature = original_func
    
    @pytest.mark.asyncio
    async def test_decorator_denies_access_raises_error(self):
        """Test decorator raises error when feature disabled - line 189-192"""
        decorated = require_feature_enabled('sales_intelligence')(test_async_func)
        
        import middleware.permissions
        original_func = middleware.permissions.can_access_rag_feature
        
        def mock_can_access(user_data, feature_name, org_id, supabase):
            return False
        
        middleware.permissions.can_access_rag_feature = mock_can_access
        
        try:
            class MockRequest:
                def __init__(self):
                    self.user = {'role': 'user', 'organization_id': 'org-123'}
                    self.organization_id = 'org-123'
            
            request = MockRequest()
            
            with pytest.raises(FeatureAccessError):
                await decorated(request)
        finally:
            middleware.permissions.can_access_rag_feature = original_func


class TestRequireAnyRoleDecoratorIntegration:
    """Test require_any_role decorator - lines 200-221"""
    
    @pytest.mark.asyncio
    async def test_decorator_allows_with_one_role(self):
        """Test decorator allows when user has one of required roles - line 213"""
        decorated = require_any_role([UserRole.MANAGER, UserRole.ORG_ADMIN])(test_async_func)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'manager'}  # Has one of the roles
        
        request = MockRequest()
        result = await decorated(request)
        
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_decorator_denies_with_no_required_role(self):
        """Test decorator raises error when no required role - line 213-217"""
        decorated = require_any_role([UserRole.MANAGER, UserRole.ORG_ADMIN])(test_async_func)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'user'}  # Not in required roles
        
        request = MockRequest()
        
        with pytest.raises(PermissionError) as exc:
            await decorated(request)
        
        assert "not in required roles" in str(exc.value)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=middleware.permissions', '--cov-report=html'])

