import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add the parent directory to the path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.context_manager import ContextManager

class TestContextManagerAdditionalCoverage:
    """Additional tests to improve ContextManager coverage to 75%+"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Create a comprehensive mock for SupabaseClientManager"""
        mock_client = Mock()
        
        # Mock the chain of methods for database operations
        mock_insert = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_order = Mock()
        mock_range = Mock()
        mock_execute = Mock()
        mock_single = Mock()
        
        # Chain the mocks
        mock_client.insert.return_value = mock_insert
        mock_insert.execute.return_value = Mock(data=[{"id": "context-123"}])
        
        mock_client.select.return_value = mock_select
        mock_select.from_.return_value = mock_select
        mock_select.eq.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.range.return_value = mock_select
        mock_select.execute.return_value = Mock(data=[
            {
                "id": "context-123",
                "item_title": "Test Item",
                "item_content": "Test Content",
                "rag_feature": "test_feature",
                "organization_id": "org-123"
            }
        ])
        
        mock_client.from_.return_value = mock_select
        
        return mock_client
    
    @pytest.fixture
    def context_manager(self, mock_supabase_client):
        """Create ContextManager instance with mocked dependencies"""
        with patch('services.context_manager.get_supabase_client', return_value=mock_supabase_client):
            return ContextManager()
    
    @pytest.mark.asyncio
    async def test_add_context_item_invalid_confidence_score(self, context_manager, mock_supabase_client):
        """Test add context item with invalid confidence score (line 31)"""
        context_data = {
            "item_id": "item-123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Item",
            "item_content": "Test Content",
            "rag_feature": "test_feature",
            "organization_id": "org-123",
            "confidence_score": 1.5  # Invalid confidence score
        }
        
        result = await context_manager.add_context_item(context_data)
        
        assert result["success"] is False
        assert "Confidence score must be between 0 and 1" in result["error"]
    
    @pytest.mark.asyncio
    async def test_add_context_item_duplicate_exists(self, context_manager, mock_supabase_client):
        """Test add context item when duplicate exists (line 46)"""
        # Mock duplicate check to return True
        context_manager._check_duplicate_item = AsyncMock(return_value=True)
        
        context_data = {
            "item_id": "item-123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Item",
            "item_content": "Test Content",
            "rag_feature": "test_feature",
            "organization_id": "org-123"
        }
        
        result = await context_manager.add_context_item(context_data)
        
        assert result["success"] is False
        assert "Item already exists" in result["error"]
    
    @pytest.mark.asyncio
    async def test_add_context_item_no_data_returned(self, context_manager, mock_supabase_client):
        """Test add context item when no data is returned (line 60)"""
        # Mock insert to return no data
        mock_supabase_client.from_.return_value.insert.return_value.execute.return_value = Mock(data=None)
        
        context_data = {
            "item_id": "item-123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Item",
            "item_content": "Test Content",
            "rag_feature": "test_feature",
            "organization_id": "org-123"
        }
        
        result = await context_manager.add_context_item(context_data)
        
        assert result["success"] is False
        assert "Failed to create context item" in result["error"]
    
    @pytest.mark.asyncio
    async def test_add_context_item_exception_handling(self, context_manager, mock_supabase_client):
        """Test add context item exception handling (lines 79-83)"""
        # Mock insert to raise an exception
        mock_supabase_client.from_.return_value.insert.return_value.execute.side_effect = Exception("Database error")
        
        context_data = {
            "item_id": "item-123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Item",
            "item_content": "Test Content",
            "rag_feature": "test_feature",
            "organization_id": "org-123"
        }
        
        result = await context_manager.add_context_item(context_data)
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_context_items_exception_handling(self, context_manager, mock_supabase_client):
        """Test get context items exception handling (lines 93-97)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.range.return_value.execute.side_effect = Exception("Database error")
        
        result = await context_manager.get_context_items(
            rag_feature="test_feature",
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_context_item_exception_handling(self, context_manager, mock_supabase_client):
        """Test update context item exception handling (lines 112-116)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await context_manager.update_context_item(
            item_id="item-123",
            updates={"item_title": "Updated Title"}
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_remove_context_item_exception_handling(self, context_manager, mock_supabase_client):
        """Test remove context item exception handling (lines 133-137)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.delete.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await context_manager.remove_context_item(
            item_id="item-123",
            reason="Test removal"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_context_status_exception_handling(self, context_manager, mock_supabase_client):
        """Test update context status exception handling (lines 158-162)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await context_manager.update_context_status(
            item_id="item-123",
            new_status="archived",
            reason="Test status update"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_search_context_items_exception_handling(self, context_manager, mock_supabase_client):
        """Test search context items exception handling (lines 251-255)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.ilike.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await context_manager.search_context_items(
            query="test query",
            rag_feature="test_feature",
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_export_context_items_exception_handling(self, context_manager, mock_supabase_client):
        """Test export context items exception handling (lines 287-291)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await context_manager.export_context_items(
            rag_feature="test_feature",
            organization_id="org-123",
            format_type="json"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_import_context_items_exception_handling(self, context_manager, mock_supabase_client):
        """Test import context items exception handling (lines 300-302)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.insert.return_value.execute.side_effect = Exception("Database error")
        
        import_data = [
            {
                "item_title": "Imported Item",
                "item_content": "Imported Content",
                "rag_feature": "test_feature",
                "organization_id": "org-123"
            }
        ]
        
        result = await context_manager.import_context_items(
            import_data=import_data,
            rag_feature="test_feature",
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_check_duplicate_items_exception_handling(self, context_manager, mock_supabase_client):
        """Test check duplicate items exception handling (lines 320-324)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.in_.return_value.execute.side_effect = Exception("Database error")
        
        result = await context_manager.check_duplicate_items(
            item_ids=["item-1", "item-2"],
            rag_feature="test_feature",
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics_exception_handling(self, context_manager, mock_supabase_client):
        """Test get performance metrics exception handling (lines 353-357)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await context_manager.get_performance_metrics(
            rag_feature="test_feature",
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_check_duplicate_item_exception_handling(self, context_manager, mock_supabase_client):
        """Test check duplicate item exception handling (lines 380-384)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await context_manager._check_duplicate_item(
            item_title="Test Item",
            rag_feature="test_feature",
            organization_id="org-123"
        )
        
        assert result is False  # Should return False on exception
    
    @pytest.mark.asyncio
    async def test_get_context_items_no_data(self, context_manager, mock_supabase_client):
        """Test get context items when no data is returned"""
        # Mock execute to return empty data
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = Mock(data=[])
        
        result = await context_manager.get_context_items(
            rag_feature="test_feature",
            organization_id="org-123"
        )
        
        assert result["success"] is True
        assert result["items"] == []
        assert result["total_count"] == 0
    
    @pytest.mark.asyncio
    async def test_search_context_items_no_data(self, context_manager, mock_supabase_client):
        """Test search context items when no data is returned"""
        # Mock execute to return empty data
        mock_supabase_client.from_.return_value.select.return_value.ilike.return_value.eq.return_value.execute.return_value = Mock(data=[])
        
        result = await context_manager.search_context_items(
            query="test query",
            rag_feature="test_feature",
            organization_id="org-123"
        )
        
        assert result["success"] is True
        assert result["items"] == []
        assert result["total_count"] == 0
    
    @pytest.mark.asyncio
    async def test_export_context_items_csv_format(self, context_manager, mock_supabase_client):
        """Test export context items in CSV format"""
        # Mock execute to return data
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[
            {
                "item_title": "Test Item",
                "item_content": "Test Content",
                "rag_feature": "test_feature"
            }
        ])
        
        result = await context_manager.export_context_items(
            rag_feature="test_feature",
            organization_id="org-123",
            format_type="csv"
        )
        
        assert result["success"] is True
        assert "csv_data" in result
    
    @pytest.mark.asyncio
    async def test_export_context_items_invalid_format(self, context_manager, mock_supabase_client):
        """Test export context items with invalid format"""
        result = await context_manager.export_context_items(
            rag_feature="test_feature",
            organization_id="org-123",
            format_type="invalid_format"
        )
        
        assert result["success"] is False
        assert "Unsupported format" in result["error"]
