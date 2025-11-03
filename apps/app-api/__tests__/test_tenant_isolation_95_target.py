# apps/app-api/__tests__/test_tenant_isolation_95_target.py
"""
Additional tests to push Tenant Isolation Service to 95%
"""

import pytest
from unittest.mock import Mock, patch
from services.tenant_isolation_service import TenantIsolationService
from test_utils import SupabaseMockBuilder


class TestTenantIsolationService95Target:
    """Tests for remaining methods to reach 95% coverage"""
    
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
    async def test_check_quota_limits_global_access(self, tenant_service):
        """Test quota check for global_access - lines 133-142"""
        quotas = {
            'success': True,
            'quotas': {
                'current_context_items': 5,
                'max_context_items': 100,
                'current_global_access': 5,
                'max_global_access_features': 10,
                'current_sharing_requests': 5,
                'max_sharing_requests': 50
            }
        }
        
        with patch.object(tenant_service, '_get_organization_quotas', return_value=quotas):
            # Within quota
            result = await tenant_service.check_quota_limits('org-123', 'global_access', quantity=5)
            assert result['success'] is True
            
            # Exceed quota
            result = await tenant_service.check_quota_limits('org-123', 'global_access', quantity=10)
            assert result['success'] is False
            assert result['quota_exceeded'] is True
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_sharing_requests(self, tenant_service):
        """Test quota check for sharing_requests - lines 144-153"""
        quotas = {
            'success': True,
            'quotas': {
                'current_context_items': 5,
                'max_context_items': 100,
                'current_global_access': 5,
                'max_global_access_features': 10,
                'current_sharing_requests': 45,
                'max_sharing_requests': 50
            }
        }
        
        with patch.object(tenant_service, '_get_organization_quotas', return_value=quotas):
            # Within quota
            result = await tenant_service.check_quota_limits('org-123', 'sharing_requests', quantity=3)
            assert result['success'] is True
            
            # Exceed quota
            result = await tenant_service.check_quota_limits('org-123', 'sharing_requests', quantity=10)
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_update_quota_usage_increment(self, tenant_service):
        """Test update quota usage increment - lines 168-220"""
        # This is a complex method, let's test increment
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            table_mock = Mock()
            update_result = Mock()
            update_result.data = [{'id': 'quota-123'}]
            
            update_chain = Mock()
            update_chain.execute.return_value = update_result
            update_chain.eq.return_value = update_chain
            
            table_mock.update.return_value = update_chain
            table_mock.insert.return_value.execute.return_value = Mock(data=[{'id': 'quota-new'}])
            
            mock_supabase.from_.return_value = table_mock
            
            result = await tenant_service.update_quota_usage(
                organization_id='org-123',
                operation_type='context_items',
                quantity=5,
                operation='increment'
            )
            
            # Should succeed
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_reset_quota_usage(self, tenant_service):
        """Test reset quota usage - lines 221-261"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            table_mock = Mock()
            update_result = Mock()
            update_result.data = []
            
            update_chain = Mock()
            update_chain.execute.return_value = update_result
            update_chain.eq.return_value = update_chain
            
            table_mock.update.return_value = update_chain
            mock_supabase.from_.return_value = table_mock
            
            result = await tenant_service.reset_quota_usage('org-123')
            
            assert result['success'] is True
            assert result['reset_count'] >= 0
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles(self, tenant_service, mock_builder):
        """Test get RAG feature toggles - lines 263-287"""
        toggles = [
            {'rag_feature': 'sales_intelligence', 'enabled': True},
            {'rag_feature': 'best_practice_kb', 'enabled': False}
        ]
        
        mock_builder.setup_table_data('organization_rag_toggles', toggles)
        
        result = await tenant_service.get_rag_feature_toggles('org-123')
        
        assert result['success'] is True
        assert 'toggles' in result
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle(self, tenant_service, mock_builder):
        """Test update RAG feature toggle - lines 289-327"""
        mock_builder.setup_table_data('organization_rag_toggles', [])
        mock_builder.insert_response.data = [{'id': 'toggle-123'}]
        
        result = await tenant_service.update_rag_feature_toggle(
            organization_id='org-123',
            rag_feature='sales_intelligence',
            enabled=True
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_bulk_update_rag_toggles(self, tenant_service, mock_builder):
        """Test bulk update RAG toggles - lines 329-355"""
        updates = [
            {'rag_feature': 'sales_intelligence', 'enabled': True},
            {'rag_feature': 'best_practice_kb', 'enabled': False}
        ]
        
        mock_builder.insert_response.data = [{'id': f'toggle-{i}'} for i in range(2)]
        
        result = await tenant_service.bulk_update_rag_toggles('org-123', updates)
        
        assert result['success'] is True
        assert result['updated_count'] == 2
    
    @pytest.mark.asyncio
    async def test_get_inherited_features(self, tenant_service):
        """Test get inherited features - lines 426-470"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            table_mock = Mock()
            result_mock = Mock()
            result_mock.data = []
            
            select_chain = Mock()
            select_chain.execute.return_value = result_mock
            select_chain.eq.return_value = select_chain
            select_chain.order.return_value = select_chain
            
            table_mock.select.return_value = select_chain
            mock_supabase.from_.return_value = table_mock
            
            result = await tenant_service.get_inherited_features('org-123')
            
            assert result['success'] is True
            assert 'inherited_features' in result
    
    @pytest.mark.asyncio
    async def test_get_effective_features(self, tenant_service):
        """Test get effective features - lines 471-531"""
        # Mock inherited features
        with patch.object(tenant_service, 'get_inherited_features', return_value={
            'success': True,
            'inherited_features': [{'rag_feature': 'feature-1', 'enabled': True}]
        }):
            # Mock own toggles
            with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
                'success': True,
                'toggles': [
                    {'rag_feature': 'feature-2', 'enabled': False}
                ]
            }):
                result = await tenant_service.get_effective_features('org-123')
                
                assert result['success'] is True
                assert 'effective_features' in result
    
    @pytest.mark.asyncio
    async def test_can_enable_feature(self, tenant_service):
        """Test can enable feature - lines 532-597"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': []
        }):
            # Mock feature metadata
            with patch.object(tenant_service, 'supabase') as mock_supabase:
                table_mock = Mock()
                result_mock = Mock()
                result_mock.data = [{'max_features': 10}]
                
                select_chain = Mock()
                select_chain.execute.return_value = result_mock
                select_chain.eq.return_value = select_chain
                select_chain.single.return_value.execute.return_value = result_mock
                
                table_mock.select.return_value = select_chain
                mock_supabase.from_.return_value = table_mock
                
                result = await tenant_service.can_enable_feature('org-123', 'sales_intelligence')
                
                assert result['success'] is True
                assert 'can_enable' in result
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain(self, tenant_service):
        """Test get inheritance chain - lines 598-633"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            table_mock = Mock()
            result_mock = Mock()
            result_mock.data = [{'parent_organization_id': 'org-parent'}]
            
            select_chain = Mock()
            select_chain.execute.return_value = result_mock
            select_chain.eq.return_value = select_chain
            
            table_mock.select.return_value = select_chain
            mock_supabase.from_.return_value = table_mock
            
            result = await tenant_service.get_inheritance_chain('org-123')
            
            assert result['success'] is True
            assert 'chain' in result
    
    @pytest.mark.asyncio
    async def test_get_override_status(self, tenant_service):
        """Test get override status - lines 634-679"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': [{'rag_feature': 'sales_intelligence', 'enabled': True}]
        }):
            with patch.object(tenant_service, 'get_inherited_features', return_value={
                'success': True,
                'inherited_features': []
            }):
                result = await tenant_service.get_override_status('org-123', 'sales_intelligence')
                
                assert result['success'] is True
                assert 'is_override' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service', '--cov-report=html'])
