# apps/app-api/__tests__/test_tenant_isolation_95_complete_final.py
"""
Complete 95% coverage for Tenant Isolation Service
Target: Lines 445->457, 477, 482, 500->497, 501->500, 510, 605->620, 642-643, 653->664, 655-656, 672-674, 718-720
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


class TestInheritedFeaturesLoop445457:
    """Test inherited features loop processing - lines 445->457"""
    
    @pytest.mark.asyncio
    async def test_get_inherited_features_processes_all_toggles(self, tenant_isolation_service):
        """Test that all parent toggles are processed - covers lines 445->457"""
        org_result = Mock()
        org_result.data = [{'parent_organization_id': 'parent-123'}]
        
        parent_result = Mock()
        parent_result.data = [
            {
                'rag_feature': 'best_practice_kb',
                'enabled': True,
                'category': 'knowledge_base',
                'created_at': '2024-01-01T00:00:00',
                'updated_at': '2024-01-01T00:00:00'
            },
            {
                'rag_feature': 'sales_intelligence',
                'enabled': True,
                'category': 'intelligence',
                'created_at': '2024-01-02T00:00:00',
                'updated_at': '2024-01-02T00:00:00'
            }
        ]
        
        org_table = Mock()
        org_table.select.return_value.eq.return_value.execute.return_value = org_result
        
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
        inherited = result.get('inherited_features', [])
        assert len(inherited) == 2
        assert all(f.get('is_inherited') for f in inherited)
        assert all(f.get('inherited_from') == 'parent-123' for f in inherited)


class TestEffectiveFeaturesLines477482500501:
    """Test effective features logic - lines 477, 482, 500->497, 501->500"""
    
    @pytest.mark.asyncio
    async def test_get_effective_features_own_fails(self, tenant_isolation_service):
        """Test get effective when own features fail - covers line 477"""
        with patch.object(tenant_isolation_service, 'get_rag_feature_toggles', return_value={'success': False, 'error': 'Failed'}):
            result = await tenant_isolation_service.get_effective_features('org-123')
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_get_effective_features_inherited_fails(self, tenant_isolation_service):
        """Test get effective when inherited features fail - covers line 482"""
        with patch.object(tenant_isolation_service, 'get_rag_feature_toggles', return_value={'success': True, 'toggles': []}):
            with patch.object(tenant_isolation_service, 'get_inherited_features', return_value={'success': False, 'error': 'Failed'}):
                result = await tenant_isolation_service.get_effective_features('org-123')
                
                assert result is not None
                assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_get_effective_features_override_logic(self, tenant_isolation_service):
        """Test effective features when own features override inherited - covers lines 500->497, 501->500"""
        with patch.object(tenant_isolation_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': [
                {'rag_feature': 'best_practice_kb', 'enabled': False}  # Override inherited
            ]
        }):
            with patch.object(tenant_isolation_service, 'get_inherited_features', return_value={
                'success': True,
                'inherited_features': [
                    {'rag_feature': 'best_practice_kb', 'enabled': True}  # Inherited from parent
                ]
            }):
                result = await tenant_isolation_service.get_effective_features('org-123')
                
                assert result is not None
                assert result.get('success') is True
                effective = result.get('effective_features', [])
                # Find the override feature
                override_feature = next((f for f in effective if f['rag_feature'] == 'best_practice_kb'), None)
                if override_feature:
                    assert override_feature['is_inherited'] is False
                    assert override_feature['inherited_from'] is None


class TestEffectiveFeaturesLine510:
    """Test effective features adding new own feature - line 510"""
    
    @pytest.mark.asyncio
    async def test_get_effective_features_adds_new_own_feature(self, tenant_isolation_service):
        """Test effective features when own feature doesn't exist in inherited - covers line 510"""
        with patch.object(tenant_isolation_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': [
                {'rag_feature': 'custom_feature', 'enabled': True}  # New own feature
            ]
        }):
            with patch.object(tenant_isolation_service, 'get_inherited_features', return_value={
                'success': True,
                'inherited_features': [
                    {'rag_feature': 'inherited_feature', 'enabled': True}
                ]
            }):
                result = await tenant_isolation_service.get_effective_features('org-123')
                
                assert result is not None
                assert result.get('success') is True
                effective = result.get('effective_features', [])
                assert len(effective) == 2  # Both inherited and own
                custom_feature = next((f for f in effective if f['rag_feature'] == 'custom_feature'), None)
                if custom_feature:
                    assert custom_feature['is_inherited'] is False


class TestInheritanceChainLines605620618:
    """Test inheritance chain loop - lines 605->620, 618"""
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_multiple_levels(self, tenant_isolation_service):
        """Test inheritance chain with multiple parent levels"""
        org_data = [
            {'id': 'org-1', 'name': 'Level 1', 'parent_organization_id': None},
            {'id': 'org-2', 'name': 'Level 2', 'parent_organization_id': 'org-1'},
            {'id': 'org-3', 'name': 'Level 3', 'parent_organization_id': 'org-2'}
        ]
        
        call_count = 0
        
        def org_side_effect():
            nonlocal call_count
            if call_count < len(org_data):
                result = Mock()
                result.data = [org_data[call_count]]
                call_count += 1
                return result
            return Mock(data=[])
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.side_effect = org_side_effect
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.get_inheritance_chain('org-3')
        
        assert result is not None
        assert result.get('success') is True
        inheritance_chain = result.get('inheritance_chain', [])
        assert len(inheritance_chain) >= 1


class TestOverrideStatusLines642643653664655656:
    """Test override status - lines 642-643, 653->664, 655-656"""
    
    @pytest.mark.asyncio
    async def test_get_override_status_explicit_setting(self, tenant_isolation_service):
        """Test override status with explicit org setting - covers lines 642-643"""
        org_result = Mock()
        org_result.data = [{'enabled': True}]
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = org_result
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.get_override_status('org-123', 'best_practice_kb')
        
        assert result is not None
        assert result.get('success') is True
        assert result.get('status') == 'enabled'
        assert result.get('is_inherited') is False
    
    @pytest.mark.asyncio
    async def test_get_override_status_inherited_feature(self, tenant_isolation_service):
        """Test override status when feature is inherited - covers lines 653->664, 655-656"""
        org_result = Mock()
        org_result.data = []  # No explicit setting
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = org_result
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        with patch.object(tenant_isolation_service, 'get_inherited_features', return_value={
            'success': True,
            'inherited_features': [
                {'rag_feature': 'best_practice_kb', 'inherited_from': 'parent-123'}
            ]
        }):
            result = await tenant_isolation_service.get_override_status('org-123', 'best_practice_kb')
            
            assert result is not None
            assert result.get('success') is True
            assert result.get('status') == 'inherited'
            assert result.get('is_inherited') is True


class TestOverrideStatusLines672674:
    """Test override status exception - lines 672-674"""
    
    @pytest.mark.asyncio
    async def test_get_override_status_exception(self, tenant_isolation_service):
        """Test override status when exception occurs - covers lines 672-674"""
        with patch.object(tenant_isolation_service.supabase, 'from_', side_effect=Exception("Database error")):
            result = await tenant_isolation_service.get_override_status('org-123', 'best_practice_kb')
            
            assert result is not None
            assert result.get('success') is False
            assert result.get('status') == 'unknown'


class TestEnforceIsolationLines718720:
    """Test enforce isolation violation - lines 718-720"""
    
    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_cross_tenant_denied(self, tenant_isolation_service):
        """Test enforce when cross-tenant access is denied - covers lines 718-720"""
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


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service', '--cov-report=html'])

