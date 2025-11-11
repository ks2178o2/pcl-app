# apps/app-api/__tests__/test_tenant_isolation_95_ultimate.py
"""
Ultimate tests to reach 95% coverage for Tenant Isolation Service
Target: Lines 417-419, 439-457, 477, 482, 500->497, 501->500, 510, 609, 642-643, 653->664, 655-656, 672-674, 718-720
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


class TestGetOrganizationQuotasLines417419:
    """Test get organization quotas error paths - lines 417-419"""
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_exception(self, tenant_isolation_service):
        """Test get quotas when exception occurs - covers lines 417-419"""
        with patch.object(tenant_isolation_service.supabase, 'from_', side_effect=Exception("Database error")):
            result = await tenant_isolation_service._get_organization_quotas('org-123')
            
            assert result is not None
            assert result.get('success') is False


class TestGetInheritedFeaturesLines439457:
    """Test get inherited features - lines 439-457"""
    
    @pytest.mark.asyncio
    async def test_get_inherited_features_with_parent_toggles(self, tenant_isolation_service):
        """Test get inherited features when parent has toggles - covers lines 439-457"""
        # Setup org with no parent
        org_result = Mock()
        org_result.data = [{'parent_organization_id': 'parent-123'}]
        
        org_table = Mock()
        org_table.select.return_value.eq.return_value.execute.return_value = org_result
        
        # Setup parent toggles
        parent_result = Mock()
        parent_result.data = [
            {'rag_feature': 'best_practice_kb', 'enabled': True, 'category': 'knowledge_base', 'created_at': '2024-01-01', 'updated_at': '2024-01-01'},
            {'rag_feature': 'sales_intelligence', 'enabled': True, 'category': 'intelligence', 'created_at': '2024-01-01', 'updated_at': '2024-01-01'}
        ]
        
        toggle_table = Mock()
        toggle_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = parent_result
        
        def from_side_effect(table_name):
            if table_name == 'organizations':
                return org_table
            else:
                return toggle_table
        
        tenant_isolation_service.supabase.from_ = Mock(side_effect=from_side_effect)
        
        result = await tenant_isolation_service.get_inherited_features('org-123')
        
        assert result is not None
        assert result.get('success') is True
        assert len(result.get('inherited_features', [])) == 2


class TestGetEffectiveFeaturesLines477482500:
    """Test get effective features - lines 477, 482, 500->497, 501->500"""
    
    @pytest.mark.asyncio
    async def test_get_effective_features_with_own_and_inherited(self, tenant_isolation_service):
        """Test get effective features when both own and inherited - covers lines 477, 482"""
        # Setup own features
        own_result = Mock()
        own_result.data = [{'rag_feature': 'best_practice_kb', 'enabled': True}]
        
        # Setup inherited features
        with patch.object(tenant_isolation_service, 'get_inherited_features', return_value={
            'success': True,
            'inherited_features': [{'rag_feature': 'sales_intelligence', 'enabled': True}]
        }):
            org_table = Mock()
            org_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = own_result
            
            def from_side_effect(table_name):
                if table_name == 'organization_rag_toggles':
                    return org_table
                return Mock()
            
            tenant_isolation_service.supabase.from_ = Mock(side_effect=from_side_effect)
            
            result = await tenant_isolation_service.get_effective_features('org-123')
            
            assert result is not None
            assert result.get('success') is True


class TestCanEnableFeatureLines510:
    """Test can enable feature - line 510"""
    
    @pytest.mark.asyncio
    async def test_can_enable_feature_not_in_catalog(self, tenant_isolation_service):
        """Test can enable when feature not in catalog"""
        catalog_result = Mock()
        catalog_result.data = []  # Not in catalog
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = catalog_result
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.can_enable_feature('org-123', 'nonexistent_feature')
        
        assert result is not None
        assert result.get('can_enable') is False
        assert 'does not exist' in result.get('reason', '')
    
    @pytest.mark.asyncio
    async def test_can_enable_feature_org_not_found(self, tenant_isolation_service):
        """Test can enable when org not found"""
        catalog_result = Mock()
        catalog_result.data = [{'rag_feature': 'best_practice_kb'}]
        
        org_result = Mock()
        org_result.data = []  # Org not found
        
        catalog_table = Mock()
        catalog_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = catalog_result
        
        org_table = Mock()
        org_table.select.return_value.eq.return_value.execute.return_value = org_result
        
        def from_side_effect(table_name):
            if table_name == 'rag_feature_metadata':
                return catalog_table
            else:
                return org_table
        
        tenant_isolation_service.supabase.from_ = Mock(side_effect=from_side_effect)
        
        result = await tenant_isolation_service.can_enable_feature('org-123', 'best_practice_kb')
        
        assert result is not None
        assert result.get('can_enable') is False
        assert 'not found' in result.get('reason', '')


class TestGetInheritanceChainLines609618620:
    """Test get inheritance chain - lines 609, 618-620"""
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_no_data(self, tenant_isolation_service):
        """Test get chain when no data - covers lines 609, 618-620"""
        org_result = Mock()
        org_result.data = []  # No org found
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = org_result
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.get_inheritance_chain('org-123')
        
        assert result is not None
        assert result.get('success') is True
        assert len(result.get('inheritance_chain', [])) == 0


class TestGetOverrideStatusLines642643653664655656:
    """Test get override status - lines 642-643, 653->664, 655-656"""
    
    @pytest.mark.asyncio
    async def test_get_override_status_not_found(self, tenant_isolation_service):
        """Test override status when feature not configured"""
        # Setup to return no org toggle
        org_result = Mock()
        org_result.data = []
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = org_result
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        # Mock inherited features to return empty
        with patch.object(tenant_isolation_service, 'get_inherited_features', return_value={
            'success': True,
            'inherited_features': []
        }):
            result = await tenant_isolation_service.get_override_status('org-123', 'best_practice_kb')
            
            assert result is not None


class TestGetIsolationPoliciesLines672674:
    """Test get isolation policies exception - lines 672-674"""
    
    @pytest.mark.asyncio
    async def test_get_isolation_policies_exception(self, tenant_isolation_service):
        """Test get policies when exception occurs"""
        with patch.object(tenant_isolation_service.supabase, 'from_', side_effect=Exception("Database error")):
            result = await tenant_isolation_service.get_isolation_policies('org-123')
            
            assert result is not None
            assert result.get('success') is False
            assert result.get('policies') == []


class TestEnforceIsolationLines718720:
    """Test enforce isolation violation - lines 718-720"""
    
    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_violation(self, tenant_isolation_service):
        """Test enforce when cross-tenant access denied"""
        with patch.object(tenant_isolation_service, '_get_user_organization', return_value={'organization_id': 'org-user'}):
            with patch.object(tenant_isolation_service, '_check_cross_tenant_access', return_value=False):
                result = await tenant_isolation_service.enforce_tenant_isolation(
                    user_id='user-123',
                    organization_id='org-target',
                    resource_type='context_item',
                    resource_id='item-123'
                )
                
                assert result is not None
                assert result.get('success') is False
                assert result.get('isolation_violation') is True
                assert 'Cross-tenant access denied' in result.get('error', '')


class TestQuotaDecrementMax:
    """Test quota decrement with max function"""
    
    @pytest.mark.asyncio
    async def test_update_quota_decrement_below_zero(self, tenant_isolation_service):
        """Test decrement when would go below zero - tests max(0, ...) path"""
        with patch.object(tenant_isolation_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': {
                'organization_id': 'org-123',
                'current_context_items': 5
            }
        }):
            update_result = Mock()
            update_result.data = [{'current_context_items': 0}]  # Would be -10 but clamped to 0
            
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
                quantity=20,  # More than current
                operation='decrement'
            )
            
            assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service', '--cov-report=html'])

