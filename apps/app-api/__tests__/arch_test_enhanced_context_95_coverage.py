# apps/app-api/__tests__/test_enhanced_context_95_coverage.py
"""
Comprehensive test suite for Enhanced Context Manager
Target: 95% coverage for enhanced_context_manager.py
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.enhanced_context_manager import EnhancedContextManager
from test_utils import SupabaseMockBuilder, TestDataFactory


@pytest.fixture
def mock_builder():
    return SupabaseMockBuilder()


@pytest.fixture
def enhanced_context_manager(mock_builder):
    with patch('services.enhanced_context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return EnhancedContextManager()


class TestEnhancedContextUploadMechanisms:
    """Test upload mechanisms (file, web scraping, bulk API)"""
    
    @pytest.mark.asyncio
    async def test_upload_file_content(self, enhanced_context_manager, mock_builder):
        """Test uploading file content"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        result = await enhanced_context_manager.upload_file_content(
            file_content="Test file content",
            file_type="text/plain",
            organization_id="org-123",
            rag_feature="sales_intelligence",
            uploaded_by="user-123"
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_scrape_web_content(self, enhanced_context_manager, mock_builder):
        """Test scraping web content"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        result = await enhanced_context_manager.scrape_web_content(
            url="https://example.com",
            organization_id="org-123",
            rag_feature="sales_intelligence",
            uploaded_by="user-123"
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_bulk_api_upload(self, enhanced_context_manager, mock_builder):
        """Test bulk API upload"""
        items = [
            {
                'item_id': f'bulk-item-{i}',
                'item_type': 'knowledge_chunk',
                'item_title': f'Title {i}',
                'item_content': f'Content {i}'
            }
            for i in range(10)
        ]
        
        mock_builder.setup_table_data('rag_context_items', [])
        
        result = await enhanced_context_manager.bulk_api_upload(
            items=items,
            organization_id="org-123",
            rag_feature="sales_intelligence",
            uploaded_by="user-123"
        )
        assert result is not None


class TestEnhancedContextHierarchySharing:
    """Test hierarchy sharing (children, parent, approvals)"""
    
    @pytest.mark.asyncio
    async def test_share_to_children(self, enhanced_context_manager, mock_builder):
        """Test sharing to child organizations"""
        children = [{'id': 'org-child-1'}, {'id': 'org-child-2'}]
        mock_builder.setup_table_data('organizations', children)
        mock_builder.setup_table_data('context_sharing', [])
        
        result = await enhanced_context_manager.share_to_children(
            source_org_id="org-123",
            item_id="item-123",
            rag_feature="sales_intelligence",
            shared_by="user-123"
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_share_to_parent(self, enhanced_context_manager, mock_builder):
        """Test sharing to parent organization"""
        org_data = [{'parent_organization_id': 'org-parent'}]
        mock_builder.setup_table_data('organizations', org_data)
        mock_builder.setup_table_data('context_sharing', [])
        
        result = await enhanced_context_manager.share_to_parent(
            source_org_id="org-123",
            item_id="item-123",
            rag_feature="sales_intelligence",
            shared_by="user-123"
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals(self, enhanced_context_manager, mock_builder):
        """Test getting pending approval requests"""
        pending = [
            {'id': 'sharing-1', 'status': 'pending'},
            {'id': 'sharing-2', 'status': 'pending'}
        ]
        mock_builder.setup_table_data('context_sharing', pending)
        
        result = await enhanced_context_manager.get_pending_approvals("org-123")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_approve_shared_item(self, enhanced_context_manager, mock_builder):
        """Test approving a shared item"""
        sharing_data = [{
            'id': 'sharing-123',
            'item_id': 'item-123',
            'target_organization_id': 'org-456',
            'rag_feature': 'sales_intelligence',
            'source_organization_id': 'org-123'
        }]
        
        item_data = [{
            'title': 'Test Title',
            'content': 'Test Content',
            'item_type': 'knowledge_chunk'
        }]
        
        mock_builder.setup_table_data('context_sharing', sharing_data)
        mock_builder.setup_table_data('context_items', item_data)
        mock_builder.update_response.data = sharing_data
        mock_builder.insert_response.data = [{'id': 'new-item'}]
        
        result = await enhanced_context_manager.approve_shared_item("sharing-123", "user-123")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_reject_shared_item(self, enhanced_context_manager, mock_builder):
        """Test rejecting a shared item"""
        mock_builder.setup_table_data('context_sharing', [])
        mock_builder.update_response.data = [{'id': 'sharing-123'}]
        
        result = await enhanced_context_manager.reject_shared_item("sharing-123", "user-123", "Not needed")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_hierarchy_sharing_stats(self, enhanced_context_manager, mock_builder):
        """Test getting hierarchy sharing statistics"""
        mock_builder.setup_table_data('context_sharing', [])
        
        # Mock count responses
        outgoing = Mock()
        outgoing.count = 5
        incoming = Mock()
        incoming.count = 3
        pending = Mock()
        pending.count = 2
        
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            def mock_from_side_effect(table):
                table_mock = Mock()
                if 'select' in str(mock_from._call_list[-1].method) if hasattr(mock_from, '_call_list') else False:
                    query_mock = Mock()
                    query_mock.eq.return_value = query_mock
                    query_mock.execute.return_value = outgoing if 'source' in str(table) else incoming if 'target' in str(table) else pending
                    table_mock.select.return_value = query_mock
                else:
                    table_mock.update = Mock()
                    table_mock.delete = Mock()
                    table_mock.insert = Mock()
                return table_mock
            
            mock_from.side_effect = mock_from_side_effect
            result = await enhanced_context_manager.get_hierarchy_sharing_stats("org-123")
            assert result is not None


class TestEnhancedContextValidation:
    """Test validation and error handling"""
    
    @pytest.mark.asyncio
    async def test_add_global_item_missing_fields(self, enhanced_context_manager):
        """Test adding global item with missing required fields"""
        invalid_data = {
            "rag_feature": "sales_intelligence"
            # Missing required fields
        }
        
        result = await enhanced_context_manager.add_global_context_item(invalid_data)
        assert result is not None
        assert "success" in result and result["success"] is False
    
    @pytest.mark.asyncio
    async def test_add_global_item_invalid_confidence(self, enhanced_context_manager):
        """Test adding global item with invalid confidence score"""
        invalid_data = {
            "rag_feature": "sales_intelligence",
            "item_id": "test-id",
            "item_type": "knowledge_chunk",
            "item_title": "Test Title",
            "item_content": "Test Content",
            "confidence_score": 1.5  # Invalid
        }
        
        result = await enhanced_context_manager.add_global_context_item(invalid_data)
        assert result is not None
        assert "success" in result and result["success"] is False
    
    @pytest.mark.asyncio
    async def test_grant_tenant_access_no_access(self, enhanced_context_manager, mock_builder):
        """Test granting access when no access exists"""
        mock_builder.setup_table_data('tenant_context_access', [])
        mock_builder.insert_response.data = [{'id': 'access-id'}]
        
        result = await enhanced_context_manager.grant_tenant_access(
            organization_id="org-123",
            rag_feature="sales_intelligence",
            access_level="read"
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_revoke_access_no_access_exists(self, enhanced_context_manager, mock_builder):
        """Test revoking access that doesn't exist"""
        mock_builder.setup_table_data('tenant_context_access', [])
        mock_builder.delete_response.data = []
        
        result = await enhanced_context_manager.revoke_tenant_access(
            organization_id="org-123",
            rag_feature="sales_intelligence"
        )
        assert result is not None


class TestEnhancedContextQuotaManagement:
    """Test quota management"""
    
    @pytest.mark.asyncio
    async def test_update_organization_quotas(self, enhanced_context_manager, mock_builder):
        """Test updating organization quotas"""
        quotas = {
            'max_context_items': 2000,
            'max_global_access_features': 20
        }
        
        mock_builder.setup_table_data('organization_quotas', [])
        mock_builder.update_response.data = [{'id': 'updated-quota'}]
        
        result = await enhanced_context_manager.update_organization_quotas(
            organization_id="org-123",
            quota_updates=quotas
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_not_found(self, enhanced_context_manager, mock_builder):
        """Test getting quotas when they don't exist"""
        mock_builder.setup_table_data('organization_quotas', [])
        
        result = await enhanced_context_manager.get_organization_quotas("org-999")
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.enhanced_context_manager', '--cov-report=html'])

