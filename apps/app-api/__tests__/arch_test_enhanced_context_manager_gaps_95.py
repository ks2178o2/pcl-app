"""
Tests to cover remaining gaps in enhanced_context_manager.py to reach 95% coverage
Targeting missing lines: 91, 152, 178, 223, 250, 308->307, 326, 385-387, 485, 504-505, 524-525, 551, 566-607, 614-651, 661-668, 684-742, 749-771, 783-788
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from services.enhanced_context_manager import EnhancedContextManager


class TestEnhancedContextManagerGaps:
    """Test missing coverage in EnhancedContextManager"""
    
    @pytest.fixture
    def enhanced_manager(self):
        """Create enhanced context manager with mocked supabase"""
        with patch('services.enhanced_context_manager.get_supabase_client') as mock_get_client:
            mock_client = Mock()
            mock_client.from_.return_value = Mock()
            mock_get_client.return_value = mock_client
            return EnhancedContextManager()
    
    @pytest.mark.asyncio
    async def test_get_global_context_items_no_access(self, enhanced_manager):
        """Test line 91: No access to RAG feature"""
        # Need to properly mock the query chain for get_global_context_items
        # The method first queries tenant_context_access, then global_context_items
        access_check = Mock()
        access_check.data = []  # No access
        
        # Setup access query chain
        access_execute = Mock()
        access_execute.execute = Mock(return_value=access_check)
        
        access_eq3 = Mock()
        access_eq3.execute = Mock(return_value=access_check)
        
        access_eq2 = Mock()
        access_eq2.eq = Mock(return_value=access_eq3)
        
        access_eq1 = Mock()
        access_eq1.eq = Mock(return_value=access_eq2)
        
        access_select = Mock()
        access_select.eq = Mock(return_value=access_eq1)
        
        access_table = Mock()
        access_table.select = Mock(return_value=access_select)
        
        # Global items table (won't be queried)
        global_table = Mock()
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if table_name == 'tenant_context_access':
                return access_table
            else:
                return global_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.get_global_context_items(
            organization_id='org-123',
            rag_feature='feature1'
        )
        assert result['success'] is True
        assert result['items'] == []
        assert result['total_count'] == 0
        assert 'No access' in result['message']
    
    @pytest.mark.asyncio
    async def test_grant_tenant_access_failed(self, enhanced_manager):
        """Test line 152: Failed grant tenant access"""
        # Mock existing query returns no data (will create new)
        existing_result = Mock()
        existing_result.data = []
        
        # Mock insert returns no data
        insert_result = Mock()
        insert_result.data = None
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=existing_result)
        
        insert_chain = Mock()
        insert_chain.execute = Mock(return_value=insert_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        table_mock.insert = Mock(return_value=insert_chain)
        enhanced_manager.supabase.from_.return_value = table_mock
        
        result = await enhanced_manager.grant_tenant_access('org-123', 'feature1', 'read')
        assert result['success'] is False
        assert 'Failed to grant' in result['error']
    
    @pytest.mark.asyncio
    async def test_revoke_tenant_access_failed(self, enhanced_manager):
        """Test line 178: Failed revoke tenant access"""
        # Mock update returns no data
        update_result = Mock()
        update_result.data = None
        
        update_chain = Mock()
        update_chain.eq = Mock(return_value=update_chain)
        update_chain.execute = Mock(return_value=update_result)
        
        table_mock = Mock()
        table_mock.update = Mock(return_value=update_chain)
        enhanced_manager.supabase.from_.return_value = table_mock
        
        result = await enhanced_manager.revoke_tenant_access('org-123', 'feature1')
        assert result['success'] is False
        assert 'Failed to revoke' in result['error']
    
    @pytest.mark.asyncio
    async def test_share_context_item_failed_insert(self, enhanced_manager):
        """Test line 223: Failed create sharing request"""
        # Mock existing query returns no data
        existing_result = Mock()
        existing_result.data = []
        
        # Mock insert returns no data
        insert_result = Mock()
        insert_result.data = None
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=existing_result)
        
        insert_chain = Mock()
        insert_chain.execute = Mock(return_value=insert_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        table_mock.insert = Mock(return_value=insert_chain)
        enhanced_manager.supabase.from_.return_value = table_mock
        
        result = await enhanced_manager.share_context_item(
            'org-1', 'org-2', 'feature1', 'item-1', 'user-123'
        )
        assert result['success'] is False
        assert 'Failed to create' in result['error']
    
    @pytest.mark.asyncio
    async def test_approve_sharing_request_failed(self, enhanced_manager):
        """Test line 250: Failed approve sharing request"""
        # Mock update returns no data
        update_result = Mock()
        update_result.data = None
        
        update_chain = Mock()
        update_chain.eq = Mock(return_value=update_chain)
        update_chain.execute = Mock(return_value=update_result)
        
        table_mock = Mock()
        table_mock.update = Mock(return_value=update_chain)
        enhanced_manager.supabase.from_.return_value = table_mock
        
        result = await enhanced_manager.approve_sharing_request('sharing-123', 'user-123')
        assert result['success'] is False
        assert 'Failed to approve' in result['error']
    
    @pytest.mark.asyncio
    async def test_upload_file_content_with_sections(self, enhanced_manager):
        """Test lines 308->307, 326: File upload with sections and error handling"""
        file_content = "Section 1\n\nSection 2\n\nSection 3"
        
        # Mock add_context_item - first success, second fails, third success
        call_count = 0
        async def add_context_item_side_effect(item_data):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return {'success': False, 'error': 'Insert failed'}
            return {'success': True, 'item_id': f'item-{call_count}'}
        
        with patch.object(enhanced_manager, 'add_context_item', side_effect=add_context_item_side_effect):
            with patch.object(enhanced_manager, '_log_upload', new_callable=AsyncMock):
                result = await enhanced_manager.upload_file_content(
                    file_content, 'txt', 'org-123', 'feature1', 'user-123'
                )
                
                assert result['success'] is True
                assert result['success_count'] == 2  # 2 out of 3 succeeded
                assert result['error_count'] == 1  # 1 failed
                assert len(result['processed_items']) == 2
        
        # Test with empty sections (to trigger line 308->307 branch where section.strip() is False)
        file_content_empty = "\n\n\n"  # Only whitespace/newlines
        
        with patch.object(enhanced_manager, 'add_context_item', return_value={'success': True, 'item_id': 'item-1'}):
            with patch.object(enhanced_manager, '_log_upload', new_callable=AsyncMock):
                result = await enhanced_manager.upload_file_content(
                    file_content_empty, 'txt', 'org-123', 'feature1', 'user-123'
                )
                
                assert result['success'] is True
                assert result['success_count'] == 0  # No sections processed
                assert result['error_count'] == 0
    
    @pytest.mark.asyncio
    async def test_scrape_web_content_exception(self, enhanced_manager):
        """Test lines 385-387: Exception in scrape_web_content"""
        with patch.object(enhanced_manager, 'add_context_item', side_effect=Exception("DB error")):
            result = await enhanced_manager.scrape_web_content(
                'https://example.com', 'org-123', 'feature1', 'user-123'
            )
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_update_organization_quotas_failed(self, enhanced_manager):
        """Test line 485: Failed update quotas"""
        # Mock update returns no data
        update_result = Mock()
        update_result.data = None
        
        update_chain = Mock()
        update_chain.eq = Mock(return_value=update_chain)
        update_chain.execute = Mock(return_value=update_result)
        
        table_mock = Mock()
        table_mock.update = Mock(return_value=update_chain)
        enhanced_manager.supabase.from_.return_value = table_mock
        
        result = await enhanced_manager.update_organization_quotas('org-123', {'max_context_items': 2000})
        assert result['success'] is False
        assert 'Failed to update' in result['error']
    
    @pytest.mark.asyncio
    async def test_check_global_duplicate_item_exception(self, enhanced_manager):
        """Test lines 504-505: Exception in _check_global_duplicate_item"""
        enhanced_manager.supabase.from_.return_value.select.side_effect = Exception("DB error")
        
        result = await enhanced_manager._check_global_duplicate_item('item-1')
        assert result is False
    
    @pytest.mark.asyncio
    async def test_log_upload_exception(self, enhanced_manager):
        """Test lines 524-525: Exception in _log_upload"""
        enhanced_manager.supabase.from_.return_value.insert.side_effect = Exception("DB error")
        
        # Should not raise, just log error
        await enhanced_manager._log_upload(
            'org-123', 'api', 'feature1', 10, 10, 0, 'source', 'user-123'
        )
        # No assertion needed - method should handle exception gracefully
    
    @pytest.mark.asyncio
    async def test_add_context_item_failed_insert(self, enhanced_manager):
        """Test line 551: Failed create context item"""
        # Mock insert returns no data
        insert_result = Mock()
        insert_result.data = None
        
        insert_chain = Mock()
        insert_chain.execute = Mock(return_value=insert_result)
        
        table_mock = Mock()
        table_mock.insert = Mock(return_value=insert_chain)
        enhanced_manager.supabase.from_.return_value = table_mock
        
        context_data = {
            'organization_id': 'org-123',
            'rag_feature': 'feature1',
            'item_id': 'item-1',
            'item_type': 'type',
            'item_title': 'Title',
            'item_content': 'Content'
        }
        
        result = await enhanced_manager.add_context_item(context_data)
        assert result['success'] is False
        assert 'Failed to create' in result['error']
    
    @pytest.mark.asyncio
    async def test_share_to_children_all_scenarios(self, enhanced_manager):
        """Test lines 566-607: share_to_children method"""
        # Test no children
        children_result = Mock()
        children_result.data = []
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=children_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        enhanced_manager.supabase.from_.return_value = table_mock
        
        result = await enhanced_manager.share_to_children('org-parent', 'item-1', 'feature1', 'user-123')
        assert result['success'] is True
        assert result['shared_count'] == 0
        
        # Test with children
        children_result.data = [{'id': 'child-1'}, {'id': 'child-2'}]
        
        # Mock insert returns data
        insert_result = Mock()
        insert_result.data = [{'id': 'share-1'}, {'id': 'share-2'}]
        
        insert_chain = Mock()
        insert_chain.execute = Mock(return_value=insert_result)
        
        table_mock2 = Mock()
        table_mock2.select = Mock(return_value=select_chain)
        table_mock2.insert = Mock(return_value=insert_chain)
        enhanced_manager.supabase.from_.return_value = table_mock2
        
        result = await enhanced_manager.share_to_children('org-parent', 'item-1', 'feature1', 'user-123')
        assert result['success'] is True
        assert result['shared_count'] == 2
        
        # Test failed insert
        insert_result.data = None
        result = await enhanced_manager.share_to_children('org-parent', 'item-1', 'feature1', 'user-123')
        assert result['success'] is False
        
        # Test exception
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        result = await enhanced_manager.share_to_children('org-parent', 'item-1', 'feature1', 'user-123')
        assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_share_to_parent_all_scenarios(self, enhanced_manager):
        """Test lines 614-651: share_to_parent method"""
        # Test no parent
        org_result = Mock()
        org_result.data = [{'parent_organization_id': None}]
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=org_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        enhanced_manager.supabase.from_.return_value = table_mock
        
        result = await enhanced_manager.share_to_parent('org-child', 'item-1', 'feature1', 'user-123')
        assert result['success'] is False
        assert 'No parent organization' in result['error']
        
        # Test org not found
        org_result.data = []
        result = await enhanced_manager.share_to_parent('org-child', 'item-1', 'feature1', 'user-123')
        assert result['success'] is False
        
        # Test with parent
        org_result.data = [{'parent_organization_id': 'org-parent'}]
        
        insert_result = Mock()
        insert_result.data = [{'id': 'share-1'}]
        
        insert_chain = Mock()
        insert_chain.execute = Mock(return_value=insert_result)
        
        table_mock2 = Mock()
        table_mock2.select = Mock(return_value=select_chain)
        table_mock2.insert = Mock(return_value=insert_chain)
        enhanced_manager.supabase.from_.return_value = table_mock2
        
        result = await enhanced_manager.share_to_parent('org-child', 'item-1', 'feature1', 'user-123')
        assert result['success'] is True
        assert result['sharing_id'] == 'share-1'
        
        # Test failed insert
        insert_result.data = None
        result = await enhanced_manager.share_to_parent('org-child', 'item-1', 'feature1', 'user-123')
        assert result['success'] is False
        
        # Test exception
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        result = await enhanced_manager.share_to_parent('org-child', 'item-1', 'feature1', 'user-123')
        assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals_all_scenarios(self, enhanced_manager):
        """Test lines 661-668: get_pending_approvals branches"""
        # Test with pending requests
        result_data = [{'id': 'req-1'}, {'id': 'req-2'}]
        query_result = Mock()
        query_result.data = result_data
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=query_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        enhanced_manager.supabase.from_.return_value = table_mock
        
        result = await enhanced_manager.get_pending_approvals('org-123')
        assert result['success'] is True
        assert len(result['pending_requests']) == 2
        assert result['count'] == 2
        
        # Test no pending requests
        query_result.data = []
        result = await enhanced_manager.get_pending_approvals('org-123')
        assert result['success'] is True
        assert result['pending_requests'] == []
        assert result['count'] == 0
        
        # Test exception
        table_mock.select.side_effect = Exception("DB error")
        result = await enhanced_manager.get_pending_approvals('org-123')
        assert result['success'] is False
        assert result['pending_requests'] == []
    
    @pytest.mark.asyncio
    async def test_approve_shared_item_all_scenarios(self, enhanced_manager):
        """Test lines 684-742: approve_shared_item method"""
        # Test failed update
        update_result = Mock()
        update_result.data = None
        
        update_chain = Mock()
        update_chain.eq = Mock(return_value=update_chain)
        update_chain.execute = Mock(return_value=update_result)
        
        table_mock = Mock()
        table_mock.update = Mock(return_value=update_chain)
        enhanced_manager.supabase.from_.return_value = table_mock
        
        result = await enhanced_manager.approve_shared_item('sharing-123', 'user-123')
        assert result['success'] is False
        assert 'Failed to approve' in result['error']
        
        # Test successful update but item not found
        update_result.data = [{'id': 'share-1', 'item_id': 'item-1', 'target_organization_id': 'org-2', 'rag_feature': 'feature1', 'source_organization_id': 'org-1'}]
        
        item_result = Mock()
        item_result.data = []  # Item not found
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            table = Mock()
            if call_count == 1:
                table.update = Mock(return_value=update_chain)
            elif call_count == 2:
                select_chain = Mock()
                select_chain.eq = Mock(return_value=select_chain)
                select_chain.execute = Mock(return_value=item_result)
                table.select = Mock(return_value=select_chain)
            return table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.approve_shared_item('sharing-123', 'user-123')
        assert result['success'] is False
        assert 'Original item not found' in result['error']
        
        # Test successful approval with item copy
        item_result.data = [{'id': 'item-1', 'title': 'Test', 'content': 'Content', 'item_type': 'type'}]
        
        insert_result = Mock()
        insert_result.data = [{'id': 'new-item-1'}]
        
        call_count = 0
        def from_side_effect2(table_name):
            nonlocal call_count
            call_count += 1
            table = Mock()
            if call_count == 1:
                table.update = Mock(return_value=update_chain)
            elif call_count == 2:
                select_chain = Mock()
                select_chain.eq = Mock(return_value=select_chain)
                select_chain.execute = Mock(return_value=item_result)
                table.select = Mock(return_value=select_chain)
            elif call_count == 3:
                insert_chain = Mock()
                insert_chain.execute = Mock(return_value=insert_result)
                table.insert = Mock(return_value=insert_chain)
            return table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect2
        
        result = await enhanced_manager.approve_shared_item('sharing-123', 'user-123')
        assert result['success'] is True
        assert result['new_item_id'] == 'new-item-1'
        
        # Test failed insert
        insert_result.data = None
        
        call_count = 0
        enhanced_manager.supabase.from_.side_effect = from_side_effect2
        
        result = await enhanced_manager.approve_shared_item('sharing-123', 'user-123')
        assert result['success'] is False
        assert 'Failed to copy item' in result['error']
        
        # Test exception
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        result = await enhanced_manager.approve_shared_item('sharing-123', 'user-123')
        assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_reject_shared_item_all_scenarios(self, enhanced_manager):
        """Test lines 749-771: reject_shared_item method"""
        # Test successful reject
        update_result = Mock()
        update_result.data = [{'id': 'share-1'}]
        
        update_chain = Mock()
        update_chain.eq = Mock(return_value=update_chain)
        update_chain.execute = Mock(return_value=update_result)
        
        table_mock = Mock()
        table_mock.update = Mock(return_value=update_chain)
        enhanced_manager.supabase.from_.return_value = table_mock
        
        result = await enhanced_manager.reject_shared_item('sharing-123', 'user-123', 'Not needed')
        assert result['success'] is True
        assert result['rejected_id'] == 'sharing-123'
        
        # Test failed update
        update_result.data = None
        result = await enhanced_manager.reject_shared_item('sharing-123', 'user-123')
        assert result['success'] is False
        assert 'Failed to reject' in result['error']
        
        # Test exception
        table_mock.update.side_effect = Exception("DB error")
        result = await enhanced_manager.reject_shared_item('sharing-123', 'user-123')
        assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_hierarchy_sharing_stats_all_scenarios(self, enhanced_manager):
        """Test lines 783-788: get_hierarchy_sharing_stats method"""
        # Mock all count queries
        outgoing_result = Mock()
        outgoing_result.count = 5
        
        incoming_result = Mock()
        incoming_result.count = 3
        
        pending_result = Mock()
        pending_result.count = 2
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            table = Mock()
            select_chain = Mock()
            select_chain.eq = Mock(return_value=select_chain)
            
            if call_count == 1:
                select_chain.execute = Mock(return_value=outgoing_result)
            elif call_count == 2:
                select_chain.execute = Mock(return_value=incoming_result)
            else:
                select_chain.execute = Mock(return_value=pending_result)
            
            table.select = Mock(return_value=select_chain)
            return table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.get_hierarchy_sharing_stats('org-123')
        assert result['success'] is True
        assert result['stats']['outgoing_shares'] == 5
        assert result['stats']['incoming_shares'] == 3
        assert result['stats']['pending_approvals'] == 2
        
        # Test with None counts
        outgoing_result.count = None
        incoming_result.count = None
        pending_result.count = None
        
        call_count = 0
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.get_hierarchy_sharing_stats('org-123')
        assert result['success'] is True
        assert result['stats']['outgoing_shares'] == 0
        assert result['stats']['incoming_shares'] == 0
        assert result['stats']['pending_approvals'] == 0
        
        # Test exception
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        result = await enhanced_manager.get_hierarchy_sharing_stats('org-123')
        assert result['success'] is False
        assert result['stats']['outgoing_shares'] == 0

