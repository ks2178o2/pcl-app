"""
Comprehensive Backend Tests for RAG Features
Tests all RAG feature functionality including permissions, inheritance, and multi-tenancy
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# Add the parent directory to the path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.tenant_isolation_service import TenantIsolationService
from services.feature_inheritance_service import FeatureInheritanceService
from services.enhanced_context_manager import EnhancedContextManager
from middleware.permissions import require_role, can_access_organization, can_access_rag_feature
from middleware.validation import rag_validator

# ==================== FIXTURES ====================

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client with comprehensive chaining"""
    mock_client = Mock()
    
    # Mock the from_ method to return a chainable query builder
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
    mock_query.execute.return_value = Mock(data=[], count=0)
    
    mock_client.from_.return_value = mock_query
    return mock_client

@pytest.fixture
def tenant_isolation_service(mock_supabase_client):
    """TenantIsolationService with mocked Supabase client"""
    with patch('services.tenant_isolation_service.get_supabase_client', return_value=mock_supabase_client):
        return TenantIsolationService()

@pytest.fixture
def feature_inheritance_service(mock_supabase_client):
    """FeatureInheritanceService with mocked Supabase client"""
    with patch('services.feature_inheritance_service.get_supabase_client', return_value=mock_supabase_client):
        return FeatureInheritanceService()

@pytest.fixture
def enhanced_context_manager(mock_supabase_client):
    """EnhancedContextManager with mocked Supabase client"""
    with patch('services.enhanced_context_manager.get_supabase_client', return_value=mock_supabase_client):
        return EnhancedContextManager()

# ==================== TEST DATA ====================

SAMPLE_ORGANIZATIONS = [
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
]

SAMPLE_RAG_FEATURES = [
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
]

SAMPLE_RAG_TOGGLES = [
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
]

# ==================== TENANT ISOLATION SERVICE TESTS ====================

