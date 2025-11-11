# apps/app-api/__tests__/test_enhanced_context_95_final_push.py
"""
Final push to 95% coverage for Enhanced Context Manager
Covering last remaining missing paths
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


class TestFileUploadLines323324:
    """Test file upload success path - lines 323-324"""
    
    @pytest.mark.asyncio
    async def test_upload_file_content_success_path(self, enhanced_context_manager, mock_builder):
        """Test upload when add_context_item succeeds - covers lines 323-324"""
        with patch.object(enhanced_context_manager, 'add_context_item') as mock_add:
            mock_add.return_value = {'success': True, 'item_id': 'item-123'}
            
            result = await enhanced_context_manager.upload_file_content(
                file_content="First section\n\nSecond section",
                file_type="txt",
                organization_id="org-123",
                rag_feature="sales_intelligence",
                uploaded_by="user-123"
            )
            
            assert result is not None
            assert result.get('success') is True
            assert mock_add.call_count == 2  # Two sections


class TestFileUploadLines341343:
    """Test file upload exception path - lines 341-343"""
    
    @pytest.mark.asyncio
    async def test_upload_file_content_exception(self, enhanced_context_manager):
        """Test upload when exception occurs - covers lines 341-343"""
        with patch.object(enhanced_context_manager, 'add_context_item') as mock_add:
            mock_add.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.upload_file_content(
                file_content="Test content",
                file_type="txt",
                organization_id="org-123",
                rag_feature="sales_intelligence",
                uploaded_by="user-123"
            )
            
            assert result is not None
            assert result.get('success') is False
            assert 'error' in result


class TestScrapeWebLines385387:
    """Test web scraping exception handling - lines 385-387"""
    
    @pytest.mark.asyncio
    async def test_scrape_web_content_exception(self, enhanced_context_manager):
        """Test scrape when exception occurs"""
        with patch.object(enhanced_context_manager, 'add_context_item') as mock_add:
            mock_add.side_effect = Exception("Network error")
            
            result = await enhanced_context_manager.scrape_web_content(
                url="https://example.com",
                organization_id="org-123",
                rag_feature="sales_intelligence",
                uploaded_by="user-123"
            )
            
            assert result is not None
            assert result.get('success') is False


class TestLogUploadLines524525:
    """Test log upload exception handling - lines 524-525"""
    
    @pytest.mark.asyncio
    async def test_log_upload_exception_path(self, enhanced_context_manager):
        """Test logging when exception occurs - covers lines 524-525"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            # Should not raise exception, just log
            await enhanced_context_manager._log_upload(
                organization_id='org-123',
                upload_type='file',
                rag_feature='sales_intelligence',
                items_count=10,
                success_count=8,
                error_count=2,
                upload_source='test',
                uploaded_by='user-123'
            )
            
            # If we get here, test passes


class TestAddContextItemLines551:
    """Test add_context_item exception path - line 551"""
    
    @pytest.mark.asyncio
    async def test_add_context_item_exception(self, enhanced_context_manager, mock_builder):
        """Test add_context_item when exception occurs"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.add_context_item({
                'organization_id': 'org-123',
                'rag_feature': 'sales_intelligence',
                'item_id': 'item-123',
                'item_type': 'knowledge_chunk',
                'item_title': 'Test',
                'item_content': 'Content'
            })
            
            assert result is not None
            assert result.get('success') is False


class TestBulkUploadLines600607:
    """Test bulk upload exception handling - lines 600-607"""
    
    @pytest.mark.asyncio
    async def test_bulk_api_upload_exception(self, enhanced_context_manager):
        """Test bulk upload when exception occurs - covers lines 600-607"""
        with patch.object(enhanced_context_manager, 'add_global_context_item') as mock_add:
            mock_add.side_effect = Exception("Connection error")
            
            result = await enhanced_context_manager.bulk_api_upload(
                items=[{'item_title': 'Test', 'item_content': 'Content'}],
                organization_id='org-123',
                rag_feature='sales_intelligence',
                uploaded_by='user-123'
            )
            
            assert result is not None
            assert result.get('success') is False


class TestShareToParentLines644651:
    """Test share to parent exception handling - lines 644-651"""
    
    @pytest.mark.asyncio
    async def test_share_to_parent_exception(self, enhanced_context_manager):
        """Test share to parent when exception occurs - covers lines 644-651"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.share_to_parent_organization(
                organization_id='org-123',
                rag_feature='sales_intelligence',
                item_id='item-123',
                shared_by='user-123'
            )
            
            assert result is not None
            assert result.get('success') is False


class TestShareToChildrenLines735742:
    """Test share to children exception handling - lines 735-742"""
    
    @pytest.mark.asyncio
    async def test_share_to_children_exception(self, enhanced_context_manager):
        """Test share to children when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.share_to_children_organizations(
                organization_id='org-123',
                rag_feature='sales_intelligence',
                item_id='item-123',
                shared_by='user-123'
            )
            
            assert result is not None
            assert result.get('success') is False


class TestGetPendingLines764771:
    """Test get pending approvals exception handling - lines 764-771"""
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals_exception(self, enhanced_context_manager):
        """Test get pending when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.get_pending_approvals('org-123')
            
            assert result is not None
            assert result.get('success') is False


class TestShareToParentNoData:
    """Test share to parent when no data returned - lines 644"""
    
    @pytest.mark.asyncio
    async def test_share_to_parent_no_data_returned(self, enhanced_context_manager):
        """Test share to parent when insert returns no data"""
        insert_result = Mock()
        insert_result.data = []
        
        chain = Mock()
        chain.insert.return_value = chain
        chain.execute.return_value = insert_result
        
        table = Mock()
        table.select = Mock()
        table.insert = Mock(return_value=chain)
        enhanced_context_manager.supabase.from_.return_value = table
        
        result = await enhanced_context_manager.share_to_parent_organization(
            organization_id='org-123',
            rag_feature='sales_intelligence',
            item_id='item-123',
            shared_by='user-123'
        )
        
        assert result is not None
        assert result.get('success') is False


class TestShareToChildrenNoData:
    """Test share to children when no data returned"""
    
    @pytest.mark.asyncio
    async def test_share_to_children_no_data(self, enhanced_context_manager, mock_builder):
        """Test share to children when returns no data"""
        # Setup empty children list
        mock_builder.setup_table_data('organizations', [])
        
        result = await enhanced_context_manager.share_to_children_organizations(
            organization_id='org-123',
            rag_feature='sales_intelligence',
            item_id='item-123',
            shared_by='user-123'
        )
        
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.enhanced_context_manager', '--cov-report=html'])

