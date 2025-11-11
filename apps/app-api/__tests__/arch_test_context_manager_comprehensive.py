# apps/app-api/__tests__/test_context_manager_comprehensive.py

import pytest
import asyncio
from unittest.mock import patch, Mock
from datetime import datetime
import json
import csv
import io

from services.context_manager import ContextManager
from test_utils import SupabaseMockBuilder, TestDataFactory, MockResponseBuilder

class TestContextManagerComprehensive:
    """Comprehensive test suite for Context Manager with 95% coverage"""

    @pytest.fixture
    def mock_builder(self):
        """Create mock builder for Supabase client"""
        return SupabaseMockBuilder()

    @pytest.fixture
    def context_manager(self, mock_builder):
        """Create ContextManager with mocked Supabase client"""
        with patch('services.context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
            return ContextManager()

    # ==================== BASIC CRUD TESTS ====================

    @pytest.mark.asyncio
    async def test_add_context_item_success(self, context_manager, mock_builder):
        """Test successful addition of a context item"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        item_data = {
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            "item_id": "knowledge_123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Knowledge",
            "item_content": "Test content",
            "status": "included",
            "priority": 1,
            "confidence_score": 0.9
        }
        
        result = await context_manager.add_context_item(item_data)
        
        assert result["success"] is True
        assert "item_id" in result

    @pytest.mark.asyncio
    async def test_add_context_item_missing_fields(self, context_manager):
        """Test adding context item with missing required fields"""
        invalid_data = {
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            # Missing required fields
        }
        
        result = await context_manager.add_context_item(invalid_data)
        
        assert result["success"] is False
        assert "Missing required fields" in result["error"]

    @pytest.mark.asyncio
    async def test_add_context_item_invalid_confidence(self, context_manager):
        """Test adding context item with invalid confidence score"""
        invalid_data = {
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            "item_id": "knowledge_123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Knowledge",
            "item_content": "Test content",
            "confidence_score": 1.5  # Invalid
        }
        
        result = await context_manager.add_context_item(invalid_data)
        
        assert result["success"] is False
        assert "Confidence score must be between 0 and 1" in result["error"]

    @pytest.mark.asyncio
    async def test_add_context_item_database_error(self, context_manager, mock_builder):
        """Test adding context item with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Insert failed')
        
        valid_data = {
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            "item_id": "knowledge_123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Knowledge",
            "item_content": "Test content"
        }
        
        result = await context_manager.add_context_item(valid_data)
        
        assert result["success"] is False
        assert "Insert failed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_context_items_success(self, context_manager, mock_builder):
        """Test successful retrieval of context items"""
        context_items = [
            TestDataFactory.create_context_item({"id": "item-1"}),
            TestDataFactory.create_context_item({"id": "item-2"})
        ]
        mock_builder.setup_table_data('rag_context_items', context_items)
        
        result = await context_manager.get_context_items(organization_id="org-123")
        
        assert result["success"] is True
        assert len(result["items"]) == 2
        assert result["total_count"] == 2

    @pytest.mark.asyncio
    async def test_get_context_items_with_filters(self, context_manager, mock_builder):
        """Test retrieval of context items with filters"""
        context_items = [
            TestDataFactory.create_context_item({"rag_feature": "best_practice_kb"}),
            TestDataFactory.create_context_item({"rag_feature": "customer_insight_rag"})
        ]
        mock_builder.setup_table_data('rag_context_items', context_items)
        
        result = await context_manager.get_context_items(
            organization_id="org-123",
            rag_feature="best_practice_kb"
        )
        
        assert result["success"] is True
        assert len(result["items"]) == 1
        assert result["items"][0]["rag_feature"] == "best_practice_kb"

    @pytest.mark.asyncio
    async def test_get_context_items_with_pagination(self, context_manager, mock_builder):
        """Test retrieval of context items with pagination"""
        context_items = [TestDataFactory.create_context_item({"id": f"item-{i}"}) for i in range(10)]
        mock_builder.setup_table_data('rag_context_items', context_items)
        
        result = await context_manager.get_context_items(
            organization_id="org-123",
            limit=5,
            offset=0
        )
        
        assert result["success"] is True
        assert len(result["items"]) == 5
        assert result["has_more"] is True

    @pytest.mark.asyncio
    async def test_get_context_items_database_error(self, context_manager, mock_builder):
        """Test retrieval of context items with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Query failed')
        
        result = await context_manager.get_context_items(organization_id="org-123")
        
        assert result["success"] is False
        assert "Query failed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_context_item_by_id_success(self, context_manager, mock_builder):
        """Test successful retrieval of context item by ID"""
        context_item = TestDataFactory.create_context_item()
        mock_builder.setup_table_data('rag_context_items', [context_item])
        
        result = await context_manager.get_context_item_by_id(item_id="context-123")
        
        assert result["success"] is True
        assert result["item"]["id"] == "context-123"

    @pytest.mark.asyncio
    async def test_get_context_item_by_id_not_found(self, context_manager, mock_builder):
        """Test retrieval of context item by ID when not found"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        result = await context_manager.get_context_item_by_id(item_id="non-existent-id")
        
        assert result["success"] is False
        assert "Item not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_context_item_by_id_database_error(self, context_manager, mock_builder):
        """Test retrieval of context item by ID with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Query failed')
        
        result = await context_manager.get_context_item_by_id(item_id="context-123")
        
        assert result["success"] is False
        assert "Query failed" in result["error"]

    @pytest.mark.asyncio
    async def test_update_context_item_success(self, context_manager, mock_builder):
        """Test successful update of context item"""
        update_data = {
            "item_title": "Updated Title",
            "confidence_score": 0.8
        }
        
        result = await context_manager.update_context_item(
            item_id="context-123",
            update_data=update_data
        )
        
        assert result["success"] is True
        assert "item_id" in result

    @pytest.mark.asyncio
    async def test_update_context_item_invalid_status(self, context_manager):
        """Test updating context item with invalid status"""
        update_data = {"status": "invalid_status"}
        
        result = await context_manager.update_context_item(
            item_id="context-123",
            update_data=update_data
        )
        
        assert result["success"] is False
        assert "Invalid status" in result["error"]

    @pytest.mark.asyncio
    async def test_update_context_item_not_found(self, context_manager, mock_builder):
        """Test updating context item that doesn't exist"""
        mock_builder.setup_table_data('rag_context_items', [])  # No items
        
        update_data = {"item_title": "New Title"}
        
        result = await context_manager.update_context_item(
            item_id="non-existent-id",
            update_data=update_data
        )
        
        assert result["success"] is False
        assert "Context item not found" in result["error"]

    @pytest.mark.asyncio
    async def test_update_context_item_database_error(self, context_manager, mock_builder):
        """Test updating context item with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Update failed')
        
        update_data = {"item_title": "New Title"}
        
        result = await context_manager.update_context_item(
            item_id="context-123",
            update_data=update_data
        )
        
        assert result["success"] is False
        assert "Update failed" in result["error"]

    @pytest.mark.asyncio
    async def test_remove_context_item_success(self, context_manager, mock_builder):
        """Test successful removal of context item"""
        result = await context_manager.remove_context_item(item_id="context-123")
        
        assert result["success"] is True
        assert "item_id" in result

    @pytest.mark.asyncio
    async def test_remove_context_item_not_found(self, context_manager, mock_builder):
        """Test removing context item that doesn't exist"""
        mock_builder.setup_table_data('rag_context_items', [])  # No items
        
        result = await context_manager.remove_context_item(item_id="non-existent-id")
        
        assert result["success"] is False
        assert "Context item not found" in result["error"]

    @pytest.mark.asyncio
    async def test_remove_context_item_database_error(self, context_manager, mock_builder):
        """Test removing context item with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Delete failed')
        
        result = await context_manager.remove_context_item(item_id="context-123")
        
        assert result["success"] is False
        assert "Delete failed" in result["error"]

    # ==================== SEARCH AND FILTER TESTS ====================

    @pytest.mark.asyncio
    async def test_search_context_items_success(self, context_manager, mock_builder):
        """Test successful search of context items"""
        context_items = [
            TestDataFactory.create_context_item({"item_title": "Sales Best Practice"}),
            TestDataFactory.create_context_item({"item_title": "Customer Service Guide"})
        ]
        mock_builder.setup_table_data('rag_context_items', context_items)
        
        result = await context_manager.search_context_items(
            organization_id="org-123",
            query="Sales"
        )
        
        assert result["success"] is True
        assert len(result["items"]) == 1
        assert "Sales" in result["items"][0]["item_title"]

    @pytest.mark.asyncio
    async def test_search_context_items_no_results(self, context_manager, mock_builder):
        """Test search of context items with no results"""
        context_items = [
            TestDataFactory.create_context_item({"item_title": "Customer Service Guide"})
        ]
        mock_builder.setup_table_data('rag_context_items', context_items)
        
        result = await context_manager.search_context_items(
            organization_id="org-123",
            query="NonExistentTerm"
        )
        
        assert result["success"] is True
        assert len(result["items"]) == 0

    @pytest.mark.asyncio
    async def test_search_context_items_database_error(self, context_manager, mock_builder):
        """Test search of context items with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Search failed')
        
        result = await context_manager.search_context_items(
            organization_id="org-123",
            query="test"
        )
        
        assert result["success"] is False
        assert "Search failed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_context_items_by_feature_success(self, context_manager, mock_builder):
        """Test retrieval of context items by RAG feature"""
        context_items = [
            TestDataFactory.create_context_item({"rag_feature": "best_practice_kb"}),
            TestDataFactory.create_context_item({"rag_feature": "customer_insight_rag"})
        ]
        mock_builder.setup_table_data('rag_context_items', context_items)
        
        result = await context_manager.get_context_items_by_feature(
            organization_id="org-123",
            rag_feature="best_practice_kb"
        )
        
        assert result["success"] is True
        assert len(result["items"]) == 1
        assert result["items"][0]["rag_feature"] == "best_practice_kb"

    @pytest.mark.asyncio
    async def test_get_context_items_by_feature_database_error(self, context_manager, mock_builder):
        """Test retrieval of context items by RAG feature with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Query failed')
        
        result = await context_manager.get_context_items_by_feature(
            organization_id="org-123",
            rag_feature="best_practice_kb"
        )
        
        assert result["success"] is False
        assert "Query failed" in result["error"]

    # ==================== EXPORT/IMPORT TESTS ====================

    @pytest.mark.asyncio
    async def test_export_context_items_csv_success(self, context_manager, mock_builder):
        """Test successful export of context items to CSV"""
        context_items = [
            TestDataFactory.create_context_item({"id": "item-1", "item_title": "Item 1"}),
            TestDataFactory.create_context_item({"id": "item-2", "item_title": "Item 2"})
        ]
        mock_builder.setup_table_data('rag_context_items', context_items)
        
        export_config = {
            "format": "csv",
            "organization_id": "org-123"
        }
        
        result = await context_manager.export_context_items(export_config)
        
        assert result["success"] is True
        assert "csv_data" in result
        assert "Item 1" in result["csv_data"]
        assert "Item 2" in result["csv_data"]

    @pytest.mark.asyncio
    async def test_export_context_items_json_success(self, context_manager, mock_builder):
        """Test successful export of context items to JSON"""
        context_items = [
            TestDataFactory.create_context_item({"id": "item-1"}),
            TestDataFactory.create_context_item({"id": "item-2"})
        ]
        mock_builder.setup_table_data('rag_context_items', context_items)
        
        export_config = {
            "format": "json",
            "organization_id": "org-123"
        }
        
        result = await context_manager.export_context_items(export_config)
        
        assert result["success"] is True
        assert "json_data" in result
        assert len(result["json_data"]) == 2

    @pytest.mark.asyncio
    async def test_export_context_items_invalid_format(self, context_manager):
        """Test export of context items with invalid format"""
        export_config = {
            "format": "invalid_format",
            "organization_id": "org-123"
        }
        
        result = await context_manager.export_context_items(export_config)
        
        assert result["success"] is False
        assert "Unsupported export format" in result["error"]

    @pytest.mark.asyncio
    async def test_export_context_items_database_error(self, context_manager, mock_builder):
        """Test export of context items with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Query failed')
        
        export_config = {
            "format": "csv",
            "organization_id": "org-123"
        }
        
        result = await context_manager.export_context_items(export_config)
        
        assert result["success"] is False
        assert "Query failed" in result["error"]

    @pytest.mark.asyncio
    async def test_import_context_items_csv_success(self, context_manager, mock_builder):
        """Test successful import of context items from CSV"""
        csv_data = """organization_id,rag_feature,item_id,item_type,item_title,item_content,status,priority,confidence_score
org-123,best_practice_kb,imported_item_1,knowledge_chunk,Imported Item 1,Imported content 1,included,1,0.8
org-123,best_practice_kb,imported_item_2,knowledge_chunk,Imported Item 2,Imported content 2,included,2,0.9"""
        
        import_config = {
            "format": "csv",
            "organization_id": "org-123",
            "data": csv_data
        }
        
        result = await context_manager.import_context_items(import_config)
        
        assert result["success"] is True
        assert result["imported_count"] == 2

    @pytest.mark.asyncio
    async def test_import_context_items_json_success(self, context_manager, mock_builder):
        """Test successful import of context items from JSON"""
        json_data = [
            {
                "organization_id": "org-123",
                "rag_feature": "best_practice_kb",
                "item_id": "imported_item_1",
                "item_type": "knowledge_chunk",
                "item_title": "Imported Item 1",
                "item_content": "Imported content 1",
                "status": "included",
                "priority": 1,
                "confidence_score": 0.8
            },
            {
                "organization_id": "org-123",
                "rag_feature": "best_practice_kb",
                "item_id": "imported_item_2",
                "item_type": "knowledge_chunk",
                "item_title": "Imported Item 2",
                "item_content": "Imported content 2",
                "status": "included",
                "priority": 2,
                "confidence_score": 0.9
            }
        ]
        
        import_config = {
            "format": "json",
            "organization_id": "org-123",
            "data": json_data
        }
        
        result = await context_manager.import_context_items(import_config)
        
        assert result["success"] is True
        assert result["imported_count"] == 2

    @pytest.mark.asyncio
    async def test_import_context_items_invalid_format(self, context_manager):
        """Test import of context items with invalid format"""
        import_config = {
            "format": "invalid_format",
            "organization_id": "org-123",
            "data": "some data"
        }
        
        result = await context_manager.import_context_items(import_config)
        
        assert result["success"] is False
        assert "Unsupported import format" in result["error"]

    @pytest.mark.asyncio
    async def test_import_context_items_database_error(self, context_manager, mock_builder):
        """Test import of context items with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Insert failed')
        
        csv_data = "organization_id,rag_feature,item_id,item_type,item_title,item_content,status,priority,confidence_score\norg-123,best_practice_kb,test_item,knowledge_chunk,Test Item,Test content,included,1,0.8"
        
        import_config = {
            "format": "csv",
            "organization_id": "org-123",
            "data": csv_data
        }
        
        result = await context_manager.import_context_items(import_config)
        
        assert result["success"] is False
        assert "Insert failed" in result["error"]

    @pytest.mark.asyncio
    async def test_import_context_items_validation_error(self, context_manager):
        """Test import of context items with validation error"""
        csv_data = "organization_id,rag_feature,item_id,item_type,item_title,item_content,status,priority,confidence_score\norg-123,best_practice_kb,test_item,knowledge_chunk,Test Item,Test content,included,1,1.5"  # Invalid confidence score
        
        import_config = {
            "format": "csv",
            "organization_id": "org-123",
            "data": csv_data
        }
        
        result = await context_manager.import_context_items(import_config)
        
        assert result["success"] is False
        assert "Validation error" in result["error"]

    # ==================== STATISTICS TESTS ====================

    @pytest.mark.asyncio
    async def test_get_context_statistics_success(self, context_manager, mock_builder):
        """Test successful retrieval of context statistics"""
        mock_builder.setup_table_data('rag_context_items', [
            {"rag_feature": "best_practice_kb", "count": 10},
            {"rag_feature": "customer_insight_rag", "count": 5}
        ])
        
        result = await context_manager.get_context_statistics(organization_id="org-123")
        
        assert result["success"] is True
        assert len(result["statistics"]) == 2
        assert result["statistics"][0]["rag_feature"] == "best_practice_kb"
        assert result["statistics"][0]["count"] == 10

    @pytest.mark.asyncio
    async def test_get_context_statistics_empty(self, context_manager, mock_builder):
        """Test retrieval of context statistics when no items exist"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        result = await context_manager.get_context_statistics(organization_id="org-123")
        
        assert result["success"] is True
        assert len(result["statistics"]) == 0

    @pytest.mark.asyncio
    async def test_get_context_statistics_database_error(self, context_manager, mock_builder):
        """Test retrieval of context statistics with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Query failed')
        
        result = await context_manager.get_context_statistics(organization_id="org-123")
        
        assert result["success"] is False
        assert "Query failed" in result["error"]

    # ==================== BULK OPERATIONS TESTS ====================

    @pytest.mark.asyncio
    async def test_bulk_add_context_items_success(self, context_manager, mock_builder):
        """Test successful bulk addition of context items"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        bulk_items = [
            {
                "organization_id": "org-123",
                "rag_feature": "best_practice_kb",
                "item_id": "bulk_item_1",
                "item_type": "knowledge_chunk",
                "item_title": "Bulk Item 1",
                "item_content": "Bulk content 1",
                "status": "included",
                "priority": 1,
                "confidence_score": 0.8
            },
            {
                "organization_id": "org-123",
                "rag_feature": "best_practice_kb",
                "item_id": "bulk_item_2",
                "item_type": "knowledge_chunk",
                "item_title": "Bulk Item 2",
                "item_content": "Bulk content 2",
                "status": "included",
                "priority": 2,
                "confidence_score": 0.9
            }
        ]
        
        result = await context_manager.bulk_add_context_items(bulk_items)
        
        assert result["success"] is True
        assert result["added_count"] == 2

    @pytest.mark.asyncio
    async def test_bulk_add_context_items_partial_success(self, context_manager, mock_builder):
        """Test bulk addition of context items with partial success"""
        # First item succeeds, second fails
        mock_builder.setup_table_data('rag_context_items', [])
        
        bulk_items = [
            {
                "organization_id": "org-123",
                "rag_feature": "best_practice_kb",
                "item_id": "bulk_item_1",
                "item_type": "knowledge_chunk",
                "item_title": "Bulk Item 1",
                "item_content": "Bulk content 1",
                "status": "included",
                "priority": 1,
                "confidence_score": 0.8
            },
            {
                "organization_id": "org-123",
                "rag_feature": "best_practice_kb",
                "item_id": "bulk_item_2",
                "item_type": "knowledge_chunk",
                "item_title": "Bulk Item 2",
                "item_content": "Bulk content 2",
                "status": "included",
                "priority": 2,
                "confidence_score": 1.5  # Invalid confidence score
            }
        ]
        
        result = await context_manager.bulk_add_context_items(bulk_items)
        
        assert result["success"] is True
        assert result["added_count"] == 1
        assert result["error_count"] == 1

    @pytest.mark.asyncio
    async def test_bulk_add_context_items_database_error(self, context_manager, mock_builder):
        """Test bulk addition of context items with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Bulk insert failed')
        
        bulk_items = [{
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            "item_id": "bulk_item_1",
            "item_type": "knowledge_chunk",
            "item_title": "Bulk Item 1",
            "item_content": "Bulk content 1",
            "status": "included",
            "priority": 1,
            "confidence_score": 0.8
        }]
        
        result = await context_manager.bulk_add_context_items(bulk_items)
        
        assert result["success"] is False
        assert "Bulk insert failed" in result["error"]

    @pytest.mark.asyncio
    async def test_bulk_update_context_items_success(self, context_manager, mock_builder):
        """Test successful bulk update of context items"""
        bulk_updates = [
            {
                "item_id": "context-123",
                "update_data": {"item_title": "Updated Title 1", "confidence_score": 0.9}
            },
            {
                "item_id": "context-456",
                "update_data": {"item_title": "Updated Title 2", "confidence_score": 0.8}
            }
        ]
        
        result = await context_manager.bulk_update_context_items(bulk_updates)
        
        assert result["success"] is True
        assert result["updated_count"] == 2

    @pytest.mark.asyncio
    async def test_bulk_update_context_items_database_error(self, context_manager, mock_builder):
        """Test bulk update of context items with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Bulk update failed')
        
        bulk_updates = [{
            "item_id": "context-123",
            "update_data": {"item_title": "Updated Title"}
        }]
        
        result = await context_manager.bulk_update_context_items(bulk_updates)
        
        assert result["success"] is False
        assert "Bulk update failed" in result["error"]

    @pytest.mark.asyncio
    async def test_bulk_remove_context_items_success(self, context_manager, mock_builder):
        """Test successful bulk removal of context items"""
        item_ids = ["context-123", "context-456", "context-789"]
        
        result = await context_manager.bulk_remove_context_items(item_ids)
        
        assert result["success"] is True
        assert result["removed_count"] == 3

    @pytest.mark.asyncio
    async def test_bulk_remove_context_items_database_error(self, context_manager, mock_builder):
        """Test bulk removal of context items with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Bulk delete failed')
        
        item_ids = ["context-123", "context-456"]
        
        result = await context_manager.bulk_remove_context_items(item_ids)
        
        assert result["success"] is False
        assert "Bulk delete failed" in result["error"]

    # ==================== HELPER METHOD TESTS ====================

    @pytest.mark.asyncio
    async def test_validate_context_item_success(self, context_manager):
        """Test successful validation of context item"""
        valid_item = {
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            "item_id": "knowledge_123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Knowledge",
            "item_content": "Test content",
            "status": "included",
            "priority": 1,
            "confidence_score": 0.9
        }
        
        result = context_manager._validate_context_item(valid_item)
        
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_context_item_missing_fields(self, context_manager):
        """Test validation of context item with missing fields"""
        invalid_item = {
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            # Missing required fields
        }
        
        result = context_manager._validate_context_item(invalid_item)
        
        assert result["valid"] is False
        assert "Missing required fields" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_context_item_invalid_confidence(self, context_manager):
        """Test validation of context item with invalid confidence score"""
        invalid_item = {
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            "item_id": "knowledge_123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Knowledge",
            "item_content": "Test content",
            "confidence_score": 1.5  # Invalid
        }
        
        result = context_manager._validate_context_item(invalid_item)
        
        assert result["valid"] is False
        assert "Confidence score must be between 0 and 1" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_context_item_invalid_status(self, context_manager):
        """Test validation of context item with invalid status"""
        invalid_item = {
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            "item_id": "knowledge_123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Knowledge",
            "item_content": "Test content",
            "status": "invalid_status"
        }
        
        result = context_manager._validate_context_item(invalid_item)
        
        assert result["valid"] is False
        assert "Invalid status" in result["error"]

    @pytest.mark.asyncio
    async def test_format_csv_data_success(self, context_manager):
        """Test successful formatting of CSV data"""
        context_items = [
            TestDataFactory.create_context_item({"id": "item-1", "item_title": "Item 1"}),
            TestDataFactory.create_context_item({"id": "item-2", "item_title": "Item 2"})
        ]
        
        csv_data = context_manager._format_csv_data(context_items)
        
        assert "Item 1" in csv_data
        assert "Item 2" in csv_data
        assert "organization_id" in csv_data  # Header

    @pytest.mark.asyncio
    async def test_parse_csv_data_success(self, context_manager):
        """Test successful parsing of CSV data"""
        csv_data = """organization_id,rag_feature,item_id,item_type,item_title,item_content,status,priority,confidence_score
