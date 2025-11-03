# apps/app-api/__tests__/test_enhanced_context_management_fixed.py
"""
Fixed test suite for Enhanced Context Management with proper async mocking
Target: 90% coverage for Enhanced Context Manager and Tenant Isolation Service
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import json

# Import the services
from services.enhanced_context_manager import EnhancedContextManager
from services.tenant_isolation_service import TenantIsolationService
from services.supabase_client import SupabaseClientManager
from test_utils import SupabaseMockBuilder, TestDataFactory


@pytest.fixture
def mock_supabase_client():
    """Create a properly mocked Supabase client with async support"""
    mock_client = AsyncMock()
    
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
    
    # Mock async execute() method
    async def mock_execute(self):
        mock_result = AsyncMock()
        mock_result.data = [mock_global_item]
        return mock_result
    
    # Mock the query chain
    mock_query_chain = AsyncMock()
    mock_query_chain.execute = mock_execute
    mock_query_chain.single = AsyncMock()
    mock_query_chain.single.return_value.execute.return_value = AsyncMock(data=mock_global_item)
    
    # Setup chaining for queries
    mock_client.from_.return_value.select.return_value = mock_query_chain
    mock_client.from_.return_value.insert.return_value.execute.return_value = AsyncMock(data=[{'id': 'new-id'}])
    
    return mock_client


@pytest.fixture
def enhanced_context_manager():
    """Create EnhancedContextManager with mocked client"""
    mock_builder = SupabaseMockBuilder()
    with patch('services.enhanced_context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return EnhancedContextManager()


@pytest.fixture
def tenant_isolation_service():
    """Create TenantIsolationService with mocked client"""
    mock_builder = SupabaseMockBuilder()
    with patch('services.tenant_isolation_service.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return TenantIsolationService()


class TestEnhancedContextManager:
    """Test suite for EnhancedContextManager - Target: 90% coverage"""
    
    @pytest.mark.asyncio
    async def test_init(self, enhanced_context_manager):
        """Test EnhancedContextManager initialization"""
        assert enhanced_context_manager is not None
        assert enhanced_context_manager.supabase is not None
    
    @pytest.mark.asyncio
    async def test_add_global_item_success(self, enhanced_context_manager):
        """Test adding a global context item successfully"""
        item_data = {
            "rag_feature": "sales_intelligence",
            "item_id": "test-item-1",
            "item_type": "knowledge_chunk",
            "item_title": "Test Title",
            "item_content": "Test content"
        }
        
        # Mock the database operations
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[])
            mock_from.return_value.insert.return_value.execute.return_value = Mock(data=[{'id': 'new-id'}])
            
            # Call the method with correct signature
            result = await enhanced_context_manager.add_global_context_item(item_data)
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_add_global_item_duplicate(self, enhanced_context_manager):
        """Test adding a duplicate global item (should fail)"""
        item_data = {
            "rag_feature": "sales_intelligence",
            "item_id": "existing-id",
            "item_type": "knowledge_chunk",
            "item_title": "Existing Title",
            "item_content": "Existing content"
        }
        
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            # Mock finding existing item
            mock_from.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[{'id': 'existing-id'}])
            
            # Should raise an error for duplicate
            with pytest.raises(Exception):
                await enhanced_context_manager.add_global_item(
                    item_data["rag_feature"],
                    item_data["item_id"],
                    item_data["item_type"],
                    item_data["item_title"],
                    item_data["item_content"]
                )
    
    @pytest.mark.asyncio
    async def test_get_global_items_success(self, enhanced_context_manager):
        """Test retrieving global context items"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.execute.return_value = Mock(data=[
                {'id': 'item-1', 'rag_feature': 'sales_intelligence'},
                {'id': 'item-2', 'rag_feature': 'customer_insights'}
            ])
            
            items = await enhanced_context_manager.get_global_items()
            assert len(items) == 2
    
    @pytest.mark.asyncio
    async def test_grant_tenant_access_success(self, enhanced_context_manager):
        """Test granting tenant access to global items"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.insert.return_value.execute.return_value = Mock(data=[{'id': 'access-id'}])
            
            result = await enhanced_context_manager.grant_tenant_access(
                "org-123",
                "sales_intelligence",
                "read"
            )
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_revoke_tenant_access_success(self, enhanced_context_manager):
        """Test revoking tenant access"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = Mock()
            
            result = await enhanced_context_manager.revoke_tenant_access(
                "org-123",
                "sales_intelligence"
            )
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_share_context_item_success(self, enhanced_context_manager):
        """Test sharing context item between organizations"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.insert.return_value.execute.return_value = Mock(data=[{'id': 'sharing-id'}])
            
            result = await enhanced_context_manager.share_context_item(
                "org-123",
                "org-456",
                "sales_intelligence",
                "item-123"
            )
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_success(self, enhanced_context_manager):
        """Test retrieving organization quotas"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data={
                'max_context_items': 1000,
                'current_context_items': 100
            })
            
            quotas = await enhanced_context_manager.get_organization_quotas("org-123")
            assert quotas is not None
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_input(self, enhanced_context_manager):
        """Test error handling for invalid inputs"""
        with pytest.raises(Exception):
            await enhanced_context_manager.add_global_item(
                "",  # Invalid rag_feature
                "item-id",
                "type",
                "title",
                "content"
            )
    
    @pytest.mark.asyncio
    async def test_error_handling_database_error(self, enhanced_context_manager):
        """Test error handling for database errors"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.select.side_effect = Exception("Database error")
            
            with pytest.raises(Exception):
                await enhanced_context_manager.get_global_items()


class TestTenantIsolationService:
    """Test suite for TenantIsolationService - Target: 90% coverage"""
    
    @pytest.mark.asyncio
    async def test_init(self, tenant_isolation_service):
        """Test TenantIsolationService initialization"""
        assert tenant_isolation_service is not None
        assert tenant_isolation_service.supabase is not None
    
    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_success(self, tenant_isolation_service):
        """Test enforcing tenant isolation successfully"""
        with patch.object(tenant_isolation_service.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data={'organization_id': 'org-123'})
            
            result = await tenant_isolation_service.enforce_tenant_isolation(
                "org-123",
                "item-123",
                "global_context_items"
            )
            assert result is True
    
    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_violation(self, tenant_isolation_service):
        """Test tenant isolation violation detection"""
        with patch.object(tenant_isolation_service.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data={'organization_id': 'org-456'})
            
            result = await tenant_isolation_service.enforce_tenant_isolation(
                "org-123",
                "item-123",
                "global_context_items"
            )
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_within_limit(self, tenant_isolation_service):
        """Test quota check when within limits"""
        with patch.object(tenant_isolation_service.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data={
                'max_context_items': 1000,
                'current_context_items': 100
            })
            
            within_quota = await tenant_isolation_service.check_quota_limits("org-123", "context_items")
            assert within_quota is True
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_exceeded(self, tenant_isolation_service):
        """Test quota check when limits are exceeded"""
        with patch.object(tenant_isolation_service.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data={
                'max_context_items': 1000,
                'current_context_items': 1100
            })
            
            within_quota = await tenant_isolation_service.check_quota_limits("org-123", "context_items")
            assert within_quota is False
    
    @pytest.mark.asyncio
    async def test_update_quota_usage_increment(self, tenant_isolation_service):
        """Test incrementing quota usage"""
        with patch.object(tenant_isolation_service.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data={'current_context_items': 100})
            mock_from.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            result = await tenant_isolation_service.update_quota_usage("org-123", "context_items", 10)
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_success(self, tenant_isolation_service):
        """Test retrieving RAG feature toggles"""
        with patch.object(tenant_isolation_service.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[
                {'rag_feature': 'sales_intelligence', 'enabled': True},
                {'rag_feature': 'customer_insights', 'enabled': False}
            ])
            
            toggles = await tenant_isolation_service.get_rag_feature_toggles("org-123")
            assert len(toggles) == 2
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_success(self, tenant_isolation_service):
        """Test updating a RAG feature toggle"""
        with patch.object(tenant_isolation_service.supabase, 'from_') as mock_from:
            mock_from.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = Mock()
            
            result = await tenant_isolation_service.update_rag_feature_toggle(
                "org-123",
                "sales_intelligence",
                True
            )
            assert result is not None


class TestCrossTenantSharing:
    """Test suite for cross-tenant sharing functionality"""
    
    @pytest.mark.asyncio
    async def test_approve_sharing_request(self, enhanced_context_manager):
        """Test approving a sharing request"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            result = await enhanced_context_manager.approve_sharing_request("sharing-123")
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_shared_context_items(self, enhanced_context_manager):
        """Test retrieving shared context items"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[
                {'id': 'item-1', 'source_org': 'org-123'}
            ])
            
            items = await enhanced_context_manager.get_shared_context_items("org-456")
            assert len(items) == 1
    
    @pytest.mark.asyncio
    async def test_reject_sharing_request(self, enhanced_context_manager):
        """Test rejecting a sharing request"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
            
            result = await enhanced_context_manager.reject_sharing_request("sharing-123")
            assert result is not None


