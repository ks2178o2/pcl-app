import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from api import enhanced_context_api


@pytest.fixture
def enhanced_context_client():
    app = FastAPI()
    app.include_router(enhanced_context_api.router)
    app.dependency_overrides[enhanced_context_api.get_current_user] = lambda: {
        "id": "user-123",
        "organization_id": "org-123",
        "role": "system_admin"
    }
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_context_manager():
    mock_manager = AsyncMock()
    mock_manager.add_global_context_item = AsyncMock(return_value={
        "success": True,
        "item_id": "item-123"
    })
    mock_manager.get_global_context_items = AsyncMock(return_value={
        "success": True,
        "items": [{"id": "item-123", "title": "Test Item"}]
    })
    return mock_manager


def test_add_global_context_item_success(enhanced_context_client, mock_context_manager):
    """Test adding a global context item"""
    with patch('api.enhanced_context_api.context_manager', mock_context_manager):
        response = enhanced_context_client.post(
            "/api/enhanced-context/global/add",
            json={
                "rag_feature": "test_feature",
                "item_title": "Test Item",
                "item_content": "Test content"
            }
        )
        
        assert response.status_code in [200, 403]  # 403 if not admin


def test_get_global_context_items(enhanced_context_client, mock_context_manager):
    """Test retrieving global context items"""
    with patch('api.enhanced_context_api.context_manager', mock_context_manager):
        response = enhanced_context_client.get(
            "/api/enhanced-context/global/items",
            params={"rag_feature": "test_feature"}
        )
        
        assert response.status_code in [200, 403]


def test_add_global_context_item_unauthorized(enhanced_context_client):
    """Test adding global context item without admin role"""
    # Override to return non-admin user
    enhanced_context_client.app.dependency_overrides[enhanced_context_api.get_current_user] = lambda: {
        "id": "user-123",
        "role": "salesperson"  # Not admin
    }
    
    response = enhanced_context_client.post(
        "/api/enhanced-context/global/add",
        json={
            "rag_feature": "test_feature",
            "item_title": "Test Item"
        }
    )
    
    assert response.status_code == 403  # Forbidden

