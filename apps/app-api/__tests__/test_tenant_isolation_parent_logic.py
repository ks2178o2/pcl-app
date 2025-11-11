# apps/app-api/__tests__/test_tenant_isolation_parent_logic.py
"""
Tests for parent organization and inheritance logic
Lines: 566-596 (can_enable_feature with parent), 598-633 (get_inheritance_chain)
"""

import pytest
from unittest.mock import Mock, patch
from services.tenant_isolation_service import TenantIsolationService


class TestTenantIsolationParentLogic:
    """Tests for parent organization checks and inheritance chains"""
    
    @pytest.fixture
    def tenant_service(self):
        """Create tenant isolation service"""
        with patch('services.tenant_isolation_service.get_supabase_client'):
            return TenantIsolationService()
    
    @pytest.mark.asyncio
    async def test_can_enable_feature_parent_not_configured(self, tenant_service):
        """Test can enable when parent doesn't have feature - lines 566-573"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': []
        }):
            with patch.object(tenant_service, 'get_inheritance_chain', return_value={
                'success': True,
                'chain': ['org-123', 'org-parent']
            }):
                with patch.object(tenant_service, 'supabase') as mock_supabase:
                    table = Mock()
                    result_mock = Mock()
                    result_mock.data = []  # Parent doesn't have feature
                    
                    select_chain = Mock()
                    select_chain.execute.return_value = result_mock
                    select_chain.eq.return_value = select_chain
                    
                    table.select.return_value = select_chain
                    mock_supabase.from_.return_value = table
                    
                    result = await tenant_service.can_enable_feature('org-123', 'new-feature')
                    
                    assert result['success'] is True
                    assert result['can_enable'] is False
                    assert 'Parent organization does not have' in result['reason']
    
    @pytest.mark.asyncio
    async def test_can_enable_feature_parent_disabled(self, tenant_service):
        """Test can enable when parent has it disabled - lines 575-582"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': []
        }):
            with patch.object(tenant_service, 'get_inheritance_chain', return_value={
                'success': True,
                'chain': ['org-123', 'org-parent']
            }):
                with patch.object(tenant_service, 'supabase') as mock_supabase:
                    table = Mock()
                    result_mock = Mock()
                    result_mock.data = [{'enabled': False}]  # Parent has it disabled
                    
                    select_chain = Mock()
                    select_chain.execute.return_value = result_mock
                    select_chain.eq.return_value = select_chain
                    
                    table.select.return_value = select_chain
                    mock_supabase.from_.return_value = table
                    
                    result = await tenant_service.can_enable_feature('org-123', 'feature')
                    
                    assert result['success'] is True
                    assert result['can_enable'] is False
                    assert 'parent organization has it disabled' in result['reason']
    
    @pytest.mark.asyncio
    async def test_can_enable_feature_parent_enabled(self, tenant_service):
        """Test can enable when parent has it enabled - lines 584-588"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': []
        }):
            with patch.object(tenant_service, 'get_inheritance_chain', return_value={
                'success': True,
                'chain': ['org-123', 'org-parent']
            }):
                with patch.object(tenant_service, 'supabase') as mock_supabase:
                    table = Mock()
                    result_mock = Mock()
                    result_mock.data = [{'enabled': True}]  # Parent has it enabled
                    
                    select_chain = Mock()
                    select_chain.execute.return_value = result_mock
                    select_chain.eq.return_value = select_chain
                    
                    table.select.return_value = select_chain
                    mock_supabase.from_.return_value = table
                    
                    result = await tenant_service.can_enable_feature('org-123', 'feature')
                    
                    assert result['success'] is True
                    assert result['can_enable'] is True
                    assert 'Parent organization has this feature enabled' in result['reason']
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_multiple_levels(self, tenant_service):
        """Test inheritance chain with multiple levels - lines 598-633"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            # Create multiple org levels
            org_data = [
                {'id': 'org-child', 'name': 'Child', 'parent_organization_id': 'org-parent'},
                {'id': 'org-parent', 'name': 'Parent', 'parent_organization_id': 'org-grandparent'},
                {'id': 'org-grandparent', 'name': 'Grandparent', 'parent_organization_id': None}
            ]
            
            call_count = 0
            def table_side_effect(table_name):
                return Mock()
            
            def execute_side_effect():
                nonlocal call_count
                call_count += 1
                result = Mock()
                if call_count <= len(org_data):
                    result.data = [org_data[call_count - 1]]
                else:
                    result.data = []
                return result
            
            table = Mock()
            select = Mock()
            select.execute = execute_side_effect
            select.eq.return_value = select
            table.select.return_value = select
            mock_supabase.from_.return_value = table
            
            result = await tenant_service.get_inheritance_chain('org-child')
            
            assert result['success'] is True
            assert 'chain' in result
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_orphan_org(self, tenant_service):
        """Test inheritance chain when org has no parent - line 618"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            table = Mock()
            result_mock = Mock()
            result_mock.data = [{'id': 'org-123', 'parent_organization_id': None}]
            
            select_chain = Mock()
            select_chain.execute.return_value = result_mock
            select_chain.eq.return_value = select_chain
            
            table.select.return_value = select_chain
            mock_supabase.from_.return_value = table
            
            result = await tenant_service.get_inheritance_chain('org-123')
            
            assert result['success'] is True
            assert result['is_at_top'] is True
    
    @pytest.mark.asyncio
    async def test_get_override_status_with_inheritance(self, tenant_service):
        """Test override status with inheritance chain - lines 634-679"""
        with patch.object(tenant_service, 'get_rag_feature_toggles', return_value={
            'success': True,
            'toggles': [{'rag_feature': 'feature-1', 'enabled': True}]
        }):
            with patch.object(tenant_service, 'get_inherited_features', return_value={
                'success': True,
                'inherited_features': [{'rag_feature': 'feature-1', 'enabled': False, 'inherited_from': 'org-parent'}]
            }):
                result = await tenant_service.get_override_status('org-123', 'feature-1')
                
                assert result['success'] is True
                assert result['is_override'] is True  # Own True vs inherited False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service'])


