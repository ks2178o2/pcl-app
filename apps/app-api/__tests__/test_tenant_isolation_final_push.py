# apps/app-api/__tests__/test_tenant_isolation_final_push.py
"""
Final push to 95% coverage for Tenant Isolation Service
Focus on missing lines: 388-419, 445-465, 566-592, 605-679
"""

import pytest
from unittest.mock import Mock, patch
from services.tenant_isolation_service import TenantIsolationService
from test_utils import SupabaseMockBuilder


class TestTenantIsolationFinalPush:
    """Tests for remaining coverage to reach 95%"""
    
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
    async def test_get_organization_quotas_with_data(self, tenant_service, mock_builder):
        """Test get quotas when data exists - lines 388-397"""
        quotas_data = {
            'organization_id': 'org-123',
            'max_context_items': 1000,
            'current_context_items': 50
        }
        
        mock_builder.setup_table_data('organization_context_quotas', [quotas_data])
        
        result = await tenant_service._get_organization_quotas('org-123')
        
        assert result['success'] is True
        assert 'quotas' in result
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_create_default(self, tenant_service, mock_builder):
        """Test get quotas creates default when missing - lines 398-415"""
        # Mock no quotas exist
        mock_builder.setup_table_data('organization_context_quotas', [])
        mock_builder.insert_response.data = [{
            'organization_id': 'org-123',
            'max_context_items': 1000
        }]
        
        result = await tenant_service._get_organization_quotas('org-123')
        
        assert result['success'] is True
        assert 'quotas' in result
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_exception(self, tenant_service):
        """Test get quotas exception handling - lines 417-419"""
        tenant_service.supabase.from_.side_effect = Exception("Quotas error")
        
        result = await tenant_service._get_organization_quotas('org-123')
        
        assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_inherited_features_with_parent_data(self, tenant_service):
        """Test get inherited features with parent data - lines 426-465"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            # Mock org with parent
            def table_side_effect(table_name):
                if table_name == 'organizations':
                    table = Mock()
                    result = Mock()
                    result.data = [{'parent_organization_id': 'org-parent'}]
                    select = Mock()
                    select.execute.return_value = result
                    select.eq.return_value = select
                    table.select.return_value = select
                    return table
                elif table_name == 'organization_rag_toggles':
                    table = Mock()
                    result = Mock()
                    result.data = [{'rag_feature': 'inherited', 'enabled': True}]
                    select = Mock()
                    select.execute.return_value = result
                    select.eq.return_value = select
                    table.select.return_value = select
                    return table
            
            mock_supabase.from_.side_effect = table_side_effect
            
            result = await tenant_service.get_inherited_features('org-123')
            
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_get_inherited_features_no_parent(self, tenant_service):
        """Test get inherited features without parent"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            table = Mock()
            result_mock = Mock()
            result_mock.data = []  # No parent
            select = Mock()
            select.execute.return_value = result_mock
            select.eq.return_value = select
            table.select.return_value = select
            mock_supabase.from_.return_value = table
            
            result = await tenant_service.get_inherited_features('org-123')
            
            assert result['success'] is True
            assert result['inherited_features'] == []
    
    @pytest.mark.asyncio
    async def test_can_enable_feature_not_at_limit(self, tenant_service):
        """Test can enable feature when not at limit - lines 532-597"""
        # Mock less toggles than max
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': [{'rag_feature': 'feature-1', 'enabled': True}]
        }):
            with patch.object(tenant_service, 'supabase') as mock_supabase:
                table = Mock()
                metadata = Mock()
                metadata.data = [{'max_features': 10}]
                
                select = Mock()
                select.execute.return_value = metadata
                select.eq.return_value = select
                select.single.return_value.execute.return_value = metadata
                
                table.select.return_value = select
                mock_supabase.from_.return_value = table
                
                result = await tenant_service.can_enable_feature('org-123', 'new-feature')
                
                assert result['success'] is True
                assert result['can_enable'] is True
    
    @pytest.mark.asyncio
    async def test_can_enable_feature_already_enabled(self, tenant_service):
        """Test can enable feature that's already enabled"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': [{'rag_feature': 'sales_intelligence', 'enabled': True}]
        }):
            result = await tenant_service.can_enable_feature('org-123', 'sales_intelligence')
            
            assert result['success'] is True
            assert result['can_enable'] is False  # Already enabled
            assert 'already' in result['reason'].lower()
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_with_parent(self, tenant_service):
        """Test inheritance chain with parent - lines 598-633"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            table = Mock()
            result_mock = Mock()
            result_mock.data = [{'parent_organization_id': 'org-parent'}]
            
            select = Mock()
            select.execute.return_value = result_mock
            select.eq.return_value = select
            
            table.select.return_value = select
            mock_supabase.from_.return_value = table
            
            result = await tenant_service.get_inheritance_chain('org-123')
            
            assert result['success'] is True
            assert 'chain' in result
            assert result['is_at_top'] is False
    
    @pytest.mark.asyncio
    async def test_get_override_status_no_override(self, tenant_service):
        """Test override status when no override - lines 634-679"""
        # Mock same values (no override)
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': [{'rag_feature': 'sales_intelligence', 'enabled': True}]
        }):
            with patch.object(tenant_service, 'get_inherited_features', return_value={
                'success': True,
                'inherited_features': [{'rag_feature': 'sales_intelligence', 'enabled': True}]
            }):
                result = await tenant_service.get_override_status('org-123', 'sales_intelligence')
                
                assert result['success'] is True
                assert result['is_override'] is False
    
    @pytest.mark.asyncio
    async def test_get_override_status_feature_not_found(self, tenant_service):
        """Test override status when feature not found"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': []  # Feature not found
        }):
            result = await tenant_service.get_override_status('org-123', 'nonexistent')
            
            assert result['success'] is True
            # Should handle not found gracefully
    
    @pytest.mark.asyncio
    async def test_get_effective_features_resolves_conflicts(self, tenant_service):
        """Test effective features resolves conflicts - lines 471-531"""
        # Own overrides inherited
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': [{'rag_feature': 'feature-1', 'enabled': True}]
        }):
            with patch.object(tenant_service, 'get_inherited_features', return_value={
                'success': True,
                'inherited_features': [{'rag_feature': 'feature-1', 'enabled': False}]
            }):
                result = await tenant_service.get_effective_features('org-123')
                
                assert result['success'] is True
                assert result['effective_features'] is not None
                # Should use own value (True) over inherited (False)
                enabled_features = [f for f in result['effective_features'] if f['enabled']]
                assert len(enabled_features) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service', '--cov-report=html'])

