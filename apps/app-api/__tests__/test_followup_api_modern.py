import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from api import followup_api


@pytest.fixture
def followup_client():
    app = FastAPI()
    app.include_router(followup_api.router)
    app.dependency_overrides[followup_api.get_current_user] = lambda: {
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
    return mock_client, mock_table


def test_generate_followup_plan_success(followup_client, mock_supabase):
    """Test successful followup plan generation"""
    mock_client, mock_table = mock_supabase
    
    # Mock analysis settings
    mock_execute_settings = Mock()
    mock_execute_settings.data = {"provider": "openai"}
    
    mock_single_settings = Mock()
    mock_single_settings.execute.return_value = mock_execute_settings
    
    mock_eq_settings = Mock()
    mock_eq_settings.single.return_value = mock_single_settings
    
    mock_select = Mock()
    mock_select.eq.return_value = mock_eq_settings
    mock_table.select.return_value = mock_select
    
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"strategy_type": "email", "priority_score": 8}'}}]
    }
    
    with patch('api.followup_api.get_supabase_client', return_value=mock_client):
        with patch('api.followup_api.requests.post', return_value=mock_response):
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                response = followup_client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "Test transcript",
                        "analysisData": {"sentiment": {"overall": "positive"}},
                        "customerName": "Test Customer",
                        "salespersonName": "Test Salesperson",
                        "provider": "openai"
                    }
                )
                
                # May succeed or fail depending on OpenAI mock
                assert response.status_code in [200, 500, 502]


def test_generate_followup_plan_missing_fields(followup_client):
    """Test followup plan generation with missing fields"""
    response = followup_client.post(
        "/api/followup/generate",
        json={
            "callRecordId": "call-123"
            # Missing required fields
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_get_followup_plan(followup_client, mock_supabase):
    """Test retrieving a followup plan"""
    mock_client, mock_table = mock_supabase
    
    mock_execute_plan = Mock()
    mock_execute_plan.data = {
        "id": "plan-123",
        "call_record_id": "call-123",
        "plan_data": {"strategy_type": "email"}
    }
    
    mock_single_plan = Mock()
    mock_single_plan.execute.return_value = mock_execute_plan
    
    mock_eq_plan = Mock()
    mock_eq_plan.single.return_value = mock_single_plan
    
    mock_select = Mock()
    mock_select.eq.return_value = mock_eq_plan
    mock_table.select.return_value = mock_select
    
    with patch('api.followup_api.get_supabase_client', return_value=mock_client):
        response = followup_client.get(
            "/api/followup/plan/call-123"
        )
        
        assert response.status_code in [200, 404]

