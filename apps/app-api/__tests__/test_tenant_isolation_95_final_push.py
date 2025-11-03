# apps/app-api/__tests__/test_tenant_isolation_95_final_push.py
"""
Final push to 95% for Tenant Isolation Service
Focusing on remaining missing paths
"""

import pytest
from unittest.mock import Mock, patch
from services.tenant_isolation_service import TenantIsolationService
from test_utils import SupabaseMockBuilder


@pytest.fixture
def mock_builder():
    return SupabaseMockBuilder()


@pytest.fixture
def tenant_isolation_service(mock_builder):
    with patch('services.tenant_isolation_service.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return TenantIsolationService()


class TestUpdateRAGTogglesLines298317:
    """Test update RAG feature toggle - lines 298, 317-320"""
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_update_existing(self, tenant_isolation_service):
        """Test update when toggle exists - covers line 298"""
        # Setup to return existing toggle
        query_result = Mock()
        query_result.data = [{'id': 'toggle-123'}]
        
        query_chain = Mock()
        query_chain.select.return_value = query_chain
        query_chain.eq.return_value = query_chain
        query_chain.execute.return_value = query_result
        
        update_result = Mock()
        update_result.data = [{'id': 'toggle-123', 'enabled': True}]
        
        update_chain = Mock()
        update_chain.update.return_value = update_chain
        update_chain.eq.return_value = update_chain
        update_chain.execute.return_value = update_result
        
        table = Mock()
        table.select.return_value = query_chain
        table.update.return_value = update_chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.update_rag_feature_toggle(
            organization_id='org-123',
            rag_feature='best_practice_kb',
            enabled=True
        )
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_no_data(self, tenant_isolation_service):
        """Test update when update returns no data - covers lines 317-320"""
        query_result = Mock()
        query_result.data = [{'id': 'toggle-123'}]
        
        query_chain = Mock()
        query_chain.select.return_value = query_chain
        query_chain.eq.return_value = query_chain
        query_chain.execute.return_value = query_result
        
        update_result = Mock()
        update_result.data = []
        
        update_chain = Mock()
        update_chain.update.return_value = update_chain
        update_chain.eq.return_value = update_chain
        update_chain.execute.return_value = update_result
        
        table = Mock()
        table.select.return_value = query_chain
        table.update.return_value = update_chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.update_rag_feature_toggle(
            organization_id='org-123',
            rag_feature='best_practice_kb',
            enabled=True
        )
        
        assert result is not None
        assert result.get('success') is False


class TestBulkUpdateTogglesLines317324340:
    """Test bulk update error paths - lines 317-324, 340"""
    
    @pytest.mark.asyncio
    async def test_bulk_update_with_partial_failures(self, tenant_isolation_service):
        """Test bulk update when some updates fail - covers line 340"""
        with patch.object(tenant_isolation_service, 'update_rag_feature_toggle') as mock_update:
            mock_update.side_effect = [
                {'success': True, 'toggle': {'id': 'toggle-1'}},
                {'success': False, 'error': 'Failed'},
                {'success': True, 'toggle': {'id': 'toggle-3'}}
            ]
            
            result = await tenant_isolation_service.bulk_update_rag_toggles(
                organization_id='org-123',
                toggle_updates={
                    'best_practice_kb': True,
                    'sales_intelligence': False,
                    'support_kb': True
                }
            )
            
            assert result is not None
            assert result.get('success') is True
            assert result.get('total_updated') == 2  # 2 successful
    
    @pytest.mark.asyncio
    async def test_bulk_update_exception(self, tenant_isolation_service):
        """Test bulk update when exception occurs"""
        with patch.object(tenant_isolation_service, 'update_rag_feature_toggle', side_effect=Exception("Database error")):
            result = await tenant_isolation_service.bulk_update_rag_toggles(
                organization_id='org-123',
                toggle_updates={'best_practice_kb': True}
            )
            
            assert result is not None
            assert result.get('success') is False


class TestCrossTenantAccessLines366372385386:
    """Test cross-tenant access checking - lines 366-386"""
    
    @pytest.mark.asyncio
    async def test_check_cross_tenant_access_no_user(self, tenant_isolation_service):
        """Test cross-tenant access when user not found - covers line 372"""
        query_result = Mock()
        query_result.data = None
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.single.return_value.execute.return_value = query_result
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service._check_cross_tenant_access(
            user_id='user-123',
            target_org_id='org-target',
            resource_type='context_item'
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_cross_tenant_access_system_admin(self, tenant_isolation_service):
        """Test cross-tenant access for system admin"""
        query_result = Mock()
        query_result.data = {'role': 'system_admin'}
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.single.return_value.execute.return_value = query_result
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service._check_cross_tenant_access(
            user_id='user-123',
            target_org_id='org-target',
            resource_type='context_item'
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_cross_tenant_access_with_permissions(self, tenant_isolation_service):
        """Test cross-tenant access with permissions"""
        user_result = Mock()
        user_result.data = {'role': 'user'}
        
        user_chain = Mock()
        user_chain.select.return_value = user_chain
        user_chain.eq.return_value = user_chain
        user_chain.single.return_value.execute.return_value = user_result
        
        perm_result = Mock()
        perm_result.data = [{'id': 'perm-123'}]
        
        perm_chain = Mock()
        perm_chain.select.return_value = perm_chain
        perm_chain.eq.return_value = perm_chain
        perm_chain.execute.return_value = perm_result
        
        def from_side_effect(table_name):
            table = Mock()
            if table_name == 'profiles':
                table.select.return_value = user_chain
            else:
                table.select.return_value = perm_chain
            return table
        
        tenant_isolation_service.supabase.from_ = Mock(side_effect=from_side_effect)
        
        result = await tenant_isolation_service._check_cross_tenant_access(
            user_id='user-123',
            target_org_id='org-target',
            resource_type='context_item'
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_cross_tenant_access_exception(self, tenant_isolation_service):
        """Test cross-tenant access when exception occurs - covers lines 385-386"""
        with patch.object(tenant_isolation_service.supabase, 'from_', side_effect=Exception("Database error")):
            result = await tenant_isolation_service._check_cross_tenant_access(
                user_id='user-123',
                target_org_id='org-target',
                resource_type='context_item'
            )
            
            assert result is False


class TestGetOrganizationQuotasLines388:
    """Test get organization quotas - lines 388+"""
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_no_data(self, tenant_isolation_service):
        """Test get quotas when no data exists"""
        query_result = Mock()
        query_result.data = None
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.single.return_value.execute.return_value = query_result
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service._get_organization_quotas('org-123')
        
        assert result is not None


class TestGetRAGTogglesLines270276:
    """Test get RAG toggles - lines 270-276"""
    
    @pytest.mark.asyncio
    async def test_get_rag_toggles_create_defaults(self, tenant_isolation_service):
        """Test get toggles when none exist and defaults created - covers lines 270-276"""
        query_result = Mock()
        query_result.data = []
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = query_result
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        with patch.object(tenant_isolation_service, '_create_default_rag_toggles', return_value=[{'id': 'toggle-1'}]):
            result = await tenant_isolation_service.get_rag_feature_toggles('org-123')
            
            assert result is not None
            assert result.get('success') is True
            assert len(result.get('toggles', [])) == 1


class TestPolicyEnforcementLines385386:
    """Test policy enforcement error paths"""
    
    @pytest.mark.asyncio
    async def test_enforce_with_policy_exception(self, tenant_isolation_service):
        """Test enforce when policy check raises exception"""
        with patch.object(tenant_isolation_service, '_get_user_organization', return_value={'organization_id': 'org-123'}):
            with patch.object(tenant_isolation_service, '_check_cross_tenant_access', side_effect=Exception("Policy error")):
                result = await tenant_isolation_service.enforce_tenant_isolation(
                    user_id='user-123',
                    organization_id='org-target',
                    resource_type='context_item',
                    resource_id='item-123'
                )
                
                assert result is not None
                assert result.get('success') is False


class TestGetRAGTogglesExceptionLines282287:
    """Test get RAG toggles exception - lines 282-287"""
    
    @pytest.mark.asyncio
    async def test_get_rag_toggles_exception_with_toggles_list(self, tenant_isolation_service):
        """Test get toggles when exception occurs but returns empty toggles list - covers lines 282-287"""
        with patch.object(tenant_isolation_service.supabase, 'from_', side_effect=Exception("Database error")):
            result = await tenant_isolation_service.get_rag_feature_toggles('org-123')
            
            assert result is not None
            assert result.get('success') is False
            assert result.get('toggles') == []


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service', '--cov-report=html'])

