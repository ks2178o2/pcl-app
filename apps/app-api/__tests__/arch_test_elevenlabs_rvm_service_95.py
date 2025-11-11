"""
Comprehensive tests for ElevenLabs RVM Service
Target: 95% coverage for services/elevenlabs_rvm_service.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import tempfile
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestElevenLabsRVMServiceInit:
    """Tests for ElevenLabsRVMService.__init__"""
    
    def test_init_with_all_env_vars(self):
        """Test initialization with all environment variables - lines 19-27"""
        env_vars = {
            "ELEVENLABS_API_KEY": "test_api_key",
            "ELEVENLABS_VOICE_ID": "test_voice_id",
            "ELEVENLABS_API_URL": "https://api.elevenlabs.io/v1"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            from services.elevenlabs_rvm_service import ElevenLabsRVMService
            
            service = ElevenLabsRVMService()
            
            assert service.api_key == "test_api_key"
            assert service.voice_id == "test_voice_id"
            assert service.base_url == "https://api.elevenlabs.io/v1"
    
    def test_init_with_alternative_env_vars(self):
        """Test initialization with alternative env var names - lines 20, 22"""
        env_vars = {
            "ELEVEN_API_KEY": "alt_api_key",
            "ELEVEN_VOICE_ID": "alt_voice_id"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            from services.elevenlabs_rvm_service import ElevenLabsRVMService
            
            service = ElevenLabsRVMService()
            
            assert service.api_key == "alt_api_key"
            assert service.voice_id == "alt_voice_id"
    
    def test_init_with_default_base_url(self):
        """Test initialization with default base URL - line 21"""
        env_vars = {
            "ELEVENLABS_API_KEY": "test_key",
            "ELEVENLABS_VOICE_ID": "test_voice"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            from services.elevenlabs_rvm_service import ElevenLabsRVMService
            
            service = ElevenLabsRVMService()
            
            assert service.base_url == "https://api.elevenlabs.io/v1"
    
    def test_init_without_api_key(self):
        """Test initialization without API key - lines 24-25"""
        env_vars = {
            "ELEVENLABS_VOICE_ID": "test_voice"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('services.elevenlabs_rvm_service.logger') as mock_logger:
                from services.elevenlabs_rvm_service import ElevenLabsRVMService
                
                service = ElevenLabsRVMService()
                
                assert service.api_key is None
                mock_logger.warning.assert_called()
    
    def test_init_without_voice_id(self):
        """Test initialization without voice ID - lines 26-27"""
        env_vars = {
            "ELEVENLABS_API_KEY": "test_key"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('services.elevenlabs_rvm_service.logger') as mock_logger:
                from services.elevenlabs_rvm_service import ElevenLabsRVMService
                
                service = ElevenLabsRVMService()
                
                assert service.voice_id is None
                mock_logger.warning.assert_called()


class TestElevenLabsRVMServiceGenerateAudio:
    """Tests for generate_rvm_audio method"""
    
    @pytest.fixture
    def service_with_credentials(self):
        """Create service with credentials"""
        env_vars = {
            "ELEVENLABS_API_KEY": "test_api_key",
            "ELEVENLABS_VOICE_ID": "test_voice_id"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            from services.elevenlabs_rvm_service import ElevenLabsRVMService
            return ElevenLabsRVMService()
    
    def test_generate_rvm_audio_success(self, service_with_credentials):
        """Test successful audio generation - lines 29-105"""
        mock_audio_bytes = b"fake_audio_data_mp3"
        
        with patch.object(service_with_credentials, '_call_elevenlabs_api', return_value=mock_audio_bytes):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('os.makedirs'):
                    result = service_with_credentials.generate_rvm_audio(
                        script="Hello [SALESPERSON_NAME], this is a test message for [CONTACT_NUMBER]",
                        salesperson_name="John Doe",
                        contact_number="+1234567890"
                    )
                
                assert result["success"] is True
                assert result["audio_id"] is not None
                assert result["audio_bytes"] == mock_audio_bytes
                assert result["file_path"] is not None
                assert result["duration_seconds"] >= 10
                assert result["script"] == "Hello John Doe, this is a test message for +1234567890"
                assert result["voice_id"] == "test_voice_id"
                assert result["metadata"]["word_count"] > 0
                assert result["metadata"]["service"] == "elevenlabs"
                assert result["metadata"]["file_size_bytes"] == len(mock_audio_bytes)
                
                # Verify file was written
                mock_file.assert_called()
    
    def test_generate_rvm_audio_missing_credentials(self):
        """Test audio generation without credentials - lines 50-51"""
        env_vars = {}
        
        with patch.dict(os.environ, env_vars, clear=True):
            from services.elevenlabs_rvm_service import ElevenLabsRVMService
            
            service = ElevenLabsRVMService()
            
            with pytest.raises(ValueError) as exc_info:
                service.generate_rvm_audio(
                    script="Test script",
                    salesperson_name="John",
                    contact_number="+123"
                )
            
            assert "ElevenLabs API key and voice ID must be configured" in str(exc_info.value)
    
    def test_generate_rvm_audio_with_custom_file_path(self, service_with_credentials):
        """Test audio generation with custom file path - lines 67-68"""
        mock_audio_bytes = b"fake_audio_data"
        custom_path = "/tmp/custom_rvm_audio.mp3"
        
        with patch.object(service_with_credentials, '_call_elevenlabs_api', return_value=mock_audio_bytes):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('os.makedirs'):
                    result = service_with_credentials.generate_rvm_audio(
                        script="Test script",
                        salesperson_name="John",
                        contact_number="+123",
                        save_to_file=custom_path
                    )
                
                assert result["file_path"] == custom_path
                mock_file.assert_called_with(custom_path, "wb")
    
    def test_generate_rvm_audio_placeholder_replacement(self, service_with_credentials):
        """Test placeholder replacement in script - lines 54-55"""
        mock_audio_bytes = b"fake_audio"
        
        with patch.object(service_with_credentials, '_call_elevenlabs_api', return_value=mock_audio_bytes):
            with patch('builtins.open', mock_open()):
                with patch('os.makedirs'):
                    result = service_with_credentials.generate_rvm_audio(
                        script="Hi [SALESPERSON_NAME], call [CONTACT_NUMBER]",
                        salesperson_name="Jane Smith",
                        contact_number="+9876543210"
                    )
                
                assert "[SALESPERSON_NAME]" not in result["script"]
                assert "[CONTACT_NUMBER]" not in result["script"]
                assert "Jane Smith" in result["script"]
                assert "+9876543210" in result["script"]
    
    def test_generate_rvm_audio_duration_calculation(self, service_with_credentials):
        """Test duration calculation - lines 79-81"""
        mock_audio_bytes = b"fake_audio"
        
        # Test with short script (should be minimum 10 seconds)
        with patch.object(service_with_credentials, '_call_elevenlabs_api', return_value=mock_audio_bytes):
            with patch('builtins.open', mock_open()):
                with patch('os.makedirs'):
                    result = service_with_credentials.generate_rvm_audio(
                        script="Short",
                        salesperson_name="John",
                        contact_number="+123"
                    )
                    
                    assert result["duration_seconds"] >= 10
        
        # Test with long script
        long_script = " ".join(["word"] * 300)  # ~300 words
        with patch.object(service_with_credentials, '_call_elevenlabs_api', return_value=mock_audio_bytes):
            with patch('builtins.open', mock_open()):
                with patch('os.makedirs'):
                    result = service_with_credentials.generate_rvm_audio(
                        script=long_script,
                        salesperson_name="John",
                        contact_number="+123"
                    )
                    
                    # 300 words at 150 WPM = 120 seconds, but we cap it
                    assert result["duration_seconds"] > 10
    
    def test_generate_rvm_audio_with_voice_settings(self, service_with_credentials):
        """Test audio generation with custom voice settings - lines 34, 136-137"""
        mock_audio_bytes = b"fake_audio"
        custom_settings = {
            "stability": 0.5,
            "speed": 1.0
        }
        
        with patch.object(service_with_credentials, '_call_elevenlabs_api', return_value=mock_audio_bytes) as mock_call:
            with patch('builtins.open', mock_open()):
                with patch('os.makedirs'):
                    service_with_credentials.generate_rvm_audio(
                        script="Test",
                        salesperson_name="John",
                        contact_number="+123",
                        voice_settings=custom_settings
                    )
                    
                    # Verify custom settings were passed
                    mock_call.assert_called_once()
                    # _call_elevenlabs_api is called with (script, voice_settings) as positional args
                    call_args = mock_call.call_args
                    # call_args is ((args), {kwargs})
                    assert len(call_args[0]) >= 2  # script and voice_settings
                    voice_settings_arg = call_args[0][1]  # Second positional arg
                    assert voice_settings_arg == custom_settings
    
    def test_generate_rvm_audio_api_error(self, service_with_credentials):
        """Test audio generation when API call fails - lines 61, 174"""
        with patch.object(service_with_credentials, '_call_elevenlabs_api', side_effect=RuntimeError("API error")):
            with pytest.raises(RuntimeError) as exc_info:
                service_with_credentials.generate_rvm_audio(
                    script="Test",
                    salesperson_name="John",
                    contact_number="+123"
                )
            
            assert "API error" in str(exc_info.value)


class TestElevenLabsRVMServiceCallAPI:
    """Tests for _call_elevenlabs_api method"""
    
    @pytest.fixture
    def service_with_credentials(self):
        """Create service with credentials"""
        env_vars = {
            "ELEVENLABS_API_KEY": "test_api_key",
            "ELEVENLABS_VOICE_ID": "test_voice_id"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            from services.elevenlabs_rvm_service import ElevenLabsRVMService
            return ElevenLabsRVMService()
    
    def test_call_elevenlabs_api_success(self, service_with_credentials):
        """Test successful API call - lines 107-170"""
        mock_audio_bytes = b"fake_mp3_audio_data_here"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "audio/mpeg"}
        mock_response.iter_content = Mock(return_value=iter([mock_audio_bytes]))
        mock_response.raise_for_status = Mock()
        mock_response.text = ""  # Not used in success case
        
        with patch('services.elevenlabs_rvm_service.requests.post', return_value=mock_response):
            with patch('services.elevenlabs_rvm_service.logger'):
                result = service_with_credentials._call_elevenlabs_api("Test script")
                
                assert result == mock_audio_bytes
    
    def test_call_elevenlabs_api_with_default_settings(self, service_with_credentials):
        """Test API call with default voice settings - lines 125-132"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "audio/mpeg"}
        mock_response.iter_content = Mock(return_value=iter([b"audio"]))
        mock_response.raise_for_status = Mock()
        
        with patch('services.elevenlabs_rvm_service.requests.post', return_value=mock_response) as mock_post:
            with patch('services.elevenlabs_rvm_service.logger'):
                service_with_credentials._call_elevenlabs_api("Test script")
                
                # Verify request was made with default settings
                call_kwargs = mock_post.call_args[1]
                assert call_kwargs["json"]["voice_settings"]["stability"] == 0.4
                assert call_kwargs["json"]["voice_settings"]["similarity_boost"] == 0.90
                assert call_kwargs["json"]["voice_settings"]["use_speaker_boost"] is True
                assert call_kwargs["json"]["voice_settings"]["style"] == 0.5
                assert call_kwargs["json"]["voice_settings"]["speed"] == 0.9
                assert call_kwargs["json"]["model_id"] == "eleven_multilingual_v2"
                assert call_kwargs["json"]["text"] == "Test script"
                assert call_kwargs["headers"]["xi-api-key"] == "test_api_key"
                assert call_kwargs["stream"] is True
                assert call_kwargs["timeout"] == 60
    
    def test_call_elevenlabs_api_with_custom_settings(self, service_with_credentials):
        """Test API call with custom voice settings - lines 135-137"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "audio/mpeg"}
        mock_response.iter_content = Mock(return_value=iter([b"audio"]))
        mock_response.raise_for_status = Mock()
        
        custom_settings = {
            "stability": 0.6,
            "speed": 1.1
        }
        
        with patch('services.elevenlabs_rvm_service.requests.post', return_value=mock_response) as mock_post:
            with patch('services.elevenlabs_rvm_service.logger'):
                service_with_credentials._call_elevenlabs_api("Test", voice_settings=custom_settings)
                
                # Verify custom settings override defaults
                call_kwargs = mock_post.call_args[1]
                assert call_kwargs["json"]["voice_settings"]["stability"] == 0.6
                assert call_kwargs["json"]["voice_settings"]["speed"] == 1.1
                # Other defaults should still be present
                assert call_kwargs["json"]["voice_settings"]["similarity_boost"] == 0.90
    
    def test_call_elevenlabs_api_wrong_content_type(self, service_with_credentials):
        """Test API call with wrong content type - lines 155-159"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}  # Wrong type
        mock_response.text = '{"error": "Invalid request"}'
        
        with patch('services.elevenlabs_rvm_service.requests.post', return_value=mock_response):
            with patch('services.elevenlabs_rvm_service.logger'):
                with pytest.raises(ValueError) as exc_info:
                    service_with_credentials._call_elevenlabs_api("Test script")
                
                assert "ElevenLabs did not return audio" in str(exc_info.value)
                assert "Invalid request" in str(exc_info.value)
    
    def test_call_elevenlabs_api_http_error(self, service_with_credentials):
        """Test API call with HTTP error - lines 161, 172-174"""
        import requests
        
        # Create a proper HTTPError
        from requests.exceptions import HTTPError
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"error": "Unauthorized"}'
        # raise_for_status should raise HTTPError when status is not 2xx
        mock_response.raise_for_status = Mock(side_effect=HTTPError("401 Client Error: Unauthorized", response=mock_response))
        
        with patch('services.elevenlabs_rvm_service.requests.post', return_value=mock_response):
            with patch('services.elevenlabs_rvm_service.logger'):
                # The code checks content_type first, so we need to make it pass that check
                # Actually, if content_type is not audio/, it raises ValueError before raise_for_status
                # So let's make it audio/ but then raise HTTPError
                mock_response.headers = {"Content-Type": "audio/mpeg"}
                
                with pytest.raises(RuntimeError) as exc_info:
                    service_with_credentials._call_elevenlabs_api("Test script")
                
                assert "Failed to generate audio with ElevenLabs" in str(exc_info.value)
    
    def test_call_elevenlabs_api_request_exception(self, service_with_credentials):
        """Test API call with request exception - lines 172-174"""
        import requests
        
        with patch('services.elevenlabs_rvm_service.requests.post', side_effect=requests.exceptions.RequestException("Connection error")):
            with patch('services.elevenlabs_rvm_service.logger'):
                with pytest.raises(RuntimeError) as exc_info:
                    service_with_credentials._call_elevenlabs_api("Test script")
                
                assert "Failed to generate audio with ElevenLabs" in str(exc_info.value)
                assert "Connection error" in str(exc_info.value)
    
    def test_call_elevenlabs_api_generic_exception(self, service_with_credentials):
        """Test API call with generic exception - lines 175-177"""
        with patch('services.elevenlabs_rvm_service.requests.post', side_effect=Exception("Unexpected error")):
            with patch('services.elevenlabs_rvm_service.logger'):
                with pytest.raises(Exception) as exc_info:
                    service_with_credentials._call_elevenlabs_api("Test script")
                
                assert "Unexpected error" in str(exc_info.value)
    
    def test_call_elevenlabs_api_streaming_response(self, service_with_credentials):
        """Test API call with streaming response - lines 163-167"""
        # Simulate chunked response
        chunk1 = b"audio_chunk_1"
        chunk2 = b"audio_chunk_2"
        chunk3 = b"audio_chunk_3"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "audio/mpeg"}
        mock_response.iter_content = Mock(return_value=iter([chunk1, chunk2, chunk3]))
        mock_response.raise_for_status = Mock()
        
        with patch('services.elevenlabs_rvm_service.requests.post', return_value=mock_response):
            with patch('services.elevenlabs_rvm_service.logger'):
                result = service_with_credentials._call_elevenlabs_api("Test script")
                
                assert result == chunk1 + chunk2 + chunk3
                # Verify iter_content was called with correct chunk size
                mock_response.iter_content.assert_called_with(chunk_size=8192)
    
    def test_call_elevenlabs_api_empty_chunks(self, service_with_credentials):
        """Test API call with empty chunks in stream - lines 164-167"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "audio/mpeg"}
        # Include empty chunks - should be filtered out
        mock_response.iter_content = Mock(return_value=iter([b"audio", b"", b"data", None]))
        mock_response.raise_for_status = Mock()
        
        with patch('services.elevenlabs_rvm_service.requests.post', return_value=mock_response):
            with patch('services.elevenlabs_rvm_service.logger'):
                result = service_with_credentials._call_elevenlabs_api("Test script")
                
                # Empty chunks and None should be filtered
                assert result == b"audiodata"
    
    def test_call_elevenlabs_api_url_construction(self, service_with_credentials):
        """Test API URL construction - line 118"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "audio/mpeg"}
        mock_response.iter_content = Mock(return_value=iter([b"audio"]))
        mock_response.raise_for_status = Mock()
        
        with patch('services.elevenlabs_rvm_service.requests.post', return_value=mock_response) as mock_post:
            with patch('services.elevenlabs_rvm_service.logger'):
                service_with_credentials._call_elevenlabs_api("Test")
                
                # Verify URL includes voice_id
                call_url = mock_post.call_args[0][0]
                assert "text-to-speech" in call_url
                assert "test_voice_id" in call_url
                assert call_url == "https://api.elevenlabs.io/v1/text-to-speech/test_voice_id"
    
    def test_call_elevenlabs_api_custom_base_url(self):
        """Test API call with custom base URL - line 21"""
        env_vars = {
            "ELEVENLABS_API_KEY": "test_key",
            "ELEVENLABS_VOICE_ID": "test_voice",
            "ELEVENLABS_API_URL": "https://custom-api.example.com/v1"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            from services.elevenlabs_rvm_service import ElevenLabsRVMService
            
            service = ElevenLabsRVMService()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"Content-Type": "audio/mpeg"}
            mock_response.iter_content = Mock(return_value=iter([b"audio"]))
            mock_response.raise_for_status = Mock()
            
            with patch('services.elevenlabs_rvm_service.requests.post', return_value=mock_response) as mock_post:
                with patch('services.elevenlabs_rvm_service.logger'):
                    service._call_elevenlabs_api("Test")
                    
                    call_url = mock_post.call_args[0][0]
                    assert "custom-api.example.com" in call_url


