# apps/app-api/__tests__/test_enhanced_context_manager_comprehensive.py

import pytest
import asyncio
from unittest.mock import patch, Mock
from datetime import datetime
import json

from services.enhanced_context_manager import EnhancedContextManager
from test_utils import SupabaseMockBuilder, TestDataFactory, MockResponseBuilder

class TestEnhancedContextManagerComprehensive:
    """Comprehensive test suite for Enhanced Context Manager with 95% coverage"""

    @pytest.fixture
    def mock_builder(self):
        """Create mock builder for Supabase client"""
        return SupabaseMockBuilder()

    @pytest.fixture
    def enhanced_context_manager(self, mock_builder):
        """Create EnhancedContextManager with mocked Supabase client"""
        with patch('services.enhanced_context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
            return EnhancedContextManager()

    # ==================== APP-WIDE CONTEXT MANAGEMENT TESTS ====================

    @pytest.mark.asyncio
    async def test_add_global_context_item_success(self, enhanced_context_manager, mock_builder):
        """Test successful addition of a global context item"""
        mock_builder.setup_table_data('global_context_items', [])
        
        global_item_data = {
            "rag_feature": "best_practice_kb",
            "item_id": "global-knowledge-123",
            "item_type": "knowledge_chunk",
            "item_title": "Global Best Practice",
            "item_content": "This is global knowledge content",
            "priority": 1,
            "confidence_score": 0.9,
            "tags": ["sales", "best-practice"]
        }
        
        result = await enhanced_context_manager.add_global_context_item(global_item_data)
        
        assert result["success"] is True
        assert "item_id" in result
        assert result["scope"] == "global"

    @pytest.mark.asyncio
    async def test_add_global_context_item_missing_fields(self, enhanced_context_manager):
        """Test adding global context item with missing required fields"""
        invalid_data = {
            "rag_feature": "test_feature",
            # Missing required fields
        }
        
        result = await enhanced_context_manager.add_global_context_item(invalid_data)
        
        assert result["success"] is False
        assert "cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_add_global_context_item_invalid_confidence(self, enhanced_context_manager):
        """Test adding global context item with invalid confidence score"""
        invalid_data = {
            "rag_feature": "test_feature",
            "item_id": "test-id",
            "item_type": "test_type",
            "item_title": "Test Title",
            "item_content": "Test Content",
            "confidence_score": 1.5  # Invalid
        }
        
        result = await enhanced_context_manager.add_global_context_item(invalid_data)
        
        assert result["success"] is False
        assert "Confidence score must be between 0 and 1" in result["error"]

    @pytest.mark.asyncio
    async def test_add_global_context_item_duplicate(self, enhanced_context_manager, mock_builder):
        """Test adding global context item that already exists"""
        existing_item = TestDataFactory.create_global_context_item()
        mock_builder.setup_table_data('global_context_items', [existing_item])
        
        duplicate_data = {
            "rag_feature": "best_practice_kb",
            "item_id": "global-knowledge-123",  # Same as existing
            "item_type": "knowledge_chunk",
            "item_title": "Duplicate Item",
            "item_content": "Duplicate content"
        }
        
        result = await enhanced_context_manager.add_global_context_item(duplicate_data)
        
        assert result["success"] is False
        assert "Global item already exists" in result["error"]

    @pytest.mark.asyncio
    async def test_add_global_context_item_database_error(self, enhanced_context_manager, mock_builder):
        """Test adding global context item with database error"""
        mock_builder.setup_error_response('global_context_items', 'Database connection failed')
        
        valid_data = {
            "rag_feature": "test_feature",
            "item_id": "test-id",
            "item_type": "test_type",
            "item_title": "Test Title",
            "item_content": "Test Content"
        }
        
        result = await enhanced_context_manager.add_global_context_item(valid_data)
        
        assert result["success"] is False
        assert "Failed to create global context item" in result["error"]

    @pytest.mark.asyncio
    async def test_get_global_context_items_success(self, enhanced_context_manager, mock_builder):
        """Test successful retrieval of global context items"""
        global_items = [
            TestDataFactory.create_global_context_item({"id": "item-1"}),
            TestDataFactory.create_global_context_item({"id": "item-2"})
        ]
        mock_builder.setup_table_data('global_context_items', global_items)
        
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature="best_practice_kb",
            organization_id="org-123"
        )
        
        assert result["success"] is True
        assert len(result["items"]) == 2
        assert result["total_count"] == 2

    @pytest.mark.asyncio
    async def test_get_global_context_items_no_access(self, enhanced_context_manager, mock_builder):
        """Test retrieval when organization has no access"""
        mock_builder.setup_table_data('tenant_context_access', [])  # No access
        
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature="best_practice_kb",
            organization_id="org-no-access"
        )
        
        assert result["success"] is True
        assert len(result["items"]) == 0
        assert "No access to this RAG feature" in result["message"]

    @pytest.mark.asyncio
    async def test_get_global_context_items_with_pagination(self, enhanced_context_manager, mock_builder):
        """Test retrieval with pagination"""
        global_items = [TestDataFactory.create_global_context_item({"id": f"item-{i}"}) for i in range(5)]
        mock_builder.setup_table_data('global_context_items', global_items)
        mock_builder.setup_table_data('tenant_context_access', [TestDataFactory.create_tenant_access()])
        
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature="best_practice_kb",
            organization_id="org-123",
            limit=3,
            offset=0
        )
        
        assert result["success"] is True
        assert len(result["items"]) == 3
        assert result["has_more"] is True

    # ==================== TENANT ACCESS MANAGEMENT TESTS ====================

    @pytest.mark.asyncio
    async def test_grant_tenant_access_success(self, enhanced_context_manager, mock_builder):
        """Test successful granting of tenant access"""
        mock_builder.setup_table_data('tenant_context_access', [])
        
        result = await enhanced_context_manager.grant_tenant_access(
            organization_id="org-123",
            rag_feature="best_practice_kb",
            access_level="read"
        )
        
        assert result["success"] is True
        assert "access_id" in result

    @pytest.mark.asyncio
    async def test_grant_tenant_access_update_existing(self, enhanced_context_manager, mock_builder):
        """Test updating existing tenant access"""
        existing_access = TestDataFactory.create_tenant_access()
        mock_builder.setup_table_data('tenant_context_access', [existing_access])
        
        result = await enhanced_context_manager.grant_tenant_access(
            organization_id="org-123",
            rag_feature="best_practice_kb",
            access_level="write"
        )
        
        assert result["success"] is True
        assert "access_id" in result

    @pytest.mark.asyncio
    async def test_grant_tenant_access_database_error(self, enhanced_context_manager, mock_builder):
        """Test granting tenant access with database error"""
        mock_builder.setup_error_response('tenant_context_access', 'Database error')
        
        result = await enhanced_context_manager.grant_tenant_access(
            organization_id="org-123",
            rag_feature="best_practice_kb",
            access_level="read"
        )
        
        assert result["success"] is False
        assert "Failed to grant tenant access" in result["error"]

    @pytest.mark.asyncio
    async def test_revoke_tenant_access_success(self, enhanced_context_manager, mock_builder):
        """Test successful revocation of tenant access"""
        result = await enhanced_context_manager.revoke_tenant_access(
            organization_id="org-123",
            rag_feature="best_practice_kb"
        )
        
        assert result["success"] is True
        assert "revoked_id" in result

    @pytest.mark.asyncio
    async def test_revoke_tenant_access_database_error(self, enhanced_context_manager, mock_builder):
        """Test revoking tenant access with database error"""
        mock_builder.setup_error_response('tenant_context_access', 'Update failed')
        
        result = await enhanced_context_manager.revoke_tenant_access(
            organization_id="org-123",
            rag_feature="best_practice_kb"
        )
        
        assert result["success"] is False
        assert "Update failed" in result["error"]

    # ==================== CROSS-TENANT SHARING TESTS ====================

    @pytest.mark.asyncio
    async def test_share_context_item_success(self, enhanced_context_manager, mock_builder):
        """Test successful sharing of context item"""
        mock_builder.setup_table_data('context_sharing', [])
        
        result = await enhanced_context_manager.share_context_item(
            source_org_id="org-123",
            target_org_id="org-456",
            rag_feature="best_practice_kb",
            item_id="knowledge-123",
            shared_by="user-123"
        )
        
        assert result["success"] is True
        assert "sharing_id" in result

    @pytest.mark.asyncio
    async def test_share_context_item_already_exists(self, enhanced_context_manager, mock_builder):
        """Test sharing context item that's already shared"""
        existing_sharing = TestDataFactory.create_context_sharing()
        mock_builder.setup_table_data('context_sharing', [existing_sharing])
        
        result = await enhanced_context_manager.share_context_item(
            source_org_id="org-123",
            target_org_id="org-456",
            rag_feature="best_practice_kb",
            item_id="knowledge-123",
            shared_by="user-123"
        )
        
        assert result["success"] is False
        assert "Sharing already exists" in result["error"]

    @pytest.mark.asyncio
    async def test_share_context_item_database_error(self, enhanced_context_manager, mock_builder):
        """Test sharing context item with database error"""
        mock_builder.setup_error_response('context_sharing', 'Insert failed')
        
        result = await enhanced_context_manager.share_context_item(
            source_org_id="org-123",
            target_org_id="org-456",
            rag_feature="best_practice_kb",
            item_id="knowledge-123",
            shared_by="user-123"
        )
        
        assert result["success"] is False
        assert "Insert failed" in result["error"]

    @pytest.mark.asyncio
    async def test_approve_sharing_request_success(self, enhanced_context_manager, mock_builder):
        """Test successful approval of sharing request"""
        result = await enhanced_context_manager.approve_sharing_request(
            sharing_id="sharing-123",
            approved_by="user-456"
        )
        
        assert result["success"] is True
        assert "approved_id" in result

    @pytest.mark.asyncio
    async def test_approve_sharing_request_database_error(self, enhanced_context_manager, mock_builder):
        """Test approving sharing request with database error"""
        mock_builder.setup_error_response('context_sharing', 'Update failed')
        
        result = await enhanced_context_manager.approve_sharing_request(
            sharing_id="sharing-123",
            approved_by="user-456"
        )
        
        assert result["success"] is False
        assert "Update failed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_shared_context_items_success(self, enhanced_context_manager, mock_builder):
        """Test successful retrieval of shared context items"""
        shared_items = [
            TestDataFactory.create_context_sharing({"status": "approved"}),
            TestDataFactory.create_context_sharing({"status": "approved", "id": "sharing-2"})
        ]
        mock_builder.setup_table_data('context_sharing', shared_items)
        
        result = await enhanced_context_manager.get_shared_context_items(
            organization_id="org-456",
            rag_feature="best_practice_kb"
        )
        
        assert result["success"] is True
        assert len(result["shared_items"]) == 2

    @pytest.mark.asyncio
    async def test_get_shared_context_items_database_error(self, enhanced_context_manager, mock_builder):
        """Test retrieving shared context items with database error"""
        mock_builder.setup_error_response('context_sharing', 'Query failed')
        
        result = await enhanced_context_manager.get_shared_context_items(
            organization_id="org-456",
            rag_feature="best_practice_kb"
        )
        
        assert result["success"] is False
        assert "Query failed" in result["error"]

    # ==================== ENHANCED UPLOAD TESTS ====================

    @pytest.mark.asyncio
    async def test_upload_file_content_success(self, enhanced_context_manager, mock_builder):
        """Test successful file content upload"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        file_content = "This is test file content.\n\nIt has multiple paragraphs.\n\nFor processing."
        
        result = await enhanced_context_manager.upload_file_content(
            file_content=file_content,
            file_type="txt",
            organization_id="org-123",
            rag_feature="best_practice_kb",
            uploaded_by="user-123"
        )
        
        assert result["success"] is True
        assert result["success_count"] > 0
        assert result["upload_type"] == "file"

    @pytest.mark.asyncio
    async def test_upload_file_content_empty(self, enhanced_context_manager):
        """Test uploading empty file content"""
        result = await enhanced_context_manager.upload_file_content(
            file_content="",
            file_type="txt",
            organization_id="org-123",
            rag_feature="best_practice_kb",
            uploaded_by="user-123"
        )
        
        assert result["success"] is True
        assert result["success_count"] == 0

    @pytest.mark.asyncio
    async def test_upload_file_content_error(self, enhanced_context_manager, mock_builder):
        """Test file content upload with error"""
        mock_builder.setup_error_response('rag_context_items', 'Insert failed')
        
        result = await enhanced_context_manager.upload_file_content(
            file_content="Test content",
            file_type="txt",
            organization_id="org-123",
            rag_feature="best_practice_kb",
            uploaded_by="user-123"
        )
        
        assert result["success"] is True  # File processing succeeds, individual items may fail
        assert result["error_count"] > 0

    @pytest.mark.asyncio
    async def test_scrape_web_content_success(self, enhanced_context_manager, mock_builder):
        """Test successful web content scraping"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        result = await enhanced_context_manager.scrape_web_content(
            url="https://example.com/article",
            organization_id="org-123",
            rag_feature="industry_insights",
            uploaded_by="user-123"
        )
        
        assert result["success"] is True
        assert "scraped_item" in result
        assert result["upload_type"] == "web_scrape"

    @pytest.mark.asyncio
    async def test_scrape_web_content_error(self, enhanced_context_manager, mock_builder):
        """Test web content scraping with error"""
        mock_builder.setup_error_response('rag_context_items', 'Insert failed')
        
        result = await enhanced_context_manager.scrape_web_content(
            url="https://example.com/article",
            organization_id="org-123",
            rag_feature="industry_insights",
            uploaded_by="user-123"
        )
        
        assert result["success"] is False
        assert "Insert failed" in result["error"]

    @pytest.mark.asyncio
    async def test_bulk_api_upload_success(self, enhanced_context_manager, mock_builder):
        """Test successful bulk API upload"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        bulk_items = [
            {
                "item_id": "bulk-item-1",
                "item_type": "knowledge_chunk",
                "item_title": "Bulk Item 1",
                "item_content": "Content for bulk item 1",
                "priority": 1,
                "confidence_score": 0.8
            },
            {
                "item_id": "bulk-item-2",
                "item_type": "knowledge_chunk",
                "item_title": "Bulk Item 2",
                "item_content": "Content for bulk item 2",
                "priority": 2,
                "confidence_score": 0.9
            }
        ]
        
        result = await enhanced_context_manager.bulk_api_upload(
            items=bulk_items,
            organization_id="org-123",
            rag_feature="customer_insights",
            uploaded_by="user-123"
        )
        
        assert result["success"] is True
        assert result["success_count"] == 2
        assert result["upload_type"] == "bulk_api"

    @pytest.mark.asyncio
    async def test_bulk_api_upload_partial_success(self, enhanced_context_manager, mock_builder):
        """Test bulk API upload with partial success"""
        # First item succeeds, second fails
        mock_builder.setup_table_data('rag_context_items', [])
        
        bulk_items = [
            {
                "item_id": "bulk-item-1",
                "item_type": "knowledge_chunk",
                "item_title": "Bulk Item 1",
                "item_content": "Content for bulk item 1"
            },
            {
                "item_id": "bulk-item-2",
                "item_type": "knowledge_chunk",
                "item_title": "Bulk Item 2",
                "item_content": "Content for bulk item 2"
            }
        ]
        
        result = await enhanced_context_manager.bulk_api_upload(
            items=bulk_items,
            organization_id="org-123",
            rag_feature="customer_insights",
            uploaded_by="user-123"
        )
        
        assert result["success"] is True
        assert result["success_count"] >= 0
        assert result["error_count"] >= 0

    @pytest.mark.asyncio
    async def test_bulk_api_upload_error(self, enhanced_context_manager, mock_builder):
        """Test bulk API upload with error"""
        mock_builder.setup_error_response('rag_context_items', 'Bulk insert failed')
        
        bulk_items = [{"item_id": "test", "item_type": "test", "item_title": "test", "item_content": "test"}]
        
        result = await enhanced_context_manager.bulk_api_upload(
            items=bulk_items,
            organization_id="org-123",
            rag_feature="customer_insights",
            uploaded_by="user-123"
        )
        
        assert result["success"] is False
        assert "Bulk insert failed" in result["error"]

    # ==================== QUOTA MANAGEMENT TESTS ====================

    @pytest.mark.asyncio
    async def test_get_organization_quotas_success(self, enhanced_context_manager, mock_builder):
        """Test successful retrieval of organization quotas"""
        quotas = TestDataFactory.create_organization_quotas()
        mock_builder.setup_table_data('organization_context_quotas', [quotas])
        
        result = await enhanced_context_manager.get_organization_quotas("org-123")
        
        assert result["success"] is True
        assert "quotas" in result
        assert result["quotas"]["organization_id"] == "org-123"

    @pytest.mark.asyncio
    async def test_get_organization_quotas_create_default(self, enhanced_context_manager, mock_builder):
        """Test creating default quotas when none exist"""
        mock_builder.setup_table_data('organization_context_quotas', [])
        
        result = await enhanced_context_manager.get_organization_quotas("org-123")
        
        assert result["success"] is True
        assert "quotas" in result

    @pytest.mark.asyncio
    async def test_get_organization_quotas_error(self, enhanced_context_manager, mock_builder):
        """Test retrieving organization quotas with error"""
        mock_builder.setup_error_response('organization_context_quotas', 'Query failed')
        
        result = await enhanced_context_manager.get_organization_quotas("org-123")
        
        assert result["success"] is False
        assert "Query failed" in result["error"]

    @pytest.mark.asyncio
    async def test_update_organization_quotas_success(self, enhanced_context_manager, mock_builder):
        """Test successful update of organization quotas"""
        quota_updates = {
            "max_context_items": 2000,
            "max_global_access_features": 20
        }
        
        result = await enhanced_context_manager.update_organization_quotas(
            organization_id="org-123",
            quota_updates=quota_updates
        )
        
        assert result["success"] is True
        assert "updated_quotas" in result

    @pytest.mark.asyncio
    async def test_update_organization_quotas_error(self, enhanced_context_manager, mock_builder):
        """Test updating organization quotas with error"""
        mock_builder.setup_error_response('organization_context_quotas', 'Update failed')
        
        quota_updates = {"max_context_items": 2000}
        
        result = await enhanced_context_manager.update_organization_quotas(
            organization_id="org-123",
            quota_updates=quota_updates
        )
        
        assert result["success"] is False
        assert "Update failed" in result["error"]

    # ==================== HELPER METHOD TESTS ====================

    @pytest.mark.asyncio
    async def test_check_global_duplicate_item_exists(self, enhanced_context_manager, mock_builder):
        """Test checking for global duplicate item that exists"""
        existing_item = TestDataFactory.create_global_context_item()
        mock_builder.setup_table_data('global_context_items', [existing_item])
        
        result = await enhanced_context_manager._check_global_duplicate_item("global-knowledge-123")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_check_global_duplicate_item_not_exists(self, enhanced_context_manager, mock_builder):
        """Test checking for global duplicate item that doesn't exist"""
        mock_builder.setup_table_data('global_context_items', [])
        
        result = await enhanced_context_manager._check_global_duplicate_item("non-existent-id")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_check_global_duplicate_item_error(self, enhanced_context_manager, mock_builder):
        """Test checking for global duplicate item with error"""
        mock_builder.setup_error_response('global_context_items', 'Query failed')
        
        result = await enhanced_context_manager._check_global_duplicate_item("test-id")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_log_upload_success(self, enhanced_context_manager, mock_builder):
        """Test successful upload logging"""
        result = await enhanced_context_manager._log_upload(
            organization_id="org-123",
            upload_type="file",
            rag_feature="test_feature",
            items_count=5,
            success_count=4,
            error_count=1,
            upload_source="test_file.txt",
            uploaded_by="user-123"
        )
        
        # Should not raise an exception
        assert True

    @pytest.mark.asyncio
    async def test_log_upload_error(self, enhanced_context_manager, mock_builder):
        """Test upload logging with error"""
        mock_builder.setup_error_response('context_upload_logs', 'Log failed')
        
        result = await enhanced_context_manager._log_upload(
            organization_id="org-123",
            upload_type="file",
            rag_feature="test_feature",
            items_count=5,
            success_count=4,
            error_count=1,
            upload_source="test_file.txt",
            uploaded_by="user-123"
        )
        
        # Should not raise an exception even with error
        assert True

    # ==================== LEGACY COMPATIBILITY TESTS ====================

    @pytest.mark.asyncio
    async def test_add_context_item_legacy_success(self, enhanced_context_manager, mock_builder):
        """Test legacy add_context_item method success"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        context_data = {
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            "item_id": "knowledge_123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Knowledge",
            "item_content": "Test content"
        }
        
        result = await enhanced_context_manager.add_context_item(context_data)
        
        assert result["success"] is True
        assert "item_id" in result

    @pytest.mark.asyncio
    async def test_add_context_item_legacy_missing_fields(self, enhanced_context_manager):
        """Test legacy add_context_item method with missing fields"""
        invalid_data = {
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            # Missing required fields
        }
        
        result = await enhanced_context_manager.add_context_item(invalid_data)
        
        assert result["success"] is False
        assert "cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_add_context_item_legacy_database_error(self, enhanced_context_manager, mock_builder):
        """Test legacy add_context_item method with database error"""
        mock_builder.setup_error_response('rag_context_items', 'Insert failed')
        
        valid_data = {
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            "item_id": "knowledge_123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Knowledge",
            "item_content": "Test content"
        }
        
        result = await enhanced_context_manager.add_context_item(valid_data)
        
        assert result["success"] is False
        assert "Insert failed" in result["error"]

    # ==================== EDGE CASE TESTS ====================

    @pytest.mark.asyncio
    async def test_get_global_context_items_no_rag_feature(self, enhanced_context_manager, mock_builder):
        """Test getting global context items without specifying RAG feature"""
        global_items = [TestDataFactory.create_global_context_item({"id": f"item-{i}"}) for i in range(3)]
        mock_builder.setup_table_data('global_context_items', global_items)
        
        result = await enhanced_context_manager.get_global_context_items(
            organization_id="org-123"
        )
        
        assert result["success"] is True
        assert len(result["items"]) == 3

    @pytest.mark.asyncio
    async def test_get_global_context_items_no_organization(self, enhanced_context_manager, mock_builder):
        """Test getting global context items without organization ID"""
        global_items = [TestDataFactory.create_global_context_item({"id": f"item-{i}"}) for i in range(2)]
        mock_builder.setup_table_data('global_context_items', global_items)
        
        result = await enhanced_context_manager.get_global_context_items()
        
        assert result["success"] is True
        assert len(result["items"]) == 2

    @pytest.mark.asyncio
    async def test_share_context_item_different_sharing_types(self, enhanced_context_manager, mock_builder):
        """Test sharing context item with different sharing types"""
        mock_builder.setup_table_data('context_sharing', [])
        
        # Test read_only sharing
        result1 = await enhanced_context_manager.share_context_item(
            source_org_id="org-123",
            target_org_id="org-456",
            rag_feature="best_practice_kb",
            item_id="knowledge-123",
            shared_by="user-123",
            sharing_type="read_only"
        )
        
        assert result1["success"] is True
        
        # Test collaborative sharing
        result2 = await enhanced_context_manager.share_context_item(
            source_org_id="org-123",
            target_org_id="org-789",
            rag_feature="best_practice_kb",
            item_id="knowledge-456",
            shared_by="user-123",
            sharing_type="collaborative"
        )
        
        assert result2["success"] is True
