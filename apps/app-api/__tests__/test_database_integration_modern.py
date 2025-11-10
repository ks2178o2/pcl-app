"""
Unit Tests for Database Operations (Mocked)
These tests use mocked Supabase client for fast, isolated unit testing.
For integration tests with real database, see test_database_integration_real.py

Use these mocked tests for:
- Fast unit testing without database dependency
- CI/CD environments without database access
- Testing error handling and edge cases

Use real database tests for:
- Actual RLS policy testing
- Database constraint validation
- Query performance testing
- End-to-end integration testing
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.supabase_client import SupabaseClientManager
from services.audit_logger import AuditLogger


@pytest.fixture
def mock_supabase_client():
    """Create a mocked Supabase client"""
    mock_client = Mock()
    mock_table = Mock()
    mock_client.from_.return_value = mock_table
    return mock_client, mock_table


class TestDatabaseIntegration:
    """Database integration tests with mocked Supabase"""
    
    @pytest.mark.asyncio
    async def test_supabase_client_health_check(self, mock_supabase_client):
        """Test Supabase client health check"""
        mock_client, mock_table = mock_supabase_client
        
        mock_execute = Mock()
        mock_execute.data = [{"id": "test"}]
        
        mock_limit = Mock()
        mock_limit.execute.return_value = mock_execute
        
        mock_select = Mock()
        mock_select.limit.return_value = mock_limit
        mock_table.select.return_value = mock_select
        
        manager = SupabaseClientManager()
        manager._client = mock_client
        
        result = await manager.health_check()
        
        assert result["success"] is True
        assert result["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_supabase_client_execute_query(self, mock_supabase_client):
        """Test executing a query"""
        mock_client, mock_table = mock_supabase_client
        
        mock_execute = Mock()
        mock_execute.data = [{"id": "1", "name": "Test"}]
        
        mock_eq = Mock()
        mock_eq.execute.return_value = mock_execute
        
        mock_select = Mock()
        mock_select.eq.return_value = mock_eq
        mock_table.select.return_value = mock_select
        
        manager = SupabaseClientManager()
        manager._client = mock_client
        
        result = await manager.execute_query("test_table", select="*", filters={"id": "1"})
        
        assert result["success"] is True
        assert len(result["data"]) == 1
    
    @pytest.mark.asyncio
    async def test_supabase_client_insert_data(self, mock_supabase_client):
        """Test inserting data"""
        mock_client, mock_table = mock_supabase_client
        
        mock_execute = Mock()
        mock_execute.data = [{"id": "new-id", "name": "Test"}]
        
        mock_insert = Mock()
        mock_insert.execute.return_value = mock_execute
        mock_table.insert.return_value = mock_insert
        
        manager = SupabaseClientManager()
        manager._client = mock_client
        
        result = await manager.insert_data("test_table", {"name": "Test"})
        
        assert result["success"] is True
        assert result["data"][0]["id"] == "new-id"
    
    @pytest.mark.asyncio
    async def test_supabase_client_update_data(self, mock_supabase_client):
        """Test updating data"""
        mock_client, mock_table = mock_supabase_client
        
        mock_execute = Mock()
        mock_execute.data = [{"id": "1", "name": "Updated"}]
        
        mock_eq = Mock()
        mock_eq.execute.return_value = mock_execute
        
        mock_update = Mock()
        mock_update.eq.return_value = mock_eq
        mock_table.update.return_value = mock_update
        
        manager = SupabaseClientManager()
        manager._client = mock_client
        
        result = await manager.update_data("test_table", {"name": "Updated"}, {"id": "1"})
        
        assert result["success"] is True
        assert result["data"][0]["name"] == "Updated"
    
    @pytest.mark.asyncio
    async def test_supabase_client_delete_data(self, mock_supabase_client):
        """Test deleting data"""
        mock_client, mock_table = mock_supabase_client
        
        mock_execute = Mock()
        mock_execute.data = [{"id": "1"}]
        
        mock_eq = Mock()
        mock_eq.execute.return_value = mock_execute
        
        mock_delete = Mock()
        mock_delete.eq.return_value = mock_eq
        mock_table.delete.return_value = mock_delete
        
        manager = SupabaseClientManager()
        manager._client = mock_client
        
        result = await manager.delete_data("test_table", {"id": "1"})
        
        assert result["success"] is True
        assert result["deleted_count"] == 1
    
    def test_audit_logger_database_operation(self):
        """Test audit logger database operations"""
        mock_client = Mock()
        mock_table = Mock()
        mock_client.from_.return_value = mock_table
        
        mock_execute = Mock()
        mock_execute.data = [{"id": "audit-123"}]
        
        mock_insert = Mock()
        mock_insert.execute.return_value = mock_execute
        mock_table.insert.return_value = mock_insert
        
        with patch('services.audit_logger.get_supabase_client', return_value=mock_client):
            logger = AuditLogger()
            result = logger.log_action(
                user_id="user-123",
                action="test_action",
                resource_type="test_resource",
                resource_id="test-123"
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, mock_supabase_client):
        """Test database error handling"""
        mock_client, mock_table = mock_supabase_client
        
        mock_execute = Mock()
        mock_execute.execute.side_effect = Exception("Database error")
        
        mock_select = Mock()
        mock_select.execute = mock_execute.execute
        mock_table.select.return_value = mock_select
        
        manager = SupabaseClientManager()
        manager._client = mock_client
        
        result = await manager.execute_query("test_table", select="*")
        
        assert result["success"] is False
        assert "error" in result

