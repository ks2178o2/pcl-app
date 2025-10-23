"""
API Endpoint Tests for RAG Feature Management
Tests all API endpoints with proper authentication and error handling
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Add the parent directory to the path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.rag_features_api import router as rag_features_router
from api.organization_toggles_api import router as organization_toggles_router
from api.organization_hierarchy_api import router as organization_hierarchy_router
from middleware.permissions import UserRole

class TestRAGFeatureAPIEndpoints:
    """Test suite for RAG Feature API endpoints"""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with routers"""
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
        """Mock Supabase client"""
        mock_client = Mock()
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

    # ==================== RAG FEATURES API TESTS ====================

    @patch('api.rag_features_api.get_supabase_client')
    def test_get_all_rag_features_success(self, mock_get_client, client, mock_supabase_client):
        """Test getting all RAG features"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock RAG features data
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[
            {
                'rag_feature': 'best_practice_kb',
                'name': 'Best Practice Knowledge Base',
                'description': 'Sales best practices and proven methodologies',
                'category': 'sales',
                'default_enabled': True
            },
            {
                'rag_feature': 'customer_insight_rag',
                'name': 'Customer Intelligence',
                'description': 'Customer history, preferences, and behavior patterns',
                'category': 'sales',
                'default_enabled': True
            }
        ])
        
        response = client.get("/api/v1/rag-features")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['rag_feature'] == 'best_practice_kb'

    @patch('api.rag_features_api.get_supabase_client')
    def test_get_rag_features_by_category(self, mock_get_client, client, mock_supabase_client):
        """Test getting RAG features filtered by category"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock filtered RAG features data
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[
            {
                'rag_feature': 'best_practice_kb',
                'name': 'Best Practice Knowledge Base',
                'category': 'sales',
                'default_enabled': True
            }
        ])
        
        response = client.get("/api/v1/rag-features?category=sales")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['category'] == 'sales'

    @patch('api.rag_features_api.get_supabase_client')
    def test_create_rag_feature_success(self, mock_get_client, client, mock_supabase_client):
        """Test creating a new RAG feature"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock successful creation
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{
            'rag_feature': 'new_feature',
            'name': 'New Feature',
            'description': 'A new RAG feature',
            'category': 'sales',
            'default_enabled': True
        }])
        
        feature_data = {
            'rag_feature': 'new_feature',
            'name': 'New Feature',
            'description': 'A new RAG feature',
            'category': 'sales',
            'default_enabled': True
        }
        
        response = client.post(
            "/api/v1/rag-features",
            json=feature_data,
            headers={'X-User-Roles': 'system_admin'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['rag_feature'] == 'new_feature'

    @patch('api.rag_features_api.get_supabase_client')
    def test_create_rag_feature_unauthorized(self, mock_get_client, client, mock_supabase_client):
        """Test creating RAG feature without proper authorization"""
        mock_get_client.return_value = mock_supabase_client
        
        feature_data = {
            'rag_feature': 'new_feature',
            'name': 'New Feature',
            'category': 'sales'
        }
        
        response = client.post(
            "/api/v1/rag-features",
            json=feature_data,
            headers={'X-User-Roles': 'user'}  # Not system_admin
        )
        
        assert response.status_code == 403

    @patch('api.rag_features_api.get_supabase_client')
    def test_update_rag_feature_success(self, mock_get_client, client, mock_supabase_client):
        """Test updating a RAG feature"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock successful update
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{
            'rag_feature': 'best_practice_kb',
            'name': 'Updated Best Practice KB',
            'description': 'Updated description'
        }])
        
        update_data = {
            'name': 'Updated Best Practice KB',
            'description': 'Updated description'
        }
        
        response = client.put(
            "/api/v1/rag-features/best_practice_kb",
            json=update_data,
            headers={'X-User-Roles': 'system_admin'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Updated Best Practice KB'

    @patch('api.rag_features_api.get_supabase_client')
    def test_delete_rag_feature_success(self, mock_get_client, client, mock_supabase_client):
        """Test deleting a RAG feature"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock successful deletion
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{'rag_feature': 'old_feature'}])
        
        response = client.delete(
            "/api/v1/rag-features/old_feature",
            headers={'X-User-Roles': 'system_admin'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'RAG feature deleted successfully'

    # ==================== ORGANIZATION TOGGLES API TESTS ====================

    @patch('api.organization_toggles_api.get_supabase_client')
    def test_get_organization_rag_toggles_success(self, mock_get_client, client, mock_supabase_client):
        """Test getting organization RAG toggles"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock organization toggles data
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[
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
        ])
        
        response = client.get(
            "/api/v1/organizations/org-123/rag-toggles",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['toggles']) == 2
        assert data['toggles'][0]['rag_feature'] == 'best_practice_kb'

    @patch('api.organization_toggles_api.get_supabase_client')
    def test_update_organization_rag_toggle_success(self, mock_get_client, client, mock_supabase_client):
        """Test updating a single organization RAG toggle"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock successful update
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{
            'rag_feature': 'best_practice_kb',
            'enabled': True,
            'organization_id': 'org-123'
        }])
        
        update_data = {
            'enabled': True,
            'reason': 'Enabling for Q4 sales push'
        }
        
        response = client.put(
            "/api/v1/organizations/org-123/rag-toggles/best_practice_kb",
            json=update_data,
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'RAG feature toggle updated successfully'

    @patch('api.organization_toggles_api.get_supabase_client')
    def test_bulk_update_organization_rag_toggles_success(self, mock_get_client, client, mock_supabase_client):
        """Test bulk updating organization RAG toggles"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock successful bulk update
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[
            {'rag_feature': 'best_practice_kb', 'enabled': True},
            {'rag_feature': 'customer_insight_rag', 'enabled': False}
        ])
        
        bulk_data = {
            'updates': {
                'best_practice_kb': True,
                'customer_insight_rag': False
            },
            'reason': 'Bulk update for new quarter'
        }
        
        response = client.post(
            "/api/v1/organizations/org-123/rag-toggles/bulk",
            json=bulk_data,
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['total_updated'] == 2

    @patch('api.organization_toggles_api.get_supabase_client')
    def test_get_enabled_rag_features_success(self, mock_get_client, client, mock_supabase_client):
        """Test getting only enabled RAG features for organization"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock enabled features data
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[
            {
                'rag_feature': 'best_practice_kb',
                'name': 'Best Practice Knowledge Base',
                'enabled': True,
                'is_inherited': False
            }
        ])
        
        response = client.get(
            "/api/v1/organizations/org-123/enabled-rag-features",
            headers={'X-User-Roles': 'salesperson', 'X-Organization-Id': 'org-123'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['enabled_features']) == 1
        assert data['enabled_features'][0]['enabled'] is True

    # ==================== ORGANIZATION HIERARCHY API TESTS ====================

    @patch('api.organization_hierarchy_api.get_supabase_client')
    def test_get_organization_hierarchy_success(self, mock_get_client, client, mock_supabase_client):
        """Test getting organization hierarchy"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock hierarchy data
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[
            {
                'id': 'org-123',
                'name': 'Parent Organization',
                'parent_organization_id': None,
                'level': 0
            },
            {
                'id': 'org-456',
                'name': 'Child Organization',
                'parent_organization_id': 'org-123',
                'level': 1
            }
        ])
        
        response = client.get(
            "/api/v1/organizations/org-123/hierarchy",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['hierarchy']) == 2
        assert data['hierarchy'][0]['name'] == 'Parent Organization'

    @patch('api.organization_hierarchy_api.get_supabase_client')
    def test_create_child_organization_success(self, mock_get_client, client, mock_supabase_client):
        """Test creating a child organization"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock successful creation
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{
            'id': 'org-789',
            'name': 'New Child Organization',
            'parent_organization_id': 'org-123'
        }])
        
        child_data = {
            'name': 'New Child Organization',
            'description': 'A new child organization'
        }
        
        response = client.post(
            "/api/v1/organizations/org-123/children",
            json=child_data,
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'New Child Organization'

    @patch('api.organization_hierarchy_api.get_supabase_client')
    def test_update_organization_parent_success(self, mock_get_client, client, mock_supabase_client):
        """Test updating organization parent"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock successful update
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[{
            'id': 'org-456',
            'name': 'Child Organization',
            'parent_organization_id': 'org-789'
        }])
        
        parent_data = {
            'parent_organization_id': 'org-789'
        }
        
        response = client.patch(
            "/api/v1/organizations/org-456/parent",
            json=parent_data,
            headers={'X-User-Roles': 'system_admin', 'X-Organization-Id': 'org-456'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['parent_organization_id'] == 'org-789'

    # ==================== ERROR HANDLING TESTS ====================

    @patch('api.rag_features_api.get_supabase_client')
    def test_get_rag_features_database_error(self, mock_get_client, client, mock_supabase_client):
        """Test error handling when database fails"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock database error
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/v1/rag-features")
        
        assert response.status_code == 500
        data = response.json()
        assert 'Database connection failed' in data['detail']

    @patch('api.organization_toggles_api.get_supabase_client')
    def test_update_toggle_unauthorized_organization(self, mock_get_client, client, mock_supabase_client):
        """Test updating toggle for unauthorized organization"""
        mock_get_client.return_value = mock_supabase_client
        
        update_data = {'enabled': True}
        
        response = client.put(
            "/api/v1/organizations/org-999/rag-toggles/best_practice_kb",
            json=update_data,
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}  # Different org
        )
        
        assert response.status_code == 403

    @patch('api.organization_hierarchy_api.get_supabase_client')
    def test_create_child_circular_dependency(self, mock_get_client, client, mock_supabase_client):
        """Test preventing circular dependency in organization hierarchy"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock circular dependency detection
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = Exception("Circular dependency detected")
        
        child_data = {
            'name': 'Circular Child',
            'parent_organization_id': 'org-456'  # This would create a circle
        }
        
        response = client.post(
            "/api/v1/organizations/org-123/children",
            json=child_data,
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'Circular dependency detected' in data['detail']

    # ==================== VALIDATION TESTS ====================

    @patch('api.rag_features_api.get_supabase_client')
    def test_create_rag_feature_invalid_category(self, mock_get_client, client, mock_supabase_client):
        """Test creating RAG feature with invalid category"""
        mock_get_client.return_value = mock_supabase_client
        
        feature_data = {
            'rag_feature': 'invalid_feature',
            'name': 'Invalid Feature',
            'category': 'invalid_category'  # Invalid category
        }
        
        response = client.post(
            "/api/v1/rag-features",
            json=feature_data,
            headers={'X-User-Roles': 'system_admin'}
        )
        
        assert response.status_code == 422  # Validation error

    @patch('api.organization_toggles_api.get_supabase_client')
    def test_update_toggle_invalid_feature(self, mock_get_client, client, mock_supabase_client):
        """Test updating toggle for non-existent feature"""
        mock_get_client.return_value = mock_supabase_client
        
        # Mock feature not found
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.return_value = Mock(data=[])
        
        update_data = {'enabled': True}
        
        response = client.put(
            "/api/v1/organizations/org-123/rag-toggles/non_existent_feature",
            json=update_data,
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert 'RAG feature not found' in data['detail']

    # ==================== INTEGRATION TESTS ====================

    @patch('api.rag_features_api.get_supabase_client')
    @patch('api.organization_toggles_api.get_supabase_client')
    def test_complete_rag_feature_workflow(self, mock_toggles_client, mock_features_client, client, mock_supabase_client):
        """Test complete RAG feature management workflow"""
        mock_features_client.return_value = mock_supabase_client
        mock_toggles_client.return_value = mock_supabase_client
        
        # Mock workflow data
        mock_query = mock_supabase_client.from_.return_value
        mock_query.execute.side_effect = [
            # Get all features
            Mock(data=[
                {'rag_feature': 'best_practice_kb', 'name': 'Best Practice KB', 'category': 'sales'}
            ]),
            # Get organization toggles
            Mock(data=[
                {'rag_feature': 'best_practice_kb', 'enabled': True, 'is_inherited': False}
            ]),
            # Update toggle
            Mock(data=[{'rag_feature': 'best_practice_kb', 'enabled': False}])
        ]
        
        # Step 1: Get all features
        response = client.get("/api/v1/rag-features")
        assert response.status_code == 200
        
        # Step 2: Get organization toggles
        response = client.get(
            "/api/v1/organizations/org-123/rag-toggles",
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 200
        
        # Step 3: Update toggle
        response = client.put(
            "/api/v1/organizations/org-123/rag-toggles/best_practice_kb",
            json={'enabled': False},
            headers={'X-User-Roles': 'org_admin', 'X-Organization-Id': 'org-123'}
        )
        assert response.status_code == 200

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
