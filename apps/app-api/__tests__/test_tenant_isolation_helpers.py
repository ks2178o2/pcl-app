# apps/app-api/__tests__/test_tenant_isolation_helpers.py
"""
Tests for helper methods to push coverage to 95%
Lines: 357-386 (helpers), 400-419 (quotas), and other missing paths
"""

import pytest
from unittest.mock import Mock, patch
from services.tenant_isolation_service import TenantIsolationService
from test_utils import SupabaseMockBuilder


class TestTenantIsolationHelpers:
    """Tests for helper methods and remaining coverage gaps"""
    
    @pytest.fixture
    def mock_builder(self):
        """Create mock builder"""
        return SupabaseMockBuilder()
    
    @pytest.fixture
    def tenant_service(self, mock_builder):
        """Create tenant isolation service"""
        with patch('services.tenant_isolation_service.get_supabase_client', return_value=mock_builder.get_mock_client()):
            return TenantIsolationService()
    
    @pytest.mark.asyncio
    async def test_get_user_organization_success(self, tenant_service):
        """Test _get_user_organization with data - lines 357-363"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            table = Mock()
            result_mock = Mock()
            result_mock.data = {'organization_id': 'org-123'}
            
            single_result = Mock()
            single_result.execute.return_value = result_mock
            
            select_chain = Mock()
            select_chain.single.return_value = single_result
            select_chain.eq.return_value = select_chain
            select_chain.select.return_value = select_chain
            
            table.select.return_value = select_chain
            mock_supabase.from_.return_value = table
            
            result = await tenant_service._get_user_organization('user-123')
            
            assert result == {'organization_id': 'org-123'}
    
    @pytest.mark.asyncio
    async def test_get_user_organization_no_data(self, tenant_service):
        """Test _get_user_organization with no data - line 361"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            table = Mock()
            result_mock = Mock()
            result_mock.data = None
            
            single_result = Mock()
            single_result.execute.return_value = result_mock
            
            select_chain = Mock()
            select_chain.single.return_value = single_result
            select_chain.eq.return_value = select_chain
            
            table.select.return_value = select_chain
            mock_supabase.from_.return_value = table
            
            result = await tenant_service._get_user_organization('user-123')
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_organization_exception(self, tenant_service):
        """Test _get_user_organization exception - line 362"""
        tenant_service.supabase.from_.side_effect = Exception("Profile error")
        
        result = await tenant_service._get_user_organization('user-123')
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_check_cross_tenant_access_system_admin(self, tenant_service):
        """Test cross-tenant access for system admin - lines 365-386"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            # Mock profiles table
            profiles_table = Mock()
            profiles_result = Mock()
            profiles_result.data = {'role': 'system_admin'}
            
            profiles_single = Mock()
            profiles_single.execute.return_value = profiles_result
            
            profiles_select = Mock()
            profiles_select.single.return_value = profiles_single
            profiles_select.eq.return_value = profiles_select
            profiles_select.select.return_value = profiles_select
            
            profiles_table.select.return_value = profiles_select
            
            # Return different tables based on call
            call_count = 0
            def table_side_effect(table_name):
                nonlocal call_count
                call_count += 1
                if call_count == 1:  # First call: profiles
                    return profiles_table
                elif call_count == 2:  # Second call: cross_tenant_permissions
                    permissions_table = Mock()
                    permissions_result = Mock()
                    permissions_result.data = []
                    
                    permissions_select = Mock()
                    permissions_select.execute.return_value = permissions_result
                    permissions_select.eq.return_value = permissions_select
                    permissions_table.select.return_value = permissions_select
                    return permissions_table
            
            mock_supabase.from_.side_effect = table_side_effect
            
            result = await tenant_service._check_cross_tenant_access(
                user_id='user-123',
                target_org_id='org-other',
                resource_type='context_item'
            )
            
            assert result is True  # System admin has access
    
    @pytest.mark.asyncio
    async def test_check_cross_tenant_access_with_permissions(self, tenant_service):
        """Test cross-tenant access with explicit permissions - lines 380-383"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            # Mock regular user
            profiles_table = Mock()
            profiles_result = Mock()
            profiles_result.data = {'role': 'user'}
            
            profiles_single = Mock()
            profiles_single.execute.return_value = profiles_result
            
            profiles_select = Mock()
            profiles_select.single.return_value = profiles_single
            profiles_select.eq.return_value = profiles_select
            profiles_select.select.return_value = profiles_select
            profiles_table.select.return_value = profiles_select
            
            # Mock permissions table with access
            permissions_table = Mock()
            permissions_result = Mock()
            permissions_result.data = [{'enabled': True}]
            
            permissions_select = Mock()
            permissions_select.execute.return_value = permissions_result
            permissions_select.eq.return_value = permissions_select
            permissions_table.select.return_value = permissions_select
            
            call_count = 0
            def table_side_effect(table_name):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return profiles_table
                else:
                    return permissions_table
            
            mock_supabase.from_.side_effect = table_side_effect
            
            result = await tenant_service._check_cross_tenant_access(
                user_id='user-123',
                target_org_id='org-other',
                resource_type='context_item'
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_cross_tenant_access_no_permissions(self, tenant_service):
        """Test cross-tenant access denied - line 383"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            # Mock regular user
            profiles_table = Mock()
            profiles_result = Mock()
            profiles_result.data = {'role': 'user'}
            
            profiles_single = Mock()
            profiles_single.execute.return_value = profiles_result
            
            profiles_select = Mock()
            profiles_select.single.return_value = profiles_single
            profiles_select.eq.return_value = profiles_select
            profiles_table.select.return_value = profiles_select
            
            # Mock permissions table with no access
            permissions_table = Mock()
            permissions_result = Mock()
            permissions_result.data = []
            
            permissions_select = Mock()
            permissions_select.execute.return_value = permissions_result
            permissions_select.eq.return_value = permissions_select
            permissions_table.select.return_value = permissions_select
            
            call_count = 0
            def table_side_effect(table_name):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return profiles_table
                else:
                    return permissions_table
            
            mock_supabase.from_.side_effect = table_side_effect
            
            result = await tenant_service._check_cross_tenant_access(
                user_id='user-123',
                target_org_id='org-other',
                resource_type='context_item'
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_cross_tenant_access_no_user(self, tenant_service):
        """Test cross-tenant access when user not found - line 371-372"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            table = Mock()
            result_mock = Mock()
            result_mock.data = None
            
            single_result = Mock()
            single_result.execute.return_value = result_mock
            
            select_chain = Mock()
            select_chain.single.return_value = single_result
            select_chain.eq.return_value = select_chain
            
            table.select.return_value = select_chain
            mock_supabase.from_.return_value = table
            
            result = await tenant_service._check_cross_tenant_access(
                user_id='user-123',
                target_org_id='org-other',
                resource_type='context_item'
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_cross_tenant_access_exception(self, tenant_service):
        """Test cross-tenant access exception - lines 384-386"""
        tenant_service.supabase.from_.side_effect = Exception("Cross-tenant error")
        
        result = await tenant_service._check_cross_tenant_access(
            user_id='user-123',
            target_org_id='org-other',
            resource_type='context_item'
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_with_insert_failure(self, tenant_service):
        """Test get quotas when insert fails - lines 400-415"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            # First call: no quotas found
            result_mock = Mock()
            result_mock.data = None
            
            single_result = Mock()
            single_result.execute.return_value = result_mock
            
            select_chain = Mock()
            select_chain.single.return_value = single_result
            select_chain.eq.return_value = select_chain
            
            table = Mock()
            table.select.return_value = select_chain
            
            # Second call: insert fails
            insert_result = Mock()
            insert_result.data = None
            
            insert_chain = Mock()
            insert_chain.execute.return_value = insert_result
            
            table.insert.return_value = insert_chain
            
            call_count = 0
            def table_side_effect(table_name):
                nonlocal call_count
                call_count += 1
                if call_count == 1:  # First from_ call
                    return table
                else:  # Second from_ call
                    table2 = Mock()
                    table2.select.return_value = select_chain
                    return table2
            
            mock_supabase.from_.side_effect = table_side_effect
            
            result = await tenant_service._get_organization_quotas('org-123')
            
            # Should fall back to default_quotas dict
            assert result['success'] is True
            assert 'quotas' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service', '--cov-report=html'])


