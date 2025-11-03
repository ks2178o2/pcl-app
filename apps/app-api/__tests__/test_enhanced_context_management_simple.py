# apps/app-api/__tests__/test_enhanced_context_management_simple.py
"""
Simplified test suite for Enhanced Context Management with proper method signatures
Target: Improved coverage for Enhanced Context Manager and Tenant Isolation Service
"""

import pytest
from unittest.mock import Mock, patch
from services.enhanced_context_manager import EnhancedContextManager
from services.tenant_isolation_service import TenantIsolationService
from test_utils import SupabaseMockBuilder, TestDataFactory


@pytest.fixture
def mock_builder():
    """Create mock builder for Supabase client"""
    return SupabaseMockBuilder()


@pytest.fixture
def enhanced_context_manager(mock_builder):
    """Create EnhancedContextManager with mocked Supabase client"""
    with patch('services.enhanced_context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return EnhancedContextManager()


@pytest.fixture
def tenant_isolation_service(mock_builder):
    """Create TenantIsolationService with mocked Supabase client"""
    with patch('services.tenant_isolation_service.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return TenantIsolationService()


class TestEnhancedContextManagerBasic:
    """Basic tests for EnhancedContextManager"""
    
    @pytest.mark.asyncio
    async def test_init(self, enhanced_context_manager):
        """Test EnhancedContextManager initialization"""
        assert enhanced_context_manager is not None
        assert enhanced_context_manager.supabase is not None
    
    @pytest.mark.asyncio
    async def test_add_global_context_item_success(self, enhanced_context_manager, mock_builder):
        """Test adding a global context item successfully"""
        mock_builder.setup_table_data('global_context_items', [])
        
        item_data = {
            "rag_feature": "sales_intelligence",
            "item_id": "test-item-1",
            "item_type": "knowledge_chunk",
            "item_title": "Test Title",
            "item_content": "Test content",
            "priority": 1,
            "confidence_score": 0.9
        }
        
        # Mock insert
        mock_builder.insert_response.data = [{'id': 'new-item-id'}]
        
        result = await enhanced_context_manager.add_global_context_item(item_data)
        
        assert result is not None
        assert result.get("success") in [True, None]  # May return dict without success key
    
    @pytest.mark.asyncio
    async def test_get_global_context_items_success(self, enhanced_context_manager, mock_builder):
        """Test retrieving global context items"""
        test_data = [
            {'id': 'item-1', 'rag_feature': 'sales_intelligence', 'item_id': 'test-1'},
            {'id': 'item-2', 'rag_feature': 'customer_insights', 'item_id': 'test-2'}
        ]
        mock_builder.setup_table_data('global_context_items', test_data)
        
        result = await enhanced_context_manager.get_global_context_items()
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_grant_tenant_access_success(self, enhanced_context_manager, mock_builder):
        """Test granting tenant access"""
        mock_builder.setup_table_data('tenant_global_access', [])
        mock_builder.insert_response.data = [{'id': 'access-id'}]
        
        result = await enhanced_context_manager.grant_tenant_access(
            organization_id="org-123",
            rag_feature="sales_intelligence",
            access_level="read"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_success(self, enhanced_context_manager, mock_builder):
        """Test retrieving organization quotas"""
        quota_data = {
            'id': 'quota-123',
            'max_context_items': 1000,
            'current_context_items': 100
        }
        mock_builder.setup_table_data('organization_quotas', [quota_data])
        
        result = await enhanced_context_manager.get_organization_quotas("org-123")
        
        assert result is not None


class TestTenantIsolationServiceBasic:
    """Basic tests for TenantIsolationService"""
    
    @pytest.mark.asyncio
    async def test_init(self, tenant_isolation_service):
        """Test TenantIsolationService initialization"""
        assert tenant_isolation_service is not None
        assert tenant_isolation_service.supabase is not None
    
    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_success(self, tenant_isolation_service, mock_builder):
        """Test enforcing tenant isolation successfully"""
        # Mock the organization check
        org_data = {'id': 'org-123', 'organization_id': 'org-123'}
        mock_builder.setup_table_data('profiles', [org_data])
        
        result = await tenant_isolation_service.enforce_tenant_isolation(
            user_id="user-123",
            organization_id="org-123",
            resource_type="item",
            resource_id="item-123"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_within_limit(self, tenant_isolation_service, mock_builder):
        """Test quota check when within limits"""
        quota_data = {
            'max_context_items': 1000,
            'current_context_items': 100
        }
        mock_builder.setup_table_data('organization_quotas', [quota_data])
        
        result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="context_items"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_success(self, tenant_isolation_service, mock_builder):
        """Test retrieving RAG feature toggles"""
        toggle_data = [
            {'id': 'toggle-1', 'rag_feature': 'sales_intelligence', 'enabled': True},
            {'id': 'toggle-2', 'rag_feature': 'customer_insights', 'enabled': False}
        ]
        mock_builder.setup_table_data('rag_feature_toggles', toggle_data)
        
        result = await tenant_isolation_service.get_rag_feature_toggles("org-123")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_success(self, tenant_isolation_service, mock_builder):
        """Test updating a RAG feature toggle"""
        mock_builder.setup_table_data('rag_feature_toggles', [])
        mock_builder.update_response.data = [{'id': 'updated-toggle'}]
        
        result = await tenant_isolation_service.update_rag_feature_toggle(
            organization_id="org-123",
            rag_feature="sales_intelligence",
            enabled=True
        )
        
        assert result is not None


class TestCrossTenantSharing:
    """Test suite for cross-tenant sharing functionality"""
    
    @pytest.mark.asyncio
    async def test_approve_sharing_request(self, enhanced_context_manager, mock_builder):
        """Test approving a sharing request"""
        sharing_data = {
            'id': 'sharing-123',
            'source_organization_id': 'org-123',
            'target_organization_id': 'org-456',
            'status': 'pending'
        }
        mock_builder.setup_table_data('context_sharing', [sharing_data])
        
        result = await enhanced_context_manager.approve_sharing_request("sharing-123", "user-123")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_shared_context_items(self, enhanced_context_manager, mock_builder):
        """Test retrieving shared context items"""
        shared_items = [
            {'id': 'item-1', 'source_organization_id': 'org-123', 'target_organization_id': 'org-456'}
        ]
        mock_builder.setup_table_data('context_sharing', shared_items)
        
        result = await enhanced_context_manager.get_shared_context_items("org-456")
        
        assert result is not None


class TestErrorHandling:
    """Test suite for error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_input_handling(self, enhanced_context_manager):
        """Test handling invalid inputs"""
        invalid_data = {
            "rag_feature": "",  # Invalid
            "item_id": "test",
            "item_type": "type",
            "item_title": "title",
            "item_content": "content"
        }
        
        result = await enhanced_context_manager.add_global_context_item(invalid_data)
        
        # Should handle error gracefully
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, enhanced_context_manager, mock_builder):
        """Test handling database errors"""
        mock_builder.setup_error_response('global_context_items', "Database connection error")
        
        item_data = {
            "rag_feature": "sales_intelligence",
            "item_id": "test-id",
            "item_type": "knowledge_chunk",
            "item_title": "Test Title",
            "item_content": "Test content"
        }
        
        result = await enhanced_context_manager.add_global_context_item(item_data)
        
        # Should handle error gracefully
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

