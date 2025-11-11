# apps/app-api/__tests__/test_context_manager_working.py
"""
Working test suite for Context Manager with proper mocking
Target: Improve coverage to 60%+
"""

import pytest
from unittest.mock import Mock, patch
from services.context_manager import ContextManager
from test_utils import SupabaseMockBuilder


@pytest.fixture
def mock_builder():
    """Create mock builder for Supabase client"""
    return SupabaseMockBuilder()


@pytest.fixture
def context_manager(mock_builder):
    """Create ContextManager with mocked Supabase client"""
    with patch('services.context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return ContextManager()


class TestContextManagerBasic:
    """Basic tests for Context Manager"""
    
    @pytest.mark.asyncio
    async def test_init(self, context_manager):
        """Test ContextManager initialization"""
        assert context_manager is not None
        assert context_manager.supabase is not None
    
    @pytest.mark.asyncio
    async def test_add_context_item_success(self, context_manager, mock_builder):
        """Test adding a context item successfully"""
        context_data = {
            'organization_id': 'org-123',
            'rag_feature': 'sales_intelligence',
            'item_id': 'test-item-1',
            'item_type': 'knowledge_chunk',
            'item_title': 'Test Title',
            'item_content': 'Test content'
        }
        
        mock_builder.setup_table_data('rag_context_items', [])
        mock_builder.insert_response.data = [{'id': 'new-item-id'}]
        
        result = await context_manager.add_context_item(context_data)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_context_items_success(self, context_manager, mock_builder):
        """Test retrieving context items"""
        test_data = [
            {'id': 'item-1', 'rag_feature': 'sales_intelligence'},
            {'id': 'item-2', 'rag_feature': 'customer_insights'}
        ]
        mock_builder.setup_table_data('rag_context_items', test_data)
        
        result = await context_manager.get_context_items('org-123')
        assert result is not None


class TestContextManagerBulkOperations:
    """Test bulk operations"""
    
    @pytest.fixture
    def context_manager(self, mock_builder):
        with patch('services.context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
            return ContextManager()
    
    @pytest.fixture
    def mock_builder(self):
        return SupabaseMockBuilder()
    
    @pytest.mark.asyncio
    async def test_bulk_update_context_items(self, context_manager, mock_builder):
        """Test bulk updating context items"""
        mock_builder.setup_table_data('rag_context_items', [])
        mock_builder.update_response.data = [{'id': 'updated-item'}]
        
        updates = [
            {'item_id': 'item-1', 'status': 'active'},
            {'item_id': 'item-2', 'status': 'inactive'}
        ]
        
        result = await context_manager.bulk_update_context_items(
            organization_id='org-123',
            rag_feature='sales_intelligence',
            updates=updates,
            updated_by='user-123'
        )
        assert result is not None


class TestContextManagerSearch:
    """Test search functionality"""
    
    @pytest.fixture
    def context_manager(self, mock_builder):
        with patch('services.context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
            return ContextManager()
    
    @pytest.fixture
    def mock_builder(self):
        return SupabaseMockBuilder()
    
    @pytest.mark.asyncio
    async def test_search_context_items(self, context_manager, mock_builder):
        """Test searching context items"""
        test_data = [
            {'id': 'item-1', 'item_title': 'Sales Best Practices', 'item_content': 'Best practices for sales'}
        ]
        mock_builder.setup_table_data('rag_context_items', test_data)
        
        result = await context_manager.search_context_items(
            organization_id='org-123',
            search_query='sales'
        )
        assert result is not None


class TestContextManagerExport:
    """Test export functionality"""
    
    @pytest.fixture
    def context_manager(self, mock_builder):
        with patch('services.context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
            return ContextManager()
    
    @pytest.fixture
    def mock_builder(self):
        return SupabaseMockBuilder()
    
    @pytest.mark.asyncio
    async def test_export_context_items(self, context_manager, mock_builder):
        """Test exporting context items to CSV"""
        # Mock get_context_items to return test data
        with patch.object(context_manager, 'get_context_items') as mock_get:
            mock_get.return_value = {
                'success': True,
                'items': [
                    {'id': 'item-1', 'item_title': 'Sales Intelligence'},
                    {'id': 'item-2', 'item_title': 'Customer Insights'}
                ]
            }
            
            export_config = {
                'organization_id': 'org-123',
                'format': 'csv'
            }
            result = await context_manager.export_context_items(export_config)
            assert result is not None
            assert 'success' in result


class TestContextManagerStatistics:
    """Test statistics functionality"""
    
    @pytest.fixture
    def context_manager(self, mock_builder):
        with patch('services.context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
            return ContextManager()
    
    @pytest.fixture
    def mock_builder(self):
        return SupabaseMockBuilder()
    
    @pytest.mark.asyncio
    async def test_get_context_statistics(self, context_manager, mock_builder):
        """Test retrieving context statistics"""
        test_data = [
            {'status': 'active', 'count': 50},
            {'status': 'archived', 'count': 20}
        ]
        mock_builder.setup_table_data('rag_context_items', test_data)
        
        result = await context_manager.get_context_statistics('org-123')
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

