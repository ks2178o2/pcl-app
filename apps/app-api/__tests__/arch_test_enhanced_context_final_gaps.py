# apps/app-api/__tests__/test_enhanced_context_final_gaps.py
"""
Final targeted tests to reach 95% coverage for Enhanced Context Manager
Focus on missing paths identified in coverage report
"""

import pytest
from unittest.mock import Mock, patch
from services.enhanced_context_manager import EnhancedContextManager
from test_utils import SupabaseMockBuilder


@pytest.fixture
def mock_builder():
    return SupabaseMockBuilder()


@pytest.fixture
def enhanced_context_manager(mock_builder):
    with patch('services.enhanced_context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return EnhancedContextManager()


class TestMissingCoveragePaths:
    """Test paths that are currently missing from coverage"""
    
    @pytest.mark.asyncio
    async def test_share_context_item_no_data_returned(self, enhanced_context_manager, mock_builder):
        """Test share context item when no data is returned"""
        mock_builder.setup_table_data('global_context_items', [{'id': 'item-123'}])
        mock_builder.insert_response.data = []  # No data returned
        
        result = await enhanced_context_manager.share_context_item(
            item_id='item-123',
            target_organization_id='org-target',
            shared_by='user-123',
            reason='Collaboration'
        )
        
        assert result is not None
        assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_approve_sharing_request_no_data_returned(self, enhanced_context_manager, mock_builder):
        """Test approve sharing when no data is returned"""
        mock_builder.setup_table_data('context_sharing', [{'id': 'share-123'}])
        mock_builder.update_response.data = []  # No data returned
        
        result = await enhanced_context_manager.approve_sharing_request(
            sharing_id='share-123',
            approved_by='user-123'
        )
        
        assert result is not None
        assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_get_shared_context_items_with_rag_feature(self, enhanced_context_manager, mock_builder):
        """Test get shared items with rag_feature filter"""
        shared_items = [
            {'id': 'share-1', 'target_organization_id': 'org-123', 'status': 'approved', 'rag_feature': 'sales_intelligence'},
            {'id': 'share-2', 'target_organization_id': 'org-123', 'status': 'approved', 'rag_feature': 'support_kb'}
        ]
        mock_builder.setup_table_data('context_sharing', shared_items)
        
        result = await enhanced_context_manager.get_shared_context_items(
            organization_id='org-123',
            rag_feature='sales_intelligence'
        )
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_scrape_web_content_error_path(self, enhanced_context_manager, mock_builder):
        """Test scrape web content error handling"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = await enhanced_context_manager.scrape_web_content(
                url="https://invalid-url.com",
                organization_id="org-123",
                rag_feature="sales_intelligence",
                uploaded_by="user-123"
            )
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_bulk_api_upload_error_path(self, enhanced_context_manager, mock_builder):
        """Test bulk API upload error handling"""
        with patch.object(enhanced_context_manager, 'add_global_context_item') as mock_add:
            mock_add.side_effect = Exception("Bulk upload failed")
            
            result = await enhanced_context_manager.bulk_api_upload(
                items=[{'item_title': 'Test', 'item_content': 'Test content'}],
                organization_id='org-123',
                rag_feature='sales_intelligence',
                uploaded_by='user-123'
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_share_context_item_exception_path(self, enhanced_context_manager):
        """Test share context item when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.share_context_item(
                item_id='item-123',
                target_organization_id='org-target',
                shared_by='user-123',
                reason='Test'
            )
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_approve_sharing_request_exception_path(self, enhanced_context_manager):
        """Test approve sharing request when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.approve_sharing_request(
                sharing_id='share-123',
                approved_by='user-123'
            )
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_get_shared_context_items_exception_path(self, enhanced_context_manager):
        """Test get shared items when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.get_shared_context_items(
                organization_id='org-123'
            )
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_check_global_duplicate_item_exception_path(self, enhanced_context_manager):
        """Test check duplicate when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager._check_global_duplicate_item('item-123')
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_upload_file_content_exception_path(self, enhanced_context_manager):
        """Test upload file when exception occurs"""
        with patch.object(enhanced_context_manager, 'add_global_context_item') as mock_add:
            mock_add.side_effect = Exception("Upload failed")
            
            result = await enhanced_context_manager.upload_file_content(
                file_content="Test",
                file_type="text/plain",
                organization_id="org-123",
                rag_feature="sales_intelligence",
                uploaded_by="user-123"
            )
            
            assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.enhanced_context_manager', '--cov-report=html'])

