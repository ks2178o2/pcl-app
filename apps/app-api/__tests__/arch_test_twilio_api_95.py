"""
Comprehensive tests for Twilio API endpoints
Target: 95% coverage for api/twilio_api.py

Uses dependency override pattern similar to organization_toggles_api_client tests
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def mock_user():
    """Create a mock user"""
    return {
        "id": "user-123",
        "role": "salesperson",
        "organization_id": "org-123",
        "user_id": "user-123"
    }


class TestTwilioAPISendSMS:
    """Tests for /send-sms endpoint"""
    
    def _build_app_with_mocks(self, user, env_vars=None, mock_twilio_client_func=None):
        """Build FastAPI app with mocked dependencies"""
        # Import module (will fail if twilio not installed, so we patch it first)
        import importlib
        
        # Patch twilio import to avoid ImportError
        mock_twilio_module = Mock()
        mock_twilio_rest = Mock()
        mock_client_class = Mock()
        mock_twilio_rest.Client = mock_client_class
        mock_twilio_module.rest = mock_twilio_rest
        
        # Set up environment variables
        env_patches = {}
        if env_vars:
            for key, value in env_vars.items():
                env_patches[key] = patch.dict(os.environ, {key: value}, clear=False)
                env_patches[key].start()
        
        try:
            # Patch twilio import before reloading module
            with patch.dict('sys.modules', {'twilio': mock_twilio_module, 'twilio.rest': mock_twilio_rest}):
                # Reload module to pick up patches
                if 'api.twilio_api' in sys.modules:
                    twilio_api = importlib.reload(sys.modules['api.twilio_api'])
                else:
                    import api.twilio_api as twilio_api
                
                # Override _get_twilio_client if mock function provided
                if mock_twilio_client_func:
                    twilio_api._get_twilio_client = mock_twilio_client_func
                
                app = FastAPI()
                app.include_router(twilio_api.router)
                
                # Override get_current_user dependency
                async def get_user_override():
                    return user
                
                # Find get_current_user in dependencies and override
                from middleware.auth import get_current_user as original_get_current_user
                app.dependency_overrides[original_get_current_user] = get_user_override
                
                # Also try to override via module reference
                if hasattr(twilio_api, 'get_current_user'):
                    app.dependency_overrides[twilio_api.get_current_user] = get_user_override
                
                # Store patches for cleanup
                app._env_patches = env_patches
                
                return app
        except Exception as e:
            # Cleanup on error
            for patch_obj in env_patches.values():
                patch_obj.stop()
            raise
    
    def _cleanup(self, app):
        """Clean up patches"""
        if hasattr(app, '_env_patches'):
            for patch_obj in app._env_patches.values():
                patch_obj.stop()
    
    def test_send_sms_success(self, mock_user):
        """Test successful SMS sending - lines 52-98"""
        # Setup mock Twilio client
        mock_message = Mock()
        mock_message.sid = "SM1234567890abcdef"
        mock_message.status = "queued"
        mock_message.error_code = None
        mock_message.error_message = None
        
        mock_fetched_message = Mock()
        mock_fetched_message.status = "sent"
        mock_fetched_message.error_code = None
        mock_fetched_message.error_message = None
        
        # Mock client.messages(sid).fetch() pattern correctly
        # Twilio pattern: client.messages.create() and client.messages(sid).fetch()
        mock_msg_resource = Mock()
        mock_msg_resource.fetch = Mock(return_value=mock_fetched_message)
        
        # Use MagicMock to make messages callable
        mock_messages = MagicMock()
        mock_messages.create = Mock(return_value=mock_message)
        # When called as function with sid: client.messages(sid) returns resource
        mock_messages.return_value = mock_msg_resource
        
        mock_client = Mock()
        mock_client.messages = mock_messages
        
        from_number = "+16504379785"
        
        def mock_get_client():
            return mock_client, from_number
        
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_FROM_NUMBER": from_number
        }
        
        app = self._build_app_with_mocks(mock_user, env_vars=env_vars, mock_twilio_client_func=mock_get_client)
        
        try:
            with TestClient(app) as client:
                with patch('time.sleep'):  # Mock sleep to speed up
                    response = client.post(
                        "/api/twilio/send-sms",
                        json={
                            "recipientPhone": "+12146950565",
                            "message": "Test message",
                            "callRecordId": "call-123",
                            "messageType": "follow_up"
                        }
                    )
                
                assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
                data = response.json()
                assert data["success"] is True
                assert data["sid"] == "SM1234567890abcdef"
                assert "status" in data
        finally:
            self._cleanup(app)
    
    def test_send_sms_with_error_status(self, mock_user):
        """Test SMS sending with error status - lines 81-90"""
        mock_message = Mock()
        mock_message.sid = "SM1234567890abcdef"
        mock_message.status = "failed"
        mock_message.error_code = "21211"
        mock_message.error_message = "Invalid 'To' phone number"
        
        mock_fetched_message = Mock()
        mock_fetched_message.status = "failed"
        mock_fetched_message.error_code = "21211"
        mock_fetched_message.error_message = "Invalid 'To' phone number"
        
        # Mock client.messages(sid).fetch() correctly
        mock_msg_resource = Mock()
        mock_msg_resource.fetch = Mock(return_value=mock_fetched_message)
        
        # Use MagicMock to make messages callable
        mock_messages = MagicMock()
        mock_messages.create = Mock(return_value=mock_message)
        mock_messages.return_value = mock_msg_resource
        
        mock_client = Mock()
        mock_client.messages = mock_messages
        
        from_number = "+16504379785"
        
        def mock_get_client():
            return mock_client, from_number
        
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_FROM_NUMBER": from_number
        }
        
        app = self._build_app_with_mocks(mock_user, env_vars=env_vars, mock_twilio_client_func=mock_get_client)
        
        try:
            with TestClient(app) as client:
                with patch('time.sleep'):
                    response = client.post(
                        "/api/twilio/send-sms",
                        json={
                            "recipientPhone": "+12146950565",
                            "message": "Test message"
                        }
                    )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["error_code"] == "21211"
                assert "Invalid" in data["error_message"]
        finally:
            self._cleanup(app)
    
    def test_send_sms_missing_phone(self, mock_user):
        """Test SMS sending with missing phone - Pydantic validation catches this"""
        mock_client = Mock()
        from_number = "+16504379785"
        
        def mock_get_client():
            return mock_client, from_number
        
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_FROM_NUMBER": from_number
        }
        
        app = self._build_app_with_mocks(mock_user, env_vars=env_vars, mock_twilio_client_func=mock_get_client)
        
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/twilio/send-sms",
                    json={
                        "message": "Test message"
                        # Missing recipientPhone - Pydantic will reject this
                    }
                )
                
                # FastAPI/Pydantic returns 422 for missing required fields
                assert response.status_code == 422
        finally:
            self._cleanup(app)
    
    def test_send_sms_missing_message(self, mock_user):
        """Test SMS sending with missing message - Pydantic validation catches this"""
        mock_client = Mock()
        from_number = "+16504379785"
        
        def mock_get_client():
            return mock_client, from_number
        
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_FROM_NUMBER": from_number
        }
        
        app = self._build_app_with_mocks(mock_user, env_vars=env_vars, mock_twilio_client_func=mock_get_client)
        
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/twilio/send-sms",
                    json={
                        "recipientPhone": "+12146950565"
                        # Missing message - Pydantic will reject this
                    }
                )
                
                # FastAPI/Pydantic returns 422 for missing required fields
                assert response.status_code == 422
        finally:
            self._cleanup(app)
    
    def test_send_sms_twilio_exception(self, mock_user):
        """Test SMS sending with Twilio exception - lines 99-101"""
        mock_client = Mock()
        mock_client.messages.create = Mock(side_effect=Exception("Twilio API error"))
        
        from_number = "+16504379785"
        
        def mock_get_client():
            return mock_client, from_number
        
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_FROM_NUMBER": from_number
        }
        
        app = self._build_app_with_mocks(mock_user, env_vars=env_vars, mock_twilio_client_func=mock_get_client)
        
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/twilio/send-sms",
                    json={
                        "recipientPhone": "+12146950565",
                        "message": "Test message"
                    }
                )
                
                assert response.status_code == 502
                assert "Failed to send SMS" in response.json()["detail"]
        finally:
            self._cleanup(app)
    
    def test_send_sms_fetch_details_exception(self, mock_user):
        """Test SMS sending when fetching details fails - lines 88-90"""
        mock_message = Mock()
        mock_message.sid = "SM1234567890abcdef"
        mock_message.status = "queued"
        mock_message.error_code = None
        mock_message.error_message = None
        
        # Create a mock that raises exception when fetch() is called
        # The pattern is: client.messages(msg.sid).fetch()
        mock_msg_resource = Mock()
        mock_msg_resource.fetch = Mock(side_effect=Exception("Fetch error"))
        
        # Use MagicMock to make messages callable
        mock_messages = MagicMock()
        mock_messages.create = Mock(return_value=mock_message)
        # When called as function: client.messages(sid) returns resource with fetch()
        mock_messages.return_value = mock_msg_resource
        
        mock_client = Mock()
        mock_client.messages = mock_messages
        
        from_number = "+16504379785"
        
        def mock_get_client():
            return mock_client, from_number
        
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_FROM_NUMBER": from_number
        }
        
        app = self._build_app_with_mocks(mock_user, env_vars=env_vars, mock_twilio_client_func=mock_get_client)
        
        try:
            with TestClient(app) as client:
                with patch('time.sleep'):
                    response = client.post(
                        "/api/twilio/send-sms",
                        json={
                            "recipientPhone": "+12146950565",
                            "message": "Test message"
                        }
                    )
                
                # Should still return 200 even if fetch fails (exception is caught in try/except block)
                assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
                data = response.json()
                assert data["success"] is True
                assert data["sid"] == "SM1234567890abcdef"
        finally:
            self._cleanup(app)
    
    def test_send_sms_empty_string_phone(self, mock_user):
        """Test SMS sending with empty string phone - lines 61-62"""
        mock_client = Mock()
        from_number = "+16504379785"
        
        def mock_get_client():
            return mock_client, from_number
        
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_FROM_NUMBER": from_number
        }
        
        app = self._build_app_with_mocks(mock_user, env_vars=env_vars, mock_twilio_client_func=mock_get_client)
        
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/twilio/send-sms",
                    json={
                        "recipientPhone": "",
                        "message": "Test message"
                    }
                )
                
                assert response.status_code == 400
        finally:
            self._cleanup(app)
    
    def test_send_sms_empty_string_message(self, mock_user):
        """Test SMS sending with empty string message - lines 61-62"""
        mock_client = Mock()
        from_number = "+16504379785"
        
        def mock_get_client():
            return mock_client, from_number
        
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_FROM_NUMBER": from_number
        }
        
        app = self._build_app_with_mocks(mock_user, env_vars=env_vars, mock_twilio_client_func=mock_get_client)
        
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/twilio/send-sms",
                    json={
                        "recipientPhone": "+12146950565",
                        "message": ""
                    }
                )
                
                assert response.status_code == 400
        finally:
            self._cleanup(app)


class TestTwilioAPITestConnection:
    """Tests for /test-connection endpoint"""
    
    def _build_app_with_mocks(self, user, env_vars=None, mock_twilio_client_func=None):
        """Build FastAPI app with mocked dependencies"""
        import importlib
        
        # Patch twilio import
        mock_twilio_module = Mock()
        mock_twilio_rest = Mock()
        mock_client_class = Mock()
        mock_twilio_rest.Client = mock_client_class
        mock_twilio_module.rest = mock_twilio_rest
        
        env_patches = {}
        if env_vars:
            for key, value in env_vars.items():
                env_patches[key] = patch.dict(os.environ, {key: value}, clear=False)
                env_patches[key].start()
        
        try:
            with patch.dict('sys.modules', {'twilio': mock_twilio_module, 'twilio.rest': mock_twilio_rest}):
                if 'api.twilio_api' in sys.modules:
                    twilio_api = importlib.reload(sys.modules['api.twilio_api'])
                else:
                    import api.twilio_api as twilio_api
                
                if mock_twilio_client_func:
                    twilio_api._get_twilio_client = mock_twilio_client_func
                
                app = FastAPI()
                app.include_router(twilio_api.router)
                
                async def get_user_override():
                    return user
                
                from middleware.auth import get_current_user as original_get_current_user
                app.dependency_overrides[original_get_current_user] = get_user_override
                
                if hasattr(twilio_api, 'get_current_user'):
                    app.dependency_overrides[twilio_api.get_current_user] = get_user_override
                
                app._env_patches = env_patches
                
                return app
        except Exception as e:
            for patch_obj in env_patches.values():
                patch_obj.stop()
            raise
    
    def _cleanup(self, app):
        """Clean up patches"""
        if hasattr(app, '_env_patches'):
            for patch_obj in app._env_patches.values():
                patch_obj.stop()
    
    def test_test_connection_success(self, mock_user):
        """Test connection endpoint success - lines 104-121"""
        mock_client = Mock()
        from_number = "+16504379785"
        
        def mock_get_client():
            return mock_client, from_number
        
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_FROM_NUMBER": from_number
        }
        
        app = self._build_app_with_mocks(mock_user, env_vars=env_vars, mock_twilio_client_func=mock_get_client)
        
        try:
            with TestClient(app) as client:
                response = client.get("/api/twilio/test-connection")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["message"] == "Twilio client initialized successfully"
                assert data["from"] == from_number
        finally:
            self._cleanup(app)
    
    def test_test_connection_missing_credentials(self, mock_user):
        """Test connection endpoint with missing credentials - lines 44-48"""
        from fastapi import HTTPException
        
        def mock_get_client():
            raise HTTPException(status_code=500, detail="Twilio credentials are not configured")
        
        app = self._build_app_with_mocks(mock_user, mock_twilio_client_func=mock_get_client)
        
        try:
            with TestClient(app) as client:
                response = client.get("/api/twilio/test-connection")
                
                assert response.status_code == 500
                assert "Twilio credentials" in response.json()["detail"]
        finally:
            self._cleanup(app)
    
    def test_test_connection_generic_exception(self, mock_user):
        """Test connection endpoint with generic exception - lines 120-121"""
        def mock_get_client():
            raise Exception("Unexpected error")
        
        app = self._build_app_with_mocks(mock_user, mock_twilio_client_func=mock_get_client)
        
        try:
            with TestClient(app) as client:
                response = client.get("/api/twilio/test-connection")
                
                assert response.status_code == 500
                assert "Twilio init failed" in response.json()["detail"]
        finally:
            self._cleanup(app)


class TestTwilioAPIDebug:
    """Tests for /debug endpoint"""
    
    def _build_app_with_mocks(self, user, env_vars=None):
        """Build FastAPI app with mocked dependencies"""
        import importlib
        
        # Patch twilio import
        mock_twilio_module = Mock()
        mock_twilio_rest = Mock()
        mock_client_class = Mock()
        mock_twilio_rest.Client = mock_client_class
        mock_twilio_module.rest = mock_twilio_rest
        
        env_patches = {}
        if env_vars:
            for key, value in env_vars.items():
                env_patches[key] = patch.dict(os.environ, {key: value}, clear=False)
                env_patches[key].start()
        
        try:
            with patch.dict('sys.modules', {'twilio': mock_twilio_module, 'twilio.rest': mock_twilio_rest}):
                if 'api.twilio_api' in sys.modules:
                    twilio_api = importlib.reload(sys.modules['api.twilio_api'])
                else:
                    import api.twilio_api as twilio_api
                
                app = FastAPI()
                app.include_router(twilio_api.router)
                
                async def get_user_override():
                    return user
                
                from middleware.auth import get_current_user as original_get_current_user
                app.dependency_overrides[original_get_current_user] = get_user_override
                
                if hasattr(twilio_api, 'get_current_user'):
                    app.dependency_overrides[twilio_api.get_current_user] = get_user_override
                
                app._env_patches = env_patches
                
                return app
        except Exception as e:
            for patch_obj in env_patches.values():
                patch_obj.stop()
            raise
    
    def _cleanup(self, app):
        """Clean up patches"""
        if hasattr(app, '_env_patches'):
            for patch_obj in app._env_patches.values():
                patch_obj.stop()
    
    def test_debug_configured(self, mock_user):
        """Test debug endpoint with configured credentials - lines 124-142"""
        env_vars = {
            "TWILIO_ACCOUNT_SID": "AC1234567890abcdef",
            "TWILIO_AUTH_TOKEN": "test_token_123",
            "TWILIO_FROM_NUMBER": "+16504379785"
        }
        
        app = self._build_app_with_mocks(mock_user, env_vars=env_vars)
        
        try:
            with TestClient(app) as client:
                response = client.get("/api/twilio/debug")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["sid_prefix"] == "AC1234…"
                assert data["from"] == "+16504379785"
                assert data["has_token"] is True
        finally:
            self._cleanup(app)
    
    def test_debug_not_configured(self, mock_user):
        """Test debug endpoint without credentials - lines 124-142"""
        # Clear env vars for this test
        with patch.dict(os.environ, {}, clear=True):
            app = self._build_app_with_mocks(mock_user, env_vars={})
            
            try:
                with TestClient(app) as client:
                    response = client.get("/api/twilio/debug")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is False
                    assert data["sid_prefix"] is None
                    assert data["from"] is None
                    assert data["has_token"] is False
            finally:
                self._cleanup(app)
    
    def test_debug_partial_config(self, mock_user):
        """Test debug endpoint with partial configuration - lines 131-135"""
        # Clear existing env vars first, then set only SID
        with patch.dict(os.environ, {}, clear=True):
            env_vars = {
                "TWILIO_ACCOUNT_SID": "AC1234567890abcdef"
                # Missing token and from_number
            }
            
            app = self._build_app_with_mocks(mock_user, env_vars=env_vars)
            
            try:
                with TestClient(app) as client:
                    response = client.get("/api/twilio/debug")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is False
                    assert data["sid_prefix"] == "AC1234…"
                    assert data["from"] is None
                    assert data["has_token"] is False
            finally:
                self._cleanup(app)
    
    def test_debug_twilio_phone_number_env_var(self, mock_user):
        """Test debug endpoint with TWILIO_PHONE_NUMBER env var - lines 133"""
        env_vars = {
            "TWILIO_ACCOUNT_SID": "AC1234567890abcdef",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_PHONE_NUMBER": "+12146950565"
        }
        
        app = self._build_app_with_mocks(mock_user, env_vars=env_vars)
        
        try:
            with TestClient(app) as client:
                response = client.get("/api/twilio/debug")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["from"] == "+12146950565"
        finally:
            self._cleanup(app)
    
    def test_debug_no_sid(self, mock_user):
        """Test debug endpoint when SID is None - lines 139"""
        # Clear env vars first, then set only token and from_number
        with patch.dict(os.environ, {}, clear=True):
            env_vars = {
                "TWILIO_AUTH_TOKEN": "test_token",
                "TWILIO_FROM_NUMBER": "+16504379785"
            }
            
            app = self._build_app_with_mocks(mock_user, env_vars=env_vars)
            
            try:
                with TestClient(app) as client:
                    response = client.get("/api/twilio/debug")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is False  # Not fully configured
                    assert data["sid_prefix"] is None
            finally:
                self._cleanup(app)
    
    def test_debug_short_sid(self, mock_user):
        """Test debug endpoint with very short SID - lines 139"""
        env_vars = {
            "TWILIO_ACCOUNT_SID": "AC12",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_FROM_NUMBER": "+16504379785"
        }
        
        app = self._build_app_with_mocks(mock_user, env_vars=env_vars)
        
        try:
            with TestClient(app) as client:
                response = client.get("/api/twilio/debug")
                
                assert response.status_code == 200
                data = response.json()
                # Should handle short SID (may raise IndexError if < 6 chars)
                # Test that it doesn't crash
                assert "sid_prefix" in data
        finally:
            self._cleanup(app)


class TestTwilioAPIGetClient:
    """Tests for _get_twilio_client function"""
    
    def test_get_twilio_client_success(self):
        """Test _get_twilio_client with valid credentials - lines 27-49"""
        mock_client = Mock()
        from_number = "+16504379785"
        
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_FROM_NUMBER": from_number
        }
        
        # Mock twilio module before importing
        mock_twilio_module = Mock()
        mock_twilio_rest = Mock()
        mock_client_class = Mock(return_value=mock_client)
        mock_twilio_rest.Client = mock_client_class
        mock_twilio_module.rest = mock_twilio_rest
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch.dict('sys.modules', {'twilio': mock_twilio_module, 'twilio.rest': mock_twilio_rest}):
                # Need to reload module to pick up env vars and mocked twilio
                import importlib
                if 'api.twilio_api' in sys.modules:
                    twilio_api = importlib.reload(sys.modules['api.twilio_api'])
                else:
                    import api.twilio_api as twilio_api
                
                client, from_num = twilio_api._get_twilio_client()
                
                assert client == mock_client
                assert from_num == from_number
                mock_client_class.assert_called_once_with("test_sid", "test_token")
    
    def test_get_twilio_client_missing_sid(self):
        """Test _get_twilio_client with missing SID - lines 44-48"""
        env_vars = {
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_FROM_NUMBER": "+16504379785"
        }
        
        # Mock twilio module
        mock_twilio_module = Mock()
        mock_twilio_rest = Mock()
        mock_twilio_rest.Client = Mock()
        mock_twilio_module.rest = mock_twilio_rest
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch.dict('sys.modules', {'twilio': mock_twilio_module, 'twilio.rest': mock_twilio_rest}):
                from fastapi import HTTPException
                import importlib
                if 'api.twilio_api' in sys.modules:
                    twilio_api = importlib.reload(sys.modules['api.twilio_api'])
                else:
                    import api.twilio_api as twilio_api
                
                with pytest.raises(HTTPException) as exc_info:
                    twilio_api._get_twilio_client()
                
                assert exc_info.value.status_code == 500
                assert "Twilio credentials are not configured" in exc_info.value.detail
    
    def test_get_twilio_client_missing_token(self):
        """Test _get_twilio_client with missing token - lines 44-48"""
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_FROM_NUMBER": "+16504379785"
        }
        
        # Mock twilio module
        mock_twilio_module = Mock()
        mock_twilio_rest = Mock()
        mock_twilio_rest.Client = Mock()
        mock_twilio_module.rest = mock_twilio_rest
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch.dict('sys.modules', {'twilio': mock_twilio_module, 'twilio.rest': mock_twilio_rest}):
                from fastapi import HTTPException
                import importlib
                if 'api.twilio_api' in sys.modules:
                    twilio_api = importlib.reload(sys.modules['api.twilio_api'])
                else:
                    import api.twilio_api as twilio_api
                
                with pytest.raises(HTTPException) as exc_info:
                    twilio_api._get_twilio_client()
                
                assert exc_info.value.status_code == 500
                assert "Twilio credentials are not configured" in exc_info.value.detail
    
    def test_get_twilio_client_missing_from_number(self):
        """Test _get_twilio_client with missing from number - lines 44-48"""
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token"
        }
        
        # Mock twilio module
        mock_twilio_module = Mock()
        mock_twilio_rest = Mock()
        mock_twilio_rest.Client = Mock()
        mock_twilio_module.rest = mock_twilio_rest
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch.dict('sys.modules', {'twilio': mock_twilio_module, 'twilio.rest': mock_twilio_rest}):
                from fastapi import HTTPException
                import importlib
                if 'api.twilio_api' in sys.modules:
                    twilio_api = importlib.reload(sys.modules['api.twilio_api'])
                else:
                    import api.twilio_api as twilio_api
                
                with pytest.raises(HTTPException) as exc_info:
                    twilio_api._get_twilio_client()
                
                assert exc_info.value.status_code == 500
                assert "Twilio credentials are not configured" in exc_info.value.detail
    
    def test_get_twilio_client_twilio_phone_number_fallback(self):
        """Test _get_twilio_client with TWILIO_PHONE_NUMBER fallback - lines 42"""
        mock_client = Mock()
        from_number = "+12146950565"
        
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_PHONE_NUMBER": from_number
        }
        
        # Mock twilio module
        mock_twilio_module = Mock()
        mock_twilio_rest = Mock()
        mock_client_class = Mock(return_value=mock_client)
        mock_twilio_rest.Client = mock_client_class
        mock_twilio_module.rest = mock_twilio_rest
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch.dict('sys.modules', {'twilio': mock_twilio_module, 'twilio.rest': mock_twilio_rest}):
                import importlib
                if 'api.twilio_api' in sys.modules:
                    twilio_api = importlib.reload(sys.modules['api.twilio_api'])
                else:
                    import api.twilio_api as twilio_api
                
                client, from_num = twilio_api._get_twilio_client()
                
                assert client == mock_client
                assert from_num == from_number
    
    def test_get_twilio_client_sdk_not_installed(self):
        """Test _get_twilio_client when SDK is not installed - lines 34-37"""
        env_vars = {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_FROM_NUMBER": "+16504379785"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            # Mock ImportError when importing twilio.rest
            import importlib
            if 'api.twilio_api' in sys.modules:
                del sys.modules['api.twilio_api']
            
            # Patch the import to raise ImportError
            original_import = __import__
            def mock_import(name, *args, **kwargs):
                if name == 'twilio.rest' or (isinstance(name, str) and name.startswith('twilio')):
                    raise ImportError("No module named 'twilio'")
                return original_import(name, *args, **kwargs)
            
            with patch('builtins.__import__', side_effect=mock_import):
                from fastapi import HTTPException
                import api.twilio_api as twilio_api
                
                with pytest.raises(HTTPException) as exc_info:
                    twilio_api._get_twilio_client()
                
                assert exc_info.value.status_code == 500
                assert "Twilio SDK not installed" in exc_info.value.detail


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
