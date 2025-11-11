"""
Comprehensive tests for RAG Feature Management system
Tests all new functionality including permissions, inheritance, and API endpoints
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Add the parent directory to the path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.tenant_isolation_service import TenantIsolationService
from services.feature_inheritance_service import FeatureInheritanceService
from services.enhanced_context_manager import EnhancedContextManager
from middleware.permissions import PermissionChecker, UserRole, can_access_organization, can_access_rag_feature
from api.rag_features_api import router as rag_features_router
from api.organization_toggles_api import router as organization_toggles_router
from api.organization_hierarchy_api import router as organization_hierarchy_router

class TestRAGFeatureManagement:
    """Test suite for RAG Feature Management system"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client with comprehensive chaining"""
        mock_client = Mock()
        
        # Mock the from_ method to return a chainable query builder
        mock_query = Mock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.insert.return_value = mock_query
        mock_query.update.return_value = mock_query
        mock_query.delete.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.single.return_value = mock_query
        mock_query.execute.return_value = Mock(data=[], count=0)
        
        mock_client.from_.return_value = mock_query
        return mock_client

    @pytest.fixture
    def tenant_isolation_service(self, mock_supabase_client):
        """Create TenantIsolationService instance with mocked client"""
        return TenantIsolationService(mock_supabase_client)

    @pytest.fixture
    def feature_inheritance_service(self, mock_supabase_client):
        """Create FeatureInheritanceService instance with mocked client"""
        return FeatureInheritanceService(mock_supabase_client)

    @pytest.fixture
    def enhanced_context_manager(self, mock_supabase_client):
        """Create EnhancedContextManager instance with mocked client"""
        return EnhancedContextManager(mock_supabase_client)

    @pytest.fixture
    def permission_checker(self, mock_supabase_client):
        """Create PermissionChecker instance with mocked client"""
        user_data = {
            'id': 'user-123',
            'role': 'org_admin',
            'organization_id': 'org-456'
        }
        return PermissionChecker(user_data, mock_supabase_client)

    # ==================== PERMISSION TESTS ====================

    def test_can_access_organization_same_org(self, mock_supabase_client):
        """Test organization access for same organization"""
        user_data = {'organization_id': 'org-123', 'role': 'org_admin'}
        result = can_access_organization(user_data, 'org-123', mock_supabase_client)
        assert result is True

    def test_can_access_organization_system_admin(self, mock_supabase_client):
        """Test organization access for system admin"""
        user_data = {'organization_id': 'org-123', 'role': 'system_admin'}
        result = can_access_organization(user_data, 'org-456', mock_supabase_client)
        assert result is True

    def test_can_access_organization_hierarchy_check(self, mock_supabase_client):
        """Test organization access with hierarchy checking"""
        user_data = {'organization_id': 'org-parent', 'role': 'org_admin'}
        
        # Mock hierarchy query result
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{'id': 'org-child'}])
        
        result = can_access_organization(user_data, 'org-child', mock_supabase_client, check_parent=True)
        assert result is True

    def test_can_access_rag_feature_enabled(self, mock_supabase_client):
        """Test RAG feature access when feature is enabled"""
        user_data = {'organization_id': 'org-123', 'role': 'user'}
        
        # Mock feature enabled check
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{'enabled': True}])
        
        result = can_access_rag_feature(user_data, 'best_practice_kb', 'org-123', mock_supabase_client)
        assert result is True

    def test_can_access_rag_feature_default_enabled(self, mock_supabase_client):
        """Test RAG feature access when using default enabled status"""
        user_data = {'organization_id': 'org-123', 'role': 'user'}
        
        # Mock no toggle found, but default enabled
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = [
            Mock(data=[]),  # No toggle found
            Mock(data=[{'default_enabled': True}])  # Default enabled
        ]
        
        result = can_access_rag_feature(user_data, 'best_practice_kb', 'org-123', mock_supabase_client)
        assert result is True

    def test_permission_checker_can_manage_rag_features(self, permission_checker):
        """Test PermissionChecker can manage RAG features"""
        result = permission_checker.can_manage_rag_features('org-456')
        assert result is True  # Same org as user

    def test_permission_checker_can_use_rag_feature(self, permission_checker, mock_supabase_client):
        """Test PermissionChecker can use RAG feature"""
        # Mock feature enabled check
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{'enabled': True}])
        
        result = permission_checker.can_use_rag_feature('best_practice_kb', 'org-456')
        assert result is True

    def test_permission_checker_get_accessible_organizations(self, permission_checker, mock_supabase_client):
        """Test PermissionChecker get accessible organizations"""
        # Mock organizations query
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[
            {'id': 'org-1'}, {'id': 'org-2'}, {'id': 'org-3'}
        ])
        
        # Change to system admin
        permission_checker.user_role = UserRole.SYSTEM_ADMIN
        
        result = permission_checker.get_accessible_organizations()
        assert len(result) == 3
        assert 'org-1' in result

    # ==================== FEATURE INHERITANCE TESTS ====================

    @pytest.mark.asyncio
    async def test_get_inherited_features_success(self, feature_inheritance_service, mock_supabase_client):
        """Test getting inherited features from parent organization"""
        # Mock parent organization query
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{'parent_organization_id': 'parent-org'}])
        
        # Mock parent features query
        mock_query.execute.side_effect = [
            Mock(data=[{'parent_organization_id': 'parent-org'}]),  # Get parent
            Mock(data=[  # Get parent features
                {'rag_feature': 'best_practice_kb', 'enabled': True},
                {'rag_feature': 'customer_insight_rag', 'enabled': True}
            ])
        ]
        
        result = await feature_inheritance_service.get_inherited_features('child-org')
        
        assert result['success'] is True
        assert len(result['inherited_features']) == 2
        assert result['inherited_features'][0]['rag_feature'] == 'best_practice_kb'

    @pytest.mark.asyncio
    async def test_get_effective_features_success(self, feature_inheritance_service, mock_supabase_client):
        """Test getting effective features (own + inherited)"""
        # Mock own features
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = [
            Mock(data=[  # Own features
                {'rag_feature': 'success_pattern_rag', 'enabled': True}
            ]),
            Mock(data=[  # Inherited features
                {'rag_feature': 'best_practice_kb', 'enabled': True, 'is_inherited': True}
            ])
        ]
        
        result = await feature_inheritance_service.get_effective_features('org-123')
        
        assert result['success'] is True
        assert len(result['effective_features']) == 2
        assert result['own_count'] == 1
        assert result['inherited_count'] == 1

    @pytest.mark.asyncio
    async def test_can_enable_feature_parent_allows(self, feature_inheritance_service, mock_supabase_client):
        """Test can enable feature when parent allows it"""
        # Mock parent features
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = [
            Mock(data=[{'parent_organization_id': 'parent-org'}]),
            Mock(data=[{'rag_feature': 'best_practice_kb', 'enabled': True}])
        ]
        
        result = await feature_inheritance_service.can_enable_feature('child-org', 'best_practice_kb')
        
        assert result['success'] is True
        assert result['can_enable'] is True

    @pytest.mark.asyncio
    async def test_can_enable_feature_parent_disallows(self, feature_inheritance_service, mock_supabase_client):
        """Test can enable feature when parent disallows it"""
        # Mock parent features
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = [
            Mock(data=[{'parent_organization_id': 'parent-org'}]),
            Mock(data=[{'rag_feature': 'best_practice_kb', 'enabled': False}])
        ]
        
        result = await feature_inheritance_service.can_enable_feature('child-org', 'best_practice_kb')
        
        assert result['success'] is True
        assert result['can_enable'] is False
        assert 'parent organization' in result['reason'].lower()

    # ==================== ENHANCED CONTEXT MANAGER TESTS ====================

    @pytest.mark.asyncio
    async def test_share_to_children_success(self, enhanced_context_manager, mock_supabase_client):
        """Test sharing context item to child organizations"""
        # Mock child organizations query
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = [
            Mock(data=[{'id': 'child-1'}, {'id': 'child-2'}]),  # Get children
            Mock(data=[{'id': 'share-1'}, {'id': 'share-2'}])   # Insert sharing requests
        ]
        
        result = await enhanced_context_manager.share_to_children(
            'parent-org', 'item-123', 'best_practice_kb', 'user-456'
        )
        
        assert result['success'] is True
        assert result['shared_count'] == 2

    @pytest.mark.asyncio
    async def test_share_to_parent_success(self, enhanced_context_manager, mock_supabase_client):
        """Test sharing context item to parent organization"""
        # Mock parent organization query
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = [
            Mock(data=[{'parent_organization_id': 'parent-org'}]),
            Mock(data=[{'id': 'share-1'}])
        ]
        
        result = await enhanced_context_manager.share_to_parent(
            'child-org', 'item-123', 'best_practice_kb', 'user-456'
        )
        
        assert result['success'] is True
        assert result['shared_count'] == 1

    @pytest.mark.asyncio
    async def test_get_pending_approvals_success(self, enhanced_context_manager, mock_supabase_client):
        """Test getting pending sharing approvals"""
        # Mock pending approvals query
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[
            {
                'id': 'approval-1',
                'source_organization_id': 'source-org',
                'rag_feature': 'best_practice_kb',
                'status': 'pending'
            }
        ])
        
        result = await enhanced_context_manager.get_pending_approvals('target-org')
        
        assert result['success'] is True
        assert len(result['pending_approvals']) == 1
        assert result['pending_approvals'][0]['status'] == 'pending'

    @pytest.mark.asyncio
    async def test_approve_shared_item_success(self, enhanced_context_manager, mock_supabase_client):
        """Test approving a shared item"""
        # Mock approval process
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = [
            Mock(data=[{'id': 'sharing-1', 'item_id': 'item-123'}]),  # Get sharing request
            Mock(data=[{'id': 'item-123'}]),  # Copy item
            Mock(data=[{'id': 'sharing-1'}])   # Update sharing status
        ]
        
        result = await enhanced_context_manager.approve_shared_item('sharing-1', 'admin-123')
        
        assert result['success'] is True
        assert result['message'] == 'Sharing request approved successfully'

    @pytest.mark.asyncio
    async def test_reject_shared_item_success(self, enhanced_context_manager, mock_supabase_client):
        """Test rejecting a shared item"""
        # Mock rejection process
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{'id': 'sharing-1'}])
        
        result = await enhanced_context_manager.reject_shared_item(
            'sharing-1', 'admin-123', 'Not relevant to our organization'
        )
        
        assert result['success'] is True
        assert result['message'] == 'Sharing request rejected successfully'

    # ==================== TENANT ISOLATION SERVICE TESTS ====================

    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_success(self, tenant_isolation_service, mock_supabase_client):
        """Test getting RAG feature toggles for organization"""
        # Mock toggles query
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[
            {'rag_feature': 'best_practice_kb', 'enabled': True},
            {'rag_feature': 'customer_insight_rag', 'enabled': False}
        ])
        
        result = await tenant_isolation_service.get_rag_feature_toggles('org-123')
        
        assert result['success'] is True
        assert len(result['toggles']) == 2
        assert result['toggles'][0]['rag_feature'] == 'best_practice_kb'

    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_success(self, tenant_isolation_service, mock_supabase_client):
        """Test updating a single RAG feature toggle"""
        # Mock update process
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{'id': 'toggle-1'}])
        
        result = await tenant_isolation_service.update_rag_feature_toggle(
            'org-123', 'best_practice_kb', True, 'admin-456'
        )
        
        assert result['success'] is True
        assert result['message'] == 'RAG feature toggle updated successfully'

    @pytest.mark.asyncio
    async def test_bulk_update_rag_toggles_success(self, tenant_isolation_service, mock_supabase_client):
        """Test bulk updating RAG feature toggles"""
        # Mock bulk update process
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[
            {'id': 'toggle-1'}, {'id': 'toggle-2'}
        ])
        
        updates = {
            'best_practice_kb': True,
            'customer_insight_rag': False
        }
        
        result = await tenant_isolation_service.bulk_update_rag_toggles(
            'org-123', updates, 'admin-456'
        )
        
        assert result['success'] is True
        assert result['total_updated'] == 2
        assert len(result['updated_toggles']) == 2

    # ==================== ERROR HANDLING TESTS ====================

    @pytest.mark.asyncio
    async def test_feature_inheritance_database_error(self, feature_inheritance_service, mock_supabase_client):
        """Test error handling in feature inheritance"""
        # Mock database error
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = Exception("Database connection failed")
        
        result = await feature_inheritance_service.get_inherited_features('org-123')
        
        assert result['success'] is False
        assert 'Database connection failed' in result['error']

    @pytest.mark.asyncio
    async def test_enhanced_context_manager_database_error(self, enhanced_context_manager, mock_supabase_client):
        """Test error handling in enhanced context manager"""
        # Mock database error
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = Exception("Database connection failed")
        
        result = await enhanced_context_manager.share_to_children(
            'parent-org', 'item-123', 'best_practice_kb', 'user-456'
        )
        
        assert result['success'] is False
        assert 'Database connection failed' in result['error']

    def test_permission_checker_database_error(self, permission_checker, mock_supabase_client):
        """Test error handling in permission checker"""
        # Mock database error
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = Exception("Database connection failed")
        
        result = permission_checker.can_use_rag_feature('best_practice_kb', 'org-456')
        
        assert result is False

    # ==================== EDGE CASE TESTS ====================

    @pytest.mark.asyncio
    async def test_get_inherited_features_no_parent(self, feature_inheritance_service, mock_supabase_client):
        """Test getting inherited features when organization has no parent"""
        # Mock no parent organization
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{'parent_organization_id': None}])
        
        result = await feature_inheritance_service.get_inherited_features('org-123')
        
        assert result['success'] is True
        assert len(result['inherited_features']) == 0

    @pytest.mark.asyncio
    async def test_share_to_children_no_children(self, enhanced_context_manager, mock_supabase_client):
        """Test sharing to children when organization has no children"""
        # Mock no child organizations
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[])
        
        result = await enhanced_context_manager.share_to_children(
            'parent-org', 'item-123', 'best_practice_kb', 'user-456'
        )
        
        assert result['success'] is True
        assert result['shared_count'] == 0
        assert 'No child organizations found' in result['message']

    @pytest.mark.asyncio
    async def test_get_pending_approvals_empty(self, enhanced_context_manager, mock_supabase_client):
        """Test getting pending approvals when none exist"""
        # Mock empty approvals
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[])
        
        result = await enhanced_context_manager.get_pending_approvals('org-123')
        
        assert result['success'] is True
        assert len(result['pending_approvals']) == 0

    # ==================== INTEGRATION TESTS ====================

    @pytest.mark.asyncio
    async def test_complete_feature_inheritance_workflow(self, feature_inheritance_service, mock_supabase_client):
        """Test complete feature inheritance workflow"""
        # Mock parent organization and features
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = [
            Mock(data=[{'parent_organization_id': 'parent-org'}]),
            Mock(data=[{'rag_feature': 'best_practice_kb', 'enabled': True}]),
            Mock(data=[{'rag_feature': 'best_practice_kb', 'enabled': True}]),
            Mock(data=[{'rag_feature': 'best_practice_kb', 'enabled': True}])
        ]
        
        # Test inheritance chain
        inheritance_result = await feature_inheritance_service.get_inheritance_chain('child-org')
        assert inheritance_result['success'] is True
        
        # Test inherited features
        inherited_result = await feature_inheritance_service.get_inherited_features('child-org')
        assert inherited_result['success'] is True
        
        # Test can enable feature
        can_enable_result = await feature_inheritance_service.can_enable_feature('child-org', 'best_practice_kb')
        assert can_enable_result['success'] is True
        
        # Test override status
        override_result = await feature_inheritance_service.get_override_status('child-org', 'best_practice_kb')
        assert override_result['success'] is True

    @pytest.mark.asyncio
    async def test_complete_sharing_workflow(self, enhanced_context_manager, mock_supabase_client):
        """Test complete context sharing workflow"""
        # Mock sharing workflow
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = [
            Mock(data=[{'id': 'child-1'}]),  # Get children
            Mock(data=[{'id': 'share-1'}]),  # Create sharing request
            Mock(data=[{'id': 'share-1', 'status': 'pending'}]),  # Get pending approvals
            Mock(data=[{'id': 'share-1', 'item_id': 'item-123'}]),  # Get sharing request
            Mock(data=[{'id': 'item-123'}]),  # Copy item
            Mock(data=[{'id': 'share-1'}])   # Update sharing status
        ]
        
        # Test share to children
        share_result = await enhanced_context_manager.share_to_children(
            'parent-org', 'item-123', 'best_practice_kb', 'user-456'
        )
        assert share_result['success'] is True
        
        # Test get pending approvals
        pending_result = await enhanced_context_manager.get_pending_approvals('child-1')
        assert pending_result['success'] is True
        
        # Test approve shared item
        approve_result = await enhanced_context_manager.approve_shared_item('share-1', 'admin-123')
        assert approve_result['success'] is True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
