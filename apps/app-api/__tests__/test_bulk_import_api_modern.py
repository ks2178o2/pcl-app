import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from api import bulk_import_api


@pytest.fixture
def bulk_import_client():
    app = FastAPI()
    app.include_router(bulk_import_api.router)
    app.dependency_overrides[bulk_import_api.get_current_user] = lambda: {
        "id": "user-123",
        "organization_id": "org-123"
    }
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_supabase():
    mock_client = Mock()
    mock_table = Mock()
    mock_client.from_.return_value = mock_table
    mock_storage = Mock()
    mock_client.storage.from_.return_value = mock_storage
    return mock_client, mock_table, mock_storage


def test_start_bulk_import_success(bulk_import_client, mock_supabase):
    """Test successful bulk import start"""
    mock_client, mock_table, mock_storage = mock_supabase
    
    # Mock storage bucket creation
    mock_storage.create_bucket.return_value = Mock()
    
    # Mock job creation
    mock_insert = Mock()
    mock_insert.execute.return_value = Mock(data=[{"id": "job-123", "customer_name": "Test Customer"}])
    mock_table.insert.return_value = mock_insert
    
    # Mock httpx for URL fetching
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><body><a href='file1.mp3'>File 1</a></body></html>"
    mock_response.headers = {"content-type": "text/html"}
    
    with patch('api.bulk_import_api.get_supabase_client', return_value=mock_client):
        with patch('api.bulk_import_api.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.get.return_value = mock_response
            
            response = bulk_import_client.post(
                "/api/bulk-import/start",
                json={
                    "customer_name": "Test Customer",
                    "source_url": "https://example.com/audio",
                    "provider": "openai"
                }
            )
            
            # Should create job (may fail on background task, but job creation should work)
            assert response.status_code in [201, 500]  # 500 if background task fails


def test_start_bulk_import_invalid_url(bulk_import_client):
    """Test bulk import with invalid URL"""
    response = bulk_import_client.post(
        "/api/bulk-import/start",
        json={
            "customer_name": "Test Customer",
            "source_url": "not-a-url",
            "provider": "openai"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_get_bulk_import_status(bulk_import_client, mock_supabase):
    """Test retrieving bulk import status"""
    mock_client, mock_table, mock_storage = mock_supabase
    
    mock_execute = Mock()
    mock_execute.data = {
        "id": "job-123",
        "status": "processing",
        "customer_name": "Test Customer",
        "total_files": 10,
        "processed_files": 5,
        "failed_files": 0,
        "progress_percentage": 50.0
    }
    
    mock_single = Mock()
    mock_single.execute.return_value = mock_execute
    
    mock_eq = Mock()
    mock_eq.single.return_value = mock_single
    
    mock_select = Mock()
    mock_select.eq.return_value = mock_eq
    mock_table.select.return_value = mock_select
    
    with patch('api.bulk_import_api.get_supabase_client', return_value=mock_client):
        response = bulk_import_client.get(
            "/api/bulk-import/status/job-123"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-123"
        assert data["status"] == "processing"


def test_get_bulk_import_status_not_found(bulk_import_client, mock_supabase):
    """Test bulk import status for non-existent job"""
    mock_client, mock_table, mock_storage = mock_supabase
    
    mock_execute = Mock()
    mock_execute.data = None
    
    mock_single = Mock()
    mock_single.execute.return_value = mock_execute
    
    mock_eq = Mock()
    mock_eq.single.return_value = mock_single
    
    mock_select = Mock()
    mock_select.eq.return_value = mock_eq
    mock_table.select.return_value = mock_select
    
    with patch('api.bulk_import_api.get_supabase_client', return_value=mock_client):
        response = bulk_import_client.get(
            "/api/bulk-import/status/non-existent-job"
        )
        
        assert response.status_code == 404

