# apps/app-api/__tests__/test_permissions_direct_95.py
"""
Direct tests to reach 95% coverage by testing decorator implementations
Lines: 129-148, 152-172, 176-196, 200-221, 324-337
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from middleware.permissions import (
    require_role, require_org_access, require_feature_enabled,
    require_any_role, require_system_admin, require_org_admin,
    require_manager_or_higher, require_salesperson_or_higher,
    require_admin_access, UserRole, PermissionError,
    OrganizationAccessError, FeatureAccessError
)


# Simple async functions for testing
async def simple_func(*args, **kwargs):
    return {"success": True}

async def func_with_user(*args, **kwargs):
    if args:
        return {"user": args[0].user if hasattr(args[0], 'user') else None}
    if 'user' in kwargs:
        return {"user": kwargs['user']}
    return {"user": None}


class TestRequireRoleImplementation:
    """Test require_role decorator implementation - lines 129-148"""
    
    @pytest.mark.asyncio
    async def test_wrapper_with_args_user_attribute(self):
        """Test wrapper path: args[0].user - line 133-134"""
        decorated = require_role(UserRole.USER)(func_with_user)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'user'}
        
        result = await decorated(MockRequest())
        assert result.get('user') == {'role': 'user'}
    
    @pytest.mark.asyncio
    async def test_wrapper_with_kwargs_user(self):
        """Test wrapper path: user in kwargs - line 135"""
        decorated = require_role(UserRole.USER)(func_with_user)
        
        result = await decorated(user={'role': 'user'})
        assert result.get('user') == {'role': 'user'}
    
    @pytest.mark.asyncio
    async def test_wrapper_raises_error_no_user(self):
        """Test wrapper raises error when no user - line 137-138"""
        decorated = require_role(UserRole.USER)(func_with_user)
        
        with pytest.raises(PermissionError) as exc:
            await decorated()
        
        assert "User data not found" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_wrapper_with_permission_denied(self):
        """Test wrapper raises error when role insufficient - line 140-144"""
        decorated = require_role(UserRole.MANAGER)(simple_func)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'user'}  # Too low
        
        with pytest.raises(PermissionError):
            await decorated(MockRequest())
    
    @pytest.mark.asyncio
    async def test_wrapper_calls_func_on_success(self):
        """Test wrapper calls func when permission granted - line 146"""
        decorated = require_role(UserRole.USER)(simple_func)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'user'}
        
        result = await decorated(MockRequest())
        assert result.get('success') is True


class TestRequireOrgAccessImplementation:
    """Test require_org_access decorator implementation - lines 152-172"""
    
    @pytest.mark.asyncio
    async def test_wrapper_with_args_hasattr_user(self):
        """Test wrapper path: args[0].user - line 156-158"""
        # Create a simple test function
        async def test_func(request):
            return request.user
        
        decorated = require_org_access(check_parent=False)(test_func)
        
        # Mock can_access_organization
        with patch('middleware.permissions.can_access_organization', return_value=True):
            class MockRequest:
                def __init__(self):
                    self.user = {'role': 'user', 'organization_id': 'org-123'}
                    self.organization_id = 'org-123'
            
            request = MockRequest()
            result = await decorated(request)
            assert result == {'role': 'user', 'organization_id': 'org-123'}
    
    @pytest.mark.asyncio
    async def test_wrapper_org_from_args_attr(self):
        """Test wrapper: org_id from args[0].organization_id - line 158"""
        async def test_func(request):
            return request.organization_id
        
        decorated = require_org_access(check_parent=False)(test_func)
        
        with patch('middleware.permissions.can_access_organization', return_value=True):
            class MockRequest:
                def __init__(self):
                    self.user = {'role': 'user'}
                    self.organization_id = 'org-123'
            
            result = await decorated(MockRequest())
            assert result == 'org-123'
    
    @pytest.mark.asyncio
    async def test_wrapper_raises_error_no_user_or_org(self):
        """Test wrapper raises error when no user/org data - line 162-163"""
        decorated = require_org_access(check_parent=False)(simple_func)
        
        with pytest.raises(OrganizationAccessError) as exc:
            await decorated()
        
        assert "User data or organization ID not found" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_wrapper_raises_error_access_denied(self):
        """Test wrapper raises error when access denied - line 165-168"""
        decorated = require_org_access(check_parent=False)(simple_func)
        
        with patch('middleware.permissions.can_access_organization', return_value=False):
            class MockRequest:
                def __init__(self):
                    self.user = {'role': 'user', 'organization_id': 'org-123'}
                    self.organization_id = 'org-other'
            
            request = MockRequest()
            
            with pytest.raises(OrganizationAccessError):
                await decorated(request)


class TestRequireFeatureEnabledImplementation:
    """Test require_feature_enabled decorator implementation - lines 176-196"""
    
    @pytest.mark.asyncio
    async def test_wrapper_extracts_user_and_org_from_args(self):
        """Test wrapper path: args[0].user - line 180-182"""
        async def test_func(request):
            return request.user
        
        decorated = require_feature_enabled('sales_intelligence')(test_func)
        
        with patch('middleware.permissions.can_access_rag_feature', return_value=True):
            class MockRequest:
                def __init__(self):
                    self.user = {'role': 'user', 'organization_id': 'org-123'}
                    self.organization_id = 'org-123'
            
            request = MockRequest()
            result = await decorated(request)
            assert result == {'role': 'user', 'organization_id': 'org-123'}
    
    @pytest.mark.asyncio
    async def test_wrapper_raises_error_feature_access_denied(self):
        """Test wrapper raises error when feature access denied - line 189-192"""
        decorated = require_feature_enabled('sales_intelligence')(simple_func)
        
        with patch('middleware.permissions.can_access_rag_feature', return_value=False):
            class MockRequest:
                def __init__(self):
                    self.user = {'role': 'user', 'organization_id': 'org-123'}
                    self.organization_id = 'org-123'
            
            request = MockRequest()
            
            with pytest.raises(FeatureAccessError):
                await decorated(request)


class TestRequireAnyRoleImplementation:
    """Test require_any_role decorator implementation - lines 200-221"""
    
    @pytest.mark.asyncio
    async def test_wrapper_extracts_user_from_args(self):
        """Test wrapper path: args[0].user - line 204-205"""
        async def test_func(request):
            return request.user
        
        decorated = require_any_role([UserRole.USER])(test_func)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'user'}
        
        request = MockRequest()
        result = await decorated(request)
        assert result == {'role': 'user'}
    
    @pytest.mark.asyncio
    async def test_wrapper_raises_error_role_not_in_list(self):
        """Test wrapper raises error when role not in required list - line 213-217"""
        decorated = require_any_role([UserRole.MANAGER, UserRole.ORG_ADMIN])(simple_func)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'user'}
        
        request = MockRequest()
        
        with pytest.raises(PermissionError) as exc:
            await decorated(request)
        
        assert "not in required roles" in str(exc.value)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=middleware.permissions', '--cov-report=html'])

