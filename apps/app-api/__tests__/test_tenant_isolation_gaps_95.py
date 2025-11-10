"""
Tests to cover remaining gaps in tenant_isolation_service.py to reach 95% coverage
Targeting missing lines: 35-46, 67-78, 100-102, 117, 133-146, 175, 184-196, 204, 227, 249-256, 281-283, 298, 322-324, 340, 348-350, 362-363, 368-386, 417-419, 439-465, 477, 482, 488-516, 534-592, 609, 618-620, 642-643, 653->664, 655-656, 672-674, 718-720
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from services.tenant_isolation_service import TenantIsolationService


class TestTenantIsolationGaps:
    """Test missing coverage in TenantIsolationService"""
    
    @pytest.fixture
    def tenant_service(self):
        """Create tenant isolation service with mocked supabase"""
        with patch('services.tenant_isolation_service.get_supabase_client') as mock_get_client:
            mock_client = Mock()
            mock_client.from_.return_value = Mock()
            mock_get_client.return_value = mock_client
            return TenantIsolationService()
    
    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_cross_tenant_denied(self, tenant_service):
        """Test lines 35-46: Cross-tenant access denied"""
        # Mock user org
        user_org_result = Mock()
        user_org_result.data = {'organization_id': 'org-1'}
        
        # Mock _get_user_organization
        with patch.object(tenant_service, '_get_user_organization', return_value={'organization_id': 'org-1'}):
            with patch.object(tenant_service, '_check_cross_tenant_access', return_value=False):
                result = await tenant_service.enforce_tenant_isolation(
                    'user-123', 'org-2', 'resource_type', 'resource-1'
                )
                assert result['success'] is False
                assert 'Cross-tenant access denied' in result['error']
                assert result['isolation_violation'] is True
    
    @pytest.mark.asyncio
    async def test_create_isolation_policy_validation_error(self, tenant_service):
        """Test lines 67-78: Validation errors and failed insert"""
        # Test missing required field
        policy_data = {
            'organization_id': 'org-123',
            'policy_type': 'type'
            # Missing policy_name and policy_rules
        }
        
        result = await tenant_service.create_isolation_policy(policy_data)
        assert result['success'] is False
        
        # Test failed insert
        policy_data = {
            'organization_id': 'org-123',
            'policy_type': 'type',
            'policy_name': 'Test Policy',
            'policy_rules': {'rule': 'value'}
        }
        
        # Mock failed insert
        insert_result = Mock()
        insert_result.data = None
        table_mock = Mock()
        table_mock.insert.return_value.execute.return_value = insert_result
        tenant_service.supabase.from_.return_value = table_mock
        
        result = await tenant_service.create_isolation_policy(policy_data)
        assert result['success'] is False
        assert 'Failed to create' in result['error']
    
    @pytest.mark.asyncio
    async def test_get_isolation_policies_exception(self, tenant_service):
        """Test lines 100-102: Exception handling"""
        tenant_service.supabase.from_.return_value.select.side_effect = Exception("DB error")
        
        result = await tenant_service.get_isolation_policies('org-123')
        assert result['success'] is False
        assert 'error' in result
        assert result['policies'] == []
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_quota_exceeded(self, tenant_service):
        """Test lines 117, 133-146: Quota exceeded scenarios"""
        quotas = {
            'current_context_items': 950,
            'max_context_items': 1000,
            'max_global_access_features': 10,
            'current_global_access': 8,
            'max_sharing_requests': 50,
            'current_sharing_requests': 45
        }
        
        with patch.object(tenant_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': quotas
        }):
            # Test context_items quota exceeded
            result = await tenant_service.check_quota_limits('org-123', 'context_items', quantity=100)
            assert result['success'] is False
            assert result['quota_exceeded'] is True
            
            # Test global_access quota exceeded (lines 144->155)
            result = await tenant_service.check_quota_limits('org-123', 'global_access', quantity=5)
            assert result['success'] is False
            assert result['quota_exceeded'] is True
            
            # Test sharing_requests quota exceeded (lines 145->155) - need to trigger the branch
            result = await tenant_service.check_quota_limits('org-123', 'sharing_requests', quantity=10)
            assert result['success'] is False
            assert result['quota_exceeded'] is True
            assert result['quota_type'] == 'sharing_requests'
    
    @pytest.mark.asyncio
    async def test_update_quota_usage_quota_get_fails(self, tenant_service):
        """Test line 175: _get_organization_quotas fails"""
        with patch.object(tenant_service, '_get_organization_quotas', return_value={
            'success': False,
            'error': 'Quota fetch failed'
        }):
            result = await tenant_service.update_quota_usage('org-123', 'context_items', 'increment', 1)
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_update_quota_usage_all_operations(self, tenant_service):
        """Test lines 184-196: All quota update operations"""
        # Test global_access increment (line 188) separately
        quotas = {
            'current_context_items': 100,
            'current_global_access': 5,
            'current_sharing_requests': 10
        }
        
        update_result = Mock()
        update_result.data = [quotas]
        
        table_mock = Mock()
        update_chain = Mock()
        update_chain.eq = Mock(return_value=update_chain)
        update_chain.execute = Mock(return_value=update_result)
        table_mock.update = Mock(return_value=update_chain)
        tenant_service.supabase.from_.return_value = table_mock
        
        with patch.object(tenant_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': quotas.copy()
        }):
            # Test global_access increment (line 188) - separate call to ensure branch coverage
            result = await tenant_service.update_quota_usage('org-123', 'global_access', 'increment', 2)
            assert result['success'] is True
        
        # Test sharing_requests operations (lines 192-196) separately
        with patch.object(tenant_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': quotas.copy()
        }):
            # Test sharing_requests increment (line 194)
            result = await tenant_service.update_quota_usage('org-123', 'sharing_requests', 'increment', 5)
            assert result['success'] is True
            
            # Test sharing_requests decrement (line 196)
            result = await tenant_service.update_quota_usage('org-123', 'sharing_requests', 'decrement', 3)
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_update_quota_usage_failed_update(self, tenant_service):
        """Test line 204: Failed update"""
        quotas = {'current_context_items': 100}
        update_result = Mock()
        update_result.data = None
        
        table_mock = Mock()
        update_chain = Mock()
        update_chain.eq = Mock(return_value=update_chain)
        update_chain.execute = Mock(return_value=update_result)
        table_mock.update = Mock(return_value=update_chain)
        tenant_service.supabase.from_.return_value = table_mock
        
        with patch.object(tenant_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': quotas
        }):
            result = await tenant_service.update_quota_usage('org-123', 'context_items', 'increment', 10)
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_reset_quota_usage_quota_get_fails(self, tenant_service):
        """Test line 227: _get_organization_quotas fails"""
        with patch.object(tenant_service, '_get_organization_quotas', return_value={
            'success': False,
            'error': 'Quota fetch failed'
        }):
            result = await tenant_service.reset_quota_usage('org-123', quota_type='context_items')
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_reset_quota_usage_all_quotas(self, tenant_service):
        """Test lines 235-237: Reset all quotas (no quota_type)"""
        quotas = {
            'current_context_items': 100,
            'current_global_access': 5,
            'current_sharing_requests': 10
        }
        
        update_result = Mock()
        update_result.data = [quotas]
        
        table_mock = Mock()
        update_chain = Mock()
        update_chain.eq = Mock(return_value=update_chain)
        update_chain.execute = Mock(return_value=update_result)
        table_mock.update = Mock(return_value=update_chain)
        tenant_service.supabase.from_.return_value = table_mock
        
        with patch.object(tenant_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': quotas
        }):
            result = await tenant_service.reset_quota_usage('org-123', quota_type=None)
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_reset_quota_usage_specific_type(self, tenant_service):
        """Test lines 249-256: Reset specific quota type and exception"""
        quotas = {
            'current_context_items': 100,
            'current_global_access': 5,
            'current_sharing_requests': 10
        }
        
        update_result = Mock()
        update_result.data = [quotas]
        
        table_mock = Mock()
        update_chain = Mock()
        update_chain.eq = Mock(return_value=update_chain)
        update_chain.execute = Mock(return_value=update_result)
        table_mock.update = Mock(return_value=update_chain)
        tenant_service.supabase.from_.return_value = table_mock
        
        with patch.object(tenant_service, '_get_organization_quotas', return_value={
            'success': True,
            'quotas': quotas
        }):
            result = await tenant_service.reset_quota_usage('org-123', quota_type='context_items')
            assert result['success'] is True
            
            # Test failed update (line 249)
            update_result.data = None
            result = await tenant_service.reset_quota_usage('org-123', quota_type='context_items')
            assert result['success'] is False
            
            # Test exception (lines 254-256)
            table_mock.update.side_effect = Exception("DB error")
            result = await tenant_service.reset_quota_usage('org-123', quota_type='context_items')
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_no_data(self, tenant_service):
        """Test lines 281-283: Exception handling in get_rag_feature_toggles"""
        tenant_service.supabase.from_.return_value.select.side_effect = Exception("DB error")
        
        result = await tenant_service.get_rag_feature_toggles('org-123')
        assert result['success'] is False
        assert result['toggles'] == []
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_update_existing(self, tenant_service):
        """Test line 298: Update existing toggle"""
        existing_result = Mock()
        existing_result.data = [{'id': 'toggle-1', 'enabled': False}]
        
        update_result = Mock()
        update_result.data = [{'id': 'toggle-1', 'enabled': True}]
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=existing_result)
        
        update_chain = Mock()
        update_chain.eq = Mock(return_value=update_chain)
        update_chain.execute = Mock(return_value=update_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        table_mock.update = Mock(return_value=update_chain)
        tenant_service.supabase.from_.return_value = table_mock
        
        result = await tenant_service.update_rag_feature_toggle('org-123', 'existing_feature', True)
        assert result['success'] is True
        assert result['toggle']['enabled'] is True
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_create_new(self, tenant_service):
        """Test lines 322-324: Create new toggle when doesn't exist and exception"""
        # Mock existing query returns no data
        existing_result = Mock()
        existing_result.data = []
        
        # Mock insert returns data
        insert_result = Mock()
        insert_result.data = [{'id': 'new-toggle', 'enabled': True}]
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=existing_result)
        
        insert_chain = Mock()
        insert_chain.execute = Mock(return_value=insert_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        table_mock.insert = Mock(return_value=insert_chain)
        tenant_service.supabase.from_.return_value = table_mock
        
        result = await tenant_service.update_rag_feature_toggle('org-123', 'new_feature', True)
        assert result['success'] is True
        assert result['toggle']['enabled'] is True
        
        # Test exception
        table_mock.select.side_effect = Exception("DB error")
        result = await tenant_service.update_rag_feature_toggle('org-123', 'new_feature', True)
        assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_bulk_update_rag_toggles_failure(self, tenant_service):
        """Test line 340: Failed update in bulk operation"""
        with patch.object(tenant_service, 'update_rag_feature_toggle', return_value={
            'success': False,
            'error': 'Update failed'
        }):
            result = await tenant_service.bulk_update_rag_toggles('org-123', {'feature1': True})
            assert result['success'] is True
            assert result['total_updated'] == 0
    
    @pytest.mark.asyncio
    async def test_bulk_update_rag_toggles_exception(self, tenant_service):
        """Test lines 348-350: Exception in bulk update"""
        with patch.object(tenant_service, 'update_rag_feature_toggle', side_effect=Exception("Error")):
            result = await tenant_service.bulk_update_rag_toggles('org-123', {'feature1': True})
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_user_organization_exception(self, tenant_service):
        """Test lines 362-363: Exception in _get_user_organization"""
        tenant_service.supabase.from_.return_value.select.side_effect = Exception("DB error")
        
        result = await tenant_service._get_user_organization('user-123')
        assert result is None
    
    @pytest.mark.asyncio
    async def test_check_cross_tenant_access_system_admin(self, tenant_service):
        """Test lines 368-386: Cross-tenant access checks"""
        # Mock system admin
        user_result = Mock()
        user_result.data = {'role': 'system_admin'}
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.single = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=user_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        tenant_service.supabase.from_.return_value = table_mock
        
        result = await tenant_service._check_cross_tenant_access('user-123', 'org-999', 'resource')
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_cross_tenant_access_no_user_data(self, tenant_service):
        """Test line 372: No user data in cross-tenant check"""
        user_result = Mock()
        user_result.data = None
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.single = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=user_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        tenant_service.supabase.from_.return_value = table_mock
        
        result = await tenant_service._check_cross_tenant_access('user-123', 'org-999', 'resource')
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_cross_tenant_access_with_permission(self, tenant_service):
        """Test cross-tenant access with specific permission"""
        # Mock non-admin user
        user_result = Mock()
        user_result.data = {'role': 'user'}
        
        # Mock cross-tenant permission exists
        cross_access_result = Mock()
        cross_access_result.data = [{'id': 'perm-1', 'enabled': True}]
        
        select_chain1 = Mock()
        select_chain1.eq = Mock(return_value=select_chain1)
        select_chain1.single = Mock(return_value=select_chain1)
        select_chain1.execute = Mock(return_value=user_result)
        
        select_chain2 = Mock()
        select_chain2.eq = Mock(return_value=select_chain2)
        select_chain2.execute = Mock(return_value=cross_access_result)
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            table_mock = Mock()
            if call_count == 1:
                table_mock.select = Mock(return_value=select_chain1)
            else:
                table_mock.select = Mock(return_value=select_chain2)
            return table_mock
        
        tenant_service.supabase.from_.side_effect = from_side_effect
        
        result = await tenant_service._check_cross_tenant_access('user-123', 'org-999', 'resource')
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_cross_tenant_access_exception(self, tenant_service):
        """Test lines 385-386: Exception in cross-tenant check"""
        tenant_service.supabase.from_.return_value.select.side_effect = Exception("DB error")
        
        result = await tenant_service._check_cross_tenant_access('user-123', 'org-999', 'resource')
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_create_default(self, tenant_service):
        """Test lines 417-419: Create default quotas when not exist and exception"""
        # Mock no quotas found
        select_result = Mock()
        select_result.data = None
        
        # Mock insert returns data
        insert_result = Mock()
        insert_result.data = [{'organization_id': 'org-123', 'max_context_items': 1000}]
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.single = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=select_result)
        
        insert_chain = Mock()
        insert_chain.execute = Mock(return_value=insert_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        table_mock.insert = Mock(return_value=insert_chain)
        tenant_service.supabase.from_.return_value = table_mock
        
        result = await tenant_service._get_organization_quotas('org-123')
        assert result['success'] is True
        assert 'quotas' in result
        
        # Test exception
        table_mock.select.side_effect = Exception("DB error")
        result = await tenant_service._get_organization_quotas('org-123')
        assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_inherited_features_with_parent(self, tenant_service):
        """Test lines 445->457, 463-465: Get inherited features from parent with data"""
        # Mock org has parent
        org_result = Mock()
        org_result.data = [{'parent_organization_id': 'org-parent'}]
        
        # Mock parent has enabled features
        parent_result = Mock()
        parent_result.data = [
            {'rag_feature': 'feature1', 'enabled': True, 'category': 'test', 'created_at': '2024-01-01', 'updated_at': '2024-01-02'}
        ]
        
        org_select = Mock()
        org_select.eq = Mock(return_value=org_select)
        org_select.execute = Mock(return_value=org_result)
        
        parent_select = Mock()
        parent_select.eq = Mock(return_value=parent_select)
        parent_select.execute = Mock(return_value=parent_result)
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            table_mock = Mock()
            if call_count == 1:
                table_mock.select = Mock(return_value=org_select)
            else:
                table_mock.select = Mock(return_value=parent_select)
            return table_mock
        
        tenant_service.supabase.from_.side_effect = from_side_effect
        
        result = await tenant_service.get_inherited_features('org-child')
        assert result['success'] is True
        assert len(result['inherited_features']) == 1
        assert result['inherited_features'][0]['is_inherited'] is True
        assert result['inherited_features'][0]['inherited_from'] == 'org-parent'
        
        # Test exception path (lines 463-465)
        tenant_service.supabase.from_.side_effect = Exception("DB error")
        result = await tenant_service.get_inherited_features('org-child')
        assert result['success'] is False
        assert result['inherited_features'] == []
    
    @pytest.mark.asyncio
    async def test_get_effective_features_own_fails(self, tenant_service):
        """Test line 477: get_rag_feature_toggles fails"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': False,
            'error': 'Failed'
        }):
            result = await tenant_service.get_effective_features('org-123')
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_effective_features_inherited_fails(self, tenant_service):
        """Test line 482: get_inherited_features fails"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': []
        }):
            with patch.object(tenant_service, 'get_inherited_features', return_value={
                'success': False,
                'error': 'Failed'
            }):
                result = await tenant_service.get_effective_features('org-123')
                assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_effective_features_override(self, tenant_service):
        """Test lines 500->497, 501->500: Feature override logic when feature exists in map"""
        own_features = [
            {'rag_feature': 'feature1', 'enabled': True}
        ]
        
        inherited_features = [
            {'rag_feature': 'feature1', 'enabled': True, 'is_inherited': True, 'inherited_from': 'org-parent'},
            {'rag_feature': 'feature2', 'enabled': True, 'is_inherited': True, 'inherited_from': 'org-parent'}
        ]
        
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': own_features
        }):
            with patch.object(tenant_service, 'get_inherited_features', return_value={
                'success': True,
                'inherited_features': inherited_features
            }):
                result = await tenant_service.get_effective_features('org-123')
                assert result['success'] is True
                assert result['own_count'] == 1
                assert result['inherited_count'] == 2
                # feature1 should be overridden (not inherited) - tests line 500->497, 501->500
                feature1 = next(f for f in result['effective_features'] if f['rag_feature'] == 'feature1')
                assert feature1['is_inherited'] is False
                # feature2 should remain inherited
                feature2 = next(f for f in result['effective_features'] if f['rag_feature'] == 'feature2')
                assert feature2['is_inherited'] is True
                
                # Test adding new own feature (not in inherited) - tests else branch
                own_features_new = [
                    {'rag_feature': 'feature3', 'enabled': True}
                ]
                
                with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
                    'success': True,
                    'toggles': own_features_new
                }):
                    result = await tenant_service.get_effective_features('org-123')
                    assert result['success'] is True
                    feature3 = next(f for f in result['effective_features'] if f['rag_feature'] == 'feature3')
                    assert feature3['is_inherited'] is False
    
    @pytest.mark.asyncio
    async def test_can_enable_feature_org_not_found(self, tenant_service):
        """Test line 549: Organization not found"""
        catalog_result = Mock()
        catalog_result.data = [{'rag_feature': 'feature1'}]
        
        org_result = Mock()
        org_result.data = []  # Org not found
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            table_mock = Mock()
            select_chain = Mock()
            select_chain.eq = Mock(return_value=select_chain)
            if call_count == 1:
                select_chain.execute = Mock(return_value=catalog_result)
            else:
                select_chain.execute = Mock(return_value=org_result)
            table_mock.select = Mock(return_value=select_chain)
            return table_mock
        
        tenant_service.supabase.from_.side_effect = from_side_effect
        
        result = await tenant_service.can_enable_feature('org-123', 'feature1')
        assert result['success'] is False
        assert 'not found' in result['reason']
    
    @pytest.mark.asyncio
    async def test_can_enable_feature_parent_not_configured(self, tenant_service):
        """Test line 569: Parent doesn't have feature configured"""
        catalog_result = Mock()
        catalog_result.data = [{'rag_feature': 'feature1'}]
        
        org_result = Mock()
        org_result.data = [{'parent_organization_id': 'org-parent'}]
        
        parent_result = Mock()
        parent_result.data = []  # Parent doesn't have feature configured
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            table_mock = Mock()
            select_chain = Mock()
            select_chain.eq = Mock(return_value=select_chain)
            if call_count == 1:
                select_chain.execute = Mock(return_value=catalog_result)
            elif call_count == 2:
                select_chain.execute = Mock(return_value=org_result)
            else:
                select_chain.execute = Mock(return_value=parent_result)
            table_mock.select = Mock(return_value=select_chain)
            return table_mock
        
        tenant_service.supabase.from_.side_effect = from_side_effect
        
        result = await tenant_service.can_enable_feature('org-123', 'feature1')
        assert result['success'] is True
        assert result['can_enable'] is False
        assert 'not have feature' in result['reason']
    
    @pytest.mark.asyncio
    async def test_can_enable_feature_all_scenarios(self, tenant_service):
        """Test lines 566-592: All scenarios in can_enable_feature"""
        # Test parent has feature disabled
        catalog_result = Mock()
        catalog_result.data = [{'rag_feature': 'feature1'}]
        
        org_result = Mock()
        org_result.data = [{'parent_organization_id': 'org-parent'}]
        
        parent_result = Mock()
        parent_result.data = [{'enabled': False}]  # Parent has it disabled
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            table_mock = Mock()
            select_chain = Mock()
            select_chain.eq = Mock(return_value=select_chain)
            if call_count == 1:
                select_chain.execute = Mock(return_value=catalog_result)
            elif call_count == 2:
                select_chain.execute = Mock(return_value=org_result)
            else:
                select_chain.execute = Mock(return_value=parent_result)
            table_mock.select = Mock(return_value=select_chain)
            return table_mock
        
        tenant_service.supabase.from_.side_effect = from_side_effect
        
        result = await tenant_service.can_enable_feature('org-123', 'feature1')
        assert result['success'] is True
        assert result['can_enable'] is False
        assert 'disabled' in result['reason']
        
        # Test parent has feature enabled
        parent_result.data = [{'enabled': True}]
        
        call_count = 0
        tenant_service.supabase.from_.side_effect = from_side_effect
        
        result = await tenant_service.can_enable_feature('org-123', 'feature1')
        assert result['success'] is True
        assert result['can_enable'] is True
        assert 'enabled' in result['reason']
    
    @pytest.mark.asyncio
    async def test_can_enable_feature_exception(self, tenant_service):
        """Test lines 590-592: Exception in can_enable_feature"""
        tenant_service.supabase.from_.return_value.select.side_effect = Exception("DB error")
        
        result = await tenant_service.can_enable_feature('org-123', 'feature1')
        assert result['success'] is False
        assert 'Error checking feature' in result['reason']
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_walking(self, tenant_service):
        """Test lines 605->620, 618: Inheritance chain walking"""
        # Mock chain: org-child -> org-parent -> None
        org_child_result = Mock()
        org_child_result.data = [{'id': 'org-child', 'name': 'Child', 'parent_organization_id': 'org-parent'}]
        
        org_parent_result = Mock()
        org_parent_result.data = [{'id': 'org-parent', 'name': 'Parent', 'parent_organization_id': None}]
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            table_mock = Mock()
            select_chain = Mock()
            select_chain.eq = Mock(return_value=select_chain)
            if call_count == 1:
                select_chain.execute = Mock(return_value=org_child_result)
            elif call_count == 2:
                select_chain.execute = Mock(return_value=org_parent_result)
            else:
                select_chain.execute = Mock(return_value=Mock(data=[]))
            table_mock.select = Mock(return_value=select_chain)
            return table_mock
        
        tenant_service.supabase.from_.side_effect = from_side_effect
        
        result = await tenant_service.get_inheritance_chain('org-child')
        assert result['success'] is True
        assert len(result['inheritance_chain']) == 2
        assert result['depth'] == 1
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_breaks(self, tenant_service):
        """Test line 609: Break condition in inheritance chain"""
        # Mock org not found (breaks the loop)
        org_result = Mock()
        org_result.data = []
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=org_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        tenant_service.supabase.from_.return_value = table_mock
        
        result = await tenant_service.get_inheritance_chain('org-123')
        assert result['success'] is True
        assert len(result['inheritance_chain']) == 0
    
    @pytest.mark.asyncio
    async def test_get_override_status_all_scenarios(self, tenant_service):
        """Test lines 642-643, 653->664, 655->654: All override status scenarios"""
        # Test organization has explicit setting (enabled)
        org_result = Mock()
        org_result.data = [{'enabled': True}]
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=org_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        tenant_service.supabase.from_.return_value = table_mock
        
        result = await tenant_service.get_override_status('org-123', 'feature1')
        assert result['success'] is True
        assert result['status'] == 'enabled'
        assert result['is_inherited'] is False
        
        # Test organization has explicit setting (disabled)
        org_result.data = [{'enabled': False}]
        result = await tenant_service.get_override_status('org-123', 'feature1')
        assert result['success'] is True
        assert result['status'] == 'disabled'
        
        # Test inherited from parent (lines 653->664, 655->654)
        org_result.data = []
        with patch.object(tenant_service, 'get_inherited_features', return_value={
            'success': True,
            'inherited_features': [
                {'rag_feature': 'feature1', 'inherited_from': 'org-parent'}
            ]
        }):
            # Reset table mock for new query
            select_chain2 = Mock()
            select_chain2.eq = Mock(return_value=select_chain2)
            select_chain2.execute = Mock(return_value=Mock(data=[]))
            table_mock2 = Mock()
            table_mock2.select = Mock(return_value=select_chain2)
            tenant_service.supabase.from_.return_value = table_mock2
            
            result = await tenant_service.get_override_status('org-123', 'feature1')
            assert result['success'] is True
            assert result['status'] == 'inherited'
            assert result['is_inherited'] is True
        
        # Test not configured (lines 642-643)
        org_result.data = []
        with patch.object(tenant_service, 'get_inherited_features', return_value={
            'success': True,
            'inherited_features': []
        }):
            # Reset table mock for new query
            select_chain3 = Mock()
            select_chain3.eq = Mock(return_value=select_chain3)
            select_chain3.execute = Mock(return_value=Mock(data=[]))
            table_mock3 = Mock()
            table_mock3.select = Mock(return_value=select_chain3)
            tenant_service.supabase.from_.return_value = table_mock3
            
            result = await tenant_service.get_override_status('org-123', 'feature1')
            assert result['success'] is True
            assert result['status'] == 'not_configured'
    
    @pytest.mark.asyncio
    async def test_create_default_rag_toggles_exception(self, tenant_service):
        """Test lines 718-720: Exception in _create_default_rag_toggles"""
        tenant_service.supabase.from_.return_value.insert.side_effect = Exception("DB error")
        
        result = await tenant_service._create_default_rag_toggles('org-123')
        assert result == []

