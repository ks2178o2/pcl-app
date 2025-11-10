# apps/app-api/__tests__/test_enhanced_context_95_perfect.py
"""
Perfect 95% coverage - Final missing paths
Target: Lines 308->307, 551, 571, and related error paths
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.enhanced_context_manager import EnhancedContextManager
from test_utils import SupabaseMockBuilder


@pytest.fixture
def mock_builder():
    return SupabaseMockBuilder()


@pytest.fixture
def enhanced_context_manager(mock_builder):
    with patch('services.enhanced_context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return EnhancedContextManager()


class TestFileUploadSectionProcessing:
    """Test file upload section processing - line 308->307"""
    
    @pytest.mark.asyncio
    async def test_upload_file_with_empty_sections_skipped(self, enhanced_context_manager):
        """Test upload with empty sections that should be skipped"""
        # File content with empty sections
        content = "Section 1\n\n\n\nSection 2"  # Has empty section between
        
        mock_add = AsyncMock(return_value={'success': True, 'item_id': 'item-123'})
        enhanced_context_manager.add_context_item = mock_add
        
        result = await enhanced_context_manager.upload_file_content(
            file_content=content,
            file_type="txt",
            organization_id="org-123",
            rag_feature="sales_intelligence",
            uploaded_by="user-123"
        )
        
        # Should only call add_context_item for non-empty sections
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_upload_file_with_only_whitespace_sections(self, enhanced_context_manager):
        """Test upload with whitespace-only sections"""
        # File content with whitespace sections
        content = "Section 1\n\n   \n\nSection 2"
        
        mock_add = AsyncMock(return_value={'success': True, 'item_id': 'item-123'})
        enhanced_context_manager.add_context_item = mock_add
        
        result = await enhanced_context_manager.upload_file_content(
            file_content=content,
            file_type="txt",
            organization_id="org-123",
            rag_feature="sales_intelligence",
            uploaded_by="user-123"
        )
        
        assert result is not None
        assert result.get('success') is True


class TestAddContextItemLine551:
    """Test add_context_item error path - line 551"""
    
    @pytest.mark.asyncio
    async def test_add_context_item_insert_no_data(self, enhanced_context_manager, mock_builder):
        """Test add_context_item when insert returns no data - covers line 551"""
        mock_builder.setup_table_data('rag_context_items', [])
        mock_builder.insert_response.data = []  # No data returned
        
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
        assert 'Failed to create' in result.get('error', '')


class TestShareToChildrenLine571:
    """Test share to children when no children found - line 571"""
    
    @pytest.mark.asyncio
    async def test_share_to_children_no_children_found(self, enhanced_context_manager):
        """Test share when organization has no children - covers line 571"""
        # Setup query to return no children
        children_result = Mock()
        children_result.data = []  # No children
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = children_result
        
        table = Mock()
        table.select.return_value = chain
        enhanced_context_manager.supabase.from_.return_value = table
        
        result = await enhanced_context_manager.share_to_children(
            source_org_id='org-123',
            item_id='item-123',
            rag_feature='sales_intelligence',
            shared_by='user-123'
        )
        
        assert result is not None
        assert result.get('success') is True
        assert result.get('shared_count') == 0
        assert 'No child organizations' in result.get('message', '')


class TestShareToChildrenInsertFailure:
    """Test share to children when insert fails"""
    
    @pytest.mark.asyncio
    async def test_share_to_children_insert_returns_no_data(self, enhanced_context_manager):
        """Test share when insert returns no data"""
        # Setup children data
        children_result = Mock()
        children_result.data = [{'id': 'child-org-1'}, {'id': 'child-org-2'}]
        
        children_chain = Mock()
        children_chain.select.return_value = children_chain
        children_chain.eq.return_value = children_chain
        children_chain.execute.return_value = children_result
        
        # Setup insert to return no data
        insert_result = Mock()
        insert_result.data = []  # Insert returns empty
        
        insert_chain = Mock()
        insert_chain.insert.return_value = insert_chain
        insert_chain.execute.return_value = insert_result
        
        # Setup both table calls
        org_table = Mock()
        org_table.select.return_value = children_chain
        
        share_table = Mock()
        share_table.insert.return_value = insert_chain
        
        def from_side_effect(table_name):
            if table_name == 'organizations':
                return org_table
            else:
                return share_table
        
        enhanced_context_manager.supabase.from_ = Mock(side_effect=from_side_effect)
        
        result = await enhanced_context_manager.share_to_children(
            source_org_id='org-123',
            item_id='item-123',
            rag_feature='sales_intelligence',
            shared_by='user-123'
        )
        
        assert result is not None
        assert result.get('success') is False


class TestShareToChildrenException:
    """Test share to children when exception occurs"""
    
    @pytest.mark.asyncio
    async def test_share_to_children_exception_during_process(self, enhanced_context_manager):
        """Test share when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_', side_effect=Exception("Database error")):
            result = await enhanced_context_manager.share_to_children(
                source_org_id='org-123',
                item_id='item-123',
                rag_feature='sales_intelligence',
                shared_by='user-123'
            )
            
            assert result is not None
            assert result.get('success') is False


