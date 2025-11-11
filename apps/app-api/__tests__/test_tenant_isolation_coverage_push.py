# apps/app-api/__tests__/test_tenant_isolation_coverage_push.py
"""
Push Tenant Isolation Service coverage from 23% to 95%
"""

import pytest
from unittest.mock import Mock, patch
from services.tenant_isolation_service import TenantIsolationService
from test_utils import SupabaseMockBuilder


class TestTenantIsolationCoveragePush:
    """Comprehensive tests to push coverage to 95%"""
    
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
    async def test_check_quota_limits_sharing_requests_exceeded(self, tenant_service):
        """Test quota exceeded for sharing_requests - lines 144-153"""
        quotas = {
            'success': True,
            'quotas': {
                'current_context_items': 5,
                'max_context_items': 100,
                'current_global_access': 2,
                'max_global_access_features': 10,
                'current_sharing_requests': 45,
                'max_sharing_requests': 50
            }
        }
        
        with patch.object(tenant_service, '_get_organization_quotas', return_value=quotas):
            result = await tenant_service.check_quota_limits('org-123', 'sharing_requests', quantity=10)
            
            assert result['success'] is False
            assert result['quota_exceeded'] is True
    
    @pytest.mark.asyncio
    async def test_update_quota_usage_decrement_operation(self, tenant_service):
        """Test update quota with decrement - lines 168-220"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            # Setup for decrement (reads first, then updates)
            table_mock = Mock()
            select_result = Mock()
            select_result.data = [{'current_context_items': 50}]
            
            select_chain = Mock()
            select_chain.execute.return_value = select_result
            select_chain.eq.return_value = select_chain
            select_chain.single.return_value.execute.return_value = select_result
            
            table_mock.select.return_value = select_chain
            
            update_result = Mock()
            update_result.data = [{'id': 'quota-123'}]
            update_chain = Mock()
            update_chain.execute.return_value = update_result
            update_chain.eq.return_value = update_chain
            table_mock.update.return_value = update_chain
            
            mock_supabase.from_.return_value = table_mock
            
            result = await tenant_service.update_quota_usage(
                organization_id='org-123',
                operation_type='context_items',
                quantity=5,
                operation='decrement'
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_empty(self, tenant_service, mock_builder):
        """Test get toggles with empty result"""
        mock_builder.setup_table_data('organization_rag_toggles', [])
        
        result = await tenant_service.get_rag_feature_toggles('org-123')
        
        assert result['success'] is True
        assert result['toggles'] == []
    
    @pytest.mark.asyncio
    async def test_get_inherited_features_with_parent(self, tenant_service):
        """Test get inherited features with parent org - lines 426-470"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            # Mock organization with parent
            org_table = Mock()
            org_result = Mock()
            org_result.data = [{'parent_organization_id': 'org-parent'}]
            org_select = Mock()
            org_select.execute.return_value = org_result
            org_select.eq.return_value = org_select
            org_table.select.return_value = org_select
            
            # Mock parent toggles
            toggles_table = Mock()
            toggles_result = Mock()
            toggles_result.data = [{'rag_feature': 'inherited-feature', 'enabled': True}]
            toggles_select = Mock()
            toggles_select.execute.return_value = toggles_result
            toggles_select.eq.return_value = toggles_select
            toggles_table.select.return_value = toggles_select
            
            def table_side_effect(table_name):
                if table_name == 'organizations':
                    return org_table
                elif table_name == 'organization_rag_toggles':
                    return toggles_table
            
            mock_supabase.from_.side_effect = table_side_effect
            
            result = await tenant_service.get_inherited_features('org-123')
            
            assert result['success'] is True
            assert 'inherited_features' in result
    
    @pytest.mark.asyncio
    async def test_get_effective_features_merges_toggles(self, tenant_service):
        """Test effective features merges own + inherited - lines 471-531"""
        # Mock own toggles
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': [
                {'rag_feature': 'own-feature', 'enabled': True}
            ]
        }):
            # Mock inherited features
            with patch.object(tenant_service, 'get_inherited_features', return_value={
                'success': True,
                'inherited_features': [
                    {'rag_feature': 'inherited-feature', 'enabled': False}
                ]
            }):
                result = await tenant_service.get_effective_features('org-123')
                
                assert result['success'] is True
                assert 'effective_features' in result
                assert len(result['effective_features']) == 2
    
    @pytest.mark.asyncio
    async def test_can_enable_feature_at_limit(self, tenant_service):
        """Test can enable when at limit - lines 532-597"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': [
                {'rag_feature': 'feature-1', 'enabled': True},
                {'rag_feature': 'feature-2', 'enabled': True},
                {'rag_feature': 'feature-3', 'enabled': True}
            ]
        }):
            # Mock metadata with limit of 3
            with patch.object(tenant_service, 'supabase') as mock_supabase:
                table_mock = Mock()
                metadata_result = Mock()
                metadata_result.data = [{'max_features': 3}]
                
                select_chain = Mock()
                select_chain.execute.return_value = metadata_result
                select_chain.single.return_value.execute.return_value = metadata_result
                select_chain.eq.return_value = select_chain
                
                table_mock.select.return_value = select_chain
                mock_supabase.from_.return_value = table_mock
                
                result = await tenant_service.can_enable_feature('org-123', 'new-feature')
                
                assert result['success'] is True
                # Should not be able to enable (at limit)
                assert result['can_enable'] is False
                assert 'max_features_reached' in result['reason']
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_flat_structure(self, tenant_service):
        """Test inheritance chain with flat structure - lines 598-633"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            table_mock = Mock()
            # No parent - flat structure
            result_mock = Mock()
            result_mock.data = []
            
            select_chain = Mock()
            select_chain.execute.return_value = result_mock
            select_chain.eq.return_value = select_chain
            
            table_mock.select.return_value = select_chain
            mock_supabase.from_.return_value = table_mock
            
            result = await tenant_service.get_inheritance_chain('org-123')
            
            assert result['success'] is True
            assert 'chain' in result
            assert result['is_at_top'] is True
    
    @pytest.mark.asyncio
    async def test_get_override_status_with_override(self, tenant_service):
        """Test override status when override exists - lines 634-679"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': [{'rag_feature': 'sales_intelligence', 'enabled': True}]
        }):
            with patch.object(tenant_service, 'get_inherited_features', return_value={
                'success': True,
                'inherited_features': [
                    {'rag_feature': 'sales_intelligence', 'enabled': False}  # Different from own
                ]
            }):
                result = await tenant_service.get_override_status('org-123', 'sales_intelligence')
                
                assert result['success'] is True
                assert result['is_override'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service', '--cov-report=html'])