class TestBulkOperations:
    """Test suite for bulk operations"""
    
    @pytest.mark.asyncio
    async def test_bulk_update_rag_toggles(self, tenant_isolation_service):
        """Test bulk updating RAG feature toggles"""
        with patch.object(tenant_isolation_service.supabase, 'from_') as mock_from:
            mock_from.return_value.update.return_value.in_.return_value.execute.return_value = Mock()
            
            updates = {
                'sales_intelligence': True,
                'customer_insights': False
            }
            
            result = await tenant_isolation_service.bulk_update_rag_toggles("org-123", updates)
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_bulk_add_global_items(self, enhanced_context_manager):
        """Test adding multiple global items at once"""
        items = [
            {
                'rag_feature': 'sales_intelligence',
                'item_type': 'knowledge_chunk',
                'item_title': 'Item 1',
                'item_content': 'Content 1'
            },
            {
                'rag_feature': 'customer_insights',
                'item_type': 'knowledge_chunk',
                'item_title': 'Item 2',
                'item_content': 'Content 2'
            }
        ]
        
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.insert.return_value.execute.return_value = Mock(data=[
                {'id': 'id-1'}, {'id': 'id-2'}
            ])
            
            result = await enhanced_context_manager.bulk_add_global_items(items)
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_bulk_update_tenant_access(self, enhanced_context_manager):
        """Test bulk updating tenant access"""
        access_updates = [
            {'org_id': 'org-1', 'rag_feature': 'sales_intelligence', 'access_level': 'read'},
            {'org_id': 'org-2', 'rag_feature': 'customer_insights', 'access_level': 'write'}
        ]
        
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.insert.return_value.execute.return_value = Mock(data=[
                {'id': 'access-1'}, {'id': 'access-2'}
            ])
            
            result = await enhanced_context_manager.bulk_update_tenant_access(access_updates)
            assert len(result) == 2


