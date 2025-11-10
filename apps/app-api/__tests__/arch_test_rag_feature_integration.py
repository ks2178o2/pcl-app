"""
End-to-End Integration Tests for RAG Feature Management
Tests complete workflows from frontend to backend with real API calls
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json

# Add the parent directory to the path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.rag_features_api import router as rag_features_router
from api.organization_toggles_api import router as organization_toggles_router
from api.organization_hierarchy_api import router as organization_hierarchy_router
from services.tenant_isolation_service import TenantIsolationService
from services.feature_inheritance_service import FeatureInheritanceService
from services.enhanced_context_manager import EnhancedContextManager
from middleware.permissions import UserRole

class TestRAGFeatureIntegration:
    """Integration tests for complete RAG feature management workflows"""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with all routers"""
        app = FastAPI()
        app.include_router(rag_features_router, prefix="/api/v1")
        app.include_router(organization_toggles_router, prefix="/api/v1")
        app.include_router(organization_hierarchy_router, prefix="/api/v1")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client with realistic data"""
        mock_client = Mock()
        
        # Mock realistic database responses
        mock_query = Mock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.insert.return_value = mock_query
        mock_query.update.return_value = mock_query
        mock_query.delete.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.single.return_value = mock_query
        
        # Default empty response
        mock_query.execute.return_value = Mock(data=[], count=0)
        mock_client.from_.return_value = mock_query
        
        return mock_client

    @pytest.fixture
    def tenant_isolation_service(self, mock_supabase_client):
        """Create TenantIsolationService with mocked client"""
        return TenantIsolationService(mock_supabase_client)

    @pytest.fixture
    def feature_inheritance_service(self, mock_supabase_client):
        """Create FeatureInheritanceService with mocked client"""
        return FeatureInheritanceService(mock_supabase_client)

    @pytest.fixture
    def enhanced_context_manager(self, mock_supabase_client):
        """Create EnhancedContextManager with mocked client"""
        return EnhancedContextManager(mock_supabase_client)

    # ==================== COMPLETE WORKFLOW TESTS ====================

    @pytest.mark.asyncio
    async def test_complete_rag_feature_management_workflow(self, client, mock_supabase_client):
        """Test complete RAG feature management workflow from API to database"""
        
        # Mock database responses for complete workflow
        mock_query = mock_supabase_client.from_.return_value
        
        # Step 1: Get all RAG features
        mock_query.execute.side_effect = [
            Mock(data=[  # Get all features
                {
                    'rag_feature': 'best_practice_kb',
                    'name': 'Best Practice Knowledge Base',
                    'description': 'Sales best practices',
                    'category': 'sales',
                    'default_enabled': True
                },
                {
                    'rag_feature': 'customer_insight_rag',
                    'name': 'Customer Intelligence',
                    'description': 'Customer insights',
                    'category': 'sales',
                    'default_enabled': True
                }
            ]),
            Mock(data=[  # Get organization toggles
                {
                    'rag_feature': 'best_practice_kb',
                    'enabled': True,
                    'is_inherited': False
                },
                {
                    'rag_feature': 'customer_insight_rag',
                    'enabled': False,
                    'is_inherited': True
                }
            ]),
            Mock(data=[{'id': 'toggle-1'}]),  # Update toggle
            Mock(data=[  # Get updated toggles
                {
                    'rag_feature': 'best_practice_kb',
                    'enabled': False,
                    'is_inherited': False
                }
            ])
        ]

        # Step 1: Get all RAG features
        response = client.get("/api/v1/rag-features")
        assert response.status_code == 200
        features = response.json()
        assert len(features) == 2
        assert features[0]['rag_feature'] == 'best_practice_kb'

        # Step 2: Get organization toggles
        response = client.get(
            "/api/v1/organizations/org-123/rag-toggles",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 200
        toggles = response.json()
        assert len(toggles['toggles']) == 2

        # Step 3: Update a toggle
        response = client.put(
            "/api/v1/organizations/org-123/rag-toggles/best_practice_kb",
            json={'enabled': False, 'reason': 'Disabling for maintenance'},
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True

        # Step 4: Verify the change
        response = client.get(
            "/api/v1/organizations/org-123/rag-toggles",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 200
        updated_toggles = response.json()
        assert updated_toggles['toggles'][0]['enabled'] is False

    @pytest.mark.asyncio
    async def test_hierarchical_organization_feature_inheritance_workflow(self, client, mock_supabase_client):
        """Test complete hierarchical organization and feature inheritance workflow"""
        
        mock_query = mock_supabase_client.from_.return_value
        
        # Mock hierarchy and inheritance data
        mock_query.execute.side_effect = [
            Mock(data=[  # Get parent organization
                {'id': 'parent-org', 'name': 'Parent Organization', 'parent_organization_id': None}
            ]),
            Mock(data=[  # Get child organizations
                {'id': 'child-org', 'name': 'Child Organization', 'parent_organization_id': 'parent-org'}
            ]),
            Mock(data=[  # Get parent features
                {'rag_feature': 'best_practice_kb', 'enabled': True},
                {'rag_feature': 'customer_insight_rag', 'enabled': True}
            ]),
            Mock(data=[  # Get child features (inherited)
                {'rag_feature': 'best_practice_kb', 'enabled': True, 'is_inherited': True},
                {'rag_feature': 'customer_insight_rag', 'enabled': True, 'is_inherited': True}
            ]),
            Mock(data=[  # Create child organization
                {'id': 'new-child', 'name': 'New Child', 'parent_organization_id': 'parent-org'}
            ])
        ]

        # Step 1: Get organization hierarchy
        response = client.get(
            "/api/v1/organizations/parent-org/hierarchy",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'parent-org'}
        )
        assert response.status_code == 200
        hierarchy = response.json()
        assert len(hierarchy['hierarchy']) == 1

        # Step 2: Get inherited features for child
        response = client.get(
            "/api/v1/organizations/child-org/rag-toggles/inherited",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'child-org'}
        )
        assert response.status_code == 200
        inherited = response.json()
        assert len(inherited['inherited_features']) == 2

        # Step 3: Create new child organization
        response = client.post(
            "/api/v1/organizations/parent-org/children",
            json={'name': 'New Child Organization', 'description': 'A new child org'},
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'parent-org'}
        )
        assert response.status_code == 201
        new_child = response.json()
        assert new_child['name'] == 'New Child Organization'

    @pytest.mark.asyncio
    async def test_context_sharing_and_approval_workflow(self, client, mock_supabase_client):
        """Test complete context sharing and approval workflow"""
        
        mock_query = mock_supabase_client.from_.return_value
        
        # Mock sharing workflow data
        mock_query.execute.side_effect = [
            Mock(data=[  # Get child organizations
                {'id': 'child-org-1'}, {'id': 'child-org-2'}
            ]),
            Mock(data=[  # Create sharing requests
                {'id': 'share-1'}, {'id': 'share-2'}
            ]),
            Mock(data=[  # Get pending approvals
                {
                    'id': 'share-1',
                    'source_organization_id': 'parent-org',
                    'target_organization_id': 'child-org-1',
                    'rag_feature': 'best_practice_kb',
                    'item_id': 'item-123',
                    'status': 'pending'
                }
            ]),
            Mock(data=[  # Get sharing request details
                {'id': 'share-1', 'item_id': 'item-123', 'status': 'pending'}
            ]),
            Mock(data=[  # Copy item to target org
                {'id': 'item-123'}
            ]),
            Mock(data=[  # Update sharing status
                {'id': 'share-1', 'status': 'approved'}
            ])
        ]

        # Step 1: Share context item to children
        response = client.post(
            "/api/v1/context/sharing/share-to-children",
            json={
                'source_org_id': 'parent-org',
                'item_id': 'item-123',
                'rag_feature': 'best_practice_kb',
                'shared_by': 'admin-123'
            },
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'parent-org'}
        )
        assert response.status_code == 200
        share_result = response.json()
        assert share_result['shared_count'] == 2

        # Step 2: Get pending approvals for child organization
        response = client.get(
            "/api/v1/context/sharing/pending-approvals",
            params={'organization_id': 'child-org-1'},
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'child-org-1'}
        )
        assert response.status_code == 200
        approvals = response.json()
        assert len(approvals['pending_approvals']) == 1

        # Step 3: Approve sharing request
        response = client.post(
            "/api/v1/context/sharing/approve",
            json={
                'sharing_id': 'share-1',
                'approved_by': 'admin-456'
            },
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'child-org-1'}
        )
        assert response.status_code == 200
        approval_result = response.json()
        assert approval_result['success'] is True

    @pytest.mark.asyncio
    async def test_bulk_operations_workflow(self, client, mock_supabase_client):
        """Test bulk operations workflow"""
        
        mock_query = mock_supabase_client.from_.return_value
        
        # Mock bulk operations data
        mock_query.execute.side_effect = [
            Mock(data=[  # Get current toggles
                {'rag_feature': 'best_practice_kb', 'enabled': False},
                {'rag_feature': 'customer_insight_rag', 'enabled': False},
                {'rag_feature': 'performance_improvement_rag', 'enabled': True}
            ]),
            Mock(data=[  # Bulk update result
                {'rag_feature': 'best_practice_kb', 'enabled': True},
                {'rag_feature': 'customer_insight_rag', 'enabled': True}
            ]),
            Mock(data=[  # Get updated toggles
                {'rag_feature': 'best_practice_kb', 'enabled': True},
                {'rag_feature': 'customer_insight_rag', 'enabled': True},
                {'rag_feature': 'performance_improvement_rag', 'enabled': True}
            ])
        ]

        # Step 1: Get current toggles
        response = client.get(
            "/api/v1/organizations/org-123/rag-toggles",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 200
        current_toggles = response.json()
        assert len(current_toggles['toggles']) == 3

        # Step 2: Perform bulk update
        bulk_updates = {
            'best_practice_kb': True,
            'customer_insight_rag': True,
            'performance_improvement_rag': True  # Already enabled
        }
        
        response = client.post(
            "/api/v1/organizations/org-123/rag-toggles/bulk",
            json={
                'updates': bulk_updates,
                'reason': 'Enabling all sales features for Q4'
            },
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 200
        bulk_result = response.json()
        assert bulk_result['total_updated'] == 2

        # Step 3: Verify bulk update
        response = client.get(
            "/api/v1/organizations/org-123/rag-toggles",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 200
        updated_toggles = response.json()
        assert all(toggle['enabled'] for toggle in updated_toggles['toggles'])

    @pytest.mark.asyncio
    async def test_permission_based_access_workflow(self, client, mock_supabase_client):
        """Test permission-based access control workflow"""
        
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{'enabled': True}])

        # Test 1: System admin can access any organization
        response = client.get(
            "/api/v1/organizations/org-999/rag-toggles",
            headers={'X-User-Roles': 'system_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 200

        # Test 2: Org admin can only access their own organization
        response = client.get(
            "/api/v1/organizations/org-123/rag-toggles",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 200

        # Test 3: Org admin cannot access other organizations
        response = client.get(
            "/api/v1/organizations/org-999/rag-toggles",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 403

        # Test 4: User can only view enabled features
        response = client.get(
            "/api/v1/organizations/org-123/enabled-rag-features",
            headers={'X-User-Roles': 'user', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 200

        # Test 5: User cannot modify toggles
        response = client.put(
            "/api/v1/organizations/org-123/rag-toggles/best_practice_kb",
            json={'enabled': False},
            headers={'X-User-Roles': 'user', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery_workflow(self, client, mock_supabase_client):
        """Test error handling and recovery workflow"""
        
        mock_query = mock_supabase_client.from_.return_value

        # Test 1: Database connection error
        mock_query.execute.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/v1/rag-features")
        assert response.status_code == 500
        error_data = response.json()
        assert 'Database connection failed' in error_data['detail']

        # Test 2: Invalid feature name
        mock_query.execute.return_value = Mock(data=[])
        
        response = client.put(
            "/api/v1/organizations/org-123/rag-toggles/invalid_feature",
            json={'enabled': True},
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 404

        # Test 3: Circular dependency in organization hierarchy
        mock_query.execute.side_effect = Exception("Circular dependency detected")
        
        response = client.post(
            "/api/v1/organizations/org-123/children",
            json={'name': 'Circular Child', 'parent_organization_id': 'org-456'},
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 400

        # Test 4: Recovery after error
        mock_query.execute.side_effect = None
        mock_query.execute.return_value = Mock(data=[
            {'rag_feature': 'best_practice_kb', 'enabled': True}
        ])
        
        response = client.get(
            "/api/v1/organizations/org-123/rag-toggles",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation_workflow(self, client, mock_supabase_client):
        """Test multi-tenant isolation workflow"""
        
        mock_query = mock_supabase_client.from_.return_value
        
        # Mock tenant isolation data
        mock_query.execute.side_effect = [
            Mock(data=[  # Org A toggles
                {'rag_feature': 'best_practice_kb', 'enabled': True, 'organization_id': 'org-a'}
            ]),
            Mock(data=[  # Org B toggles
                {'rag_feature': 'best_practice_kb', 'enabled': False, 'organization_id': 'org-b'}
            ]),
            Mock(data=[  # Org A context items
                {'id': 'item-a-1', 'organization_id': 'org-a', 'rag_feature': 'best_practice_kb'}
            ]),
            Mock(data=[])  # Org B should not see Org A's items
        ]

        # Test 1: Organization A gets their toggles
        response = client.get(
            "/api/v1/organizations/org-a/rag-toggles",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-a'}
        )
        assert response.status_code == 200
        org_a_toggles = response.json()
        assert org_a_toggles['toggles'][0]['enabled'] is True

        # Test 2: Organization B gets their toggles (different state)
        response = client.get(
            "/api/v1/organizations/org-b/rag-toggles",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-b'}
        )
        assert response.status_code == 200
        org_b_toggles = response.json()
        assert org_b_toggles['toggles'][0]['enabled'] is False

        # Test 3: Organization A cannot access Organization B's data
        response = client.get(
            "/api/v1/organizations/org-b/rag-toggles",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-a'}
        )
        assert response.status_code == 403

        # Test 4: Context items are isolated
        response = client.get(
            "/api/v1/context/items",
            params={'organization_id': 'org-a'},
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-a'}
        )
        assert response.status_code == 200
        org_a_items = response.json()
        assert len(org_a_items['items']) == 1

        response = client.get(
            "/api/v1/context/items",
            params={'organization_id': 'org-b'},
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-b'}
        )
        assert response.status_code == 200
        org_b_items = response.json()
        assert len(org_b_items['items']) == 0

    @pytest.mark.asyncio
    async def test_performance_and_scalability_workflow(self, client, mock_supabase_client):
        """Test performance and scalability with large datasets"""
        
        mock_query = mock_supabase_client.from_.return_value
        
        # Mock large dataset
        large_feature_list = [
            {'rag_feature': f'feature_{i}', 'name': f'Feature {i}', 'category': 'sales', 'default_enabled': True}
            for i in range(100)
        ]
        
        mock_query.execute.return_value = Mock(data=large_feature_list)

        # Test 1: Handle large feature catalog
        response = client.get("/api/v1/rag-features")
        assert response.status_code == 200
        features = response.json()
        assert len(features) == 100

        # Test 2: Pagination works
        response = client.get("/api/v1/rag-features?limit=10&offset=0")
        assert response.status_code == 200
        paginated_features = response.json()
        assert len(paginated_features) == 10

        # Test 3: Search performance
        response = client.get("/api/v1/rag-features?search=feature_1")
        assert response.status_code == 200
        search_results = response.json()
        assert len(search_results) > 0

        # Test 4: Category filtering performance
        response = client.get("/api/v1/rag-features?category=sales")
        assert response.status_code == 200
        category_results = response.json()
        assert all(feature['category'] == 'sales' for feature in category_results)

    # ==================== SERVICE INTEGRATION TESTS ====================

    @pytest.mark.asyncio
    async def test_service_layer_integration(self, tenant_isolation_service, feature_inheritance_service, enhanced_context_manager):
        """Test integration between different service layers"""
        
        # Mock comprehensive service interactions
        with patch.object(tenant_isolation_service.supabase, 'from_') as mock_from:
            mock_query = Mock()
            mock_query.select.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.insert.return_value = mock_query
            mock_query.execute.return_value = Mock(data=[
                {'rag_feature': 'best_practice_kb', 'enabled': True}
            ])
            mock_from.return_value = mock_query

            # Test 1: TenantIsolationService -> FeatureInheritanceService
            toggles_result = await tenant_isolation_service.get_rag_feature_toggles('org-123')
            assert toggles_result['success'] is True

            # Test 2: FeatureInheritanceService -> EnhancedContextManager
            inherited_result = await feature_inheritance_service.get_inherited_features('org-123')
            assert inherited_result['success'] is True

            # Test 3: EnhancedContextManager -> TenantIsolationService
            sharing_result = await enhanced_context_manager.share_to_children(
                'parent-org', 'item-123', 'best_practice_kb', 'user-456'
            )
            assert sharing_result['success'] is True

    @pytest.mark.asyncio
    async def test_database_transaction_integration(self, client, mock_supabase_client):
        """Test database transaction integration"""
        
        mock_query = mock_supabase_client.from_.return_value
        
        # Mock transaction-like behavior
        mock_query.execute.side_effect = [
            Mock(data=[{'id': 'toggle-1'}]),  # Update toggle
            Mock(data=[{'id': 'audit-1'}]),   # Create audit log
            Mock(data=[{'id': 'notification-1'}])  # Send notification
        ]

        # Test atomic operation (toggle update with audit and notification)
        response = client.put(
            "/api/v1/organizations/org-123/rag-toggles/best_practice_kb",
            json={
                'enabled': True,
                'reason': 'Enabling for Q4 sales push',
                'create_audit': True,
                'send_notification': True
            },
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'audit_log_id' in result
        assert 'notification_sent' in result

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