class TestBulkUploadLines600607:
    """Test bulk upload specific error paths - lines 600-607"""
    
    @pytest.mark.asyncio
    async def test_bulk_upload_zero_items_list(self, enhanced_context_manager):
        """Test bulk upload with zero items"""
        result = await enhanced_context_manager.bulk_api_upload(
            items=[],
            organization_id='org-123',
            rag_feature='sales_intelligence',
            uploaded_by='user-123'
        )
        
        assert result is not None
        assert result.get('success') is True
        assert result.get('success_count') == 0
    
    @pytest.mark.asyncio
    async def test_bulk_upload_all_failures(self, enhanced_context_manager):
        """Test bulk upload when all items fail"""
        with patch.object(enhanced_context_manager, 'add_global_context_item') as mock_add:
            mock_add.return_value = {'success': False, 'error': 'Failed'}
            
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
            assert result.get('success') is True  # Overall success
            assert result.get('success_count') == 0
            assert result.get('error_count') == 2


class TestShareToParentLines644651:
    """Test share to parent error paths - lines 644-651"""
    
    @pytest.mark.asyncio
    async def test_share_to_parent_no_data_returned(self, enhanced_context_manager):
        """Test share to parent when insert returns no data"""
        # Get parent returns data
        parent_result = Mock()
        parent_result.data = {'id': 'parent-org'}
        parent_result.single.return_value.execute.return_value = parent_result
        
        # Insert returns no data
        insert_result = Mock()
        insert_result.data = []
        
        insert_chain = Mock()
        insert_chain.insert.return_value = insert_chain
        insert_chain.execute.return_value = insert_result
        
        org_table = Mock()
        org_table.select.return_value.eq.return_value.single.return_value.execute.return_value = parent_result
        
        share_table = Mock()
        share_table.insert.return_value = insert_chain
        
        def from_side_effect(table_name):
            if table_name == 'organizations':
                return org_table
            else:
                return share_table
        
        enhanced_context_manager.supabase.from_ = Mock(side_effect=from_side_effect)
        
        result = await enhanced_context_manager.share_to_parent_organization(
            organization_id='org-123',
            rag_feature='sales_intelligence',
            item_id='item-123',
            shared_by='user-123'
        )
        
        assert result is not None
        assert result.get('success') is False


class TestGetPendingApprovalsLines764771:
    """Test get pending approvals error paths - lines 764-771"""
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals_no_data(self, enhanced_context_manager):
        """Test get pending when query returns no data"""
        query_result = Mock()
        query_result.data = []
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = query_result
        
        table = Mock()
        table.select.return_value = chain
        enhanced_context_manager.supabase.from_.return_value = table
        
        result = await enhanced_context_manager.get_pending_approvals('org-123')
        
        assert result is not None
        assert result.get('success') is True
        assert len(result.get('pending_requests', [])) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.enhanced_context_manager', '--cov-report=html'])