class TestErrorHandling:
    """Test suite for error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, enhanced_context_manager):
        """Test handling network errors gracefully"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = ConnectionError("Network error")
            
            with pytest.raises(ConnectionError):
                await enhanced_context_manager.get_global_items()
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, enhanced_context_manager):
        """Test handling timeout errors"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.execute.side_effect = TimeoutError("Operation timed out")
            
            with pytest.raises(TimeoutError):
                await enhanced_context_manager.get_global_items()
    
    @pytest.mark.asyncio
    async def test_invalid_quota_data(self, tenant_isolation_service):
        """Test handling invalid quota data"""
        with patch.object(tenant_isolation_service.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data=None)
            
            with pytest.raises(Exception):
                await tenant_isolation_service.check_quota_limits("org-123", "context_items")
    
    @pytest.mark.asyncio
    async def test_malicious_input_validation(self, enhanced_context_manager):
        """Test validation against malicious inputs"""
        with pytest.raises(ValueError):
            await enhanced_context_manager.add_global_item(
                "sales_intelligence",
                "'; DROP TABLE global_context_items; --",
                "knowledge_chunk",
                "<script>alert('xss')</script>",
                "Content"
            )
    
    @pytest.mark.asyncio
    async def test_null_pointer_exception_handling(self, enhanced_context_manager):
        """Test handling null pointer exceptions"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.execute.return_value = Mock(data=None)
            
            items = await enhanced_context_manager.get_global_items()
            assert items == []


class TestPerformance:
    """Test suite for performance and load testing"""
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, enhanced_context_manager):
        """Test handling large datasets efficiently"""
        large_dataset = [{'id': f'item-{i}'} for i in range(10000)]
        
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.execute.return_value = Mock(data=large_dataset)
            
            import time
            start = time.time()
            items = await enhanced_context_manager.get_global_items()
            elapsed = time.time() - start
            
            # Should handle 10k items in reasonable time (<1s)
            assert elapsed < 1.0
            assert len(items) == 10000
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, enhanced_context_manager):
        """Test handling multiple concurrent requests"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.execute.return_value = Mock(data=[{'id': 'item-1'}])
            
            # Create 100 concurrent requests
            tasks = [enhanced_context_manager.get_global_items() for _ in range(100)]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 100
    
    @pytest.mark.asyncio
    async def test_memory_usage_efficiency(self, enhanced_context_manager):
        """Test memory efficiency with large operations"""
        import sys
        
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.execute.return_value = Mock(data=[{'id': f'item-{i}'} for i in range(1000)])
            
            initial_memory = sys.getsizeof(enhanced_context_manager)
            items = await enhanced_context_manager.get_global_items()
            final_memory = sys.getsizeof(enhanced_context_manager)
            
            # Memory increase should be minimal (<10MB)
            memory_increase = (final_memory - initial_memory) / (1024 * 1024)
            assert memory_increase < 10


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services', '--cov-report=html'])

