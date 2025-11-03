# apps/app-api/__tests__/test_permissions_final_95_push.py
"""
Final push to 95% for Permissions Middleware
Target: Last 15 missing lines - 160-161, 183-187, 206-209, 225, 229, 233, 237, 241, 326
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from middleware.permissions import (
    require_org_access, require_feature_enabled, require_any_role,
    require_system_admin, require_org_admin, require_manager_or_higher,
    require_salesperson_or_higher, require_admin_access,
    OrganizationAccessError, FeatureAccessError, UserRole, validate_permissions
)


# Test functions - used by decorators (not pytest functions)
async def _test_func(*args, **kwargs):
    """Helper function for testing decorators"""
    return {"success": True}


class TestOrgAccessDecoratorPaths:
    """Test org_access decorator - lines 160-161"""
    
    @pytest.mark.asyncio
    async def test_org_access_kwargs_extraction(self):
        """Test decorator with user and org_id in kwargs - line 159-161"""
        decorated = require_org_access(check_parent=False)(_test_func)
        
        with patch('middleware.permissions.can_access_organization', return_value=True):
            result = await decorated(user={'role': 'user', 'organization_id': 'org-123'},
                                   organization_id='org-123')
            assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_org_access_raises_error_missing_data(self):
        """Test decorator raises error when missing user/org - line 162-163"""
        decorated = require_org_access(check_parent=False)(_test_func)
        
        with pytest.raises(OrganizationAccessError) as exc:
            await decorated()
        
        assert "User data or organization ID not found" in str(exc.value)


class TestFeatureEnabledDecoratorPaths:
    """Test feature_enabled decorator - lines 183-187"""
    
    @pytest.mark.asyncio
    async def test_feature_enabled_kwargs_extraction(self):
        """Test decorator with user and org_id in kwargs - line 182-185"""
        decorated = require_feature_enabled('sales_intelligence')(_test_func)
        
        with patch('middleware.permissions.can_access_rag_feature', return_value=True):
            result = await decorated(user={'role': 'user', 'organization_id': 'org-123'},
                                    organization_id='org-123')
            assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_feature_enabled_raises_error_missing_data(self):
        """Test decorator raises error when missing user/org - line 186-187"""
        decorated = require_feature_enabled('sales_intelligence')(_test_func)
        
        with pytest.raises(FeatureAccessError) as exc:
            await decorated()
        
        assert "User data or organization ID not found" in str(exc.value)


class TestAnyRoleDecoratorPaths:
    """Test any_role decorator - lines 206-209"""
    
    @pytest.mark.asyncio
    async def test_any_role_with_kwargs_user(self):
        """Test decorator with user in kwargs - line 206"""
        decorated = require_any_role([UserRole.USER])(_test_func)
        
        result = await decorated(user={'role': 'user'})
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_any_role_raises_error_no_user(self):
        """Test decorator raises error when no user - line 208-209"""
        decorated = require_any_role([UserRole.MANAGER])(_test_func)
        
        with pytest.raises(Exception):  # PermissionError
            await decorated()


class TestConvenienceDecoratorsFinal:
    """Test convenience decorators to hit lines 225, 229, 233, 237, 241"""
    
    @pytest.mark.asyncio
    async def test_require_system_admin_call(self):
        """Test require_system_admin calls require_role - line 225"""
        # By using the decorator, we exercise line 225
        decorated = require_system_admin(_test_func)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'system_admin'}
        
        result = await decorated(MockRequest())
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_org_admin_call(self):
        """Test require_org_admin calls require_role - line 229"""
        decorated = require_org_admin(_test_func)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'org_admin'}
        
        result = await decorated(MockRequest())
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_manager_or_higher_call(self):
        """Test require_manager_or_higher calls require_role - line 233"""
        decorated = require_manager_or_higher(_test_func)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'manager'}
        
        result = await decorated(MockRequest())
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_salesperson_or_higher_call(self):
        """Test require_salesperson_or_higher calls require_role - line 237"""
        decorated = require_salesperson_or_higher(_test_func)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'salesperson'}
        
        result = await decorated(MockRequest())
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_admin_access_call(self):
        """Test require_admin_access calls require_any_role - line 241"""
        decorated = require_admin_access(_test_func)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'system_admin'}
        
        result = await decorated(MockRequest())
        assert result.get('success') is True


class TestValidatePermissionsBranch:
    """Test validate_permissions missing branch - line 326"""
    
    def test_validate_with_supabase_none(self):
        """Test validate when supabase is None - line 325-326"""
        user_data = {'role': 'system_admin', 'organization_id': 'org-123'}
        
        # This will get supabase from get_supabase_client()
        # We need to patch it to avoid real connection
        with patch('middleware.permissions.get_supabase_client') as mock_get:
            mock_client = Mock()
            mock_get.return_value = mock_client
            
            result = validate_permissions(user_data, "manage_rag_features", 'org-123')
            
            # Should call get_supabase_client when supabase is None
            mock_get.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=middleware.permissions', '--cov-report=html'])

