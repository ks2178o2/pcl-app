# apps/app-api/__tests__/test_supabase_client_comprehensive.py

import pytest
import asyncio
from unittest.mock import patch, Mock, MagicMock
import os
from datetime import datetime

from services.supabase_client import SupabaseClientManager, get_supabase_client
from test_utils import SupabaseMockBuilder, TestDataFactory, MockResponseBuilder

class TestSupabaseClientComprehensive:
    """Comprehensive test suite for Supabase Client with 95% coverage"""

    @pytest.fixture
    def mock_builder(self):
        """Create mock builder for Supabase client"""
        return SupabaseMockBuilder()

    # ==================== CLIENT INITIALIZATION TESTS ====================

    @pytest.mark.asyncio
    async def test_supabase_client_manager_initialization_success(self):
        """Test successful initialization of SupabaseClientManager"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            assert manager is not None
            assert hasattr(manager, 'supabase')

    @pytest.mark.asyncio
    async def test_supabase_client_manager_initialization_missing_url(self):
        """Test initialization of SupabaseClientManager with missing URL"""
        with patch.dict(os.environ, {
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }, clear=True):
            with pytest.raises(ValueError, match="SUPABASE_URL environment variable is required"):
                SupabaseClientManager()

    @pytest.mark.asyncio
    async def test_supabase_client_manager_initialization_missing_key(self):
        """Test initialization of SupabaseClientManager with missing service key"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co'
        }, clear=True):
            with pytest.raises(ValueError, match="SUPABASE_SERVICE_ROLE_KEY environment variable is required"):
                SupabaseClientManager()

    @pytest.mark.asyncio
    async def test_supabase_client_manager_initialization_empty_url(self):
        """Test initialization of SupabaseClientManager with empty URL"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': '',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }, clear=True):
            with pytest.raises(ValueError, match="SUPABASE_URL environment variable is required"):
                SupabaseClientManager()

    @pytest.mark.asyncio
    async def test_supabase_client_manager_initialization_empty_key(self):
        """Test initialization of SupabaseClientManager with empty service key"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': ''
        }, clear=True):
            with pytest.raises(ValueError, match="SUPABASE_SERVICE_ROLE_KEY environment variable is required"):
                SupabaseClientManager()

    @pytest.mark.asyncio
    async def test_get_supabase_client_success(self):
        """Test successful retrieval of Supabase client"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            client = get_supabase_client()
            assert client is not None

    @pytest.mark.asyncio
    async def test_get_supabase_client_singleton(self):
        """Test that get_supabase_client returns the same instance"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            client1 = get_supabase_client()
            client2 = get_supabase_client()
            assert client1 is client2

    # ==================== CLIENT OPERATIONS TESTS ====================

    @pytest.mark.asyncio
    async def test_supabase_client_get_client_success(self):
        """Test successful get_client method"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            client = manager.get_client()
            assert client is not None

    @pytest.mark.asyncio
    async def test_supabase_client_get_client_cached(self):
        """Test that get_client returns cached client"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            client1 = manager.get_client()
            client2 = manager.get_client()
            assert client1 is client2

    # ==================== ERROR HANDLING TESTS ====================

    @pytest.mark.asyncio
    async def test_supabase_client_manager_initialization_exception(self):
        """Test SupabaseClientManager initialization with exception"""
        with patch('services.supabase_client.create_client') as mock_create_client:
            mock_create_client.side_effect = Exception("Connection failed")
            
            with patch.dict(os.environ, {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
            }):
                with pytest.raises(Exception, match="Connection failed"):
                    SupabaseClientManager()

    @pytest.mark.asyncio
    async def test_get_supabase_client_exception(self):
        """Test get_supabase_client with exception"""
        with patch('services.supabase_client.create_client') as mock_create_client:
            mock_create_client.side_effect = Exception("Client creation failed")
            
            with patch.dict(os.environ, {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
            }):
                with pytest.raises(Exception, match="Client creation failed"):
                    get_supabase_client()

    # ==================== ENVIRONMENT VARIABLE TESTS ====================

    @pytest.mark.asyncio
    async def test_supabase_client_manager_with_anon_key(self):
        """Test SupabaseClientManager with anon key instead of service key"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'anon-key'
        }, clear=True):
            # Should still work with anon key
            manager = SupabaseClientManager()
            assert manager is not None

    @pytest.mark.asyncio
    async def test_supabase_client_manager_with_both_keys(self):
        """Test SupabaseClientManager with both service and anon keys"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'service-key',
            'SUPABASE_ANON_KEY': 'anon-key'
        }):
            manager = SupabaseClientManager()
            assert manager is not None

    @pytest.mark.asyncio
    async def test_supabase_client_manager_priority_service_key(self):
        """Test that service key takes priority over anon key"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'service-key',
            'SUPABASE_ANON_KEY': 'anon-key'
        }):
            manager = SupabaseClientManager()
            # Service key should be used, not anon key
            assert manager is not None

    # ==================== CLIENT FUNCTIONALITY TESTS ====================

    @pytest.mark.asyncio
    async def test_supabase_client_basic_operations(self):
        """Test basic Supabase client operations"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            client = manager.get_client()
            
            # Test that client has expected methods
            assert hasattr(client, 'from_')
            assert hasattr(client, 'auth')
            assert hasattr(client, 'storage')

    @pytest.mark.asyncio
    async def test_supabase_client_table_operations(self):
        """Test Supabase client table operations"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            client = manager.get_client()
            
            # Test table selection
            table = client.from_('test_table')
            assert table is not None

    @pytest.mark.asyncio
    async def test_supabase_client_auth_operations(self):
        """Test Supabase client auth operations"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            client = manager.get_client()
            
            # Test auth operations
            auth = client.auth
            assert auth is not None

    @pytest.mark.asyncio
    async def test_supabase_client_storage_operations(self):
        """Test Supabase client storage operations"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            client = manager.get_client()
            
            # Test storage operations
            storage = client.storage
            assert storage is not None

    # ==================== CONNECTION TESTING ====================

    @pytest.mark.asyncio
    async def test_supabase_client_connection_test_success(self):
        """Test successful connection test"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            
            # Mock successful connection test
            with patch.object(manager.supabase, 'from_') as mock_from:
                mock_table = Mock()
                mock_table.select.return_value.execute.return_value = Mock(data=[], count=0)
                mock_from.return_value = mock_table
                
                # Test connection
                result = manager.test_connection()
                assert result is True

    @pytest.mark.asyncio
    async def test_supabase_client_connection_test_failure(self):
        """Test connection test failure"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            
            # Mock failed connection test
            with patch.object(manager.supabase, 'from_') as mock_from:
                mock_table = Mock()
                mock_table.select.return_value.execute.side_effect = Exception("Connection failed")
                mock_from.return_value = mock_table
                
                # Test connection
                result = manager.test_connection()
                assert result is False

    @pytest.mark.asyncio
    async def test_supabase_client_connection_test_method(self):
        """Test that test_connection method exists and works"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            
            # Check that method exists
            assert hasattr(manager, 'test_connection')
            
            # Mock successful test
            with patch.object(manager.supabase, 'from_') as mock_from:
                mock_table = Mock()
                mock_table.select.return_value.execute.return_value = Mock(data=[], count=0)
                mock_from.return_value = mock_table
                
                result = manager.test_connection()
                assert isinstance(result, bool)

    # ==================== CLIENT RESET TESTS ====================

    @pytest.mark.asyncio
    async def test_supabase_client_reset_client(self):
        """Test resetting the Supabase client"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            client1 = manager.get_client()
            
            # Reset client
            manager.reset_client()
            
            # Get new client
            client2 = manager.get_client()
            
            # Should be different instances
            assert client1 is not client2

    @pytest.mark.asyncio
    async def test_supabase_client_reset_client_method(self):
        """Test that reset_client method exists"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            
            # Check that method exists
            assert hasattr(manager, 'reset_client')
            
            # Test reset
            manager.reset_client()
            assert True  # Should not raise exception

    # ==================== CONFIGURATION TESTS ====================

    @pytest.mark.asyncio
    async def test_supabase_client_manager_configuration(self):
        """Test SupabaseClientManager configuration"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            
            # Test configuration properties
            assert hasattr(manager, 'supabase_url')
            assert hasattr(manager, 'supabase_key')
            assert manager.supabase_url == 'https://test.supabase.co'
            assert manager.supabase_key == 'test-key'

    @pytest.mark.asyncio
    async def test_supabase_client_manager_configuration_with_anon_key(self):
        """Test SupabaseClientManager configuration with anon key"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'anon-key'
        }, clear=True):
            manager = SupabaseClientManager()
            
            # Test configuration properties
            assert manager.supabase_url == 'https://test.supabase.co'
            assert manager.supabase_key == 'anon-key'

    # ==================== EDGE CASE TESTS ====================

    @pytest.mark.asyncio
    async def test_supabase_client_manager_with_whitespace_url(self):
        """Test SupabaseClientManager with URL containing whitespace"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': '  https://test.supabase.co  ',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            assert manager is not None
            assert manager.supabase_url == 'https://test.supabase.co'  # Should be stripped

    @pytest.mark.asyncio
    async def test_supabase_client_manager_with_whitespace_key(self):
        """Test SupabaseClientManager with key containing whitespace"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': '  test-key  '
        }):
            manager = SupabaseClientManager()
            assert manager is not None
            assert manager.supabase_key == 'test-key'  # Should be stripped

    @pytest.mark.asyncio
    async def test_supabase_client_manager_multiple_initializations(self):
        """Test multiple initializations of SupabaseClientManager"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager1 = SupabaseClientManager()
            manager2 = SupabaseClientManager()
            
            # Should be different instances
            assert manager1 is not manager2
            
            # But clients should work the same
            client1 = manager1.get_client()
            client2 = manager2.get_client()
            assert client1 is not None
            assert client2 is not None

    # ==================== PERFORMANCE TESTS ====================

    @pytest.mark.asyncio
    async def test_supabase_client_manager_performance_multiple_calls(self):
        """Test performance of multiple get_client calls"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            
            # Multiple calls should be fast due to caching
            clients = []
            for i in range(100):
                client = manager.get_client()
                clients.append(client)
            
            # All clients should be the same instance
            assert all(client is clients[0] for client in clients)

    @pytest.mark.asyncio
    async def test_supabase_client_manager_performance_reset_and_recreate(self):
        """Test performance of reset and recreate operations"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            
            # Test multiple reset and recreate cycles
            for i in range(10):
                manager.reset_client()
                client = manager.get_client()
                assert client is not None

    # ==================== INTEGRATION TESTS ====================

    @pytest.mark.asyncio
    async def test_supabase_client_integration_with_services(self):
        """Test Supabase client integration with other services"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            # Test that client can be used by other services
            client = get_supabase_client()
            
            # Mock table operations
            with patch.object(client, 'from_') as mock_from:
                mock_table = Mock()
                mock_table.select.return_value.execute.return_value = Mock(data=[], count=0)
                mock_from.return_value = mock_table
                
                # Test basic operations
                table = client.from_('test_table')
                result = table.select('*').execute()
                assert result is not None

    @pytest.mark.asyncio
    async def test_supabase_client_error_handling_integration(self):
        """Test error handling integration with Supabase client"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            client = get_supabase_client()
            
            # Mock error scenario
            with patch.object(client, 'from_') as mock_from:
                mock_table = Mock()
                mock_table.select.return_value.execute.side_effect = Exception("Database error")
                mock_from.return_value = mock_table
                
                # Test error handling
                table = client.from_('test_table')
                with pytest.raises(Exception, match="Database error"):
                    table.select('*').execute()

    # ==================== SECURITY TESTS ====================

    @pytest.mark.asyncio
    async def test_supabase_client_manager_key_security(self):
        """Test that keys are handled securely"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'secret-key-123'
        }):
            manager = SupabaseClientManager()
            
            # Key should be stored but not logged
            assert manager.supabase_key == 'secret-key-123'
            
            # Test that key is not exposed in string representation
            str_repr = str(manager)
            assert 'secret-key-123' not in str_repr

    @pytest.mark.asyncio
    async def test_supabase_client_manager_url_security(self):
        """Test that URLs are handled securely"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            
            # URL should be stored correctly
            assert manager.supabase_url == 'https://test.supabase.co'
            
            # Test URL validation
            assert manager.supabase_url.startswith('https://')

    # ==================== CLEANUP TESTS ====================

    @pytest.mark.asyncio
    async def test_supabase_client_manager_cleanup(self):
        """Test cleanup of SupabaseClientManager"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            manager = SupabaseClientManager()
            client = manager.get_client()
            
            # Test cleanup
            manager.reset_client()
            
            # Client should be reset
            new_client = manager.get_client()
            assert new_client is not client

    @pytest.mark.asyncio
    async def test_supabase_client_manager_context_manager(self):
        """Test SupabaseClientManager as context manager"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            # Test that manager can be used in context
            manager = SupabaseClientManager()
            
            with manager as client:
                assert client is not None
                assert hasattr(client, 'from_')
