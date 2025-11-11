# apps/app-api/__tests__/test_enhanced_context_coverage_gaps.py
"""
Test suite to cover remaining gaps in Enhanced Context Manager
Target: Reach 95% coverage
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


class TestEnhancedContextAccessControl:
    """Test access control and filtering logic"""
    
    @pytest.mark.asyncio
    async def test_get_global_context_with_access_check(self, enhanced_context_manager, mock_builder):
        """Test getting global context with access check"""
        mock_builder.setup_table_data('tenant_context_access', [{'enabled': True}])
        mock_builder.setup_table_data('global_context_items', [])
        
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature="sales_intelligence",
            organization_id="org-123"
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_global_context_no_access(self, enhanced_context_manager, mock_builder):
        """Test getting global context without access"""
        mock_builder.setup_table_data('tenant_context_access', [])
        mock_builder.setup_table_data('global_context_items', [])
        
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature="sales_intelligence",
            organization_id="org-123"
        )
        assert result is not None
        assert result.get('message') == "No access to this RAG feature"
    
    @pytest.mark.asyncio
    async def test_get_global_context_with_pagination(self, enhanced_context_manager, mock_builder):
        """Test getting global context with pagination"""
        large_dataset = [{'id': f'item-{i}'} for i in range(200)]
        mock_builder.setup_table_data('tenant_context_access', [{'enabled': True}])
        mock_builder.setup_table_data('global_context_items', large_dataset)
        
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature="sales_intelligence",
            organization_id="org-123",
            limit=50,
            offset=0
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_global_context_without_rag_feature_filter(self, enhanced_context_manager, mock_builder):
        """Test getting all global context without RAG feature filter"""
        items = [{'id': 'item-1'}, {'id': 'item-2'}]
        mock_builder.setup_table_data('global_context_items', items)
        
        result = await enhanced_context_manager.get_global_context_items()
        assert result is not None


class TestEnhancedContextShareContext:
    """Test sharing context between organizations"""
    
    @pytest.mark.asyncio
    async def test_share_context_item_read_only(self, enhanced_context_manager, mock_builder):
        """Test sharing context item with read-only access"""
        mock_builder.setup_table_data('context_sharing', [])
        mock_builder.insert_response.data = [{'id': 'sharing-id'}]
        
        result = await enhanced_context_manager.share_context_item(
            source_org_id="org-123",
            target_org_id="org-456",
            rag_feature="sales_intelligence",
            item_id="item-123",
            shared_by="user-123",
            sharing_type="read_only"
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_share_context_item_read_write(self, enhanced_context_manager, mock_builder):
        """Test sharing context item with read-write access"""
        mock_builder.setup_table_data('context_sharing', [])
        mock_builder.insert_response.data = [{'id': 'sharing-id'}]
        
        result = await enhanced_context_manager.share_context_item(
            source_org_id="org-123",
            target_org_id="org-456",
            rag_feature="sales_intelligence",
            item_id="item-123",
            shared_by="user-123",
            sharing_type="read_write"
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_shared_context_items_with_filter(self, enhanced_context_manager, mock_builder):
        """Test getting shared items with RAG feature filter"""
        shared_items = [
            {'id': 'item-1', 'rag_feature': 'sales_intelligence'},
            {'id': 'item-2', 'rag_feature': 'customer_insights'}
        ]
        mock_builder.setup_table_data('context_sharing', shared_items)
        
        result = await enhanced_context_manager.get_shared_context_items(
            organization_id="org-456",
            rag_feature="sales_intelligence"
        )
        assert result is not None


class TestEnhancedContextUploadProcessing:
    """Test upload content processing"""
    
    @pytest.mark.asyncio
    async def test_upload_file_content_processing(self, enhanced_context_manager, mock_builder):
        """Test file content processing logic"""
        mock_builder.setup_table_data('rag_context_items', [])
        mock_builder.insert_response.data = [{'id': 'new-item'}]
        
        result = await enhanced_context_manager.upload_file_content(
            file_content="Test content with keywords: sales, revenue, growth",
            file_type="text/plain",
            organization_id="org-123",
            rag_feature="sales_intelligence",
            uploaded_by="user-123"
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_scrape_web_content_processing(self, enhanced_context_manager, mock_builder):
        """Test web content scraping processing"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        result = await enhanced_context_manager.scrape_web_content(
            url="https://example.com/article",
            organization_id="org-123",
            rag_feature="sales_intelligence",
            uploaded_by="user-123"
        )
        assert result is not None


class TestEnhancedContextApprovalWorkflows:
    """Test approval workflow logic"""
    
    @pytest.mark.asyncio
    async def test_approve_shared_item_with_item_data(self, enhanced_context_manager, mock_builder):
        """Test approving with complete item data"""
        sharing_data = [{
            'id': 'sharing-123',
            'item_id': 'item-123',
            'target_organization_id': 'org-456',
            'rag_feature': 'sales_intelligence',
            'source_organization_id': 'org-123'
        }]
        
        item_data = [{
            'title': 'Test Title',
            'content': 'Test Content',
            'item_type': 'knowledge_chunk',
            'metadata': {'source': 'shared'}
        }]
        
        mock_builder.setup_table_data('context_sharing', sharing_data)
        mock_builder.setup_table_data('context_items', item_data)
        mock_builder.update_response.data = sharing_data
        mock_builder.insert_response.data = [{'id': 'new-item'}]
        
        result = await enhanced_context_manager.approve_shared_item("sharing-123", "user-123")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_reject_shared_item_with_reason(self, enhanced_context_manager, mock_builder):
        """Test rejecting with reason"""
        mock_builder.setup_table_data('context_sharing', [])
        mock_builder.update_response.data = [{'id': 'sharing-123'}]
        
        result = await enhanced_context_manager.reject_shared_item(
            sharing_id="sharing-123",
            rejected_by="user-123",
            reason="Content not suitable"
        )
        assert result is not None


class TestEnhancedContextStatistics:
    """Test statistics and aggregation"""
    
    @pytest.mark.asyncio
    async def test_get_hierarchy_sharing_stats_detailed(self, enhanced_context_manager, mock_builder):
        """Test getting detailed hierarchy stats"""
        # Set up complex mocking for count operations
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            def side_effect(table):
                if table == 'context_sharing':
                    mock = Mock()
                    count_mock = Mock()
                    count_mock.count = 5 if 'source' in str(mock_from.call_args) else 3
                    query_mock = Mock()
                    query_mock.eq.return_value = query_mock
                    query_mock.execute.return_value = count_mock
                    mock.select.return_value = query_mock
                    return mock
                return Mock()
            
            mock_from.side_effect = side_effect
            result = await enhanced_context_manager.get_hierarchy_sharing_stats("org-123")
            assert result is not None


class TestEnhancedContextErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_get_global_context_database_error(self, enhanced_context_manager, mock_builder):
        """Test handling database errors"""
        mock_builder.setup_error_response('global_context_items', "Database error")
        
        result = await enhanced_context_manager.get_global_context_items()
        assert result is not None
        assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_grant_access_database_error(self, enhanced_context_manager, mock_builder):
        """Test handling errors when granting access"""
        mock_builder.setup_error_response('tenant_context_access', "Insert error")
        
        result = await enhanced_context_manager.grant_tenant_access(
            organization_id="org-123",
            rag_feature="sales_intelligence",
            access_level="read"
        )
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.enhanced_context_manager', '--cov-report=html'])

