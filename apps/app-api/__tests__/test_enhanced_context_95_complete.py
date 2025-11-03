# apps/app-api/__tests__/test_enhanced_context_95_complete.py
"""
Final tests to reach 95% coverage for Enhanced Context Manager
Target: Missing lines and edge cases
"""

import pytest
from unittest.mock import Mock, patch
from services.enhanced_context_manager import EnhancedContextManager
from test_utils import SupabaseMockBuilder, TestDataFactory


@pytest.fixture
def mock_builder():
    return SupabaseMockBuilder()


@pytest.fixture
def enhanced_context_manager(mock_builder):
    with patch('services.enhanced_context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return EnhancedContextManager()


class TestDuplicateItemHandling:
    """Test duplicate item detection and error handling"""
    
    @pytest.mark.asyncio
    async def test_add_global_context_duplicate_item(self, enhanced_context_manager, mock_builder):
        """Test adding global context item when item already exists"""
        # Setup to return existing item
        mock_builder.setup_table_data('global_context_items', [{'id': 'existing-123', 'item_id': 'duplicate-123'}])
        
        context_data = {
            'item_id': 'duplicate-123',
            'rag_feature': 'sales_intelligence',
            'item_type': 'knowledge_chunk',
            'item_title': 'Test',
            'item_content': 'Content'
        }
        
        result = await enhanced_context_manager.add_global_context_item(context_data)
        
        assert result is not None
        assert result.get('success') is False
        assert 'already exists' in result.get('error', '').lower()
    
    @pytest.mark.asyncio
    async def test_add_global_context_insert_failure(self, enhanced_context_manager, mock_builder):
        """Test adding global context when insert fails"""
        # No existing items
        mock_builder.setup_table_data('global_context_items', [])
        mock_builder.insert_response.data = []  # No data returned from insert
        
        context_data = {
            'item_id': 'new-item-123',
            'rag_feature': 'sales_intelligence',
            'item_type': 'knowledge_chunk',
            'item_title': 'Test',
            'item_content': 'Content'
        }
        
        result = await enhanced_context_manager.add_global_context_item(context_data)
        
        assert result is not None
        assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_add_global_context_exception_path(self, enhanced_context_manager):
        """Test add global context when exception occurs"""
        with patch.object(enhanced_context_manager, '_check_global_duplicate_item') as mock_check:
            mock_check.side_effect = Exception("Database error")
            
            context_data = {
                'item_id': 'test-123',
                'rag_feature': 'sales_intelligence',
                'item_type': 'knowledge_chunk',
                'item_title': 'Test',
                'item_content': 'Content'
            }
            
            result = await enhanced_context_manager.add_global_context_item(context_data)
            
            assert result is not None
            assert result.get('success') is False


class TestSharingRequestHandling:
    """Test sharing request error paths"""
    
    @pytest.mark.asyncio
    async def test_share_context_item_insert_failure(self, enhanced_context_manager, mock_builder):
        """Test share when insert returns no data"""
        mock_builder.setup_table_data('global_context_items', [{'id': 'item-123'}])
        mock_builder.insert_response.data = []
        
        result = await enhanced_context_manager.share_context_item(
            item_id='item-123',
            target_organization_id='org-target',
            shared_by='user-123',
            reason='Test'
        )
        
        assert result is not None
        assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_approve_sharing_no_data_returned(self, enhanced_context_manager, mock_builder):
        """Test approve when update returns no data"""
        mock_builder.setup_table_data('context_sharing', [{'id': 'share-123', 'status': 'pending'}])
        mock_builder.update_response.data = []
        
        result = await enhanced_context_manager.approve_sharing_request(
            sharing_id='share-123',
            approved_by='user-123'
        )
        
        assert result is not None
        assert result.get('success') is False


class TestGlobalContextAccess:
    """Test global context item access scenarios"""
    
    @pytest.mark.asyncio
    async def test_get_global_context_no_access(self, enhanced_context_manager, mock_builder):
        """Test get global items when org has no access"""
        mock_builder.setup_table_data('global_context_items', [{'id': 'item-123'}])
        mock_builder.setup_table_data('tenant_context_access', [])  # No access
        
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature='sales_intelligence',
            organization_id='org-no-access',
            limit=100,
            offset=0
        )
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_get_global_context_with_pagination(self, enhanced_context_manager, mock_builder):
        """Test get global items with pagination"""
        items = [{'id': f'item-{i}'} for i in range(20)]
        mock_builder.setup_table_data('global_context_items', items)
        
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature='sales_intelligence',
            organization_id='org-123',
            limit=10,
            offset=0
        )
        
        assert result is not None
        assert result.get('success') is True


class TestWebScrapingAndBulkUpload:
    """Test web scraping and bulk upload error paths"""
    
    @pytest.mark.asyncio
    async def test_scrape_web_content_no_requests(self, enhanced_context_manager, mock_builder):
        """Test scrape when requests module not available"""
        # This will test the error path when requests.get fails
        with patch('requests.get') as mock_get:
            mock_get.side_effect = ImportError("No module named 'requests'")
            
            result = await enhanced_context_manager.scrape_web_content(
                url="https://example.com",
                organization_id="org-123",
                rag_feature="sales_intelligence",
                uploaded_by="user-123"
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_bulk_api_upload_partial_failures(self, enhanced_context_manager, mock_builder):
        """Test bulk upload when some items fail"""
        with patch.object(enhanced_context_manager, 'add_global_context_item') as mock_add:
            # First succeeds, second fails
            mock_add.side_effect = [
                {'success': True, 'item_id': 'item-1'},
                {'success': False, 'error': 'Failed'}
            ]
            
            result = await enhanced_context_manager.bulk_api_upload(
                items=[
                    {'item_title': 'Test 1', 'item_content': 'Content 1'},
                    {'item_title': 'Test 2', 'item_content': 'Content 2'}
                ],
                organization_id='org-123',
                rag_feature='sales_intelligence',
                uploaded_by='user-123'
            )
            
            assert result is not None


class TestQuotaAndStatistics:
    """Test quota management and statistics"""
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_not_found(self, enhanced_context_manager, mock_builder):
        """Test get quotas when organization has none"""
        mock_builder.setup_table_data('organization_quotas', [])
        
        result = await enhanced_context_manager.get_organization_quotas('org-123')
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_update_organization_quotas_failure(self, enhanced_context_manager, mock_builder):
        """Test update quotas when update fails"""
        mock_builder.setup_table_data('organization_quotas', [{'organization_id': 'org-123'}])
        mock_builder.update_response.data = []
        
        result = await enhanced_context_manager.update_organization_quotas(
            organization_id='org-123',
            quotas={'max_context_items': 1000}
        )
        
        assert result is not None
        assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals_empty(self, enhanced_context_manager, mock_builder):
        """Test get pending approvals when none exist"""
        mock_builder.setup_table_data('context_sharing', [])
        
        result = await enhanced_context_manager.get_pending_approvals('org-123')
        
        assert result is not None
        assert result.get('success') is True
        assert len(result.get('pending_requests', [])) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.enhanced_context_manager', '--cov-report=html'])

