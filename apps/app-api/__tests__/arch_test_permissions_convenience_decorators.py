# apps/app-api/__tests__/test_permissions_convenience_decorators.py
"""
Tests for convenience decorators to push to 95%
Lines: 225, 229, 233, 237, 241
"""

import pytest
from unittest.mock import Mock
from middleware.permissions import (
    require_system_admin, require_org_admin,
    require_manager_or_higher, require_salesperson_or_higher,
    require_admin_access, UserRole
)


async def sample_function():
    return {"success": True}


class TestConvenienceDecorators:
    """Test convenience decorators - lines 225, 229, 233, 237, 241"""
    
    @pytest.mark.asyncio
    async def test_require_system_admin_decorator(self):
        """Test require_system_admin convenience decorator - line 225"""
        decorated = require_system_admin(sample_function)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'system_admin'}
        
        request = MockRequest()
        result = await decorated(request)
        
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_system_admin_denies_lower_role(self):
        """Test require_system_admin denies lower roles"""
        decorated = require_system_admin(sample_function)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'org_admin'}
        
        request = MockRequest()
        
        with pytest.raises(Exception):  # PermissionError
            await decorated(request)
    
    @pytest.mark.asyncio
    async def test_require_org_admin_decorator(self):
        """Test require_org_admin convenience decorator - line 229"""
        decorated = require_org_admin(sample_function)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'org_admin'}
        
        request = MockRequest()
        result = await decorated(request)
        
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_manager_or_higher_decorator(self):
        """Test require_manager_or_higher convenience decorator - line 233"""
        decorated = require_manager_or_higher(sample_function)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'manager'}
        
        request = MockRequest()
        result = await decorated(request)
        
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_manager_or_higher_allows_higher_roles(self):
        """Test require_manager_or_higher allows system admin"""
        decorated = require_manager_or_higher(sample_function)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'system_admin'}  # Higher than manager
        
        request = MockRequest()
        result = await decorated(request)
        
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_salesperson_or_higher_decorator(self):
        """Test require_salesperson_or_higher convenience decorator - line 237"""
        decorated = require_salesperson_or_higher(sample_function)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'salesperson'}
        
        request = MockRequest()
        result = await decorated(request)
        
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_admin_access_system_admin(self):
        """Test require_admin_access with system admin - line 241"""
        decorated = require_admin_access(sample_function)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'system_admin'}  # One of admin roles
        
        request = MockRequest()
        result = await decorated(request)
        
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_admin_access_org_admin(self):
        """Test require_admin_access with org admin"""
        decorated = require_admin_access(sample_function)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'org_admin'}  # Other admin role
        
        request = MockRequest()
        result = await decorated(request)
        
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_require_admin_access_denies_manager(self):
        """Test require_admin_access denies manager role"""
        decorated = require_admin_access(sample_function)
        
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'manager'}  # Not admin
        
        request = MockRequest()
        
        with pytest.raises(Exception):  # PermissionError
            await decorated(request)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=middleware.permissions', '--cov-report=html'])

