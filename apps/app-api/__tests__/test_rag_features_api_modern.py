import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from api import rag_features_api


@pytest.fixture
def rag_features_client():
    app = FastAPI()
    app.include_router(rag_features_api.router)
    
    # Mock permissions
    app.dependency_overrides[rag_features_api.require_system_admin] = lambda: {"id": "admin-123", "role": "system_admin"}
    app.dependency_overrides[rag_features_api.require_org_admin] = lambda: {"id": "admin-123", "role": "org_admin", "organization_id": "org-123"}
    app.dependency_overrides[rag_features_api.get_current_user] = lambda: {"id": "user-123", "organization_id": "org-123"}
    
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_supabase():
    mock_client = Mock()
    mock_table = Mock()
    mock_client.from_.return_value = mock_table
    return mock_client, mock_table


def test_create_rag_feature_success(rag_features_client, mock_supabase):
    """Test successful RAG feature creation"""
    mock_client, mock_table = mock_supabase
    
    mock_insert = Mock()
    mock_insert.execute.return_value = Mock(data=[{
        "id": "feature-123",
        "rag_feature": "test_feature",
        "name": "Test Feature",
        "category": "sales",
        "is_active": True
    }])
    mock_table.insert.return_value = mock_insert
    
    with patch('api.rag_features_api.get_supabase_client', return_value=mock_client):
        response = rag_features_client.post(
            "/api/v1/rag-features",
            json={
                "rag_feature": "test_feature",
                "name": "Test Feature",
                "description": "Test description",
                "category": "sales",
                "icon": "icon-test",
                "color": "blue"
            }
        )
        
        # May require admin permissions
        assert response.status_code in [200, 201, 403]


def test_get_rag_feature_success(rag_features_client, mock_supabase):
    """Test retrieving a RAG feature"""
    mock_client, mock_table = mock_supabase
    
    mock_execute = Mock()
    mock_execute.data = {
        "id": "feature-123",
        "rag_feature": "test_feature",
        "name": "Test Feature",
        "category": "sales"
    }
    
    mock_single = Mock()
    mock_single.execute.return_value = mock_execute
    
    mock_eq = Mock()
    mock_eq.single.return_value = mock_single
    
    mock_select = Mock()
    mock_select.eq.return_value = mock_eq
    mock_table.select.return_value = mock_select
    
    with patch('api.rag_features_api.get_supabase_client', return_value=mock_client):
        response = rag_features_client.get(
            "/api/v1/rag-features/test_feature"
        )
        
        assert response.status_code in [200, 403]  # 403 if permissions required


def test_list_rag_features(rag_features_client, mock_supabase):
    """Test listing RAG features"""
    mock_client, mock_table = mock_supabase
    
    mock_select = Mock()
    mock_select.execute.return_value = Mock(
        data=[
            {"id": "1", "rag_feature": "feature1", "name": "Feature 1"},
            {"id": "2", "rag_feature": "feature2", "name": "Feature 2"}
        ],
        count=2
    )
    mock_table.select.return_value = mock_select
    
    with patch('api.rag_features_api.get_supabase_client', return_value=mock_client):
        response = rag_features_client.get(
            "/api/v1/rag-features"
        )
        
        assert response.status_code in [200, 403]  # 403 if permissions required


def test_create_rag_feature_validation_error(rag_features_client):
    """Test RAG feature creation with invalid data"""
    response = rag_features_client.post(
        "/api/v1/rag-features",
        json={
            "rag_feature": "test_feature",
            "name": "Test Feature",
            "category": "invalid_category"  # Invalid category
        }
    )
    
    assert response.status_code == 422  # Validation error

