# apps/app-api/__tests__/test_context_manager_95_coverage.py
"""
Tests to push Context Manager coverage from 56.91% to 95%
Targeting missing lines: 26, 31, 46, 60-67, 75-100, 108-140, etc.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from services.context_manager import ContextManager


class TestContextManager95Coverage:
    """Tests to reach 95% coverage for Context Manager"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager with mocked supabase"""
        with patch('services.context_manager.get_supabase_client') as mock_get_client:
            mock_client = Mock()
            table_mock = Mock()
            
            # Setup basic chains
            insert_result = Mock()
            insert_result.data = [{'id': 'test-id'}]
            table_mock.insert.return_value.execute.return_value = insert_result
            
            select_result = Mock()
            select_result.data = []
            select_chain = Mock()
            select_chain.eq = Mock(return_value=select_chain)
            select_chain.order = Mock(return_value=select_chain)
            select_chain.execute = Mock(return_value=select_result)
            table_mock.select.return_value = select_chain
            
            update_result = Mock()
            update_result.data = [{'id': 'updated-id'}]
            update_chain = Mock()
            update_chain.eq = Mock(return_value=update_chain)
            update_chain.execute = Mock(return_value=update_result)
            table_mock.update.return_value = update_chain
            
            delete_result = Mock()
            delete_result.data = []
            delete_chain = Mock()
            delete_chain.eq = Mock(return_value=delete_chain)
            delete_chain.execute = Mock(return_value=delete_result)
            table_mock.delete.return_value = delete_chain
            
            mock_client.from_.return_value = table_mock
            mock_get_client.return_value = mock_client
            
            return ContextManager()
    
    # Test validation error (line 26)
    @pytest.mark.asyncio
    async def test_add_context_item_validation_error(self, context_manager):
        """Test add with invalid data - line 26"""
        context_data = {
            'organization_id': 'org-123',
            'rag_feature': 'test'
            # Missing required fields
        }
        
        result = await context_manager.add_context_item(context_data)
        assert result['success'] is False
        assert 'error' in result
    
    # Test confidence score validation (line 31)
    @pytest.mark.asyncio
    async def test_add_context_item_invalid_confidence(self, context_manager):
        """Test add with invalid confidence score - line 31"""
        context_data = {
            'organization_id': 'org-123',
            'rag_feature': 'feature',
            'item_id': 'test-1',
            'item_type': 'type',
            'item_title': 'Test',
            'item_content': 'Content',
            'confidence_score': 1.5  # Invalid (>1)
        }
        
        result = await context_manager.add_context_item(context_data)
        assert result['success'] is False
        assert 'Confidence score must be between 0 and 1' in result['error']
    
    # Test duplicate item (line 46)
    @pytest.mark.asyncio
    async def test_add_context_item_duplicate(self, context_manager):
        """Test add duplicate item - line 46"""
        # Mock _check_duplicate_item to return True
        with patch.object(context_manager, '_check_duplicate_item', return_value=True):
            context_data = {
                'organization_id': 'org-123',
                'rag_feature': 'feature',
                'item_id': 'existing-1',
                'item_type': 'type',
                'item_title': 'Test',
                'item_content': 'Content'
            }
            
            result = await context_manager.add_context_item(context_data)
            assert result['success'] is False
            assert 'Item already exists' in result['error']
    
    # Test insert failure (lines 60-63)
    @pytest.mark.asyncio
    async def test_add_context_item_insert_failure(self, context_manager):
        """Test insert failure - lines 60-63"""
        context_data = {
            'organization_id': 'org-123',
            'rag_feature': 'feature',
            'item_id': 'test-1',
            'item_type': 'type',
            'item_title': 'Test',
            'item_content': 'Content'
        }
        
        # Mock insert to return no data
        context_manager.supabase.from_.return_value.insert.return_value.execute.return_value.data = None
        
        with patch.object(context_manager, '_check_duplicate_item', return_value=False):
            result = await context_manager.add_context_item(context_data)
            assert result['success'] is False
            assert 'Failed to create context item' in result['error']
    
    # Test exception handling (lines 65-70)
    @pytest.mark.asyncio
    async def test_add_context_item_exception(self, context_manager):
        """Test exception handling - lines 65-70"""
        context_manager.supabase.from_.side_effect = Exception("DB error")
        
        context_data = {
            'organization_id': 'org-123',
            'rag_feature': 'feature',
            'item_id': 'test-1',
            'item_type': 'type',
            'item_title': 'Test',
            'item_content': 'Content'
        }
        
        result = await context_manager.add_context_item(context_data)
        assert result['success'] is False
    
    # Test remove_context_item when item not found (lines 78-82)
    @pytest.mark.asyncio
    async def test_remove_context_item_not_found(self, context_manager):
        """Test remove non-existent item - lines 78-82"""
        with patch.object(context_manager, '_get_context_item', return_value=None):
            result = await context_manager.remove_context_item(
                organization_id='org-123',
                rag_feature='feature',
                item_id='nonexistent',
                reason='test',
                removed_by='user-123'
            )
            
            assert result['success'] is False
            assert 'Item not found' in result['error']
    
    # Test remove success (lines 88-91)
    @pytest.mark.asyncio
    async def test_remove_context_item_success(self, context_manager):
        """Test successful removal - lines 88-91"""
        existing_item = {'id': 'item-123'}
        delete_result = Mock()
        delete_result.data = [{'id': 'item-123'}]
        
        context_manager.supabase.from_.return_value.delete.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = delete_result
        
        with patch.object(context_manager, '_get_context_item', return_value=existing_item):
            result = await context_manager.remove_context_item(
                organization_id='org-123',
                rag_feature='feature',
                item_id='test-1',
                reason='test',
                removed_by='user-123'
            )
            
            assert result['success'] is True
    
    # Test remove failure (lines 92-96)
    @pytest.mark.asyncio
    async def test_remove_context_item_delete_failure(self, context_manager):
        """Test delete failure - lines 92-96"""
        existing_item = {'id': 'item-123'}
        delete_result = Mock()
        delete_result.data = None
        
        context_manager.supabase.from_.return_value.delete.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = delete_result
        
        with patch.object(context_manager, '_get_context_item', return_value=existing_item):
            result = await context_manager.remove_context_item(
                organization_id='org-123',
                rag_feature='feature',
                item_id='test-1',
                reason='test',
                removed_by='user-123'
            )
            
            assert result['success'] is False
            assert 'Failed to remove' in result['error']
    
    # Test remove exception (lines 98-103)
    @pytest.mark.asyncio
    async def test_remove_context_item_exception(self, context_manager):
        """Test remove exception - lines 98-103"""
        context_manager.supabase.from_.side_effect = Exception("DB error")
        
        with patch.object(context_manager, '_get_context_item', return_value={'id': 'item-123'}):
            result = await context_manager.remove_context_item(
                organization_id='org-123',
                rag_feature='feature',
                item_id='test-1',
                reason='test',
                removed_by='user-123'
            )
            
            assert result['success'] is False
    
    # Test update_context_status when item not found (lines 111-115)
    @pytest.mark.asyncio
    async def test_update_context_status_not_found(self, context_manager):
        """Test update non-existent item - lines 111-115"""
        with patch.object(context_manager, '_get_context_item', return_value=None):
            result = await context_manager.update_context_status(
                organization_id='org-123',
                rag_feature='feature',
                item_id='nonexistent',
                new_status='excluded',
                reason='test',
                updated_by='user-123'
            )
            
            assert result['success'] is False
            assert 'Item not found' in result['error']
    
    # Test update success (lines 127-131)
    @pytest.mark.asyncio
    async def test_update_context_status_success(self, context_manager):
        """Test successful update - lines 127-131"""
        existing_item = {'id': 'item-123'}
        update_result = Mock()
        update_result.data = [{'id': 'item-123'}]
        
        context_manager.supabase.from_.return_value.update.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = update_result
        
        with patch.object(context_manager, '_get_context_item', return_value=existing_item):
            result = await context_manager.update_context_status(
                organization_id='org-123',
                rag_feature='feature',
                item_id='test-1',
                new_status='excluded',
                reason='test',
                updated_by='user-123'
            )
            
            assert result['success'] is True
    
    # Test update failure (lines 132-136)
    @pytest.mark.asyncio
    async def test_update_context_status_update_failure(self, context_manager):
        """Test update failure - lines 132-136"""
        existing_item = {'id': 'item-123'}
        update_result = Mock()
        update_result.data = None
        
        context_manager.supabase.from_.return_value.update.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = update_result
        
        with patch.object(context_manager, '_get_context_item', return_value=existing_item):
            result = await context_manager.update_context_status(
                organization_id='org-123',
                rag_feature='feature',
                item_id='test-1',
                new_status='excluded',
                reason='test',
                updated_by='user-123'
            )
            
            assert result['success'] is False
            assert 'Failed to update' in result['error']
    
    # Test update exception (lines 138-143)
    @pytest.mark.asyncio
    async def test_update_context_status_exception(self, context_manager):
        """Test update exception - lines 138-143"""
        context_manager.supabase.from_.side_effect = Exception("DB error")
        
        with patch.object(context_manager, '_get_context_item', return_value={'id': 'item-123'}):
            result = await context_manager.update_context_status(
                organization_id='org-123',
                rag_feature='feature',
                item_id='test-1',
                new_status='excluded',
                reason='test',
                updated_by='user-123'
            )
            
            assert result['success'] is False
    
    # Test get_context_items with filters (lines 157-164)
    @pytest.mark.asyncio
    async def test_get_context_items_with_filters(self, context_manager):
        """Test get with additional filters - lines 157-164"""
        select_result = Mock()
        select_result.data = [{'id': 'item-1', 'status': 'included'}]
        
        eq_chain = Mock()
        eq_chain.order = Mock(return_value=eq_chain)
        eq_chain.execute = Mock(return_value=select_result)
        
        in_chain = Mock()
        in_chain.gte = Mock(return_value=in_chain)
        in_chain.lte = Mock(return_value=in_chain)
        in_chain.order = Mock(return_value=eq_chain)
        in_chain.execute = Mock(return_value=select_result)
        
        status_chain = Mock()
        status_chain.in_ = Mock(return_value=in_chain)
        
        eq_chain2 = Mock()
        eq_chain2.eq = Mock(return_value=status_chain)
        eq_chain2.order = Mock(return_value=eq_chain)
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=eq_chain2)
        
        context_manager.supabase.from_.return_value.select.return_value = select_chain
        
        filters = {
            'status': 'included',
            'item_types': ['type1', 'type2'],
            'min_confidence': 0.7,
            'max_priority': 5
        }
        
        result = await context_manager.get_context_items('org-123', filters=filters)
        assert result['success'] is True
    
    # Test get_context_items exception (lines 175-180)
    @pytest.mark.asyncio
    async def test_get_context_items_exception(self, context_manager):
        """Test get exception - lines 175-180"""
        context_manager.supabase.from_.return_value.select.side_effect = Exception("DB error")
        
        result = await context_manager.get_context_items('org-123')
        assert result['success'] is False
    
    # Test get_context_statistics exception (lines 235-240)
    @pytest.mark.asyncio
    async def test_get_context_statistics_exception(self, context_manager):
        """Test statistics exception - lines 235-240"""
        context_manager.supabase.from_.return_value.select.return_value.eq.side_effect = Exception("Error")
        
        result = await context_manager.get_context_statistics('org-123')
        assert result['success'] is False
    
    # Test bulk_update with no item_id (line 251)
    @pytest.mark.asyncio
    async def test_bulk_update_missing_item_id(self, context_manager):
        """Test bulk update with missing item_id - line 251"""
        updates = [
            {'item_id': 'test-1', 'status': 'included'},
            {'status': 'excluded'},  # Missing item_id - should be skipped
            {'item_id': 'test-2', 'status': 'included'}
        ]
        
        # Mock successful updates
        update_result = Mock()
        update_result.data = [{'id': 'updated'}]
        
        context_manager.supabase.from_.return_value.update.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = update_result
        
        result = await context_manager.bulk_update_context_items(
            organization_id='org-123',
            rag_feature='feature',
            updates=updates,
            updated_by='user-123'
        )
        
        assert result['success'] is True
        assert result['updated_count'] == 2  # Only 2 with item_id
    
    # Test bulk_update exception (lines 273-278)
    @pytest.mark.asyncio
    async def test_bulk_update_exception(self, context_manager):
        """Test bulk update exception - lines 273-278"""
        context_manager.supabase.from_.side_effect = Exception("DB error")
        
        updates = [{'item_id': 'test-1', 'status': 'included'}]
        
        result = await context_manager.bulk_update_context_items(
            organization_id='org-123',
            rag_feature='feature',
            updates=updates,
            updated_by='user-123'
        )
        
        assert result['success'] is False
    
    # Test search_context_items exception (lines 300-305)
    @pytest.mark.asyncio
    async def test_search_context_items_exception(self, context_manager):
        """Test search exception - lines 300-305"""
        context_manager.supabase.from_.return_value.select.return_value.eq.side_effect = Exception("Error")
        
        result = await context_manager.search_context_items(
            organization_id='org-123',
            search_query='test'
        )
        
        assert result['success'] is False
    
    # Test export_context_items when get fails (lines 317-318)
    @pytest.mark.asyncio
    async def test_export_context_items_get_failure(self, context_manager):
        """Test export when get fails - lines 317-318"""
        with patch.object(context_manager, 'get_context_items', return_value={
            'success': False,
            'error': 'Failed to get items'
        }):
            result = await context_manager.export_context_items({
                'organization_id': 'org-123',
                'format': 'csv'
            })
            
            assert result['success'] is False
    
    # Test export with empty items (line 330)
    @pytest.mark.asyncio
    async def test_export_context_items_empty(self, context_manager):
        """Test export with empty items - line 330"""
        with patch.object(context_manager, 'get_context_items', return_value={
            'success': True,
            'items': []
        }):
            result = await context_manager.export_context_items({
                'organization_id': 'org-123',
                'format': 'csv'
            })
            
            assert result['success'] is True
            assert result['csv_data'] == "No data found"
    
    # Test export unsupported format (lines 338-341)
    @pytest.mark.asyncio
    async def test_export_context_items_unsupported_format(self, context_manager):
        """Test unsupported format - lines 338-341"""
        with patch.object(context_manager, 'get_context_items', return_value={
            'success': True,
            'items': [{'id': 'item-1'}]
        }):
            result = await context_manager.export_context_items({
                'organization_id': 'org-123',
                'format': 'xml'  # Unsupported
            })
            
            assert result['success'] is False
            assert 'Unsupported format' in result['error']
    
    # Test export exception (lines 343-348)
    @pytest.mark.asyncio
    async def test_export_context_items_exception(self, context_manager):
        """Test export exception - lines 343-348"""
        with patch.object(context_manager, 'get_context_items', side_effect=Exception("Error")):
            result = await context_manager.export_context_items({
                'organization_id': 'org-123',
                'format': 'csv'
            })
            
            assert result['success'] is False
    
    # Test import_context_items partial failure
    @pytest.mark.asyncio
    async def test_import_context_items_partial(self, context_manager):
        """Test import with some failures"""
        with patch.object(context_manager, 'add_context_item', side_effect=[
            {'success': True},  # First succeeds
            {'success': False},  # Second fails
            {'success': True}  # Third succeeds
        ]):
            items = [
                {'item_id': '1', 'item_type': 'type', 'item_title': 'Test', 'item_content': 'Content'},
                {'item_id': '2', 'item_type': 'type', 'item_title': 'Test2', 'item_content': 'Content2'},
                {'item_id': '3', 'item_type': 'type', 'item_title': 'Test3', 'item_content': 'Content3'}
            ]
            
            result = await context_manager.import_context_items(
                organization_id='org-123',
                rag_feature='feature',
                items=items,
                imported_by='user-123'
            )
            
            assert result['success'] is True
            assert result['imported_count'] == 2  # Only 2 successful
    
    # Test import exception (lines 370-375)
    @pytest.mark.asyncio
    async def test_import_context_items_exception(self, context_manager):
        """Test import exception - lines 370-375"""
        with patch.object(context_manager, 'add_context_item', side_effect=Exception("Error")):
            items = [{'item_id': '1', 'item_type': 'type', 'item_title': 'Test', 'item_content': 'Content'}]
            
            result = await context_manager.import_context_items(
                organization_id='org-123',
                rag_feature='feature',
                items=items,
                imported_by='user-123'
            )
            
            assert result['success'] is False
    
    # Test check_duplicate_items exception (lines 388-393)
    @pytest.mark.asyncio
    async def test_check_duplicate_items_exception(self, context_manager):
        """Test check duplicates exception - lines 388-393"""
        context_manager.supabase.from_.return_value.select.return_value.eq.return_value.eq.return_value.in_.side_effect = Exception("Error")
        
        result = await context_manager.check_duplicate_items(
            organization_id='org-123',
            rag_feature='feature',
            item_ids=['id1', 'id2']
        )
        
        assert result['success'] is False
    
    # Test _check_duplicate_item exception (lines 424-425)
    @pytest.mark.asyncio
    async def test_check_duplicate_item_exception(self, context_manager):
        """Test _check_duplicate_item exception - lines 424-425"""
        context_manager.supabase.from_.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Error")
        
        result = await context_manager._check_duplicate_item('org-123', 'feature', 'item-1')
        assert result is False
    
    # Test _get_context_item exception (lines 432-433)
    @pytest.mark.asyncio
    async def test_get_context_item_exception(self, context_manager):
        """Test _get_context_item exception - lines 432-433"""
        context_manager.supabase.from_.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Error")
        
        result = await context_manager._get_context_item('org-123', 'feature', 'item-1')
        assert result is None
    
    # Test filter_context_by_item_type
    @pytest.mark.asyncio
    async def test_filter_context_by_item_type(self, context_manager):
        """Test filter by item type"""
        with patch.object(context_manager, 'get_context_items', return_value={
            'success': True,
            'items': [{'id': 'item-1', 'item_type': 'type1'}]
        }):
            result = await context_manager.filter_context_by_item_type(
                organization_id='org-123',
                item_types=['type1', 'type2']
            )
            
            assert result['success'] is True
    
    # Test filter_context_by_confidence
    @pytest.mark.asyncio
    async def test_filter_context_by_confidence(self, context_manager):
        """Test filter by confidence"""
        with patch.object(context_manager, 'get_context_items', return_value={
            'success': True,
            'items': [{'id': 'item-1', 'confidence_score': 0.8}]
        }):
            result = await context_manager.filter_context_by_confidence(
                organization_id='org-123',
                min_confidence=0.7,
                max_confidence=0.9
            )
            
            assert result['success'] is True
    
    # Test filter_context_by_priority
    @pytest.mark.asyncio
    async def test_filter_context_by_priority(self, context_manager):
        """Test filter by priority"""
        with patch.object(context_manager, 'get_context_items', return_value={
            'success': True,
            'items': [{'id': 'item-1', 'priority': 3}]
        }):
            result = await context_manager.filter_context_by_priority(
                organization_id='org-123',
                min_priority=1,
                max_priority=5
            )
            
            assert result['success'] is True
    
    # Test filter_context_by_feature (line 184)
    @pytest.mark.asyncio
    async def test_filter_context_by_feature(self, context_manager):
        """Test filter by feature - line 184"""
        with patch.object(context_manager, 'get_context_items', return_value={
            'success': True,
            'items': [{'id': 'item-1', 'rag_feature': 'test_feature'}]
        }):
            result = await context_manager.filter_context_by_feature(
                organization_id='org-123',
                rag_feature='test_feature'
            )
            
            assert result['success'] is True
    
    # Test get_context_statistics with actual data (lines 213-226)
    @pytest.mark.asyncio
    async def test_get_context_statistics_with_data(self, context_manager):
        """Test statistics with real data - lines 213-226"""
        select_result = Mock()
        select_result.data = [
            {'rag_feature': 'feature1', 'confidence_score': 0.8},
            {'rag_feature': 'feature1', 'confidence_score': 0.7},
            {'rag_feature': 'feature2', 'confidence_score': 0.9}
        ]
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=select_result)
        
        context_manager.supabase.from_.return_value.select.return_value = select_chain
        
        result = await context_manager.get_context_statistics('org-123')
        
        assert result['success'] is True
        assert result['statistics']['total_items'] == 3
        assert result['statistics']['feature_counts']['feature1'] == 2
        assert result['statistics']['feature_counts']['feature2'] == 1
        assert result['statistics']['avg_confidence'] > 0
    
    # Test search_context_items with actual data (line 288)
    @pytest.mark.asyncio
    async def test_search_context_items_success(self, context_manager):
        """Test search functionality - line 288"""
        select_result = Mock()
        select_result.data = [{'id': 'item-1', 'item_title': 'Test Title', 'item_content': 'Test content'}]
        
        # Setup chain for search with .or_
        or_result = Mock()
        or_result.execute = Mock(return_value=select_result)
        
        eq_chain = Mock()
        eq_chain.eq = Mock(return_value=eq_chain)
        eq_chain.or_ = Mock(return_value=or_result)
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=eq_chain)
        
        context_manager.supabase.from_.return_value.select.return_value = select_chain
        
        result = await context_manager.search_context_items(
            organization_id='org-123',
            search_query='test'
        )
        
        assert result['success'] is True
        assert len(result['items']) == 1
    
    # Test bulk_update with actual update (line 265->248)
    @pytest.mark.asyncio
    async def test_bulk_update_success(self, context_manager):
        """Test bulk update success - line 265->248"""
        updates = [
            {'item_id': 'test-1', 'status': 'included', 'reason': 'approved'},
            {'item_id': 'test-2', 'status': 'excluded', 'reason': 'rejected'}
        ]
        
        update_result = Mock()
        update_result.data = [{'id': 'updated'}]
        
        eq_chain = Mock()
        eq_chain.eq = Mock(return_value=eq_chain)
        eq_chain.execute = Mock(return_value=update_result)
        
        update_chain = Mock()
        update_chain.eq = Mock(return_value=eq_chain)
        
        context_manager.supabase.from_.return_value.update.return_value = update_chain
        
        result = await context_manager.bulk_update_context_items(
            organization_id='org-123',
            rag_feature='feature',
            updates=updates,
            updated_by='user-123'
        )
        
        assert result['success'] is True
        assert result['updated_count'] == 2
    
    # Test check_duplicate_items with actual data (line 383)
    @pytest.mark.asyncio
    async def test_check_duplicate_items_success(self, context_manager):
        """Test check duplicates success - line 383"""
        select_result = Mock()
        select_result.data = [
            {'id': 'id1', 'item_id': 'test-1', 'item_title': 'Title 1'},
            {'id': 'id2', 'item_id': 'test-2', 'item_title': 'Title 2'}
        ]
        
        in_chain = Mock()
        in_chain.execute = Mock(return_value=select_result)
        
        eq_chain = Mock()
        eq_chain.eq = Mock(return_value=eq_chain)
        eq_chain.in_ = Mock(return_value=in_chain)
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=eq_chain)
        
        context_manager.supabase.from_.return_value.select.return_value = select_chain
        
        result = await context_manager.check_duplicate_items(
            organization_id='org-123',
            rag_feature='feature',
            item_ids=['test-1', 'test-2', 'test-3']
        )
        
        assert result['success'] is True
        assert len(result['duplicates']) == 2
    
    # Test get_performance_metrics success (lines 397-414)
    @pytest.mark.asyncio
    async def test_get_performance_metrics_success(self, context_manager):
        """Test performance metrics success - lines 397-414"""
        result = await context_manager.get_performance_metrics(
            organization_id='org-123',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow()
        )
        
        assert result['success'] is True
        assert 'metrics' in result
        assert 'best_practice_kb' in result['metrics']
    

    @pytest.mark.asyncio
    async def test_check_duplicate_item_exception(self, context_manager):
        """Test _check_duplicate_item exception - line 424-425"""
        context_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await context_manager._check_duplicate_item('org-123', 'feature', 'item-1')
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_context_item_exception(self, context_manager):
        """Test _get_context_item exception - line 432-433"""
        context_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await context_manager._get_context_item('org-123', 'feature', 'item-1')
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_check_duplicate_items_exception(self, context_manager):
        """Test check_duplicate_items exception - lines 388-393"""
        context_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await context_manager.check_duplicate_items('org-123', 'feature', ['item-1'])
        
        assert result['success'] is False
        assert 'error' in result
