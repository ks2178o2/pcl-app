# apps/app-api/__tests__/test_context_manager_85_coverage.py
"""
Comprehensive tests to push Context Manager coverage from 65.85% to 85%+
Current: 65.85%, Target: 85%+, Goal: 19.15% improvement
"""

import pytest
from unittest.mock import Mock, patch
from services.context_manager import ContextManager
from test_utils import SupabaseMockBuilder


@pytest.fixture
def mock_builder():
    return SupabaseMockBuilder()


@pytest.fixture
def context_manager(mock_builder):
    with patch('services.context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return ContextManager()


class TestUpdateContextItemLines118143:
    """Test update context item error paths - lines 118-143"""
    
    @pytest.mark.asyncio
    async def test_update_context_status_no_data(self, context_manager):
        """Test update when returns no data - covers lines 132-136"""
        # Mock _get_context_item to return existing item
        with patch.object(context_manager, '_get_context_item', return_value={'id': 'item-123'}):
            # Setup update to return no data
            update_result = Mock()
            update_result.data = []
            
            chain = Mock()
            chain.update.return_value = chain
            chain.eq.return_value = chain
            chain.execute.return_value = update_result
            
            table = Mock()
            table.update.return_value = chain
            context_manager.supabase.from_.return_value = table
            
            result = await context_manager.update_context_status(
                organization_id='org-123',
                rag_feature='sales_intelligence',
                item_id='item-123',
                new_status='excluded',
                updated_by='user-123',
                reason='Test update'
            )
            
            assert result is not None
            assert result.get('success') is False
            assert 'Failed to update' in result.get('error', '')
    
    @pytest.mark.asyncio
    async def test_update_context_status_exception(self, context_manager):
        """Test update when exception occurs - covers lines 138-143"""
        with patch.object(context_manager.supabase, 'from_', side_effect=Exception("Database error")):
            result = await context_manager.update_context_status(
                organization_id='org-123',
                rag_feature='sales_intelligence',
                item_id='item-123',
                new_status='excluded',
                updated_by='user-123',
                reason='Test update'
            )
            
            assert result is not None
            assert result.get('success') is False


class TestGetContextItemsLines156177:
    """Test get context items filter paths - lines 156-177"""
    
    @pytest.mark.asyncio
    async def test_get_context_items_with_all_filters(self, context_manager):
        """Test get items with all filter types - covers lines 156-164"""
        filters = {
            'status': 'included',
            'item_types': ['knowledge_chunk', 'faq'],
            'min_confidence': 0.5,
            'max_priority': 5
        }
        
        query_result = Mock()
        query_result.data = [{'id': 'item-123'}]
        
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.in_.return_value = chain
        chain.gte.return_value = chain
        chain.lte.return_value = chain
        chain.order.return_value = chain
        chain.execute.return_value = query_result
        
        table = Mock()
        table.select.return_value = chain
        context_manager.supabase.from_.return_value = table
        
        result = await context_manager.get_context_items('org-123', rag_feature='sales_intelligence', filters=filters)
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_get_context_items_exception(self, context_manager):
        """Test get items when exception occurs - covers lines 175-177"""
        with patch.object(context_manager.supabase, 'from_', side_effect=Exception("Database error")):
            result = await context_manager.get_context_items('org-123')
            
            assert result is not None
            assert result.get('success') is False


class TestFilterMethodsLines184189193197201205:
    """Test filter methods - lines 184, 188-189, 193-197, 201-205"""
    
    @pytest.mark.asyncio
    async def test_filter_by_feature(self, context_manager):
        """Test filter by feature - covers line 184"""
        with patch.object(context_manager, 'get_context_items', return_value={'success': True, 'items': []}):
            result = await context_manager.filter_context_by_feature('org-123', 'sales_intelligence')
            
            assert result is not None
            assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_filter_by_item_type(self, context_manager):
        """Test filter by item type - covers lines 186-189"""
        with patch.object(context_manager, 'get_context_items', return_value={'success': True, 'items': []}):
            result = await context_manager.filter_context_by_item_type('org-123', ['knowledge_chunk', 'faq'])
            
            assert result is not None
            assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_filter_by_confidence(self, context_manager):
        """Test filter by confidence - covers lines 191-197"""
        with patch.object(context_manager, 'get_context_items', return_value={'success': True, 'items': []}):
            result = await context_manager.filter_context_by_confidence('org-123', 0.5, 0.9)
            
            assert result is not None
            assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_filter_by_priority(self, context_manager):
        """Test filter by priority - covers lines 199-205"""
        with patch.object(context_manager, 'get_context_items', return_value={'success': True, 'items': []}):
            result = await context_manager.filter_context_by_priority('org-123', 1, 5)
            
            assert result is not None
            assert result.get('success') is True


class TestContextStatisticsLines235237:
    """Test context statistics error paths - lines 235-237"""
    
    @pytest.mark.asyncio
    async def test_get_statistics_exception(self, context_manager):
        """Test get statistics when exception occurs - covers lines 235-237"""
        with patch.object(context_manager.supabase, 'from_', side_effect=Exception("Database error")):
            result = await context_manager.get_context_statistics('org-123')
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_get_statistics_with_data(self, context_manager):
        """Test get statistics with actual data"""
        query_result = Mock()
        query_result.data = [
            {'rag_feature': 'sales_intelligence', 'confidence_score': 0.8},
            {'rag_feature': 'sales_intelligence', 'confidence_score': 0.9},
            {'rag_feature': 'support_kb', 'confidence_score': 0.7}
        ]
        
        # Setup proper chaining for select().eq().execute()
        chain = Mock()
        chain.eq.return_value = chain
        chain.execute.return_value = query_result
        
        table = Mock()
        table.select.return_value = chain
        context_manager.supabase.from_.return_value = table
        
        result = await context_manager.get_context_statistics('org-123')
        
        assert result is not None
        assert result.get('success') is True
        stats = result.get('statistics', {})
        assert stats.get('total_items') == 3
        assert stats.get('feature_counts', {}).get('sales_intelligence') == 2


class TestRemoveContextItemLines92100:
    """Test remove context item - lines 92-100"""
    
    @pytest.mark.asyncio
    async def test_remove_context_item_no_data(self, context_manager):
        """Test remove when returns no data - covers lines 92-96"""
        with patch.object(context_manager, '_get_context_item', return_value={'id': 'item-123'}):
            update_result = Mock()
            update_result.data = []
            
            chain = Mock()
            chain.delete.return_value = chain
            chain.eq.return_value = chain
            chain.execute.return_value = update_result
            
            table = Mock()
            table.delete.return_value = chain
            context_manager.supabase.from_.return_value = table
            
            result = await context_manager.remove_context_item(
                organization_id='org-123',
                rag_feature='sales_intelligence',
                item_id='item-123',
                reason='Test removal',
                removed_by='user-123'
            )
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_remove_context_item_exception(self, context_manager):
        """Test remove when exception occurs - covers lines 98-100"""
        with patch.object(context_manager, '_get_context_item', return_value={'id': 'item-123'}):
            with patch.object(context_manager.supabase, 'from_', side_effect=Exception("Database error")):
                result = await context_manager.remove_context_item(
                    organization_id='org-123',
                    rag_feature='sales_intelligence',
                    item_id='item-123',
                    reason='Test removal',
                    removed_by='user-123'
                )
                
                assert result is not None
                assert result.get('success') is False


class TestAddContextItemLines265273:
    """Test add context item error paths - lines 265->248, 273-275"""
    
    @pytest.mark.asyncio
    async def test_add_context_item_validation_error(self, context_manager):
        """Test add with validation error"""
        result = await context_manager.add_context_item({
            'organization_id': 'org-123',
            'rag_feature': 'sales_intelligence',
            'item_id': '',  # Empty field
            'item_type': '',
            'item_title': '',
            'item_content': ''
        })
        
        assert result is not None
        assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_add_context_item_invalid_confidence(self, context_manager):
        """Test add with invalid confidence score"""
        result = await context_manager.add_context_item({
            'organization_id': 'org-123',
            'rag_feature': 'sales_intelligence',
            'item_id': 'item-123',
            'item_type': 'knowledge_chunk',
            'item_title': 'Test',
            'item_content': 'Content',
            'confidence_score': 1.5  # Invalid
        })
        
        assert result is not None
        assert result.get('success') is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.context_manager', '--cov-report=html'])

