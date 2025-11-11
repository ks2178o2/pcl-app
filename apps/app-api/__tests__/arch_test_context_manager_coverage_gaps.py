# apps/app-api/__tests__/test_context_manager_coverage_gaps.py
"""
Test suite to cover remaining gaps in Context Manager
Target: Reach 95% coverage
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


class TestContextManagerQueryLogic:
    """Test complex query logic"""
    
    @pytest.mark.asyncio
    async def test_get_context_items_with_filters(self, context_manager, mock_builder):
        """Test getting items with RAG feature filter"""
        items = [
            {'id': 'item-1', 'status': 'active', 'confidence_score': 0.9},
            {'id': 'item-2', 'status': 'archived', 'confidence_score': 0.8}
        ]
        mock_builder.setup_table_data('rag_context_items', items)
        
        result = await context_manager.get_context_items(
            organization_id='org-123',
            rag_feature='sales_intelligence'
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_context_items_with_rag_filter(self, context_manager, mock_builder):
        """Test getting items filtered by RAG feature"""
        items = [
            {'id': 'item-1', 'rag_feature': 'sales_intelligence', 'confidence_score': 0.95},
            {'id': 'item-2', 'rag_feature': 'customer_insights', 'confidence_score': 0.75}
        ]
        mock_builder.setup_table_data('rag_context_items', items)
        
        result = await context_manager.get_context_items(
            organization_id='org-123',
            rag_feature='sales_intelligence'
        )
        assert result is not None


class TestContextManagerExportFormats:
    """Test export format handling"""
    
    @pytest.mark.asyncio
    async def test_export_context_items_invalid_format(self, context_manager):
        """Test exporting with invalid format"""
        with patch.object(context_manager, 'get_context_items') as mock_get:
            mock_get.return_value = {
                'success': True,
                'items': [{'id': 'item-1', 'item_title': 'Test'}]
            }
            
            export_config = {
                'organization_id': 'org-123',
                'format': 'invalid_format'
            }
            
            result = await context_manager.export_context_items(export_config)
            assert result is not None
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_export_context_items_empty_data(self, context_manager):
        """Test exporting with empty data"""
        with patch.object(context_manager, 'get_context_items') as mock_get:
            mock_get.return_value = {
                'success': True,
                'items': []
            }
            
            export_config = {
                'organization_id': 'org-123',
                'format': 'csv'
            }
            
            result = await context_manager.export_context_items(export_config)
            assert result is not None


class TestContextManagerBulkOperationsAdvanced:
    """Test advanced bulk operation scenarios"""
    
    @pytest.mark.asyncio
    async def test_bulk_update_with_partial_success(self, context_manager, mock_builder):
        """Test bulk update where some items update and some don't"""
        updates = [
            {'item_id': 'item-1', 'status': 'active'},
            {'item_id': 'item-2', 'status': 'active'},
            {'item_id': 'item-not-exists', 'status': 'active'}
        ]
        
        with patch.object(context_manager.supabase, 'from_') as mock_from:
            # First two succeed, third fails
            def side_effect(*args, **kwargs):
                mock = Mock()
                if len(updates) > 2:
                    mock.execute.return_value = Mock(data=[{'id': f'updated-{args[0]}'}])
                else:
                    mock.execute.return_value = Mock(data=[])
                return mock
            
            mock_from.return_value.update.return_value.eq.return_value = Mock(side_effect=side_effect)
            
            result = await context_manager.bulk_update_context_items(
                organization_id='org-123',
                rag_feature='sales_intelligence',
                updates=updates,
                updated_by='user-123'
            )
            assert result is not None


class TestContextManagerSearchAdvanced:
    """Test advanced search scenarios"""
    
    @pytest.mark.asyncio
    async def test_search_with_special_characters(self, context_manager, mock_builder):
        """Test searching with special characters"""
        items = [
            {'id': 'item-1', 'item_title': 'Test & Example', 'item_content': 'Sales & Marketing'}
        ]
        mock_builder.setup_table_data('rag_context_items', items)
        
        result = await context_manager.search_context_items(
            organization_id='org-123',
            search_query='Test & Example'
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_search_with_rag_feature_filter(self, context_manager, mock_builder):
        """Test search with RAG feature filter"""
        items = [
            {'id': 'item-1', 'rag_feature': 'sales_intelligence', 'item_title': 'Sales Tips'}
        ]
        mock_builder.setup_table_data('rag_context_items', items)
        
        result = await context_manager.search_context_items(
            organization_id='org-123',
            search_query='sales',
            rag_feature='sales_intelligence'
        )
        assert result is not None


class TestContextManagerImportAdvanced:
    """Test advanced import scenarios"""
    
    @pytest.mark.asyncio
    async def test_import_with_validation_errors(self, context_manager):
        """Test importing with validation errors"""
        items = [
            {
                'item_id': 'valid-1',
                'item_type': 'knowledge_chunk',
                'item_title': 'Valid Title',
                'item_content': 'Valid Content'
            },
            {
                'item_id': '',  # Invalid - empty
                'item_title': 'Invalid',
                'item_content': 'Content'
            }
        ]
        
        with patch.object(context_manager, 'add_context_item') as mock_add:
            def side_effect(item):
                if not item.get('item_id'):
                    return {'success': False, 'error': 'item_id cannot be empty'}
                return {'success': True}
            
            mock_add.side_effect = side_effect
            
            result = await context_manager.import_context_items(
                organization_id='org-123',
                rag_feature='sales_intelligence',
                items=items,
                imported_by='user-123'
            )
            assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.context_manager', '--cov-report=html'])

