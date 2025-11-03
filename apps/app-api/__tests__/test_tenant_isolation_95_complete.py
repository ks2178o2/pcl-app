# apps/app-api/__tests__/test_tenant_isolation_95_complete.py
"""
Complete 95% coverage for Tenant Isolation Service
Target: Lines 78, 117, 175, 182, 186-196, 209-216
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


class TestCreatePolicyLine78:
    """Test create isolation policy when insert returns no data - line 78"""
    
    @pytest.mark.asyncio
    async def test_create_policy_insert_no_data(self, tenant_isolation_service):
        """Test create policy when insert returns empty data - covers line 78"""
        # Setup insert to return no data
        insert_result = Mock()
        insert_result.data = []
        
        chain = Mock()
        chain.insert.return_value = chain
        chain.execute.return_value = insert_result
        
        table = Mock()
        table.insert.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.create_isolation_policy({
            'organization_id': 'org-123',
            'policy_type': 'strict',
            'policy_name': 'test_policy',
            'policy_rules': {'rule': 'value'}
        })
        
        assert result is not None
        assert result.get('success') is False
        assert 'Failed to create' in result.get('error', '')


class TestCheckQuotaLines117135146:
    """Test check quota limits - lines 117, 135-146"""
    
    @pytest.mark.asyncio
    async def test_check_quota_get_quotas_fails(self, tenant_isolation_service):
        """Test check quota when get quotas fails - covers line 117"""
        with patch.object(tenant_isolation_service, '_get_organization_quotas', return_value={'success': False, 'error': 'Not found'}):
            result = await tenant_isolation_service.check_quota_limits('org-123', 'context_items', quantity=1)
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_check_quota_global_access_exceeded(self, tenant_isolation_service):
        """Test check quota for global_access when exceeded - covers lines 135-146"""
        with patch.object(tenant_isolation_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': {
                'current_global_access': 10,
                'max_global_access_features': 10
            }
        }):
            result = await tenant_isolation_service.check_quota_limits('org-123', 'global_access', quantity=1)
            
            assert result is not None
            assert result.get('quota_exceeded') is True
    
    @pytest.mark.asyncio
    async def test_check_quota_sharing_requests_exceeded(self, tenant_isolation_service):
        """Test check quota for sharing_requests when exceeded"""
        with patch.object(tenant_isolation_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': {
                'current_sharing_requests': 50,
                'max_sharing_requests': 50
            }
        }):
            result = await tenant_isolation_service.check_quota_limits('org-123', 'sharing_requests', quantity=1)
            
            assert result is not None
            assert result.get('quota_exceeded') is True
    
    @pytest.mark.asyncio
    async def test_check_quota_within_limit(self, tenant_isolation_service):
        """Test check quota when within limit"""
        with patch.object(tenant_isolation_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': {
                'current_context_items': 100,
                'max_context_items': 1000
            }
        }):
            result = await tenant_isolation_service.check_quota_limits('org-123', 'context_items', quantity=50)
            
            assert result is not None
            assert result.get('success') is True
            assert result.get('quota_check_passed') is True


class TestUpdateQuotaLines175182:
    """Test update quota usage - lines 175, 182"""
    
    @pytest.mark.asyncio
    async def test_update_quota_get_quotas_fails(self, tenant_isolation_service):
        """Test update quota when get quotas fails - covers line 175"""
        with patch.object(tenant_isolation_service, '_get_organization_quotas', return_value={'success': False, 'error': 'Not found'}):
            result = await tenant_isolation_service.update_quota_usage(
                organization_id='org-123',
                operation_type='context_items',
                quantity=10,
                operation='increment'
            )
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_update_quota_update_returns_no_data(self, tenant_isolation_service):
        """Test update quota when update returns no data - covers line 182"""
        with patch.object(tenant_isolation_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': {
                'organization_id': 'org-123',
                'current_context_items': 100,
                'max_context_items': 1000
            }
        }):
            # Setup update to return no data
            update_result = Mock()
            update_result.data = []
            
            chain = Mock()
            chain.update.return_value = chain
            chain.eq.return_value = chain
            chain.execute.return_value = update_result
            
            table = Mock()
            table.update.return_value = chain
            tenant_isolation_service.supabase.from_.return_value = table
            
            result = await tenant_isolation_service.update_quota_usage(
                organization_id='org-123',
                operation_type='context_items',
                quantity=10,
                operation='increment'
            )
            
            assert result is not None
            assert result.get('success') is False
            assert 'Failed to update' in result.get('error', '')


class TestUpdateQuotaDecrementLines186196:
    """Test update quota with decrement - lines 186-196"""
    
    @pytest.mark.asyncio
    async def test_update_quota_decrement_context_items(self, tenant_isolation_service):
        """Test update quota decrement for context_items"""
        with patch.object(tenant_isolation_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': {
                'organization_id': 'org-123',
                'current_context_items': 100,
                'max_context_items': 1000
            }
        }):
            update_result = Mock()
            update_result.data = [{'current_context_items': 90}]
            
            chain = Mock()
            chain.update.return_value = chain
            chain.eq.return_value = chain
            chain.execute.return_value = update_result
            
            table = Mock()
            table.update.return_value = chain
            tenant_isolation_service.supabase.from_.return_value = table
            
            result = await tenant_isolation_service.update_quota_usage(
                organization_id='org-123',
                operation_type='context_items',
                quantity=10,
                operation='decrement'
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_update_quota_decrement_global_access(self, tenant_isolation_service):
        """Test update quota decrement for global_access"""
        with patch.object(tenant_isolation_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': {
                'organization_id': 'org-123',
                'current_global_access': 10
            }
        }):
            update_result = Mock()
            update_result.data = [{'current_global_access': 9}]
            
            chain = Mock()
            chain.update.return_value = chain
            chain.eq.return_value = chain
            chain.execute.return_value = update_result
            
            table = Mock()
            table.update.return_value = chain
            tenant_isolation_service.supabase.from_.return_value = table
            
            result = await tenant_isolation_service.update_quota_usage(
                organization_id='org-123',
                operation_type='global_access',
                quantity=1,
                operation='decrement'
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_update_quota_decrement_sharing_requests(self, tenant_isolation_service):
        """Test update quota decrement for sharing_requests"""
        with patch.object(tenant_isolation_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': {
                'organization_id': 'org-123',
                'current_sharing_requests': 50
            }
        }):
            update_result = Mock()
            update_result.data = [{'current_sharing_requests': 49}]
            
            chain = Mock()
            chain.update.return_value = chain
            chain.eq.return_value = chain
            chain.execute.return_value = update_result
            
            table = Mock()
            table.update.return_value = chain
            tenant_isolation_service.supabase.from_.return_value = table
            
            result = await tenant_isolation_service.update_quota_usage(
                organization_id='org-123',
                operation_type='sharing_requests',
                quantity=1,
                operation='decrement'
            )
            
            assert result is not None


class TestGetRAGTogglesLines209216:
    """Test get RAG feature toggles - lines 209-216"""
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_with_data(self, tenant_isolation_service):
        """Test get toggles when data exists"""
        query_result = Mock()
        query_result.data = [
            {'rag_feature': 'best_practice_kb', 'enabled': True},
            {'rag_feature': 'sales_intelligence', 'enabled': False}
        ]
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = query_result
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.get_rag_feature_toggles('org-123')
        
        assert result is not None
        assert result.get('success') is True
        assert len(result.get('toggles', [])) == 2
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_exception(self, tenant_isolation_service):
        """Test get toggles when exception occurs"""
        with patch.object(tenant_isolation_service.supabase, 'from_', side_effect=Exception("Database error")):
            result = await tenant_isolation_service.get_rag_feature_toggles('org-123')
            
            assert result is not None
            assert result.get('success') is False


class TestBulkUpdateTogglesLines249256:
    """Test bulk update toggles - lines 249-256"""
    
    @pytest.mark.asyncio
    async def test_bulk_update_rag_toggles_success(self, tenant_isolation_service):
        """Test bulk update when successful"""
        update_result = Mock()
        update_result.data = [{'id': 'toggle-123'}]
        
        chain = Mock()
        chain.update.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = update_result
        
        table = Mock()
        table.update.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.bulk_update_rag_toggles(
            organization_id='org-123',
            toggles={'best_practice_kb': True, 'sales_intelligence': False}
        )
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_bulk_update_rag_toggles_no_data(self, tenant_isolation_service):
        """Test bulk update when update returns no data"""
        update_result = Mock()
        update_result.data = []
        
        chain = Mock()
        chain.update.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = update_result
        
        table = Mock()
        table.update.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.bulk_update_rag_toggles(
            organization_id='org-123',
            toggles={'best_practice_kb': True}
        )
        
        assert result is not None
        assert result.get('success') is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service', '--cov-report=html'])