class TestTenantIsolationService:
    """Test TenantIsolationService RAG feature functionality"""

    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_success(self, tenant_isolation_service, mock_supabase_client):
        """Test successful retrieval of RAG feature toggles"""
        # Mock the database response
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = SAMPLE_RAG_TOGGLES
        
        result = await tenant_isolation_service.get_rag_feature_toggles('org-root')
        
        assert result['success'] is True
        assert 'toggles' in result
        assert len(result['toggles']) == 2
        assert result['toggles'][0]['rag_feature'] == 'best_practice_kb'

    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_no_data(self, tenant_isolation_service, mock_supabase_client):
        """Test RAG feature toggles when no data exists"""
        # Mock empty response
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        result = await tenant_isolation_service.get_rag_feature_toggles('org-root')
        
        assert result['success'] is True
        assert result['toggles'] == []

    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_database_error(self, tenant_isolation_service, mock_supabase_client):
        """Test RAG feature toggles with database error"""
        # Mock database error
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database connection failed")
        
        result = await tenant_isolation_service.get_rag_feature_toggles('org-root')
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Database connection failed' in result['error']

    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_success(self, tenant_isolation_service, mock_supabase_client):
        """Test successful RAG feature toggle update"""
        # Mock successful update
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
            'id': 'toggle-1',
            'organization_id': 'org-root',
            'rag_feature': 'best_practice_kb',
            'enabled': False
        }]
        
        result = await tenant_isolation_service.update_rag_feature_toggle(
            'org-root', 'best_practice_kb', False
        )
        
        assert result['success'] is True
        assert result['toggle']['enabled'] is False

    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_not_found(self, tenant_isolation_service, mock_supabase_client):
        """Test RAG feature toggle update when toggle doesn't exist"""
        # Mock no data returned
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        result = await tenant_isolation_service.update_rag_feature_toggle(
            'org-root', 'nonexistent_feature', False
        )
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    @pytest.mark.asyncio
    async def test_bulk_update_rag_toggles_success(self, tenant_isolation_service, mock_supabase_client):
        """Test successful bulk RAG feature toggle update"""
        # Mock successful bulk update
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.in_.return_value.execute.return_value.data = [
            {'id': 'toggle-1', 'enabled': True},
            {'id': 'toggle-2', 'enabled': False}
        ]
        
        updates = {
            'best_practice_kb': True,
            'performance_analytics': False
        }
        
        result = await tenant_isolation_service.bulk_update_rag_toggles('org-root', updates)
        
        assert result['success'] is True
        assert result['total_updated'] == 2
        assert len(result['updated_toggles']) == 2

    @pytest.mark.asyncio
    async def test_get_inherited_features_success(self, tenant_isolation_service, mock_supabase_client):
        """Test successful retrieval of inherited features"""
        # Mock organization with parent
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'parent_organization_id': 'org-root'
        }]
        
        # Mock parent's enabled features
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = SAMPLE_RAG_TOGGLES
        
        result = await tenant_isolation_service.get_inherited_features('org-child-1')
        
        assert result['success'] is True
        assert 'inherited_features' in result
        assert result['parent_organization_id'] == 'org-root'

    @pytest.mark.asyncio
    async def test_get_inherited_features_no_parent(self, tenant_isolation_service, mock_supabase_client):
        """Test inherited features when organization has no parent"""
        # Mock organization without parent
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'parent_organization_id': None
        }]
        
        result = await tenant_isolation_service.get_inherited_features('org-root')
        
        assert result['success'] is True
        assert result['inherited_features'] == []
        assert result['parent_organization_id'] is None

    @pytest.mark.asyncio
    async def test_get_effective_features_success(self, tenant_isolation_service, mock_supabase_client):
        """Test successful retrieval of effective features (own + inherited)"""
        # Mock own features
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_RAG_TOGGLES[0]]
        
        # Mock inherited features
        with patch.object(tenant_isolation_service, 'get_inherited_features', return_value={
            'success': True,
            'inherited_features': [SAMPLE_RAG_TOGGLES[1]]
        }):
            result = await tenant_isolation_service.get_effective_features('org-child-1')
        
        assert result['success'] is True
        assert 'effective_features' in result
        assert result['own_count'] == 1
        assert result['inherited_count'] == 1
        assert result['total_count'] == 2

    @pytest.mark.asyncio
    async def test_can_enable_feature_success(self, tenant_isolation_service, mock_supabase_client):
        """Test successful feature enablement check"""
        # Mock feature exists in catalog
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [SAMPLE_RAG_FEATURES[0]]
        
        # Mock organization has parent
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'parent_organization_id': 'org-root'
        }]
        
        # Mock parent has feature enabled
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': True
        }]
        
        result = await tenant_isolation_service.can_enable_feature('org-child-1', 'best_practice_kb')
        
        assert result['success'] is True
        assert result['can_enable'] is True

    @pytest.mark.asyncio
    async def test_can_enable_feature_parent_disabled(self, tenant_isolation_service, mock_supabase_client):
        """Test feature enablement check when parent has it disabled"""
        # Mock feature exists in catalog
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [SAMPLE_RAG_FEATURES[0]]
        
        # Mock organization has parent
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'parent_organization_id': 'org-root'
        }]
        
        # Mock parent has feature disabled
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': False
        }]
        
        result = await tenant_isolation_service.can_enable_feature('org-child-1', 'best_practice_kb')
        
        assert result['success'] is True
        assert result['can_enable'] is False
        assert 'parent organization has it disabled' in result['reason']

# ==================== FEATURE INHERITANCE SERVICE TESTS ====================

