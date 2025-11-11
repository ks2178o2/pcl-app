import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from api import twilio_api


@pytest.fixture
def twilio_client():
    app = FastAPI()
    app.include_router(twilio_api.router)
    app.dependency_overrides[twilio_api.get_current_user] = lambda: {
        "id": "user-123",
        "organization_id": "org-123"
    }
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_send_sms_success(twilio_client):
    """Test successful SMS sending"""
    mock_twilio_client = Mock()
    mock_message = Mock()
    mock_message.sid = "SM123456"
    mock_message.status = "queued"
    mock_message.error_code = None
    mock_message.error_message = None
    mock_twilio_client.messages.create.return_value = mock_message
    mock_twilio_client.messages.return_value.fetch.return_value = mock_message
    
    with patch('api.twilio_api._get_twilio_client', return_value=(mock_twilio_client, "+1234567890")):
        response = twilio_client.post(
            "/api/twilio/send-sms",
            json={
                "recipientPhone": "+1234567890",
                "message": "Test message",
                "callRecordId": "call-123"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["sid"] == "SM123456"


def test_send_sms_missing_fields(twilio_client):
    """Test SMS sending with missing fields"""
    response = twilio_client.post(
        "/api/twilio/send-sms",
        json={
            "recipientPhone": "+1234567890"
            # Missing message
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_send_sms_twilio_not_configured(twilio_client):
    """Test SMS sending when Twilio is not configured"""
    with patch('api.twilio_api._get_twilio_client', side_effect=Exception("Twilio not configured")):
        response = twilio_client.post(
            "/api/twilio/send-sms",
            json={
                "recipientPhone": "+1234567890",
                "message": "Test message"
            }
        )
        
        assert response.status_code in [500, 502]


def test_test_connection_success(twilio_client):
    """Test Twilio connection test"""
    mock_twilio_client = Mock()
    
    with patch('api.twilio_api._get_twilio_client', return_value=(mock_twilio_client, "+1234567890")):
        response = twilio_client.get("/api/twilio/test-connection")
        
        assert response.status_code == 200
        assert response.json()["success"] is True


def test_debug_endpoint(twilio_client):
    """Test Twilio debug endpoint"""
    with patch.dict('os.environ', {
        'TWILIO_ACCOUNT_SID': 'AC123456',
        'TWILIO_AUTH_TOKEN': 'token123',
        'TWILIO_FROM_NUMBER': '+1234567890'
    }):
        response = twilio_client.get("/api/twilio/debug")
        
        assert response.status_code == 200
        assert response.json()["success"] is True