org-123,best_practice_kb,parsed_item_1,knowledge_chunk,Parsed Item 1,Parsed content 1,included,1,0.8
org-123,best_practice_kb,parsed_item_2,knowledge_chunk,Parsed Item 2,Parsed content 2,included,2,0.9"""
        
        parsed_items = context_manager._parse_csv_data(csv_data)
        
        assert len(parsed_items) == 2
        assert parsed_items[0]["item_title"] == "Parsed Item 1"
        assert parsed_items[1]["item_title"] == "Parsed Item 2"

    @pytest.mark.asyncio
    async def test_parse_csv_data_invalid_format(self, context_manager):
        """Test parsing of CSV data with invalid format"""
        invalid_csv = "invalid,csv,format"
        
        parsed_items = context_manager._parse_csv_data(invalid_csv)
        
        assert len(parsed_items) == 0

    # ==================== EDGE CASE TESTS ====================

    @pytest.mark.asyncio
    async def test_get_context_items_empty_organization(self, context_manager, mock_builder):
        """Test retrieval of context items for empty organization"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        result = await context_manager.get_context_items(organization_id="empty-org")
        
        assert result["success"] is True
        assert len(result["items"]) == 0
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_search_context_items_empty_query(self, context_manager, mock_builder):
        """Test search of context items with empty query"""
        context_items = [TestDataFactory.create_context_item()]
        mock_builder.setup_table_data('rag_context_items', context_items)
        
        result = await context_manager.search_context_items(
            organization_id="org-123",
            query=""
        )
        
        assert result["success"] is True
        assert len(result["items"]) == 1  # Should return all items

    @pytest.mark.asyncio
    async def test_export_context_items_empty_data(self, context_manager, mock_builder):
        """Test export of context items with no data"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        export_config = {
            "format": "csv",
            "organization_id": "org-123"
        }
        
        result = await context_manager.export_context_items(export_config)
        
        assert result["success"] is True
        assert "csv_data" in result
        assert "organization_id" in result["csv_data"]  # Should have header

    @pytest.mark.asyncio
    async def test_import_context_items_empty_data(self, context_manager):
        """Test import of context items with empty data"""
        import_config = {
            "format": "csv",
            "organization_id": "org-123",
            "data": ""
        }
        
        result = await context_manager.import_context_items(import_config)
        
        assert result["success"] is True
        assert result["imported_count"] == 0

    @pytest.mark.asyncio
    async def test_bulk_add_context_items_empty_list(self, context_manager):
        """Test bulk addition of context items with empty list"""
        result = await context_manager.bulk_add_context_items([])
        
        assert result["success"] is True
        assert result["added_count"] == 0

    @pytest.mark.asyncio
    async def test_bulk_update_context_items_empty_list(self, context_manager):
        """Test bulk update of context items with empty list"""
        result = await context_manager.bulk_update_context_items([])
        
        assert result["success"] is True
        assert result["updated_count"] == 0

    @pytest.mark.asyncio
    async def test_bulk_remove_context_items_empty_list(self, context_manager):
        """Test bulk removal of context items with empty list"""
        result = await context_manager.bulk_remove_context_items([])
        
        assert result["success"] is True
        assert result["removed_count"] == 0
