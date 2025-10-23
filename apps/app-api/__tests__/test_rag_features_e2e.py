"""
End-to-End Integration Tests for RAG Workflows
Comprehensive E2E tests covering complete RAG feature management workflows
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Add the parent directory to the path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.tenant_isolation_service import TenantIsolationService
from services.feature_inheritance_service import FeatureInheritanceService
from services.enhanced_context_manager import EnhancedContextManager
from middleware.permissions import require_role, check_organization_access, check_rag_feature_access
from middleware.validation import validate_rag_feature_exists, validate_organization_hierarchy

# ==================== E2E TEST SCENARIOS ====================

class TestRAGFeatureE2EWorkflows:
    """End-to-end workflow tests for RAG feature management"""

    @pytest.fixture
    def setup_e2e_environment(self):
        """Set up complete E2E test environment with all services"""
        # Mock Supabase client for all services
        mock_supabase_client = Mock()
        
        # Configure mock responses for different scenarios
        self.mock_supabase_responses = {
            'organizations': [
                {
                    'id': 'org-root',
                    'name': 'Root Organization',
                    'parent_organization_id': None
                },
                {
                    'id': 'org-child-1',
                    'name': 'Child Organization 1',
                    'parent_organization_id': 'org-root'
                },
                {
                    'id': 'org-child-2',
                    'name': 'Child Organization 2',
                    'parent_organization_id': 'org-root'
                }
            ],
            'rag_features': [
                {
                    'rag_feature': 'best_practice_kb',
                    'description': 'Sales best practices and proven methodologies',
                    'category': 'sales',
                    'default_enabled': True,
                    'allowed_roles': ['system_admin', 'org_admin', 'salesperson']
                },
                {
                    'rag_feature': 'performance_analytics',
                    'description': 'Team performance insights and recommendations',
                    'category': 'manager',
                    'default_enabled': True,
                    'allowed_roles': ['system_admin', 'org_admin', 'manager']
                },
                {
                    'rag_feature': 'regulatory_guidance',
                    'description': 'Compliance and regulatory information',
                    'category': 'admin',
                    'default_enabled': True,
                    'allowed_roles': ['system_admin']
                }
            ],
            'rag_toggles': [
                {
                    'id': 'toggle-1',
                    'organization_id': 'org-root',
                    'rag_feature': 'best_practice_kb',
                    'enabled': True,
                    'is_inherited': False,
                    'inherited_from': None
                },
                {
                    'id': 'toggle-2',
                    'organization_id': 'org-child-1',
                    'rag_feature': 'best_practice_kb',
                    'enabled': True,
                    'is_inherited': True,
                    'inherited_from': 'org-root'
                }
            ],
            'context_items': [
                {
                    'id': 'item-1',
                    'organization_id': 'org-root',
                    'rag_feature': 'best_practice_kb',
                    'title': 'Q4 Sales Best Practices',
                    'content': 'Key strategies for closing deals in Q4...',
                    'item_type': 'document',
                    'status': 'active'
                }
            ],
            'context_sharing': [
                {
                    'id': 'sharing-1',
                    'source_organization_id': 'org-root',
                    'target_organization_id': 'org-child-1',
                    'rag_feature': 'best_practice_kb',
                    'item_id': 'item-1',
                    'sharing_type': 'hierarchy_down',
                    'status': 'pending',
                    'shared_by': 'admin@root.com'
                }
            ]
        }
        
        # Configure mock client responses
        def mock_from_response(table_name):
            mock_query = Mock()
            mock_query.select.return_value = mock_query
            mock_query.insert.return_value = mock_query
            mock_query.update.return_value = mock_query
            mock_query.delete.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.ne.return_value = mock_query
            mock_query.in_.return_value = mock_query
            mock_query.order.return_value = mock_query
            mock_query.range.return_value = mock_query
            mock_query.single.return_value = mock_query
            
            # Return appropriate data based on table and query
            if table_name in self.mock_supabase_responses:
                mock_query.execute.return_value = Mock(
                    data=self.mock_supabase_responses[table_name],
                    count=len(self.mock_supabase_responses[table_name])
                )
            else:
                mock_query.execute.return_value = Mock(data=[], count=0)
            
            return mock_query
        
        mock_supabase_client.from_.side_effect = mock_from_response
        
        # Initialize services with mocked client
        with patch('services.tenant_isolation_service.get_supabase_client', return_value=mock_supabase_client):
            tenant_service = TenantIsolationService()
        
        with patch('services.feature_inheritance_service.get_supabase_client', return_value=mock_supabase_client):
            inheritance_service = FeatureInheritanceService()
        
        with patch('services.enhanced_context_manager.get_supabase_client', return_value=mock_supabase_client):
            context_manager = EnhancedContextManager()
        
        return {
            'tenant_service': tenant_service,
            'inheritance_service': inheritance_service,
            'context_manager': context_manager,
            'mock_client': mock_supabase_client
        }

    # ==================== WORKFLOW 1: SYSTEM ADMIN ENABLES FEATURE ====================

    @pytest.mark.asyncio
    async def test_system_admin_enables_feature_workflow(self, setup_e2e_environment):
        """E2E: System admin enables a RAG feature for root organization"""
        env = setup_e2e_environment
        tenant_service = env['tenant_service']
        
        # Step 1: System admin views current feature toggles
        result = await tenant_service.get_rag_feature_toggles('org-root')
        assert result['success'] is True
        assert len(result['toggles']) > 0
        
        # Step 2: System admin enables a feature
        result = await tenant_service.update_rag_feature_toggle(
            'org-root', 'best_practice_kb', True
        )
        assert result['success'] is True
        assert result['toggle']['enabled'] is True
        
        # Step 3: Verify feature is now enabled
        result = await tenant_service.get_rag_feature_toggles('org-root')
        enabled_features = [t for t in result['toggles'] if t['enabled']]
        assert any(t['rag_feature'] == 'best_practice_kb' for t in enabled_features)

    # ==================== WORKFLOW 2: FEATURE INHERITANCE ====================

    @pytest.mark.asyncio
    async def test_feature_inheritance_workflow(self, setup_e2e_environment):
        """E2E: Parent enables feature, child inherits it"""
        env = setup_e2e_environment
        tenant_service = env['tenant_service']
        inheritance_service = env['inheritance_service']
        
        # Step 1: Parent organization enables a feature
        result = await tenant_service.update_rag_feature_toggle(
            'org-root', 'best_practice_kb', True
        )
        assert result['success'] is True
        
        # Step 2: Child organization checks inherited features
        result = await inheritance_service.get_inherited_features('org-child-1')
        assert result['success'] is True
        assert result['parent_organization_id'] == 'org-root'
        
        # Step 3: Child organization gets effective features (own + inherited)
        result = await inheritance_service.get_effective_features('org-child-1')
        assert result['success'] is True
        assert result['inherited_count'] > 0
        
        # Step 4: Verify child can see inherited feature
        result = await tenant_service.get_rag_feature_toggles('org-child-1')
        inherited_features = [t for t in result['toggles'] if t['is_inherited']]
        assert any(t['rag_feature'] == 'best_practice_kb' for t in inherited_features)

    # ==================== WORKFLOW 3: CHILD OVERRIDES INHERITED FEATURE ====================

    @pytest.mark.asyncio
    async def test_child_overrides_inherited_feature_workflow(self, setup_e2e_environment):
        """E2E: Child organization overrides inherited feature"""
        env = setup_e2e_environment
        tenant_service = env['tenant_service']
        inheritance_service = env['inheritance_service']
        
        # Step 1: Parent has feature enabled
        await tenant_service.update_rag_feature_toggle('org-root', 'best_practice_kb', True)
        
        # Step 2: Child inherits the feature
        result = await inheritance_service.get_inherited_features('org-child-1')
        assert result['success'] is True
        
        # Step 3: Child checks if they can override
        result = await inheritance_service.can_override_feature('org-child-1', 'best_practice_kb')
        assert result['success'] is True
        assert result['can_override'] is True
        
        # Step 4: Child explicitly disables the feature (override)
        result = await tenant_service.update_rag_feature_toggle(
            'org-child-1', 'best_practice_kb', False
        )
        assert result['success'] is True
        
        # Step 5: Verify child now has explicit setting
        result = await tenant_service.get_rag_feature_toggles('org-child-1')
        child_toggles = [t for t in result['toggles'] if t['rag_feature'] == 'best_practice_kb']
        assert len(child_toggles) == 1
        assert child_toggles[0]['enabled'] is False
        assert child_toggles[0]['is_inherited'] is False

    # ==================== WORKFLOW 4: CONTEXT SHARING WITH HIERARCHY ====================

    @pytest.mark.asyncio
    async def test_context_sharing_hierarchy_workflow(self, setup_e2e_environment):
        """E2E: Parent shares context to children, children approve"""
        env = setup_e2e_environment
        context_manager = env['context_manager']
        
        # Step 1: Parent organization shares context to all children
        result = await context_manager.share_to_children(
            'org-root', 'item-1', 'best_practice_kb', 'admin@root.com'
        )
        assert result['success'] is True
        assert result['shared_count'] > 0
        
        # Step 2: Child organization checks pending approvals
        result = await context_manager.get_pending_approvals('org-child-1')
        assert result['success'] is True
        assert result['count'] > 0
        
        # Step 3: Child organization approves the shared item
        sharing_request = result['pending_requests'][0]
        result = await context_manager.approve_shared_item(
            sharing_request['id'], 'admin@child.com'
        )
        assert result['success'] is True
        assert result['new_item_id'] is not None
        
        # Step 4: Verify sharing statistics
        result = await context_manager.get_hierarchy_sharing_stats('org-root')
        assert result['success'] is True
        assert result['stats']['outgoing_shares'] > 0

    # ==================== WORKFLOW 5: BULK FEATURE MANAGEMENT ====================

    @pytest.mark.asyncio
    async def test_bulk_feature_management_workflow(self, setup_e2e_environment):
        """E2E: Org admin performs bulk feature management"""
        env = setup_e2e_environment
        tenant_service = env['tenant_service']
        
        # Step 1: Org admin views current state
        result = await tenant_service.get_rag_feature_toggles('org-root')
        initial_count = len(result['toggles'])
        
        # Step 2: Org admin performs bulk update
        bulk_updates = {
            'best_practice_kb': True,
            'performance_analytics': False,
            'regulatory_guidance': True
        }
        
        result = await tenant_service.bulk_update_rag_toggles('org-root', bulk_updates)
        assert result['success'] is True
        assert result['total_updated'] == len(bulk_updates)
        
        # Step 3: Verify bulk changes were applied
        result = await tenant_service.get_rag_feature_toggles('org-root')
        updated_toggles = {t['rag_feature']: t['enabled'] for t in result['toggles']}
        
        for feature, expected_enabled in bulk_updates.items():
            assert updated_toggles.get(feature) == expected_enabled

    # ==================== WORKFLOW 6: ROLE-BASED ACCESS CONTROL ====================

    @pytest.mark.asyncio
    async def test_role_based_access_control_workflow(self, setup_e2e_environment):
        """E2E: Different roles have different access levels"""
        env = setup_e2e_environment
        
        # Test system admin access
        with patch('middleware.permissions.get_current_user_roles', return_value=['system_admin']):
            # System admin can access any organization
            result = await check_organization_access('org-child-1', Mock())
            assert result is True
            
            # System admin can access any RAG feature
            result = await check_rag_feature_access('regulatory_guidance', 'org-child-1', Mock())
            assert result is True
        
        # Test org admin access
        with patch('middleware.permissions.get_current_user_roles', return_value=['org_admin']):
            # Org admin can access their own organization
            mock_request = Mock()
            mock_request.headers = {'X-Organization-Id': 'org-root'}
            result = await check_organization_access('org-root', mock_request)
            assert result is True
            
            # Org admin cannot access admin-only features
            with pytest.raises(Exception):  # Should raise HTTPException
                await check_rag_feature_access('regulatory_guidance', 'org-root', mock_request)

    # ==================== WORKFLOW 7: FEATURE VALIDATION ====================

    @pytest.mark.asyncio
    async def test_feature_validation_workflow(self, setup_e2e_environment):
        """E2E: Feature validation prevents invalid operations"""
        env = setup_e2e_environment
        
        # Test invalid feature name
        with patch('middleware.validation.get_supabase_client', return_value=env['mock_client']):
            with pytest.raises(Exception):  # Should raise HTTPException
                await validate_rag_feature_exists('invalid_feature_name')
        
        # Test circular organization hierarchy
        with patch('middleware.validation.get_supabase_client', return_value=env['mock_client']):
            # Mock circular dependency
            env['mock_client'].from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {'ancestor_id': 'org-child-1'}
            ]
            
            with pytest.raises(Exception):  # Should raise HTTPException
                await validate_organization_hierarchy('org-child-1', 'org-parent')

    # ==================== WORKFLOW 8: ERROR HANDLING AND RECOVERY ====================

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery_workflow(self, setup_e2e_environment):
        """E2E: System handles errors gracefully and recovers"""
        env = setup_e2e_environment
        tenant_service = env['tenant_service']
        
        # Test database connection error
        env['mock_client'].from_.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database connection failed")
        
        result = await tenant_service.get_rag_feature_toggles('org-root')
        assert result['success'] is False
        assert 'error' in result
        assert 'Database connection failed' in result['error']
        
        # Test recovery - reset mock and try again
        env['mock_client'].from_.return_value.select.return_value.eq.return_value.execute.side_effect = None
        env['mock_client'].from_.return_value.select.return_value.eq.return_value.execute.return_value.data = env['mock_supabase_responses']['rag_toggles']
        
        result = await tenant_service.get_rag_feature_toggles('org-root')
        assert result['success'] is True
        assert len(result['toggles']) > 0

    # ==================== WORKFLOW 9: PERFORMANCE UNDER LOAD ====================

    @pytest.mark.asyncio
    async def test_performance_under_load_workflow(self, setup_e2e_environment):
        """E2E: System performs well under load"""
        env = setup_e2e_environment
        tenant_service = env['tenant_service']
        
        import time
        
        # Test bulk operations performance
        large_updates = {f'feature_{i}': i % 2 == 0 for i in range(100)}
        
        start_time = time.time()
        result = await tenant_service.bulk_update_rag_toggles('org-root', large_updates)
        end_time = time.time()
        
        assert result['success'] is True
        assert result['total_updated'] == 100
        assert (end_time - start_time) < 2.0  # Should complete within 2 seconds
        
        # Test concurrent operations
        tasks = []
        for i in range(10):
            task = tenant_service.get_rag_feature_toggles(f'org-child-{i % 3}')
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        assert all(result['success'] for result in results)
        assert (end_time - start_time) < 1.0  # Should complete within 1 second

    # ==================== WORKFLOW 10: COMPLETE USER JOURNEY ====================

    @pytest.mark.asyncio
    async def test_complete_user_journey_workflow(self, setup_e2e_environment):
        """E2E: Complete user journey from feature enablement to usage"""
        env = setup_e2e_environment
        tenant_service = env['tenant_service']
        inheritance_service = env['inheritance_service']
        context_manager = env['context_manager']
        
        # Step 1: System admin enables features for root organization
        await tenant_service.update_rag_feature_toggle('org-root', 'best_practice_kb', True)
        await tenant_service.update_rag_feature_toggle('org-root', 'performance_analytics', True)
        
        # Step 2: Child organization inherits features
        result = await inheritance_service.get_effective_features('org-child-1')
        assert result['success'] is True
        assert result['inherited_count'] >= 2
        
        # Step 3: Parent shares context to children
        result = await context_manager.share_to_children(
            'org-root', 'item-1', 'best_practice_kb', 'admin@root.com'
        )
        assert result['success'] is True
        
        # Step 4: Child approves shared content
        result = await context_manager.get_pending_approvals('org-child-1')
        if result['count'] > 0:
            sharing_request = result['pending_requests'][0]
            result = await context_manager.approve_shared_item(
                sharing_request['id'], 'admin@child.com'
            )
            assert result['success'] is True
        
        # Step 5: Child overrides one inherited feature
        result = await tenant_service.update_rag_feature_toggle(
            'org-child-1', 'performance_analytics', False
        )
        assert result['success'] is True
        
        # Step 6: Verify final state
        result = await tenant_service.get_rag_feature_toggles('org-child-1')
        child_toggles = {t['rag_feature']: t for t in result['toggles']}
        
        # Should have inherited best_practice_kb enabled
        assert child_toggles['best_practice_kb']['enabled'] is True
        assert child_toggles['best_practice_kb']['is_inherited'] is True
        
        # Should have overridden performance_analytics disabled
        assert child_toggles['performance_analytics']['enabled'] is False
        assert child_toggles['performance_analytics']['is_inherited'] is False

# ==================== INTEGRATION TESTS WITH EXTERNAL SYSTEMS ====================

class TestRAGFeatureExternalIntegration:
    """Integration tests with external systems"""

    @pytest.mark.asyncio
    async def test_supabase_integration(self):
        """Test integration with actual Supabase (if available)"""
        # This would test against a real Supabase instance
        # Skip if not available
        pytest.skip("Requires real Supabase instance")

    @pytest.mark.asyncio
    async def test_api_gateway_integration(self):
        """Test integration with API gateway"""
        # This would test the full API stack
        pytest.skip("Requires full API stack")

    @pytest.mark.asyncio
    async def test_frontend_backend_integration(self):
        """Test frontend-backend integration"""
        # This would test the complete frontend-backend flow
        pytest.skip("Requires full frontend-backend stack")

# ==================== DATA CONSISTENCY TESTS ====================

class TestRAGFeatureDataConsistency:
    """Tests for data consistency across the system"""

    @pytest.mark.asyncio
    async def test_feature_toggle_consistency(self, setup_e2e_environment):
        """Test that feature toggles are consistent across all views"""
        env = setup_e2e_environment
        tenant_service = env['tenant_service']
        inheritance_service = env['inheritance_service']
        
        # Enable a feature
        await tenant_service.update_rag_feature_toggle('org-root', 'best_practice_kb', True)
        
        # Check consistency across different views
        result1 = await tenant_service.get_rag_feature_toggles('org-root')
        result2 = await inheritance_service.get_effective_features('org-root')
        
        # Both should show the same enabled state
        toggle1 = next(t for t in result1['toggles'] if t['rag_feature'] == 'best_practice_kb')
        toggle2 = next(t for t in result2['effective_features'] if t['rag_feature'] == 'best_practice_kb')
        
        assert toggle1['enabled'] == toggle2['enabled']

    @pytest.mark.asyncio
    async def test_inheritance_chain_consistency(self, setup_e2e_environment):
        """Test that inheritance chains are consistent"""
        env = setup_e2e_environment
        inheritance_service = env['inheritance_service']
        
        # Get inheritance chain for child
        result = await inheritance_service.get_inheritance_chain('org-child-1')
        assert result['success'] is True
        
        # Verify chain includes parent
        chain_ids = [org['id'] for org in result['inheritance_chain']]
        assert 'org-root' in chain_ids
        assert 'org-child-1' in chain_ids

# ==================== SECURITY TESTS ====================

class TestRAGFeatureSecurity:
    """Security tests for RAG feature system"""

    @pytest.mark.asyncio
    async def test_tenant_isolation_security(self, setup_e2e_environment):
        """Test that tenant isolation is maintained"""
        env = setup_e2e_environment
        tenant_service = env['tenant_service']
        
        # Try to access another organization's features
        result = await tenant_service.get_rag_feature_toggles('org-child-1')
        assert result['success'] is True
        
        # Verify we only get org-child-1's features
        for toggle in result['toggles']:
            assert toggle['organization_id'] == 'org-child-1'

    @pytest.mark.asyncio
    async def test_role_escalation_prevention(self, setup_e2e_environment):
        """Test that role escalation is prevented"""
        # Test that users cannot escalate their roles
        with patch('middleware.permissions.get_current_user_roles', return_value=['user']):
            with pytest.raises(Exception):  # Should raise HTTPException
                await check_rag_feature_access('regulatory_guidance', 'org-root', Mock())

# ==================== CLEANUP AND TEARDOWN ====================

@pytest.fixture(autouse=True)
def cleanup_after_tests():
    """Clean up after each test"""
    yield
    # Cleanup code here if needed
    pass

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