class TestFeatureInheritanceService:
    """Test FeatureInheritanceService functionality"""

    @pytest.mark.asyncio
    async def test_resolve_features_success(self, feature_inheritance_service, mock_supabase_client):
        """Test successful feature resolution with inheritance details"""
        # Mock inheritance chain
        with patch.object(feature_inheritance_service, 'get_inheritance_chain', return_value={
            'success': True,
            'inheritance_chain': SAMPLE_ORGANIZATIONS
        }):
            # Mock effective features
            with patch.object(feature_inheritance_service.tenant_service, 'get_effective_features', return_value={
                'success': True,
                'effective_features': SAMPLE_RAG_TOGGLES,
                'own_count': 1,
                'inherited_count': 1,
                'total_count': 2
            }):
                result = await feature_inheritance_service.resolve_features('org-child-1')
        
        assert result['success'] is True
        assert 'effective_features' in result
        assert 'inheritance_chain' in result
        assert result['own_count'] == 1
        assert result['inherited_count'] == 1

    @pytest.mark.asyncio
    async def test_get_inheritance_chain_success(self, feature_inheritance_service, mock_supabase_client):
        """Test successful inheritance chain retrieval"""
        # Mock organization hierarchy
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 'org-child-1', 'name': 'Child Org', 'parent_organization_id': 'org-root'},
            {'id': 'org-root', 'name': 'Root Org', 'parent_organization_id': None}
        ]
        
        result = await feature_inheritance_service.get_inheritance_chain('org-child-1')
        
        assert result['success'] is True
        assert 'inheritance_chain' in result
        assert len(result['inheritance_chain']) == 2
        assert result['depth'] == 1

    @pytest.mark.asyncio
    async def test_can_override_feature_explicit(self, feature_inheritance_service, mock_supabase_client):
        """Test override capability for explicit features"""
        # Mock organization has explicit setting
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [SAMPLE_RAG_TOGGLES[0]]
        
        with patch.object(feature_inheritance_service, 'get_inheritance_chain', return_value={
            'success': True,
            'inheritance_chain': SAMPLE_ORGANIZATIONS
        }):
            result = await feature_inheritance_service.can_override_feature('org-root', 'best_practice_kb')
        
        assert result['success'] is True
        assert result['can_override'] is True
        assert result['current_status'] == 'explicit'

    @pytest.mark.asyncio
    async def test_can_override_feature_inherited(self, feature_inheritance_service, mock_supabase_client):
        """Test override capability for inherited features"""
        # Mock organization has no explicit setting
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        # Mock parent has feature
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [SAMPLE_RAG_TOGGLES[1]]
        
        with patch.object(feature_inheritance_service, 'get_inheritance_chain', return_value={
            'success': True,
            'inheritance_chain': SAMPLE_ORGANIZATIONS
        }):
            result = await feature_inheritance_service.can_override_feature('org-child-1', 'best_practice_kb')
        
        assert result['success'] is True
        assert result['can_override'] is True
        assert result['current_status'] == 'inherited'

    @pytest.mark.asyncio
    async def test_get_override_status_explicit(self, feature_inheritance_service, mock_supabase_client):
        """Test override status for explicit features"""
        # Mock organization has explicit setting
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [SAMPLE_RAG_TOGGLES[0]]
        
        with patch.object(feature_inheritance_service, 'get_inheritance_chain', return_value={
            'success': True,
            'inheritance_chain': SAMPLE_ORGANIZATIONS
        }):
            result = await feature_inheritance_service.get_override_status('org-root', 'best_practice_kb')
        
        assert result['success'] is True
        assert result['status'] == 'enabled'
        assert result['is_inherited'] is False
        assert result['override_type'] == 'explicit'

    @pytest.mark.asyncio
    async def test_get_inheritance_summary_success(self, feature_inheritance_service, mock_supabase_client):
        """Test successful inheritance summary generation"""
        # Mock resolve features
        with patch.object(feature_inheritance_service, 'resolve_features', return_value={
            'success': True,
            'effective_features': SAMPLE_RAG_TOGGLES,
            'inheritance_chain': SAMPLE_ORGANIZATIONS
        }):
            result = await feature_inheritance_service.get_inheritance_summary('org-child-1')
        
        assert result['success'] is True
        assert 'summary' in result
        assert 'inheritance_chain' in result
        assert 'feature_breakdown' in result
        assert result['summary']['total_features'] == 2

    @pytest.mark.asyncio
    async def test_validate_inheritance_rules_enable_allowed(self, feature_inheritance_service, mock_supabase_client):
        """Test inheritance rule validation for allowed enablement"""
        # Mock inheritance chain
        with patch.object(feature_inheritance_service, 'get_inheritance_chain', return_value={
            'success': True,
            'inheritance_chain': SAMPLE_ORGANIZATIONS
        }):
            # Mock parent has feature enabled
            mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
                'enabled': True
            }]
            
            result = await feature_inheritance_service.validate_inheritance_rules('org-child-1', 'best_practice_kb', True)
        
        assert result['success'] is True
        assert result['can_proceed'] is True

    @pytest.mark.asyncio
    async def test_validate_inheritance_rules_enable_blocked(self, feature_inheritance_service, mock_supabase_client):
        """Test inheritance rule validation for blocked enablement"""
        # Mock inheritance chain
        with patch.object(feature_inheritance_service, 'get_inheritance_chain', return_value={
            'success': True,
            'inheritance_chain': SAMPLE_ORGANIZATIONS
        }):
            # Mock parent has feature disabled
            mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
                'enabled': False
            }]
            
            result = await feature_inheritance_service.validate_inheritance_rules('org-child-1', 'best_practice_kb', True)
        
        assert result['success'] is False
        assert result['can_proceed'] is False
        assert 'parent organization' in result['reason']

