# apps/app-api/__tests__/test_enhanced_context_management.py

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

# Import the enhanced services
from services.enhanced_context_manager import EnhancedContextManager
from services.tenant_isolation_service import TenantIsolationService
from services.supabase_client import SupabaseClientManager

class TestEnhancedContextManagement:
    """Test suite for enhanced context management features"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Create a properly mocked Supabase client"""
        mock_client = Mock()
        
        # Mock data responses
        mock_global_item = {
            "id": "global-123",
            "rag_feature": "best_practice_kb",
            "item_id": "global-knowledge-123",
            "item_type": "knowledge_chunk",
            "item_title": "Global Best Practice",
            "item_content": "This is global knowledge",
            "status": "active",
            "priority": 1,
            "confidence_score": 0.9,
            "created_at": "2024-01-15T10:00:00Z"
        }
        
        mock_tenant_access = {
            "id": "access-123",
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            "access_level": "read",
            "enabled": True
        }
        
        mock_context_sharing = {
            "id": "sharing-123",
            "source_organization_id": "org-123",
            "target_organization_id": "org-456",
            "rag_feature": "best_practice_kb",
            "item_id": "knowledge-123",
            "sharing_type": "read_only",
            "status": "approved"
        }
        
        mock_quotas = {
            "id": "quota-123",
            "organization_id": "org-123",
            "max_context_items": 1000,
            "max_global_access_features": 10,
            "max_sharing_requests": 50,
            "current_context_items": 100,
            "current_global_access": 2,
            "current_sharing_requests": 5
        }
        
        # Mock insert operations
        mock_insert_result = Mock()
        mock_insert_result.data = [{'id': 'new-item-id'}]
        mock_client.from_.return_value.insert.return_value.execute.return_value = mock_insert_result
        
        # Mock select operations for duplicate checking
        mock_duplicate_check = Mock()
        mock_duplicate_check.data = []  # No duplicates
        mock_client.from_.return_value.select.return_value.eq.return_value.execute.return_value = mock_duplicate_check
        
        # Mock select operations
        mock_select_result = Mock()
        mock_select_result.data = [mock_global_item]
        mock_select_result.count = 1
        
        mock_query_chain = Mock()
        mock_query_chain.eq.return_value = mock_query_chain
        mock_query_chain.order.return_value = mock_query_chain
        mock_query_chain.range.return_value = mock_query_chain
        mock_query_chain.execute.return_value = mock_select_result
        mock_query_chain.single.return_value.execute.return_value = Mock(data=mock_global_item)
        
        mock_client.from_.return_value.select.return_value = mock_query_chain
        
        # Mock select operations
        mock_select_result = Mock()
        mock_select_result.data = [mock_global_item]
        mock_select_result.count = 1
        
        # Create separate mock chains for different query patterns
        mock_query_chain = Mock()
        mock_query_chain.eq.return_value = mock_query_chain
        mock_query_chain.order.return_value = mock_query_chain
        mock_query_chain.range.return_value = mock_query_chain
        mock_query_chain.execute.return_value = mock_select_result
        mock_query_chain.single.return_value.execute.return_value = Mock(data=mock_global_item)
        
        # Mock for duplicate checking (returns empty)
        mock_duplicate_chain = Mock()
        mock_duplicate_chain.eq.return_value = mock_duplicate_chain
        mock_duplicate_chain.execute.return_value = Mock(data=[])
        
        # Mock for access checking
        mock_access_chain = Mock()
        mock_access_chain.eq.return_value = mock_access_chain
        mock_access_chain.eq.return_value = mock_access_chain
        mock_access_chain.eq.return_value = mock_access_chain
        mock_access_chain.execute.return_value = Mock(data=[mock_tenant_access])
        
        # Set up different return values based on table name
        def mock_from_side_effect(table_name):
            mock_table = Mock()
            if table_name == 'global_context_items':
                mock_table.select.return_value = mock_query_chain
                mock_table.insert.return_value.execute.return_value = mock_insert_result
            elif table_name == 'tenant_context_access':
                mock_table.select.return_value = mock_access_chain
                mock_table.insert.return_value.execute.return_value = mock_insert_result
                mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_result
            else:
                mock_table.select.return_value = mock_query_chain
                mock_table.insert.return_value.execute.return_value = mock_insert_result
                mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_result
                mock_table.delete.return_value.eq.return_value.execute.return_value = mock_delete_result
            return mock_table
        
        # Mock update operations
        mock_update_result = Mock()
        mock_update_result.data = [{'id': 'updated-item-id'}]
        
        # Mock delete operations
        mock_delete_result = Mock()
        mock_delete_result.data = [{'id': 'deleted-item-id'}]
        
        mock_client.from_.side_effect = mock_from_side_effect
        
        return mock_client

    @pytest.fixture
    def enhanced_context_manager(self, mock_supabase_client):
        """Create EnhancedContextManager instance with mocked Supabase client"""
        with patch.object(SupabaseClientManager, 'get_client', return_value=mock_supabase_client):
            return EnhancedContextManager()

    @pytest.fixture
    def tenant_isolation_service(self, mock_supabase_client):
        """Create TenantIsolationService instance with mocked Supabase client"""
        with patch.object(SupabaseClientManager, 'get_client', return_value=mock_supabase_client):
            return TenantIsolationService()

    # ==================== APP-WIDE CONTEXT TESTS ====================

    @pytest.mark.asyncio
    async def test_add_global_context_item_success(self, enhanced_context_manager):
        """Test successful addition of a global context item"""
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
    async def test_add_global_context_item_invalid_confidence(self, enhanced_context_manager):
        """Test adding global context item with invalid confidence score"""
        global_item_data = {
            "rag_feature": "best_practice_kb",
            "item_id": "global-knowledge-124",
            "item_type": "knowledge_chunk",
            "item_title": "Invalid Global Knowledge",
            "item_content": "Content.",
            "confidence_score": 1.5  # Invalid score
        }
        
        result = await enhanced_context_manager.add_global_context_item(global_item_data)
        
        assert result["success"] is False
        assert "Confidence score must be between 0 and 1" in result["error"]

    @pytest.mark.asyncio
    async def test_get_global_context_items_success(self, enhanced_context_manager):
        """Test successful retrieval of global context items"""
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature="best_practice_kb",
            organization_id="org-123"
        )
        
        assert result["success"] is True
        assert len(result["items"]) == 1
        assert result["total_count"] == 1
        assert result["items"][0]["rag_feature"] == "best_practice_kb"

    @pytest.mark.asyncio
    async def test_get_global_context_items_no_access(self, enhanced_context_manager, mock_supabase_client):
        """Test retrieval of global context items when organization has no access"""
        # Mock no access
        mock_access_check = Mock()
        mock_access_check.data = []
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_access_check
        
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature="best_practice_kb",
            organization_id="org-no-access"
        )
        
        assert result["success"] is True
        assert len(result["items"]) == 0
        assert "No access to this RAG feature" in result["message"]

    # ==================== TENANT ACCESS MANAGEMENT TESTS ====================

    @pytest.mark.asyncio
    async def test_grant_tenant_access_success(self, enhanced_context_manager):
        """Test successful granting of tenant access"""
        result = await enhanced_context_manager.grant_tenant_access(
            organization_id="org-123",
            rag_feature="best_practice_kb",
            access_level="read"
        )
        
        assert result["success"] is True
        assert "access_id" in result

    @pytest.mark.asyncio
    async def test_revoke_tenant_access_success(self, enhanced_context_manager):
        """Test successful revocation of tenant access"""
        result = await enhanced_context_manager.revoke_tenant_access(
            organization_id="org-123",
            rag_feature="best_practice_kb"
        )
        
        assert result["success"] is True
        assert "revoked_id" in result

    # ==================== CROSS-TENANT SHARING TESTS ====================

    @pytest.mark.asyncio
    async def test_share_context_item_success(self, enhanced_context_manager):
        """Test successful sharing of context item"""
        result = await enhanced_context_manager.share_context_item(
            source_org_id="org-123",
            target_org_id="org-456",
            rag_feature="best_practice_kb",
            item_id="knowledge-123",
            sharing_type="read_only",
            shared_by="user-123"
        )
        
        assert result["success"] is True
        assert "sharing_id" in result

    @pytest.mark.asyncio
    async def test_approve_sharing_request_success(self, enhanced_context_manager):
        """Test successful approval of sharing request"""
        result = await enhanced_context_manager.approve_sharing_request(
            sharing_id="sharing-123",
            approved_by="user-123"
        )
        
        assert result["success"] is True
        assert "approved_id" in result

    @pytest.mark.asyncio
    async def test_get_shared_context_items_success(self, enhanced_context_manager):
        """Test successful retrieval of shared context items"""
        result = await enhanced_context_manager.get_shared_context_items(
            organization_id="org-456",
            rag_feature="best_practice_kb"
        )
        
        assert result["success"] is True
        assert len(result["shared_items"]) == 1

    # ==================== ENHANCED UPLOAD TESTS ====================

    @pytest.mark.asyncio
    async def test_upload_file_content_success(self, enhanced_context_manager):
        """Test successful file content upload"""
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
    async def test_scrape_web_content_success(self, enhanced_context_manager):
        """Test successful web content scraping"""
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
    async def test_bulk_api_upload_success(self, enhanced_context_manager):
        """Test successful bulk API upload"""
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

    # ==================== QUOTA MANAGEMENT TESTS ====================

    @pytest.mark.asyncio
    async def test_get_organization_quotas_success(self, enhanced_context_manager):
        """Test successful retrieval of organization quotas"""
        result = await enhanced_context_manager.get_organization_quotas("org-123")
        
        assert result["success"] is True
        assert "quotas" in result
        assert result["quotas"]["organization_id"] == "org-123"

    @pytest.mark.asyncio
    async def test_update_organization_quotas_success(self, enhanced_context_manager):
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

    # ==================== TENANT ISOLATION TESTS ====================

    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_success(self, tenant_isolation_service):
        """Test successful tenant isolation enforcement"""
        result = await tenant_isolation_service.enforce_tenant_isolation(
            user_id="user-123",
            organization_id="org-123",
            resource_type="context_item",
            resource_id="item-123"
        )
        
        assert result["success"] is True
        assert result["access_granted"] is True

    @pytest.mark.asyncio
    async def test_check_quota_limits_within_limit(self, tenant_isolation_service):
        """Test quota limit check when within limits"""
        result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="context_items",
            quantity=10
        )
        
        assert result["success"] is True
        assert result["quota_check_passed"] is True

    @pytest.mark.asyncio
    async def test_check_quota_limits_exceeded(self, tenant_isolation_service, mock_supabase_client):
        """Test quota limit check when limits would be exceeded"""
        # Mock quotas with high current usage
        mock_quotas = Mock()
        mock_quotas.data = {
            "organization_id": "org-123",
            "current_context_items": 950,
            "max_context_items": 1000
        }
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_quotas
        
        result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="context_items",
            quantity=100  # This would exceed the limit
        )
        
        assert result["success"] is False
        assert result["quota_exceeded"] is True
        assert result["quota_type"] == "context_items"

    @pytest.mark.asyncio
    async def test_update_quota_usage_increment(self, tenant_isolation_service):
        """Test quota usage update with increment"""
        result = await tenant_isolation_service.update_quota_usage(
            organization_id="org-123",
            operation_type="context_items",
            quantity=5,
            operation="increment"
        )
        
        assert result["success"] is True
        assert "updated_quotas" in result

    @pytest.mark.asyncio
    async def test_update_quota_usage_decrement(self, tenant_isolation_service):
        """Test quota usage update with decrement"""
        result = await tenant_isolation_service.update_quota_usage(
            organization_id="org-123",
            operation_type="context_items",
            quantity=3,
            operation="decrement"
        )
        
        assert result["success"] is True
        assert "updated_quotas" in result

    # ==================== RAG FEATURE TOGGLES TESTS ====================

    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_success(self, tenant_isolation_service):
        """Test successful retrieval of RAG feature toggles"""
        result = await tenant_isolation_service.get_rag_feature_toggles("org-123")
        
        assert result["success"] is True
        assert "toggles" in result

    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_success(self, tenant_isolation_service):
        """Test successful update of RAG feature toggle"""
        result = await tenant_isolation_service.update_rag_feature_toggle(
            organization_id="org-123",
            rag_feature="best_practice_kb",
            enabled=False
        )
        
        assert result["success"] is True
        assert "toggle" in result

    @pytest.mark.asyncio
    async def test_bulk_update_rag_toggles_success(self, tenant_isolation_service):
        """Test successful bulk update of RAG feature toggles"""
        toggle_updates = {
            "best_practice_kb": True,
            "customer_insight_rag": False,
            "success_pattern_rag": True
        }
        
        result = await tenant_isolation_service.bulk_update_rag_toggles(
            organization_id="org-123",
            toggle_updates=toggle_updates
        )
        
        assert result["success"] is True
        assert result["total_updated"] == 3

    # ==================== INTEGRATION TESTS ====================

    @pytest.mark.asyncio
    async def test_end_to_end_context_workflow(self, enhanced_context_manager, tenant_isolation_service):
        """Test end-to-end context management workflow"""
        # 1. Add global context item
        global_item = {
            "rag_feature": "best_practice_kb",
            "item_id": "e2e-global-123",
            "item_type": "knowledge_chunk",
            "item_title": "E2E Test Knowledge",
            "item_content": "End-to-end test content",
            "priority": 1,
            "confidence_score": 0.9
        }
        
        add_result = await enhanced_context_manager.add_global_context_item(global_item)
        assert add_result["success"] is True
        
        # 2. Grant tenant access
        access_result = await enhanced_context_manager.grant_tenant_access(
            organization_id="org-123",
            rag_feature="best_practice_kb",
            access_level="read"
        )
        assert access_result["success"] is True
        
        # 3. Check quota limits
        quota_result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="global_access",
            quantity=1
        )
        assert quota_result["success"] is True
        
        # 4. Update quota usage
        usage_result = await tenant_isolation_service.update_quota_usage(
            organization_id="org-123",
            operation_type="global_access",
            quantity=1,
            operation="increment"
        )
        assert usage_result["success"] is True
        
        # 5. Get global context items
        items_result = await enhanced_context_manager.get_global_context_items(
            rag_feature="best_practice_kb",
            organization_id="org-123"
        )
        assert items_result["success"] is True

    @pytest.mark.asyncio
    async def test_error_handling_and_validation(self, enhanced_context_manager):
        """Test error handling and validation across services"""
        # Test missing required fields
        invalid_item = {
            "rag_feature": "test_feature",
            # Missing required fields
        }
        
        result = await enhanced_context_manager.add_global_context_item(invalid_item)
        assert result["success"] is False
        assert "cannot be empty" in result["error"]
        
        # Test invalid confidence score
        invalid_confidence_item = {
            "rag_feature": "test_feature",
            "item_id": "test-id",
            "item_type": "test_type",
            "item_title": "Test Title",
            "item_content": "Test Content",
            "confidence_score": 2.0  # Invalid
        }
        
        result = await enhanced_context_manager.add_global_context_item(invalid_confidence_item)
        assert result["success"] is False
        assert "Confidence score must be between 0 and 1" in result["error"]