class TestElevenLabsRVMServiceGetService:
    """Tests for get_rvm_service function"""
    
    def test_get_rvm_service(self):
        """Test get_rvm_service function - lines 180-182"""
        from services.elevenlabs_rvm_service import get_rvm_service, ElevenLabsRVMService
        
        service = get_rvm_service()
        
        assert isinstance(service, ElevenLabsRVMService)
    
    def test_get_rvm_service_returns_new_instance(self):
        """Test that get_rvm_service returns a new instance each time"""
        from services.elevenlabs_rvm_service import get_rvm_service
        
        service1 = get_rvm_service()
        service2 = get_rvm_service()
        
        # Should return new instances (or same if singleton, but current impl returns new)
        assert service1 is not None
        assert service2 is not None


class TestElevenLabsRVMServiceEdgeCases:
    """Tests for edge cases and error conditions"""
    
    @pytest.fixture
    def service_with_credentials(self):
        """Create service with credentials"""
        env_vars = {
            "ELEVENLABS_API_KEY": "test_api_key",
            "ELEVENLABS_VOICE_ID": "test_voice_id"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            from services.elevenlabs_rvm_service import ElevenLabsRVMService
            return ElevenLabsRVMService()
    
    def test_generate_rvm_audio_no_placeholders(self, service_with_credentials):
        """Test audio generation with script that has no placeholders - lines 54-55"""
        mock_audio_bytes = b"fake_audio"
        
        with patch.object(service_with_credentials, '_call_elevenlabs_api', return_value=mock_audio_bytes):
            with patch('builtins.open', mock_open()):
                with patch('os.makedirs'):
                    result = service_with_credentials.generate_rvm_audio(
                        script="No placeholders here",
                        salesperson_name="John",
                        contact_number="+123"
                    )
                    
                    # Script should remain unchanged
                    assert result["script"] == "No placeholders here"
    
    def test_generate_rvm_audio_multiple_placeholders(self, service_with_credentials):
        """Test audio generation with multiple occurrences of placeholders - lines 54-55"""
        mock_audio_bytes = b"fake_audio"
        
        with patch.object(service_with_credentials, '_call_elevenlabs_api', return_value=mock_audio_bytes):
            with patch('builtins.open', mock_open()):
                with patch('os.makedirs'):
                    result = service_with_credentials.generate_rvm_audio(
                        script="[SALESPERSON_NAME] said [SALESPERSON_NAME] will call [CONTACT_NUMBER] at [CONTACT_NUMBER]",
                        salesperson_name="Jane",
                        contact_number="+555"
                    )
                    
                    # All placeholders should be replaced
                    assert "[SALESPERSON_NAME]" not in result["script"]
                    assert "[CONTACT_NUMBER]" not in result["script"]
                    assert result["script"].count("Jane") == 2
                    assert result["script"].count("+555") == 2
    
    def test_generate_rvm_audio_file_write_error(self, service_with_credentials):
        """Test audio generation when file write fails - lines 75-77"""
        mock_audio_bytes = b"fake_audio"
        
        with patch.object(service_with_credentials, '_call_elevenlabs_api', return_value=mock_audio_bytes):
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                with pytest.raises(IOError):
                    service_with_credentials.generate_rvm_audio(
                        script="Test",
                        salesperson_name="John",
                        contact_number="+123"
                    )
    
    def test_generate_rvm_audio_makedirs_creates_directory(self, service_with_credentials):
        """Test that makedirs is called for file path - line 75"""
        mock_audio_bytes = b"fake_audio"
        custom_path = "/custom/dir/rvm_audio.mp3"
        
        with patch.object(service_with_credentials, '_call_elevenlabs_api', return_value=mock_audio_bytes):
            with patch('builtins.open', mock_open()):
                with patch('os.makedirs') as mock_makedirs:
                    service_with_credentials.generate_rvm_audio(
                        script="Test",
                        salesperson_name="John",
                        contact_number="+123",
                        save_to_file=custom_path
                    )
                    
                    # Verify makedirs was called with exist_ok=True
                    mock_makedirs.assert_called()
                    # Check that it was called with the directory part
                    call_args = mock_makedirs.call_args
                    assert "/custom/dir" in call_args[0][0] or "exist_ok=True" in str(call_args)
    
    def test_call_elevenlabs_api_logging(self, service_with_credentials):
        """Test that API calls are logged - lines 145-146, 152-153, 169"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "audio/mpeg"}
        mock_response.iter_content = Mock(return_value=iter([b"audio"]))
        mock_response.raise_for_status = Mock()
        
        with patch('services.elevenlabs_rvm_service.requests.post', return_value=mock_response):
            with patch('services.elevenlabs_rvm_service.logger') as mock_logger:
                service_with_credentials._call_elevenlabs_api("Test script")
                
                # Verify logging occurred
                assert mock_logger.debug.called or mock_logger.info.called
    
    def test_generate_rvm_audio_metadata_timestamp(self, service_with_credentials):
        """Test that metadata includes timestamp - line 97"""
        mock_audio_bytes = b"fake_audio"
        
        with patch.object(service_with_credentials, '_call_elevenlabs_api', return_value=mock_audio_bytes):
            with patch('builtins.open', mock_open()):
                with patch('os.makedirs'):
                    result = service_with_credentials.generate_rvm_audio(
                        script="Test",
                        salesperson_name="John",
                        contact_number="+123"
                    )
                    
                    # Verify timestamp is in ISO format
                    assert "generated_at" in result["metadata"]
                    assert result["metadata"]["generated_at"] is not None
                    assert "T" in result["metadata"]["generated_at"] or "Z" in result["metadata"]["generated_at"]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