# ==================== ENHANCED CONTEXT MANAGER TESTS ====================

class TestEnhancedContextManagerHierarchy:
    """Test EnhancedContextManager hierarchy sharing functionality"""

    @pytest.mark.asyncio
    async def test_share_to_children_success(self, enhanced_context_manager, mock_supabase_client):
        """Test successful sharing to child organizations"""
        # Mock child organizations
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 'org-child-1'},
            {'id': 'org-child-2'}
        ]
        
        # Mock successful insert
        mock_supabase_client.from_.return_value.insert.return_value.execute.return_value.data = [
            {'id': 'sharing-1'},
            {'id': 'sharing-2'}
        ]
        
        result = await enhanced_context_manager.share_to_children(
            'org-root', 'item-1', 'best_practice_kb', 'user-1'
        )
        
        assert result['success'] is True
        assert result['shared_count'] == 2
        assert 'child organizations' in result['message']

    @pytest.mark.asyncio
    async def test_share_to_children_no_children(self, enhanced_context_manager, mock_supabase_client):
        """Test sharing to children when no children exist"""
        # Mock no child organizations
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        result = await enhanced_context_manager.share_to_children(
            'org-root', 'item-1', 'best_practice_kb', 'user-1'
        )
        
        assert result['success'] is True
        assert result['shared_count'] == 0
        assert 'No child organizations found' in result['message']

    @pytest.mark.asyncio
    async def test_share_to_parent_success(self, enhanced_context_manager, mock_supabase_client):
        """Test successful sharing to parent organization"""
        # Mock organization has parent
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'parent_organization_id': 'org-root'
        }]
        
        # Mock successful insert
        mock_supabase_client.from_.return_value.insert.return_value.execute.return_value.data = [{
            'id': 'sharing-1'
        }]
        
        result = await enhanced_context_manager.share_to_parent(
            'org-child-1', 'item-1', 'best_practice_kb', 'user-1'
        )
        
        assert result['success'] is True
        assert result['sharing_id'] == 'sharing-1'
        assert 'parent organization' in result['message']

    @pytest.mark.asyncio
    async def test_share_to_parent_no_parent(self, enhanced_context_manager, mock_supabase_client):
        """Test sharing to parent when no parent exists"""
        # Mock organization has no parent
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'parent_organization_id': None
        }]
        
        result = await enhanced_context_manager.share_to_parent(
            'org-root', 'item-1', 'best_practice_kb', 'user-1'
        )
        
        assert result['success'] is False
        assert 'No parent organization found' in result['error']

    @pytest.mark.asyncio
    async def test_get_pending_approvals_success(self, enhanced_context_manager, mock_supabase_client):
        """Test successful retrieval of pending approvals"""
        # Mock pending requests
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {
                'id': 'sharing-1',
                'source_organization_id': 'org-parent',
                'target_organization_id': 'org-child',
                'rag_feature': 'best_practice_kb',
                'status': 'pending'
            }
        ]
        
        result = await enhanced_context_manager.get_pending_approvals('org-child')
        
        assert result['success'] is True
        assert result['count'] == 1
        assert len(result['pending_requests']) == 1

    @pytest.mark.asyncio
    async def test_approve_shared_item_success(self, enhanced_context_manager, mock_supabase_client):
        """Test successful approval of shared item"""
        # Mock sharing update
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            'id': 'sharing-1',
            'item_id': 'item-1',
            'target_organization_id': 'org-child',
            'rag_feature': 'best_practice_kb',
            'source_organization_id': 'org-parent'
        }]
        
        # Mock original item retrieval
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'title': 'Test Item',
            'content': 'Test content',
            'item_type': 'document'
        }]
        
        # Mock new item creation
        mock_supabase_client.from_.return_value.insert.return_value.execute.return_value.data = [{
            'id': 'new-item-1'
        }]
        
        result = await enhanced_context_manager.approve_shared_item('sharing-1', 'user-1')
        
        assert result['success'] is True
        assert result['approved_id'] == 'sharing-1'
        assert result['new_item_id'] == 'new-item-1'

    @pytest.mark.asyncio
    async def test_reject_shared_item_success(self, enhanced_context_manager, mock_supabase_client):
        """Test successful rejection of shared item"""
        # Mock sharing update
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            'id': 'sharing-1'
        }]
        
        result = await enhanced_context_manager.reject_shared_item('sharing-1', 'user-1', 'Not relevant')
        
        assert result['success'] is True
        assert result['rejected_id'] == 'sharing-1'
        assert 'rejected' in result['message']

    @pytest.mark.asyncio
    async def test_get_hierarchy_sharing_stats_success(self, enhanced_context_manager, mock_supabase_client):
        """Test successful retrieval of hierarchy sharing statistics"""
        # Mock outgoing shares count
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.count = 5
        
        # Mock incoming shares count
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.count = 3
        
        # Mock pending approvals count
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.count = 2
        
        result = await enhanced_context_manager.get_hierarchy_sharing_stats('org-root')
        
        assert result['success'] is True
        assert result['stats']['outgoing_shares'] == 5
        assert result['stats']['incoming_shares'] == 3
        assert result['stats']['pending_approvals'] == 2

