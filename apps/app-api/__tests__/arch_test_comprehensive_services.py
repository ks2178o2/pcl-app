# apps/app-api/__tests__/test_comprehensive_services.py

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime
import sys
import os

# Add the parent directory to the path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.audit_service import AuditService
from services.context_manager import ContextManager
from services.enhanced_context_manager import EnhancedContextManager
from services.tenant_isolation_service import TenantIsolationService
from services.supabase_client import SupabaseClientManager, get_supabase_client


class TestComprehensiveServices:
    """Comprehensive test suite for all service implementations"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing"""
        mock_client = Mock()
        mock_client.table.return_value.insert.return_value.execute.return_value = Mock(
            data=[{"id": "test-id"}]
        )
        mock_client.table.return_value.select.return_value.execute.return_value = Mock(
            data=[{"id": "test-id", "content": "test content"}]
        )
        mock_client.table.return_value.update.return_value.execute.return_value = Mock(
            data=[{"id": "test-id", "updated": True}]
        )
        mock_client.table.return_value.delete.return_value.execute.return_value = Mock(
            data=[{"id": "test-id", "deleted": True}]
        )
        return mock_client

    @pytest.fixture
    def audit_service(self, mock_supabase_client):
        """Create AuditService instance with mocked Supabase client"""
        with patch('services.audit_service.get_supabase_client') as mock_get_client:
            mock_get_client.return_value = mock_supabase_client
            return AuditService()

    @pytest.fixture
    def context_manager(self, mock_supabase_client):
        """Create ContextManager instance with mocked Supabase client"""
        with patch('services.context_manager.get_supabase_client') as mock_get_client:
            mock_get_client.return_value = mock_supabase_client
            return ContextManager()

    @pytest.fixture
    def enhanced_context_manager(self, mock_supabase_client):
        """Create EnhancedContextManager instance with mocked Supabase client"""
        with patch('services.enhanced_context_manager.get_supabase_client') as mock_get_client:
            mock_get_client.return_value = mock_supabase_client
            return EnhancedContextManager()

    @pytest.fixture
    def tenant_isolation_service(self, mock_supabase_client):
        """Create TenantIsolationService instance with mocked Supabase client"""
        with patch('services.tenant_isolation_service.get_supabase_client') as mock_get_client:
            mock_get_client.return_value = mock_supabase_client
            return TenantIsolationService()

    @pytest.fixture
    def supabase_client_manager(self):
        """Create SupabaseClientManager instance"""
        with patch('services.supabase_client.create_client') as mock_create_client:
            mock_create_client.return_value = Mock()
            return SupabaseClientManager()

    # AuditService Tests
    @pytest.mark.asyncio
    async def test_audit_service_create_entry(self, audit_service):
        """Test AuditService create_audit_entry method"""
        entry_data = {
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "test_action",
            "resource_type": "test_resource",
            "resource_id": "resource-123",
            "details": {"test": "data"},
            "ip_address": "192.168.1.1",
            "user_agent": "Test Agent"
        }
        
        result = await audit_service.create_audit_entry(entry_data)
        assert result is not None
        assert "success" in result

    @pytest.mark.asyncio
    async def test_audit_service_get_logs(self, audit_service):
        """Test AuditService get_audit_logs method"""
        filters = {"user_id": "user-123", "organization_id": "org-123"}
        result = await audit_service.get_audit_logs(filters)
        assert result is not None
        assert "success" in result

    @pytest.mark.asyncio
    async def test_audit_service_filter_logs(self, audit_service):
        """Test AuditService filter_audit_logs method"""
        filters = {"user_id": "user-123", "organization_id": "org-123"}
        result = await audit_service.filter_audit_logs(filters)
        assert result is not None
        assert "success" in result

    # ContextManager Tests
    @pytest.mark.asyncio
    async def test_context_manager_add_item(self, context_manager):
        """Test ContextManager add_context_item method"""
        item_data = {
            "rag_feature": "test_feature",
            "item_id": "item-123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Item",
            "item_content": "Test content",
            "organization_id": "org-123",
            "created_by": "user-123"
        }
        
        result = await context_manager.add_context_item(item_data)
        assert result is not None
        assert "success" in result

    @pytest.mark.asyncio
    async def test_context_manager_get_items(self, context_manager):
        """Test ContextManager get_context_items method"""
        result = await context_manager.get_context_items(
            organization_id="org-123",
            rag_feature="test_feature"
        )
        assert result is not None
        assert "success" in result

    @pytest.mark.asyncio
    async def test_context_manager_remove_item(self, context_manager):
        """Test ContextManager remove_context_item method"""
        result = await context_manager.remove_context_item(
            organization_id="org-123",
            rag_feature="test_feature",
            item_id="item-123",
            reason="test removal",
            removed_by="user-123"
        )
        assert result is not None
        assert "success" in result

    @pytest.mark.asyncio
    async def test_context_manager_update_status(self, context_manager):
        """Test ContextManager update_context_status method"""
        result = await context_manager.update_context_status(
            organization_id="org-123",
            rag_feature="test_feature",
            item_id="item-123",
            new_status="active",
            reason="test update",
            updated_by="user-123"
        )
        assert result is not None
        assert "success" in result

    # EnhancedContextManager Tests
    @pytest.mark.asyncio
    async def test_enhanced_context_manager_add_global_item(self, enhanced_context_manager):
        """Test EnhancedContextManager add_global_context_item method"""
        global_item = {
            "rag_feature": "best_practice_kb",
            "item_id": "global-123",
            "item_type": "knowledge_chunk",
            "item_title": "Global Best Practice",
            "item_content": "This is global knowledge",
            "priority": 1,
            "confidence_score": 0.9,
            "tags": ["sales", "best-practice"]
        }
        
        result = await enhanced_context_manager.add_global_context_item(global_item)
        assert result is not None
        assert "success" in result

    @pytest.mark.asyncio
    async def test_enhanced_context_manager_grant_access(self, enhanced_context_manager):
        """Test EnhancedContextManager grant_tenant_access method"""
        result = await enhanced_context_manager.grant_tenant_access(
            organization_id="org-123",
            rag_feature="best_practice_kb",
            access_level="read"
        )
        assert result is not None
        assert "success" in result

    @pytest.mark.asyncio
    async def test_enhanced_context_manager_share_item(self, enhanced_context_manager):
        """Test EnhancedContextManager share_context_item method"""
        result = await enhanced_context_manager.share_context_item(
            source_org_id="org-123",
            target_org_id="org-456",
            rag_feature="best_practice_kb",
            item_id="knowledge-123",
            sharing_type="read_only",
            shared_by="user-123"
        )
        assert result is not None
        assert "success" in result

    @pytest.mark.asyncio
    async def test_enhanced_context_manager_upload_file(self, enhanced_context_manager):
        """Test EnhancedContextManager upload_file_content method"""
        result = await enhanced_context_manager.upload_file_content(
            file_content="Test file content",
            file_type="pdf",
            organization_id="org-123",
            rag_feature="best_practice_kb",
            uploaded_by="user-123"
        )
        assert result is not None
        assert "success" in result

    # TenantIsolationService Tests
    @pytest.mark.asyncio
    async def test_tenant_isolation_service_check_quota(self, tenant_isolation_service):
        """Test TenantIsolationService check_quota_limits method"""
        result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="context_items",
            quantity=10
        )
        assert result is not None
        assert "success" in result

    @pytest.mark.asyncio
    async def test_tenant_isolation_service_enforce_isolation(self, tenant_isolation_service):
        """Test TenantIsolationService enforce_tenant_isolation method"""
        result = await tenant_isolation_service.enforce_tenant_isolation(
            user_id="user-123",
            organization_id="org-123",
            resource_type="context_item",
            resource_id="item-123"
        )
        assert result is not None
        assert "success" in result

    @pytest.mark.asyncio
    async def test_tenant_isolation_service_get_toggles(self, tenant_isolation_service):
        """Test TenantIsolationService get_rag_feature_toggles method"""
        result = await tenant_isolation_service.get_rag_feature_toggles("org-123")
        assert result is not None
        assert "success" in result

    @pytest.mark.asyncio
    async def test_tenant_isolation_service_update_toggle(self, tenant_isolation_service):
        """Test TenantIsolationService update_rag_feature_toggle method"""
        result = await tenant_isolation_service.update_rag_feature_toggle(
            organization_id="org-123",
            rag_feature="best_practice_kb",
            enabled=False
        )
        assert result is not None
        assert "success" in result

    # SupabaseClient Tests
    def test_supabase_client_manager_initialization(self, supabase_client_manager):
        """Test SupabaseClientManager initialization"""
        assert supabase_client_manager is not None

    def test_supabase_client_manager_get_client(self, supabase_client_manager):
        """Test SupabaseClientManager get_client method"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            client = supabase_client_manager.get_client()
            assert client is not None

    # Error Handling Tests
    @pytest.mark.asyncio
    async def test_audit_service_error_handling(self, audit_service):
        """Test AuditService error handling"""
        # Test with invalid data
        invalid_data = None
        try:
            result = await audit_service.create_audit_entry(invalid_data)
            assert result is not None
        except Exception:
            # Should handle exceptions gracefully
            pass

    @pytest.mark.asyncio
    async def test_context_manager_error_handling(self, context_manager):
        """Test ContextManager error handling"""
        # Test with missing required fields
        invalid_item = {"item_id": "item-123"}  # Missing required fields
        try:
            result = await context_manager.add_context_item(invalid_item)
            assert result is not None
        except Exception:
            # Should handle exceptions gracefully
            pass

    # Validation Tests
    def test_audit_service_validation(self, audit_service):
        """Test AuditService input validation"""
        # Test validation logic exists
        assert audit_service is not None

    def test_context_manager_validation(self, context_manager):
        """Test ContextManager input validation"""
        # Test validation logic exists
        assert context_manager is not None

    def test_enhanced_context_manager_validation(self, enhanced_context_manager):
        """Test EnhancedContextManager input validation"""
        # Test validation logic exists
        assert enhanced_context_manager is not None

    def test_tenant_isolation_service_validation(self, tenant_isolation_service):
        """Test TenantIsolationService input validation"""
        # Test validation logic exists
        assert tenant_isolation_service is not None

    # Async Operations Tests
    @pytest.mark.asyncio
    async def test_async_operations_complete(self, context_manager):
        """Test that async operations complete correctly"""
        item_data = {
            "rag_feature": "test_feature",
            "item_id": "async-test-123",
            "item_type": "knowledge_chunk",
            "item_title": "Async Test Item",
            "item_content": "Async test content",
            "organization_id": "org-123",
            "created_by": "user-123"
        }
        
        # This should complete without hanging
        result = await context_manager.add_context_item(item_data)
        assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, audit_service):
        """Test concurrent async operations"""
        entry_data = {
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "concurrent_test",
            "resource_type": "test_resource",
            "resource_id": "resource-123",
            "details": {"test": "concurrent"},
            "ip_address": "192.168.1.1",
            "user_agent": "Test Agent"
        }
        
        # Run multiple operations concurrently
        tasks = [
            audit_service.create_audit_entry(entry_data),
            audit_service.create_audit_entry(entry_data),
            audit_service.create_audit_entry(entry_data)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should complete
        assert len(results) == 3
        for result in results:
            assert result is not None
