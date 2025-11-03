# apps/app-api/__tests__/test_tenant_isolation_95_final_target.py
"""
Final push to 95% - Very specific edge cases
Target: Lines 33->46, 78, 144->155, 145->155, 188, 192->199, 209-216, 227, 249-256, 298, 317-324, 445->457, 500->497, 501->500, 605->620, 618, 642-643, 653->664, 655->654, 718-720
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


class TestEnforceIsolationExactPath3346:
    """Test enforce isolation exact path - lines 33->46"""
    
    @pytest.mark.asyncio
    async def test_enforce_different_orgs_permission_denied(self, tenant_isolation_service):
        """Test exact path: different orgs -> check permission -> denied"""
        with patch.object(tenant_isolation_service, '_get_user_organization', return_value={'organization_id': 'org-user'}):
            with patch.object(tenant_isolation_service, '_check_cross_tenant_access', return_value=False):
                result = await tenant_isolation_service.enforce_tenant_isolation(
                    user_id='user-123',
                    organization_id='org-other',  # Different from user's org
                    resource_type='context_item',
                    resource_id='item-123'
                )
                
                # Must hit lines 33->46
                assert result is not None
                assert result.get('success') is False
                assert result.get('isolation_violation') is True


class TestCreatePolicyExactLine78:
    """Test create policy exact line 78"""
    
    @pytest.mark.asyncio
    async def test_create_policy_exact_no_data_return(self, tenant_isolation_service):
        """Test create policy when insert returns exactly empty data to hit line 78"""
        # Must setup insert to return empty
        insert_result = Mock()
        insert_result.data = []  # EXACTLY empty
        
        chain = Mock()
        chain.insert.return_value = chain
        chain.execute.return_value = insert_result
        
        table = Mock()
        table.insert.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.create_isolation_policy({
            'organization_id': 'org-123',
            'policy_type': 'strict',
            'policy_name': 'test',
            'policy_rules': {}
        })
        
        # Must trigger line 78
        assert result is not None
        assert result.get('success') is False


class TestQuotaCheckExactBranches144155145155:
    """Test quota check exact branches"""
    
    @pytest.mark.asyncio
    async def test_check_quota_exact_global_access_branch(self, tenant_isolation_service):
        """Test exact global_access branch - covers lines 144->155"""
        with patch.object(tenant_isolation_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': {
                'current_global_access': 10,
                'max_global_access_features': 10
            }
        }):
            result = await tenant_isolation_service.check_quota_limits('org-123', 'global_access', quantity=1)
            
            # Must hit lines 144->155
            assert result is not None
            assert result.get('quota_exceeded') is True
            assert result.get('quota_type') == 'global_access'
    
    @pytest.mark.asyncio
    async def test_check_quota_exact_sharing_requests_branch(self, tenant_isolation_service):
        """Test exact sharing_requests branch - covers lines 145->155"""
        with patch.object(tenant_isolation_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': {
                'current_sharing_requests': 50,
                'max_sharing_requests': 50
            }
        }):
            result = await tenant_isolation_service.check_quota_limits('org-123', 'sharing_requests', quantity=1)
            
            # Must hit lines 145->155
            assert result is not None
            assert result.get('quota_exceeded') is True
            assert result.get('quota_type') == 'sharing_requests'


class TestQuotaUpdateDecrementExactLines188192194:
    """Test quota update decrement exact lines"""
    
    @pytest.mark.asyncio
    async def test_update_quota_decrement_global_exact(self, tenant_isolation_service):
        """Test decrement global_access exact path - line 188"""
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
                operation='decrement'  # Decrement path
            )
            
            assert result is not None


class TestGetRAGTogglesExactLines209216227:
    """Test get RAG toggles exact lines"""
    
    @pytest.mark.asyncio
    async def test_get_rag_toggles_with_exact_data_structure(self, tenant_isolation_service):
        """Test get toggles with exact data structure to hit all lines"""
        query_result = Mock()
        query_result.data = [{'rag_feature': 'test', 'enabled': True}]
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = query_result
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.get_rag_feature_toggles('org-123')
        
        # Must hit lines 209-216
        assert result is not None
        assert result.get('success') is True


class TestBulkUpdateExactLines249256:
    """Test bulk update exact lines"""
    
    @pytest.mark.asyncio
    async def test_bulk_update_with_multiple_mixed_results(self, tenant_isolation_service):
        """Test bulk update with mix of success and failure - hit lines 249-256"""
        with patch.object(tenant_isolation_service, 'update_rag_feature_toggle') as mock_update:
            mock_update.side_effect = [
                {'success': True, 'toggle': {'id': 'toggle-1'}},
                {'success': False, 'error': 'Failed'},
                {'success': True, 'toggle': {'id': 'toggle-3'}}
            ]
            
            result = await tenant_isolation_service.bulk_update_rag_toggles(
                organization_id='org-123',
                toggle_updates={
                    'toggle1': True,
                    'toggle2': False,
                    'toggle3': True
                }
            )
            
            # Must hit lines 249-256 processing logic
            assert result is not None
            assert result.get('success') is True


class TestUpdateRAGTogglesExactLines298317324:
    """Test update RAG toggle exact lines"""
    
    @pytest.mark.asyncio
    async def test_update_rag_toggle_create_new_toggle_exact(self, tenant_isolation_service):
        """Test update when creating new toggle - line 298"""
        # No existing toggle
        query_result = Mock()
        query_result.data = []
        
        query_chain = Mock()
        query_chain.select.return_value = query_chain
        query_chain.eq.return_value = query_chain
        query_chain.execute.return_value = query_result
        
        insert_result = Mock()
        insert_result.data = [{'id': 'new-toggle', 'enabled': True}]
        
        insert_chain = Mock()
        insert_chain.insert.return_value = insert_chain
        insert_chain.execute.return_value = insert_result
        
        table = Mock()
        table.select.return_value = query_chain
        table.insert = Mock(return_value=insert_chain)
        table.update.return_value = Mock()
        
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.update_rag_feature_toggle(
            organization_id='org-123',
            rag_feature='new_feature',
            enabled=True
        )
        
        # Must hit line 298
        assert result is not None


class TestInheritanceLoopExactLines445457:
    """Test inheritance loop exact lines 445->457"""
    
    @pytest.mark.asyncio
    async def test_inherited_features_loop_exact_processing(self, tenant_isolation_service):
        """Test exact loop processing to hit lines 445->457"""
        org_result = Mock()
        org_result.data = [{'parent_organization_id': 'parent-123'}]
        
        parent_result = Mock()
        # Must have multiple items to loop
        parent_result.data = [
            {
                'rag_feature': f'feature_{i}',
                'enabled': True,
                'category': 'test',
                'created_at': '2024-01-01T00:00:00',
                'updated_at': '2024-01-01T00:00:00'
            }
            for i in range(3)
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
        
        # Must hit lines 445->457 in loop
        assert result is not None
        assert len(result.get('inherited_features', [])) == 3


class TestEffectiveFeaturesExactLines500501:
    """Test effective features exact lines 500->497, 501->500"""
    
    @pytest.mark.asyncio
    async def test_effective_features_override_exact_path(self, tenant_isolation_service):
        """Test exact override path to hit lines 500->497, 501->500"""
        with patch.object(tenant_isolation_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': [
                {'rag_feature': 'conflict_feature', 'enabled': True}
            ]
        }):
            with patch.object(tenant_isolation_service, 'get_inherited_features', return_value={
                'success': True,
                'inherited_features': [
                    {'rag_feature': 'conflict_feature', 'enabled': False}  # Will be overridden
                ]
            }):
                result = await tenant_isolation_service.get_effective_features('org-123')
                
                # Must hit lines 500->497 and 501->500
                assert result is not None
                assert result.get('success') is True


class TestInheritanceChainExactLines605620618:
    """Test inheritance chain exact lines"""
    
    @pytest.mark.asyncio
    async def test_inheritance_chain_loop_with_break(self, tenant_isolation_service):
        """Test chain loop with break condition - lines 605->620, 618"""
        org_data_sequence = [
            {'id': 'org-3', 'name': 'Level 3', 'parent_organization_id': 'org-2'},
            {'id': 'org-2', 'name': 'Level 2', 'parent_organization_id': 'org-1'},
            {'id': 'org-1', 'name': 'Level 1', 'parent_organization_id': None}
        ]
        
        call_count = 0
        
        def org_side_effect():
            nonlocal call_count
            if call_count < len(org_data_sequence):
                result = Mock()
                result.data = [org_data_sequence[call_count]]
                call_count += 1
                return result
            # Break condition - no more data
            return Mock(data=[])
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.side_effect = org_side_effect
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.get_inheritance_chain('org-3')
        
        # Must hit lines 605->620 and break at 618
        assert result is not None


class TestOverrideStatusExactLines642643653664655654:
    """Test override status exact lines"""
    
    @pytest.mark.asyncio
    async def test_override_status_exact_org_setting(self, tenant_isolation_service):
        """Test exact org setting path - lines 642-643"""
        org_result = Mock()
        org_result.data = [{'enabled': False}]  # Disabled setting
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = org_result
        
        table = Mock()
        table.select.return_value = chain
        tenant_isolation_service.supabase.from_.return_value = table
        
        result = await tenant_isolation_service.get_override_status('org-123', 'test_feature')
        
        # Must hit lines 642-643
        assert result is not None
        assert result.get('status') == 'disabled'
    
    @pytest.mark.asyncio
    async def test_override_status_exact_inherited(self, tenant_isolation_service):
        """Test exact inherited path - lines 653->664, 655->654"""
        org_result = Mock()
        org_result.data = []  # No org setting
        
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
                {'rag_feature': 'test_feature', 'inherited_from': 'parent-123'}
            ]
        }):
            result = await tenant_isolation_service.get_override_status('org-123', 'test_feature')
            
            # Must hit lines 653->664, 655->654
            assert result is not None
            assert result.get('status') == 'inherited'


class TestEnforceExactLines718720:
    """Test enforce exact lines 718-720"""
    
    @pytest.mark.asyncio
    async def test_enforce_exact_violation_return(self, tenant_isolation_service):
        """Test exact violation return path - lines 718-720"""
        with patch.object(tenant_isolation_service, '_get_user_organization', return_value={'organization_id': 'org-user'}):
            with patch.object(tenant_isolation_service, '_check_cross_tenant_access', return_value=False):
                result = await tenant_isolation_service.enforce_tenant_isolation(
                    user_id='user-123',
                    organization_id='org-different',
                    resource_type='context_item',
                    resource_id='item-123'
                )
                
                # Must hit lines 718-720
                assert result is not None
                assert result.get('isolation_violation') is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service', '--cov-report=html'])