# ==================== PERMISSION MIDDLEWARE TESTS ====================

class TestPermissionMiddleware:
    """Test permission middleware functionality"""

    @pytest.mark.asyncio
    async def test_require_role_system_admin_success(self):
        """Test require_role decorator for system admin success"""
        @require_role(['system_admin'])
        async def test_function(request):
            return {'success': True}
        
        # Mock request with system admin role
        mock_request = Mock()
        mock_request.headers = {'X-User-Roles': 'system_admin'}
        
        result = await test_function(request=mock_request)
        assert result['success'] is True

    @pytest.mark.asyncio
    async def test_require_role_insufficient_permissions(self):
        """Test require_role decorator with insufficient permissions"""
        @require_role(['system_admin'])
        async def test_function(request):
            return {'success': True}
        
        # Mock request with user role
        mock_request = Mock()
        mock_request.headers = {'X-User-Roles': 'user'}
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await test_function(request=mock_request)

    @pytest.mark.asyncio
    async def test_check_organization_access_same_org(self, mock_supabase_client):
        """Test organization access check for same organization"""
        # Mock request with same organization
        mock_request = Mock()
        mock_request.headers = {'X-Organization-Id': 'org-1'}
        
        with patch('middleware.permissions.get_supabase_client', return_value=mock_supabase_client):
            result = await check_organization_access('org-1', mock_request)
            assert result is True

    @pytest.mark.asyncio
    async def test_check_rag_feature_access_system_admin(self, mock_supabase_client):
        """Test RAG feature access check for system admin"""
        # Mock request with system admin role
        mock_request = Mock()
        mock_request.headers = {'X-User-Roles': 'system_admin'}
        
        with patch('middleware.permissions.get_supabase_client', return_value=mock_supabase_client):
            result = await check_rag_feature_access('best_practice_kb', 'org-1', mock_request)
            assert result is True

