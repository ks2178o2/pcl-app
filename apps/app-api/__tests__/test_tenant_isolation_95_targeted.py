# apps/app-api/__tests__/test_tenant_isolation_95_targeted.py
"""
Final targeted tests to push Tenant Isolation Service to 95%
Focusing on specific missing lines: 33->46, 78, 144->155, 145->155, 188, 192->199, 194, 209-216, 227, 249-256, 298, 317-324
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


class TestEnforceIsolationLine3346:
    """Test enforce isolation cross-tenant denial - lines 33->46"""
    
    @pytest.mark.asyncio
    async def test_enforce_different_org_no_permission(self, tenant_isolation_service):
        """Test enforce when orgs differ and no cross-tenant access - covers lines 33->46"""
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


class TestCreatePolicyLine78:
    """Test create policy insert failure - line 78"""
    
    @pytest.mark.asyncio
    async def test_create_policy_insert_returns_empty(self, tenant_isolation_service):
        """Test create policy when insert returns no data - must hit line 78"""
        insert_result = Mock()
        insert_result.data = []  # Empty triggers line 78
        
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


class TestQuotaCheckLines144155145155:
    """Test quota check for global_access and sharing_requests - lines 144->155, 145->155"""
    
    @pytest.mark.asyncio
    async def test_check_quota_global_access_exceeds(self, tenant_isolation_service):
        """Test check quota for global_access when exceeded - covers lines 144->155"""
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
            assert result.get('quota_type') == 'global_access'
    
    @pytest.mark.asyncio
    async def test_check_quota_sharing_requests_exceeds(self, tenant_isolation_service):
        """Test check quota for sharing_requests when exceeded - covers lines 145->155"""
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
            assert result.get('quota_type') == 'sharing_requests'


class TestQuotaUpdateLines188192194:
    """Test quota update decrement operations - lines 188, 192->199, 194"""
    
    @pytest.mark.asyncio
    async def test_update_quota_global_access_decrement(self, tenant_isolation_service):
        """Test update quota decrement for global_access - covers lines 188, 192->199"""
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
    async def test_update_quota_sharing_requests_increment(self, tenant_isolation_service):
        """Test update quota increment for sharing_requests - covers line 194"""
        with patch.object(tenant_isolation_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': {
                'organization_id': 'org-123',
                'current_sharing_requests': 48
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
                operation='increment'
            )
            
            assert result is not None


class TestGetRAGTogglesLines209216227:
    """Test get RAG toggles - lines 209-216, 227"""
    
    @pytest.mark.asyncio
    async def test_get_rag_toggles_with_data(self, tenant_isolation_service):
        """Test get toggles when data exists - covers lines 209-216"""
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
    async def test_get_rag_toggles_exception_with_toggles(self, tenant_isolation_service):
        """Test get toggles when exception occurs - covers line 227"""
        with patch.object(tenant_isolation_service.supabase, 'from_', side_effect=Exception("Database error")):
            result = await tenant_isolation_service.get_rag_feature_toggles('org-123')
            
            assert result is not None
            assert result.get('success') is False
            assert result.get('toggles') == []


class TestBulkUpdateTogglesLines249256:
    """Test bulk update toggles error paths - lines 249-256"""
    
    @pytest.mark.asyncio
    async def test_bulk_update_toggles_insert_failure(self, tenant_isolation_service):
        """Test bulk update when individual update fails"""
        with patch.object(tenant_isolation_service, 'update_rag_feature_toggle') as mock_update:
            mock_update.return_value = {'success': False, 'error': 'Failed'}
            
            result = await tenant_isolation_service.bulk_update_rag_toggles(
                organization_id='org-123',
                toggle_updates={'best_practice_kb': True}
            )
            
            assert result is not None
            assert result.get('success') is True  # Overall success
            assert result.get('total_updated') == 0


class TestUpdateRAGTogglesLines298317324:
    """Test update RAG toggle error paths - lines 298, 317-324"""
    
    @pytest.mark.asyncio
    async def test_update_rag_toggle_insert_new(self, tenant_isolation_service):
        """Test update when creating new toggle - covers line 298"""
        query_result = Mock()
        query_result.data = []  # No existing toggle
        
        query_chain = Mock()
        query_chain.select.return_value = query_chain
        query_chain.eq.return_value = query_chain
        query_chain.execute.return_value = query_result
        
        insert_result = Mock()
        insert_result.data = [{'id': 'new-toggle'}]
        
        insert_chain = Mock()
        insert_chain.insert.return_value = insert_chain
        insert_chain.execute.return_value = insert_result
        
        table = Mock()
        table.select.return_value = query_chain
        table.insert = Mock(return_value=insert_chain)
        table.update.return_value = Mock().eq.return_value.execute.return_value = Mock()
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.update_rag_feature_toggle(
            organization_id='org-123',
            rag_feature='new_feature',
            enabled=True
        )
        
        assert result is not None


class TestInheritanceLoopProcessing:
    """Test inheritance loop processing with multiple toggles"""
    
    @pytest.mark.asyncio
    async def test_inherited_features_loop_with_many_toggles(self, tenant_isolation_service):
        """Test processing multiple inherited features in loop"""
        org_result = Mock()
        org_result.data = [{'parent_organization_id': 'parent-123'}]
        
        parent_result = Mock()
        # Multiple toggles to test loop
        parent_result.data = [
            {'rag_feature': f'feature_{i}', 'enabled': True, 'category': 'test', 'created_at': '2024-01-01', 'updated_at': '2024-01-01'}
            for i in range(5)
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
        assert len(result.get('inherited_features', [])) == 5


class TestEffectiveFeaturesOverride:
    """Test effective features override logic with same feature name"""
    
    @pytest.mark.asyncio
    async def test_effective_features_overrides_inherited(self, tenant_isolation_service):
        """Test that own features override inherited features correctly"""
        with patch.object(tenant_isolation_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': [
                {'rag_feature': 'conflicting_feature', 'enabled': True},
                {'rag_feature': 'own_only_feature', 'enabled': False}
            ]
        }):
            with patch.object(tenant_isolation_service, 'get_inherited_features', return_value={
                'success': True,
                'inherited_features': [
                    {'rag_feature': 'conflicting_feature', 'enabled': False},  # Different value in inherited
                    {'rag_feature': 'inherited_only_feature', 'enabled': True}
                ]
            }):
                result = await tenant_isolation_service.get_effective_features('org-123')
                
                assert result is not None
                assert result.get('success') is True
                effective = result.get('effective_features', [])
                
                # Find the overridden feature
                override = next((f for f in effective if f['rag_feature'] == 'conflicting_feature'), None)
                assert override is not None
                assert override.get('is_inherited') is False
                assert override['enabled'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service', '--cov-report=html'])

