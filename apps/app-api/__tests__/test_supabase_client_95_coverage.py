# apps/app-api/__tests__/test_supabase_client_95_coverage.py

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
import os
import sys

# Add the parent directory to the path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.supabase_client import SupabaseClientManager, get_supabase_client


class TestSupabaseClient95Coverage:
    """Comprehensive test suite for SupabaseClient to achieve 95% coverage"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing"""
        mock_client = Mock()
        
        # Mock table and query chains
        mock_table = Mock()
        
        # Mock select chain
        mock_select = Mock()
        mock_select.eq.return_value = mock_select
        mock_select.limit.return_value = mock_select
        mock_select.execute.return_value = Mock(
            data=[{"id": "test-id", "name": "test-name"}],
            count=1
        )
        mock_table.select.return_value = mock_select
        
        # Mock insert chain
        mock_insert = Mock()
        mock_insert.execute.return_value = Mock(data=[{"id": "new-id", "created": True}])
        mock_table.insert.return_value = mock_insert
        
        # Mock update chain
        mock_update = Mock()
        mock_update.eq.return_value = mock_update
        mock_update.execute.return_value = Mock(data=[{"id": "updated-id", "updated": True}])
        mock_table.update.return_value = mock_update
        
        # Mock delete chain
        mock_delete = Mock()
        mock_delete.eq.return_value = mock_delete
        mock_delete.execute.return_value = Mock(data=[{"id": "deleted-id", "deleted": True}])
        mock_table.delete.return_value = mock_delete
        
        mock_client.from_.return_value = mock_table
        
        return mock_client

    @pytest.fixture
    def supabase_client_manager(self, mock_supabase_client):
        """Create SupabaseClientManager instance with mocked client"""
        with patch('services.supabase_client.create_client') as mock_create_client:
            mock_create_client.return_value = mock_supabase_client
            with patch.dict(os.environ, {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
            }, clear=True):
                # Reset singleton instance
                SupabaseClientManager._instance = None
                SupabaseClientManager._client = None
                manager = SupabaseClientManager()
                # Initialize the client
                manager.get_client()
                return manager

    # Test singleton pattern - covers lines 17-20
    def test_singleton_pattern(self):
        """Test that SupabaseClientManager follows singleton pattern"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            # Reset singleton instance
            SupabaseClientManager._instance = None
            SupabaseClientManager._client = None
            
            manager1 = SupabaseClientManager()
            manager2 = SupabaseClientManager()
            
            assert manager1 is manager2
            assert id(manager1) == id(manager2)

    # Test get_client method - covers lines 22-38
    def test_get_client_success(self, supabase_client_manager):
        """Test successful client retrieval - covers lines 22-38"""
        client = supabase_client_manager.get_client()
        
        assert client is not None
        assert hasattr(client, 'from_')

    def test_get_client_missing_url(self):
        """Test client retrieval with missing SUPABASE_URL - covers lines 28-29"""
        with patch.dict(os.environ, {}, clear=True):
            # Reset singleton instance
            SupabaseClientManager._instance = None
            SupabaseClientManager._client = None
            
            manager = SupabaseClientManager()
            
            with pytest.raises(ValueError, match="SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set"):
                manager.get_client()

    def test_get_client_missing_key(self):
        """Test client retrieval with missing SUPABASE_SERVICE_ROLE_KEY - covers lines 28-29"""
        with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co'}, clear=True):
            # Reset singleton instance
            SupabaseClientManager._instance = None
            SupabaseClientManager._client = None
            
            manager = SupabaseClientManager()
            
            with pytest.raises(ValueError, match="SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set"):
                manager.get_client()

    def test_get_client_creation_error(self):
        """Test client retrieval with creation error - covers lines 34-36"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            with patch('services.supabase_client.create_client') as mock_create_client:
                mock_create_client.side_effect = Exception("Connection failed")
                
                # Reset singleton instance
                SupabaseClientManager._instance = None
                SupabaseClientManager._client = None
                
                manager = SupabaseClientManager()
                
                with pytest.raises(Exception, match="Connection failed"):
                    manager.get_client()

    def test_get_client_cached(self, supabase_client_manager):
        """Test that client is cached after first creation - covers lines 24-25"""
        client1 = supabase_client_manager.get_client()
        client2 = supabase_client_manager.get_client()
        
        assert client1 is client2

    # Test health_check method - covers lines 40-58
    @pytest.mark.asyncio
    async def test_health_check_success(self, supabase_client_manager):
        """Test successful health check - covers lines 40-52"""
        result = await supabase_client_manager.health_check()
        
        assert result["success"] is True
        assert result["status"] == "healthy"
        assert "response_time" in result

    @pytest.mark.asyncio
    async def test_health_check_failure(self, supabase_client_manager):
        """Test health check failure - covers lines 53-58"""
        # Mock the client to raise an exception
        supabase_client_manager.get_client().from_.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("Connection failed")
        
        result = await supabase_client_manager.health_check()
        
        assert result["success"] is False
        assert "error" in result
        assert "Connection failed" in result["error"]

    # Test execute_query method - covers lines 59-80
    @pytest.mark.asyncio
    async def test_execute_query_success(self, supabase_client_manager):
        """Test successful query execution - covers lines 59-75"""
        result = await supabase_client_manager.execute_query(
            table="test_table",
            select="id, name",
            filters={"status": "active"}
        )
        
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_execute_query_no_filters(self, supabase_client_manager):
        """Test query execution without filters - covers lines 59-75"""
        result = await supabase_client_manager.execute_query(
            table="test_table",
            select="*"
        )
        
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_execute_query_database_error(self, supabase_client_manager):
        """Test query execution with database error - covers lines 76-80"""
        supabase_client_manager.get_client().from_.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await supabase_client_manager.execute_query(
            table="test_table",
            filters={"status": "active"}
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test insert_data method - covers lines 81-96
    @pytest.mark.asyncio
    async def test_insert_data_success(self, supabase_client_manager):
        """Test successful data insertion - covers lines 81-91"""
        data = {"name": "test", "status": "active"}
        
        result = await supabase_client_manager.insert_data(
            table="test_table",
            data=data
        )
        
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_insert_data_database_error(self, supabase_client_manager):
        """Test data insertion with database error - covers lines 92-96"""
        supabase_client_manager.get_client().from_.return_value.insert.return_value.execute.side_effect = Exception("Database error")
        
        data = {"name": "test", "status": "active"}
        
        result = await supabase_client_manager.insert_data(
            table="test_table",
            data=data
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test update_data method - covers lines 97-117
    @pytest.mark.asyncio
    async def test_update_data_success(self, supabase_client_manager):
        """Test successful data update - covers lines 97-113"""
        data = {"name": "updated", "status": "inactive"}
        filters = {"id": "test-id"}
        
        result = await supabase_client_manager.update_data(
            table="test_table",
            data=data,
            filters=filters
        )
        
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_update_data_database_error(self, supabase_client_manager):
        """Test data update with database error - covers lines 114-117"""
        supabase_client_manager.get_client().from_.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        data = {"name": "updated"}
        filters = {"id": "test-id"}
        
        result = await supabase_client_manager.update_data(
            table="test_table",
            data=data,
            filters=filters
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test delete_data method - covers lines 118-139
    @pytest.mark.asyncio
    async def test_delete_data_success(self, supabase_client_manager):
        """Test successful data deletion - covers lines 118-134"""
        filters = {"id": "test-id"}
        
        result = await supabase_client_manager.delete_data(
            table="test_table",
            filters=filters
        )
        
        assert result["success"] is True
        assert "deleted_count" in result

    @pytest.mark.asyncio
    async def test_delete_data_database_error(self, supabase_client_manager):
        """Test data deletion with database error - covers lines 135-139"""
        supabase_client_manager.get_client().from_.return_value.delete.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        filters = {"id": "test-id"}
        
        result = await supabase_client_manager.delete_data(
            table="test_table",
            filters=filters
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test get_supabase_client function - covers lines 140-143
    def test_get_supabase_client_function(self, supabase_client_manager):
        """Test the get_supabase_client function - covers lines 140-143"""
        with patch('services.supabase_client.SupabaseClientManager') as mock_manager_class:
            mock_manager_instance = Mock()
            mock_manager_instance.get_client.return_value = "mock-client"
            mock_manager_class.return_value = mock_manager_instance
            
            client = get_supabase_client()
            
            assert client == "mock-client"

    # Test edge cases and error conditions
    @pytest.mark.asyncio
    async def test_execute_query_empty_filters(self, supabase_client_manager):
        """Test query execution with empty filters"""
        result = await supabase_client_manager.execute_query(
            table="test_table",
            filters={}
        )
        
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_execute_query_none_filters(self, supabase_client_manager):
        """Test query execution with None filters"""
        result = await supabase_client_manager.execute_query(
            table="test_table",
            filters=None
        )
        
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_insert_data_empty_data(self, supabase_client_manager):
        """Test data insertion with empty data"""
        result = await supabase_client_manager.insert_data(
            table="test_table",
            data={}
        )
        
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_update_data_empty_filters(self, supabase_client_manager):
        """Test data update with empty filters"""
        data = {"name": "updated"}
        
        result = await supabase_client_manager.update_data(
            table="test_table",
            data=data,
            filters={}
        )
        
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_delete_data_empty_filters(self, supabase_client_manager):
        """Test data deletion with empty filters"""
        result = await supabase_client_manager.delete_data(
            table="test_table",
            filters={}
        )
        
        assert result["success"] is True
        assert "deleted_count" in result

    # Test concurrent operations
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, supabase_client_manager):
        """Test concurrent operations"""
        tasks = [
            supabase_client_manager.health_check(),
            supabase_client_manager.execute_query("test_table"),
            supabase_client_manager.insert_data("test_table", {"name": "test"}),
            supabase_client_manager.update_data("test_table", {"name": "updated"}, {"id": "test-id"}),
            supabase_client_manager.delete_data("test_table", {"id": "test-id"})
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should complete
        assert len(results) == 5
        for result in results:
            assert result is not None
            if isinstance(result, dict):
                assert "success" in result

    # Test multiple filter conditions
    @pytest.mark.asyncio
    async def test_execute_query_multiple_filters(self, supabase_client_manager):
        """Test query execution with multiple filters"""
        filters = {
            "status": "active",
            "type": "premium",
            "created_at": "2024-01-01"
        }
        
        result = await supabase_client_manager.execute_query(
            table="test_table",
            filters=filters
        )
        
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_update_data_multiple_filters(self, supabase_client_manager):
        """Test data update with multiple filters"""
        data = {"name": "updated", "status": "inactive"}
        filters = {"id": "test-id", "status": "active"}
        
        result = await supabase_client_manager.update_data(
            table="test_table",
            data=data,
            filters=filters
        )
        
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_delete_data_multiple_filters(self, supabase_client_manager):
        """Test data deletion with multiple filters"""
        filters = {"id": "test-id", "status": "inactive"}
        
        result = await supabase_client_manager.delete_data(
            table="test_table",
            filters=filters
        )
        
        assert result["success"] is True
        assert "deleted_count" in result

    # Test error handling for different exception types
    @pytest.mark.asyncio
    async def test_health_check_timeout_error(self, supabase_client_manager):
        """Test health check with timeout error"""
        supabase_client_manager.get_client().from_.return_value.select.return_value.limit.return_value.execute.side_effect = TimeoutError("Request timeout")
        
        result = await supabase_client_manager.health_check()
        
        assert result["success"] is False
        assert "Request timeout" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_query_connection_error(self, supabase_client_manager):
        """Test query execution with connection error"""
        supabase_client_manager.get_client().from_.return_value.select.return_value.eq.return_value.execute.side_effect = ConnectionError("Connection lost")
        
        result = await supabase_client_manager.execute_query(
            table="test_table",
            filters={"status": "active"}
        )
        
        assert result["success"] is False
        assert "Connection lost" in result["error"]

    # Test singleton reset functionality
    def test_singleton_reset(self):
        """Test that singleton can be reset"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            # Reset singleton instance
            SupabaseClientManager._instance = None
            SupabaseClientManager._client = None
            
            manager1 = SupabaseClientManager()
            client1 = manager1.get_client()
            
            # Reset singleton
            SupabaseClientManager._instance = None
            SupabaseClientManager._client = None
            
            manager2 = SupabaseClientManager()
            client2 = manager2.get_client()
            
            # Should be different instances
            assert manager1 is not manager2
            assert client1 is not client2