# ==================== VALIDATION MIDDLEWARE TESTS ====================

class TestValidationMiddleware:
    """Test validation middleware functionality"""

    @pytest.mark.asyncio
    async def test_validate_rag_feature_exists_success(self, mock_supabase_client):
        """Test RAG feature validation when feature exists"""
        # Mock feature exists
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[SAMPLE_RAG_FEATURES[0]])
        rag_validator.supabase = mock_supabase_client

        result = await rag_validator.validate_rag_feature_exists('best_practice_kb')
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_rag_feature_exists_not_found(self, mock_supabase_client):
        """Test RAG feature validation when feature doesn't exist"""
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[])
        rag_validator.supabase = mock_supabase_client

        result = await rag_validator.validate_rag_feature_exists('nonexistent_feature')
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_organization_hierarchy_success(self, mock_supabase_client):
        """Test organization hierarchy validation success"""
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[{"parent_organization_id": None}])
        rag_validator.supabase = mock_supabase_client

        result, message = await rag_validator.validate_org_hierarchy('org-child', 'org-parent')
        assert result is True
        assert message == ""

    @pytest.mark.asyncio
    async def test_validate_organization_hierarchy_circular_dependency(self, mock_supabase_client):
        """Test organization hierarchy validation with circular dependency"""
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[{'parent_organization_id': 'org-child'}])
        rag_validator.supabase = mock_supabase_client

        result, message = await rag_validator.validate_org_hierarchy('org-child', 'org-parent')
        assert result is False
        assert "Circular" in message

# ==================== INTEGRATION TESTS ====================

class TestRAGFeatureIntegration:
    """Integration tests for RAG feature workflows"""

    @pytest.mark.asyncio
    async def test_end_to_end_feature_toggle_workflow(self, tenant_isolation_service, mock_supabase_client):
        """Test complete feature toggle workflow"""
        # Mock initial state - feature disabled
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'id': 'toggle-1',
            'organization_id': 'org-root',
            'rag_feature': 'best_practice_kb',
            'enabled': False
        }]
        
        # Mock successful update
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
            'id': 'toggle-1',
            'organization_id': 'org-root',
            'rag_feature': 'best_practice_kb',
            'enabled': True
        }]
        
        # Test workflow
        result = await tenant_isolation_service.update_rag_feature_toggle(
            'org-root', 'best_practice_kb', True
        )
        
        assert result['success'] is True
        assert result['toggle']['enabled'] is True

    @pytest.mark.asyncio
    async def test_end_to_end_inheritance_workflow(self, feature_inheritance_service, mock_supabase_client):
        """Test complete inheritance workflow"""
        # Mock inheritance chain
        with patch.object(feature_inheritance_service, 'get_inheritance_chain', return_value={
            'success': True,
            'inheritance_chain': SAMPLE_ORGANIZATIONS
        }):
            # Mock effective features
            with patch.object(feature_inheritance_service.tenant_service, 'get_effective_features', return_value={
                'success': True,
                'effective_features': SAMPLE_RAG_TOGGLES,
                'own_count': 1,
                'inherited_count': 1,
                'total_count': 2
            }):
                result = await feature_inheritance_service.resolve_features('org-child-1')
        
        assert result['success'] is True
        assert result['own_count'] == 1
        assert result['inherited_count'] == 1

    @pytest.mark.asyncio
    async def test_end_to_end_sharing_workflow(self, enhanced_context_manager, mock_supabase_client):
        """Test complete sharing workflow"""
        # Mock child organizations
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 'org-child-1'}
        ]
        
        # Mock successful sharing
        mock_supabase_client.from_.return_value.insert.return_value.execute.return_value.data = [
            {'id': 'sharing-1'}
        ]
        
        # Test sharing
        share_result = await enhanced_context_manager.share_to_children(
            'org-root', 'item-1', 'best_practice_kb', 'user-1'
        )
        
        assert share_result['success'] is True
        
        # Mock pending approvals
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {
                'id': 'sharing-1',
                'source_organization_id': 'org-root',
                'target_organization_id': 'org-child-1',
                'rag_feature': 'best_practice_kb',
                'item_id': 'item-1',
                'status': 'pending'
            }
        ]
        
        # Test approval retrieval
        approval_result = await enhanced_context_manager.get_pending_approvals('org-child-1')
        
        assert approval_result['success'] is True
        assert approval_result['count'] == 1

