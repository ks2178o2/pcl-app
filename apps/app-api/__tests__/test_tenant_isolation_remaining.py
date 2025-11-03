# apps/app-api/__tests__/test_tenant_isolation_remaining.py
"""
Tests for remaining lines to push coverage to 95%
"""

import pytest
from unittest.mock import Mock, patch
from services.tenant_isolation_service import TenantIsolationService


class TestTenantIsolationRemaining:
    """Tests for remaining coverage gaps"""
    
    @pytest.fixture
    def tenant_service(self):
        """Create tenant isolation service"""
        with patch('services.tenant_isolation_service.get_supabase_client'):
            return TenantIsolationService()
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_exception(self, tenant_service):
        """Test check quota limits exception handling - lines 161-166"""
        with patch.object(tenant_service, '_get_organization_quotas', side_effect=Exception("Quota error")):
            result = await tenant_service.check_quota_limits('org-123', 'context_items')
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_update_quota_usage_decrement(self, tenant_service):
        """Test update quota usage decrement - lines 168-220"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            table_mock = Mock()
            update_result = Mock()
            update_result.data = [{'usage': 50}]
            
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
                operation='decrement'
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_update_quota_usage_exception(self, tenant_service):
        """Test update quota usage exception - lines 217-220"""
        with patch.object(tenant_service, 'supabase', side_effect=Exception("Update error")):
            result = await tenant_service.update_quota_usage(
                organization_id='org-123',
                operation_type='context_items',
                quantity=5,
                operation='increment'
            )
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_reset_quota_usage_exception(self, tenant_service):
        """Test reset quota exception - lines 252-256"""
        with patch.object(tenant_service, 'supabase', side_effect=Exception("Reset error")):
            result = await tenant_service.reset_quota_usage('org-123')
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_exception(self, tenant_service):
        """Test get toggles exception - lines 278-283"""
        with patch.object(tenant_service, 'supabase', side_effect=Exception("Toggles error")):
            result = await tenant_service.get_rag_feature_toggles('org-123')
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_exception(self, tenant_service):
        """Test update toggle exception - lines 318-324"""
        with patch.object(tenant_service, 'supabase', side_effect=Exception("Update toggle error")):
            result = await tenant_service.update_rag_feature_toggle(
                organization_id='org-123',
                rag_feature='sales_intelligence',
                enabled=True
            )
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_bulk_update_rag_toggles_exception(self, tenant_service):
        """Test bulk update exception - lines 338-342"""
        updates = [{'rag_feature': 'sales_intelligence', 'enabled': True}]
        
        with patch.object(tenant_service, 'supabase', side_effect=Exception("Bulk update error")):
            result = await tenant_service.bulk_update_rag_toggles('org-123', updates)
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_inherited_features_exception(self, tenant_service):
        """Test get inherited features exception - lines 461-465"""
        with patch.object(tenant_service, 'supabase', side_effect=Exception("Inherited error")):
            result = await tenant_service.get_inherited_features('org-123')
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_effective_features_exception(self, tenant_service):
        """Test get effective features exception - lines 518-522"""
        with patch.object(tenant_service, 'get_inherited_features', side_effect=Exception("Effective error")):
            result = await tenant_service.get_effective_features('org-123')
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_can_enable_feature_exception(self, tenant_service):
        """Test can enable feature exception - lines 584-588"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', side_effect=Exception("Enable error")):
            result = await tenant_service.can_enable_feature('org-123', 'sales_intelligence')
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_exception(self, tenant_service):
        """Test get inheritance chain exception - lines 612-616"""
        with patch.object(tenant_service, 'supabase', side_effect=Exception("Chain error")):
            result = await tenant_service.get_inheritance_chain('org-123')
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_override_status_exception(self, tenant_service):
        """Test get override status exception - lines 655-656"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', side_effect=Exception("Override error")):
            result = await tenant_service.get_override_status('org-123', 'sales_intelligence')
            
            assert result['success'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service'])

