import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add the parent directory to the path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.enhanced_context_manager import EnhancedContextManager

class TestEnhancedContextManagerAdditionalCoverage:
    """Additional tests to improve EnhancedContextManager coverage to 85%+"""
    
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
    def enhanced_context_manager(self, mock_supabase_client):
        """Create EnhancedContextManager instance with mocked dependencies"""
        with patch('services.enhanced_context_manager.get_supabase_client', return_value=mock_supabase_client):
            return EnhancedContextManager()
    
    @pytest.mark.asyncio
    async def test_add_global_context_item_no_data_returned(self, enhanced_context_manager, mock_supabase_client):
        """Test add global context item when no data is returned (line 61)"""
        # Mock insert to return no data
        mock_supabase_client.from_.return_value.insert.return_value.execute.return_value = Mock(data=None)
        
        context_data = {
            "rag_feature": "test_feature",
            "item_id": "item-123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Item",
            "item_content": "Test Content"
        }
        
        result = await enhanced_context_manager.add_global_context_item(context_data)
        
        assert result["success"] is False
        assert "Failed to create global context item" in result["error"]
    
    @pytest.mark.asyncio
    async def test_add_global_context_item_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test add global context item exception handling (lines 66-70)"""
        # Mock insert to raise an exception
        mock_supabase_client.from_.return_value.insert.return_value.execute.side_effect = Exception("Database error")
        
        context_data = {
            "rag_feature": "test_feature",
            "item_id": "item-123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Item",
            "item_content": "Test Content"
        }
        
        result = await enhanced_context_manager.add_global_context_item(context_data)
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_global_context_items_no_access(self, enhanced_context_manager, mock_supabase_client):
        """Test get global context items when organization has no access (lines 89-91)"""
        # Mock access check to return no data
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[])
        
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature="test_feature",
            organization_id="org-123"
        )
        
        assert result["success"] is True
        assert result["items"] == []
        assert result["total_count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_global_context_items_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test get global context items exception handling (lines 95-99)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature="test_feature",
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_grant_tenant_access_create_new_access(self, enhanced_context_manager, mock_supabase_client):
        """Test grant tenant access when creating new access (line 139)"""
        # Mock access check to return no existing access
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[])
        
        result = await enhanced_context_manager.grant_tenant_access(
            organization_id="org-123",
            rag_feature="test_feature",
            access_level="read"
        )
        
        assert result["success"] is True
        assert "access_granted" in result
    
    @pytest.mark.asyncio
    async def test_grant_tenant_access_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test grant tenant access exception handling (lines 152-156)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await enhanced_context_manager.grant_tenant_access(
            organization_id="org-123",
            rag_feature="test_feature",
            access_level="read"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_revoke_tenant_access_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test revoke tenant access exception handling (lines 178-182)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await enhanced_context_manager.revoke_tenant_access(
            organization_id="org-123",
            rag_feature="test_feature"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_share_context_item_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test share context item exception handling (lines 201-205)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await enhanced_context_manager.share_context_item(
            source_org_id="org-123",
            target_org_id="org-456",
            rag_feature="test_feature",
            item_id="item-123",
            shared_by="user-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_approve_sharing_request_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test approve sharing request exception handling (lines 223-227)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await enhanced_context_manager.approve_sharing_request(
            sharing_id="request-123",
            approved_by="user-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_shared_context_items_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test get shared context items exception handling (lines 250-254)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await enhanced_context_manager.get_shared_context_items(
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_upload_file_content_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test upload file content exception handling (lines 306-310)"""
        # Mock the method to raise an exception
        enhanced_context_manager._log_upload = AsyncMock(side_effect=Exception("Database error"))
        
        result = await enhanced_context_manager.upload_file_content(
            file_content="Test content",
            file_type="text",
            organization_id="org-123",
            rag_feature="test_feature",
            uploaded_by="user-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_scrape_web_content_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test scrape web content exception handling (lines 326-330)"""
        # Mock the method to raise an exception
        enhanced_context_manager.add_context_item = AsyncMock(side_effect=Exception("Database error"))
        
        result = await enhanced_context_manager.scrape_web_content(
            url="https://example.com",
            organization_id="org-123",
            rag_feature="test_feature",
            uploaded_by="user-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_bulk_api_upload_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test bulk API upload exception handling (lines 385-389)"""
        # Mock the method to raise an exception
        enhanced_context_manager.add_context_item = AsyncMock(side_effect=Exception("Database error"))
        
        items = [
            {
                "item_id": "item1",
                "item_type": "knowledge_chunk",
                "item_title": "Title 1",
                "item_content": "Content 1"
            }
        ]
        
        result = await enhanced_context_manager.bulk_api_upload(
            items=items,
            organization_id="org-123",
            rag_feature="test_feature",
            uploaded_by="user-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test get organization quotas exception handling (lines 411-415)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("Database error")
        
        result = await enhanced_context_manager.get_organization_quotas(
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_organization_quotas_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test update organization quotas exception handling (lines 447-451)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        quota_updates = {
            "max_context_items": 1000,
            "max_file_uploads": 100
        }
        
        result = await enhanced_context_manager.update_organization_quotas(
            organization_id="org-123",
            quota_updates=quota_updates
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_check_global_duplicate_item_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test check global duplicate item exception handling (lines 485-489)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await enhanced_context_manager._check_global_duplicate_item(
            item_title="Test Item",
            rag_feature="test_feature"
        )
        
        assert result is False  # Should return False on exception
    
    @pytest.mark.asyncio
    async def test_log_upload_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test log upload exception handling (lines 501-505)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.insert.return_value.execute.side_effect = Exception("Database error")
        
        result = await enhanced_context_manager._log_upload(
            upload_type="file_upload",
            filename="test.txt",
            rag_feature="test_feature",
            organization_id="org-123",
            success=True
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_add_context_item_exception_handling(self, enhanced_context_manager, mock_supabase_client):
        """Test add context item exception handling (lines 524-528)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.insert.return_value.execute.side_effect = Exception("Database error")
        
        context_data = {
            "rag_feature": "test_feature",
            "item_id": "item-123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Item",
            "item_content": "Test Content"
        }
        
        result = await enhanced_context_manager.add_context_item(context_data)
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_add_context_item_duplicate_check_exception(self, enhanced_context_manager, mock_supabase_client):
        """Test add context item when duplicate check raises exception (lines 537-541)"""
        # Mock duplicate check to raise an exception
        enhanced_context_manager._check_global_duplicate_item = AsyncMock(side_effect=Exception("Duplicate check error"))
        
        context_data = {
            "rag_feature": "test_feature",
            "item_id": "item-123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Item",
            "item_content": "Test Content"
        }
        
        result = await enhanced_context_manager.add_context_item(context_data)
        
        assert result["success"] is False
        assert "Duplicate check error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_add_context_item_no_data_returned(self, enhanced_context_manager, mock_supabase_client):
        """Test add context item when no data is returned (lines 551-555)"""
        # Mock insert to return no data
        mock_supabase_client.from_.return_value.insert.return_value.execute.return_value = Mock(data=None)
        
        context_data = {
            "rag_feature": "test_feature",
            "item_id": "item-123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Item",
            "item_content": "Test Content"
        }
        
        result = await enhanced_context_manager.add_context_item(context_data)
        
        assert result["success"] is False
        assert "Failed to create context item" in result["error"]