# ==================== PERFORMANCE TESTS ====================

class TestRAGFeaturePerformance:
    """Performance tests for RAG feature operations"""

    @pytest.mark.asyncio
    async def test_bulk_toggle_performance(self, tenant_isolation_service, mock_supabase_client):
        """Test performance of bulk toggle operations"""
        import time
        
        # Mock large number of toggles
        large_updates = {f'feature_{i}': i % 2 == 0 for i in range(100)}
        
        # Mock successful bulk update
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.in_.return_value.execute.return_value.data = [
            {'id': f'toggle-{i}'} for i in range(100)
        ]
        
        start_time = time.time()
        result = await tenant_isolation_service.bulk_update_rag_toggles('org-root', large_updates)
        end_time = time.time()
        
        assert result['success'] is True
        assert result['total_updated'] == 100
        assert (end_time - start_time) < 1.0  # Should complete within 1 second

    @pytest.mark.asyncio
    async def test_inheritance_resolution_performance(self, feature_inheritance_service, mock_supabase_client):
        """Test performance of inheritance resolution"""
        import time
        
        # Mock deep hierarchy
        deep_hierarchy = [
            {'id': f'org-level-{i}', 'name': f'Level {i}', 'parent_organization_id': f'org-level-{i-1}' if i > 0 else None}
            for i in range(10)
        ]
        
        with patch.object(feature_inheritance_service, 'get_inheritance_chain', return_value={
            'success': True,
            'inheritance_chain': deep_hierarchy
        }):
            with patch.object(feature_inheritance_service.tenant_service, 'get_effective_features', return_value={
                'success': True,
                'effective_features': SAMPLE_RAG_TOGGLES,
                'own_count': 1,
                'inherited_count': 1,
                'total_count': 2
            }):
                start_time = time.time()
                result = await feature_inheritance_service.resolve_features('org-level-9')
                end_time = time.time()
        
        assert result['success'] is True
        assert (end_time - start_time) < 0.5  # Should complete within 0.5 seconds

# ==================== ERROR HANDLING TESTS ====================

class TestRAGFeatureErrorHandling:
    """Test error handling in RAG feature operations"""

    @pytest.mark.asyncio
    async def test_database_connection_error(self, tenant_isolation_service, mock_supabase_client):
        """Test handling of database connection errors"""
        # Mock database connection error
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Connection timeout")
        
        result = await tenant_isolation_service.get_rag_feature_toggles('org-root')
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Connection timeout' in result['error']

    @pytest.mark.asyncio
    async def test_invalid_organization_id(self, tenant_isolation_service, mock_supabase_client):
        """Test handling of invalid organization IDs"""
        # Mock no organization found
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        result = await tenant_isolation_service.get_rag_feature_toggles('invalid-org')
        
        assert result['success'] is True
        assert result['toggles'] == []

    @pytest.mark.asyncio
    async def test_malformed_feature_name(self, tenant_isolation_service, mock_supabase_client):
        """Test handling of malformed feature names"""
        # Mock database error for malformed feature name
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Invalid feature name")
        
        result = await tenant_isolation_service.update_rag_feature_toggle(
            'org-root', 'invalid-feature-name!', True
        )
        
        assert result['success'] is False
        assert 'error' in result

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
