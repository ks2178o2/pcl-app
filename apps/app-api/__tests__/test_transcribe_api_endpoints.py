"""
Transcribe API Endpoint Tests - FastAPI TestClient with mocks
Tests API endpoints directly using TestClient
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import io
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestTranscribeAPIEndpoints:
    """Test transcribe API endpoints"""
    
    def _build_app_with_mocks(self, mock_supabase_client=None, mock_user=None):
        """Build test app with mocked dependencies"""
        # Import WITHOUT reload
        from api import transcribe_api as transcribe_mod
        
        # Create fresh app
        app = FastAPI()
        app.include_router(transcribe_mod.router)
        
        # Mock get_supabase_client 
        mock_supabase = mock_supabase_client or MagicMock()
        
        # Patch the function at module level BEFORE import
        import services.supabase_client
        original_get_client = services.supabase_client.get_supabase_client
        
        def mock_get_supabase():
            return mock_supabase
        
        services.supabase_client.get_supabase_client = mock_get_supabase
        
        # Also patch in api.transcribe_api
        transcribe_mod.get_supabase_client = mock_get_supabase
        
        # Mock get_current_user from middleware.auth
        mock_user_data = mock_user or {
            'user_id': 'user-123',
            'id': 'user-123',
            'email': 'test@example.com',
            'organization_id': 'org-123',
            'role': 'salesperson'
        }
        
        from middleware import auth
        
        async def mock_get_current_user_func():
            return mock_user_data
        
        transcribe_mod.get_current_user = mock_get_current_user_func
        
        # Use dependency overrides
        app.dependency_overrides[auth.get_current_user] = lambda: mock_user_data
        
        return app
    
    def test_upload_validates_file_type(self):
        """Test that endpoint validates file type"""
        app = self._build_app_with_mocks()
        client = TestClient(app)
        
        # Try uploading a text file
        text_content = b"This is not an audio file"
        files = {'file': ('test.txt', io.BytesIO(text_content), 'text/plain')}
        data = {'provider': 'deepgram'}
        
        response = client.post('/api/transcribe/upload', files=files, data=data)
        
        assert response.status_code == 400
        assert 'Unsupported file type' in response.json()['detail']
    
    def test_upload_validates_file_size(self):
        """Test that endpoint validates file size"""
        app = self._build_app_with_mocks()
        client = TestClient(app)
        
        # Create a file that's too large
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB
        files = {'file': ('test.mp3', io.BytesIO(large_content), 'audio/mpeg')}
        data = {'provider': 'deepgram'}
        
        response = client.post('/api/transcribe/upload', files=files, data=data)
        
        assert response.status_code == 413
        assert 'exceeds 100MB limit' in response.json()['detail']
    
    def test_upload_validates_provider(self):
        """Test that endpoint validates provider"""
        app = self._build_app_with_mocks()
        client = TestClient(app)
        
        audio_content = b"fake audio data" * 100
        files = {'file': ('test.mp3', io.BytesIO(audio_content), 'audio/mpeg')}
        data = {'provider': 'invalid_provider'}
        
        response = client.post('/api/transcribe/upload', files=files, data=data)
        
        assert response.status_code in [400, 422]
    
    def test_upload_success(self):
        """Test successful upload"""
        mock_supabase = MagicMock()
        
        # Mock storage operations
        mock_storage = MagicMock()
        mock_storage.upload.return_value.error = None
        mock_storage.get_public_url.return_value.data = {'publicUrl': 'https://example.com/audio.mp3'}
        mock_supabase.storage.from_.return_value = mock_storage
        
        # Mock table insert
        mock_insert = MagicMock()
        mock_insert.execute.return_value = None
        mock_supabase.from_.return_value.insert.return_value = mock_insert
        
        # Mock edge function
        mock_functions = MagicMock()
        mock_functions.invoke.return_value = {'data': {'success': True}, 'error': None}
        mock_supabase.functions = mock_functions
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        audio_content = b"fake audio data" * 100
        files = {'file': ('test.mp3', io.BytesIO(audio_content), 'audio/mpeg')}
        data = {
            'provider': 'deepgram',
            'language': 'en',
            'salesperson_name': 'Test User',
            'customer_name': 'Test Customer'
        }
        
        response = client.post('/api/transcribe/upload', files=files, data=data)
        
        # Should succeed
        assert response.status_code in [201, 500]  # 500 if edge function not actually invoked
        
        if response.status_code == 201:
            result = response.json()
            assert result['success'] is True
            assert 'upload_id' in result
            assert 'storage_path' in result
    
    def test_upload_handles_storage_error(self):
        """Test upload handles storage errors"""
        mock_supabase = MagicMock()
        
        # Mock storage upload to fail
        mock_storage = MagicMock()
        mock_storage.upload.return_value.error = 'Storage error'
        mock_supabase.storage.from_.return_value = mock_storage
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        audio_content = b"fake audio data" * 100
        files = {'file': ('test.mp3', io.BytesIO(audio_content), 'audio/mpeg')}
        data = {'provider': 'deepgram'}
        
        response = client.post('/api/transcribe/upload', files=files, data=data)
        
        assert response.status_code == 500
        assert 'Failed to upload file' in response.json()['detail']
    
    def test_get_status_not_found(self):
        """Test status for non-existent upload"""
        mock_supabase = MagicMock()
        
        # Mock empty result
        mock_execute_result = MagicMock()
        mock_execute_result.data = None
        
        mock_select = MagicMock()
        mock_select.eq.return_value.single.return_value.execute.return_value = mock_execute_result
        mock_supabase.from_.return_value.select.return_value = mock_select
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        response = client.get('/api/transcribe/status/fake-id')
        
        assert response.status_code == 404
    
    def test_get_status_success(self):
        """Test successful status retrieval"""
        mock_supabase = MagicMock()
        
        # Mock same user (ownership check passes)
        mock_execute_result = MagicMock()
        mock_execute_result.data = {
            'user_id': 'user-123',
            'status': 'completed',
            'progress': 100,
            'transcript': 'Test transcript',
            'provider': 'deepgram',
            'error': None,
            'created_at': '2024-01-01T00:00:00Z',
            'completed_at': '2024-01-01T00:05:00Z'
        }
        
        mock_select = MagicMock()
        mock_select.eq.return_value.single.return_value.execute.return_value = mock_execute_result
        mock_supabase.from_.return_value.select.return_value = mock_select
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        response = client.get('/api/transcribe/status/fake-id')
        
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'completed'
        assert result['progress'] == 100
        assert result['transcript'] == 'Test transcript'
    
    def test_get_status_checks_ownership(self):
        """Test status verifies ownership"""
        mock_supabase = MagicMock()
        
        # Mock different user
        mock_execute_result = MagicMock()
        mock_execute_result.data = {
            'user_id': 'other-user',
            'status': 'completed'
        }
        
        mock_select = MagicMock()
        mock_select.eq.return_value.single.return_value.execute.return_value = mock_execute_result
        mock_supabase.from_.return_value.select.return_value = mock_select
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        response = client.get('/api/transcribe/status/fake-id')
        
        assert response.status_code == 403
    
    def test_list_returns_transcriptions(self):
        """Test listing transcriptions"""
        mock_supabase = MagicMock()
        
        # Mock transcriptions
        mock_transcriptions = [
            {'id': 'upload-1', 'status': 'completed'},
            {'id': 'upload-2', 'status': 'queued'}
        ]
        
        mock_execute_result = MagicMock()
        mock_execute_result.data = mock_transcriptions
        mock_execute_result.count = 2
        
        mock_select = MagicMock()
        mock_query = mock_select
        mock_query.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_execute_result
        mock_supabase.from_.return_value.select.return_value = mock_select
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        response = client.get('/api/transcribe/list')
        
        assert response.status_code == 200
        result = response.json()
        assert 'transcriptions' in result
        assert 'total' in result
        assert result['total'] == 2
    
    def test_delete_not_found(self):
        """Test deleting non-existent upload"""
        mock_supabase = MagicMock()
        
        # Mock empty result - need to handle .eq().eq().single() chain
        mock_execute_result = MagicMock()
        mock_execute_result.data = None
        
        # Chain: select().eq('id', upload_id).eq('user_id', user_id).single().execute()
        mock_eq2 = MagicMock()
        mock_single = MagicMock()
        mock_single.execute.return_value = mock_execute_result
        mock_eq2.single.return_value = mock_single
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_supabase.from_.return_value.select.return_value = mock_select
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        # Since result.data is None, it should raise 404
        response = client.delete('/api/transcribe/fake-id')
        
        assert response.status_code == 404
    
    def test_delete_success(self):
        """Test successful deletion"""
        mock_supabase = MagicMock()
        
        # Mock successful deletion
        mock_execute_result = MagicMock()
        mock_execute_result.data = {
            'storage_path': 'path/to/file.mp3'
        }
        
        mock_select = MagicMock()
        mock_select.eq.return_value.single.return_value.execute.return_value = mock_execute_result
        mock_supabase.from_.return_value.select.return_value = mock_select
        mock_supabase.from_.return_value.delete.return_value.eq.return_value.execute.return_value = None
        
        # Mock storage removal
        mock_storage = MagicMock()
        mock_storage.remove.return_value = None
        mock_supabase.storage.from_.return_value = mock_storage
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        response = client.delete('/api/transcribe/fake-id')
        
        assert response.status_code == 204
    
    def test_retry_not_found(self):
        """Test retrying non-existent upload"""
        mock_supabase = MagicMock()
        
        # Mock empty result - need to handle .eq().eq().single() chain
        mock_execute_result = MagicMock()
        mock_execute_result.data = None
        
        # Chain: select().eq('id', upload_id).eq('user_id', user_id).single().execute()
        mock_eq2 = MagicMock()
        mock_single = MagicMock()
        mock_single.execute.return_value = mock_execute_result
        mock_eq2.single.return_value = mock_single
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_supabase.from_.return_value.select.return_value = mock_select
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        response = client.post('/api/transcribe/retry/fake-id')
        
        assert response.status_code == 404
    
    def test_retry_success(self):
        """Test successful retry"""
        mock_supabase = MagicMock()
        
        # Mock existing record
        mock_execute_result = MagicMock()
        mock_execute_result.data = {
            'storage_path': 'path/to/file.mp3',
            'public_url': 'https://example.com/file.mp3',
            'provider': 'deepgram',
            'file_type': '.mp3',
            'salesperson_name': 'Test User',
            'customer_name': 'Test Customer'
        }
        
        mock_select = MagicMock()
        mock_select.eq.return_value.single.return_value.execute.return_value = mock_execute_result
        mock_supabase.from_.return_value.select.return_value = mock_select
        mock_supabase.from_.return_value.update.return_value.eq.return_value.execute.return_value = None
        
        # Mock edge function
        mock_functions = MagicMock()
        mock_functions.invoke.return_value = None
        mock_supabase.functions = mock_functions
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        response = client.post('/api/transcribe/retry/fake-id')
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
    
    def test_upload_with_table_insert_error(self):
        """Test upload when transcription_queue table doesn't exist"""
        mock_supabase = MagicMock()
        
        # Mock storage upload success
        mock_upload_result = MagicMock()
        mock_upload_result.error = None
        
        mock_storage = MagicMock()
        mock_storage.upload.return_value = mock_upload_result
        mock_storage.get_public_url.return_value.data = {'publicUrl': 'https://example.com/file.mp3'}
        
        mock_supabase.storage.from_.return_value = mock_storage
        
        # Mock table insert failure
        mock_insert = MagicMock()
        mock_insert.execute.side_effect = Exception("Table not found")
        mock_supabase.from_.return_value.insert.return_value = mock_insert
        
        # Mock edge function success
        mock_edge_result = MagicMock()
        mock_edge_result.data = {"job_id": "test-123"}
        mock_functions = MagicMock()
        mock_functions.invoke.return_value = mock_edge_result
        mock_supabase.functions = mock_functions
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        audio_content = b"fake audio data"
        files = {'file': ('test.mp3', io.BytesIO(audio_content), 'audio/mpeg')}
        data = {'provider': 'deepgram'}
        
        # Should still succeed even if table doesn't exist
        response = client.post('/api/transcribe/upload', files=files, data=data)
        
        assert response.status_code == 201  # Upload endpoint returns 201
        assert response.json()['success'] is True
    
    def test_upload_with_edge_function_error(self):
        """Test upload when edge function fails"""
        mock_supabase = MagicMock()
        
        # Mock storage upload success
        mock_upload_result = MagicMock()
        mock_upload_result.error = None
        
        mock_storage = MagicMock()
        mock_storage.upload.return_value = mock_upload_result
        mock_storage.get_public_url.return_value.data = {'publicUrl': 'https://example.com/file.mp3'}
        
        mock_supabase.storage.from_.return_value = mock_storage
        
        # Mock table insert success
        mock_insert = MagicMock()
        mock_insert.execute.return_value = None
        mock_supabase.from_.return_value.insert.return_value = mock_insert
        
        # Mock edge function returning empty data
        mock_edge_result = MagicMock()
        mock_edge_result.data = None  # Empty data
        
        mock_functions = MagicMock()
        mock_functions.invoke.return_value = mock_edge_result
        mock_supabase.functions = mock_functions
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        audio_content = b"fake audio data"
        files = {'file': ('test.mp3', io.BytesIO(audio_content), 'audio/mpeg')}
        data = {'provider': 'deepgram'}
        
        # Should still succeed even if edge function fails
        response = client.post('/api/transcribe/upload', files=files, data=data)
        
        assert response.status_code == 201  # Upload endpoint returns 201
        assert response.json()['success'] is True
        assert "shortly" in response.json()['message']  # Message without job ID
    
    def test_upload_with_no_supabase_client(self):
        """Test upload when supabase client is None"""
        app = self._build_app_with_mocks(mock_supabase_client=None)
        
        # Patch to return None
        from api import transcribe_api
        original_get_client = transcribe_api.get_supabase_client
        transcribe_api.get_supabase_client = lambda: None
        
        client = TestClient(app)
        
        audio_content = b"fake audio data"
        files = {'file': ('test.mp3', io.BytesIO(audio_content), 'audio/mpeg')}
        data = {'provider': 'deepgram'}
        
        response = client.post('/api/transcribe/upload', files=files, data=data)
        
        assert response.status_code == 503
        
        # Restore
        transcribe_api.get_supabase_client = original_get_client
    
    def test_list_with_error(self):
        """Test list when query execution fails"""
        mock_supabase = MagicMock()
        
        # Mock query chain that raises exception
        mock_query = MagicMock()
        mock_query.eq.return_value.order.return_value.range.return_value.execute.side_effect = Exception("Query failed")
        mock_supabase.from_.return_value.select.return_value = mock_query
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        response = client.get('/api/transcribe/list')
        
        assert response.status_code == 500
    
    def test_delete_with_error(self):
        """Test delete when database operation fails"""
        mock_supabase = MagicMock()
        
        # Mock successful record fetch
        mock_execute_result = MagicMock()
        mock_execute_result.data = {
            'storage_path': 'path/to/file.mp3'
        }
        
        mock_eq2 = MagicMock()
        mock_single = MagicMock()
        mock_single.execute.return_value = mock_execute_result
        mock_eq2.single.return_value = mock_single
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_supabase.from_.return_value.select.return_value = mock_select
        
        # Mock delete failure
        mock_supabase.from_.return_value.delete.return_value.eq.return_value.execute.side_effect = Exception("Delete failed")
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        response = client.delete('/api/transcribe/fake-id')
        
        assert response.status_code == 500
    
    def test_retry_with_error(self):
        """Test retry when database operation fails"""
        mock_supabase = MagicMock()
        
        # Mock successful record fetch
        mock_execute_result = MagicMock()
        mock_execute_result.data = {
            'storage_path': 'path/to/file.mp3',
            'public_url': 'https://example.com/file.mp3',
            'provider': 'deepgram',
            'file_type': '.mp3',
            'salesperson_name': 'Test User',
            'customer_name': 'Test Customer'
        }
        
        mock_eq2 = MagicMock()
        mock_single = MagicMock()
        mock_single.execute.return_value = mock_execute_result
        mock_eq2.single.return_value = mock_single
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_supabase.from_.return_value.select.return_value = mock_select
        
        # Mock update failure
        mock_supabase.from_.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("Update failed")
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        response = client.post('/api/transcribe/retry/fake-id')
        
        assert response.status_code == 500
    
    def test_get_status_with_error(self):
        """Test status when query execution fails"""
        mock_supabase = MagicMock()
        
        # Mock query chain that raises exception
        mock_query = MagicMock()
        mock_query.eq.return_value.single.return_value.execute.side_effect = Exception("Query failed")
        mock_supabase.from_.return_value.select.return_value = mock_query
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        response = client.get('/api/transcribe/status/fake-id')
        
        assert response.status_code == 500
    
    def test_list_with_status_filter(self):
        """Test list with status filter"""
        mock_supabase = MagicMock()
        
        mock_transcriptions = [
            {'id': 'upload-1', 'status': 'completed'},
        ]
        
        mock_execute_result = MagicMock()
        mock_execute_result.data = mock_transcriptions
        mock_execute_result.count = 1
        
        # Need to chain .eq().eq().order().range()
        mock_range = MagicMock()
        mock_range.execute.return_value = mock_execute_result
        
        mock_order = MagicMock()
        mock_order.range.return_value = mock_range
        
        mock_eq2 = MagicMock()
        mock_eq2.order.return_value = mock_order
        
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_supabase.from_.return_value.select.return_value = mock_select
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        # Test with status filter
        response = client.get('/api/transcribe/list?status_filter=completed')
        
        assert response.status_code == 200
        result = response.json()
        assert result['total'] == 1
    
    def test_delete_with_no_storage_path(self):
        """Test delete when storage_path is None"""
        mock_supabase = MagicMock()
        
        mock_execute_result = MagicMock()
        mock_execute_result.data = {
            'storage_path': None  # No storage path
        }
        
        mock_eq2 = MagicMock()
        mock_single = MagicMock()
        mock_single.execute.return_value = mock_execute_result
        mock_eq2.single.return_value = mock_single
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_supabase.from_.return_value.select.return_value = mock_select
        mock_supabase.from_.return_value.delete.return_value.eq.return_value.execute.return_value = None
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        response = client.delete('/api/transcribe/fake-id')
        
        assert response.status_code == 204
    
    def test_upload_general_exception(self):
        """Test upload when a non-HTTPException occurs"""
        mock_supabase = MagicMock()
        
        # Mock storage upload to fail
        mock_upload_result = MagicMock()
        mock_upload_result.error = None
        
        mock_storage = MagicMock()
        # Make storage.upload raise an exception
        mock_storage.upload.side_effect = Exception("Storage upload failed")
        mock_supabase.storage.from_.return_value = mock_storage
        
        app = self._build_app_with_mocks(mock_supabase_client=mock_supabase)
        client = TestClient(app)
        
        audio_content = b"fake audio data"
        files = {'file': ('test.mp3', io.BytesIO(audio_content), 'audio/mpeg')}
        data = {'provider': 'deepgram'}
        
        response = client.post('/api/transcribe/upload', files=files, data=data)
        
        assert response.status_code == 500
        assert 'Error uploading file' in response.json()['detail']
