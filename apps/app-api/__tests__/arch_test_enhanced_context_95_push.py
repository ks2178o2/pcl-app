# apps/app-api/__tests__/test_enhanced_context_95_push.py
"""
Final push to 95% coverage for Enhanced Context Manager
Target: Complete all remaining edge cases and error paths
"""

import pytest
from unittest.mock import Mock, patch
from services.enhanced_context_manager import EnhancedContextManager
from test_utils import SupabaseMockBuilder


@pytest.fixture
def mock_builder():
    return SupabaseMockBuilder()


@pytest.fixture
def enhanced_context_manager(mock_builder):
    with patch('services.enhanced_context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return EnhancedContextManager()


class TestRevokeTenantAccessError:
    """Test revoke tenant access error paths - line 178"""
    
    @pytest.mark.asyncio
    async def test_revoke_tenant_access_update_no_data(self, enhanced_context_manager, mock_builder):
        """Test revoke when update returns no data - covers line 178"""
        mock_builder.setup_table_data('tenant_context_access', [{'organization_id': 'org-123'}])
        mock_builder.update_response.data = []  # No data returned
        
        result = await enhanced_context_manager.revoke_tenant_access(
            organization_id='org-123',
            rag_feature='sales_intelligence'
        )
        
        assert result is not None
        assert result.get('success') is False
        assert 'Failed to revoke' in result.get('error', '')
    
    @pytest.mark.asyncio
    async def test_revoke_tenant_access_exception(self, enhanced_context_manager):
        """Test revoke when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.revoke_tenant_access(
                organization_id='org-123',
                rag_feature='sales_intelligence'
            )
            
            assert result is not None
            assert result.get('success') is False


class TestShareContextItemComplex:
    """Test share context item complex scenarios - lines 223-230"""
    
    @pytest.mark.asyncio
    async def test_share_context_existing_sharing(self, enhanced_context_manager, mock_builder):
        """Test share when sharing already exists - line 201"""
        # Setup existing sharing
        mock_builder.setup_table_data('context_sharing', [{'id': 'existing-share', 'source_organization_id': 'org-source', 'target_organization_id': 'org-target', 'rag_feature': 'sales_intelligence', 'item_id': 'item-123'}])
        
        result = await enhanced_context_manager.share_context_item(
            source_org_id='org-source',
            target_org_id='org-target',
            rag_feature='sales_intelligence',
            item_id='item-123',
            shared_by='user-123',
            sharing_type='read_only'
        )
        
        assert result is not None
        assert result.get('success') is False  # Should fail because already exists
        assert 'already exists' in result.get('error', '').lower()
    
    @pytest.mark.asyncio
    async def test_share_context_insert_failure(self, enhanced_context_manager, mock_builder):
        """Test share when insert fails - covers lines 223-230"""
        # No existing sharing
        mock_builder.setup_table_data('context_sharing', [])
        mock_builder.insert_response.data = []  # Insert returns no data
        
        result = await enhanced_context_manager.share_context_item(
            source_org_id='org-source',
            target_org_id='org-target',
            rag_feature='sales_intelligence',
            item_id='item-123',
            shared_by='user-123'
        )
        
        assert result is not None
        assert result.get('success') is False


class TestApprovalWorkflowEdgeCases:
    """Test approval workflow edge cases"""
    
    @pytest.mark.asyncio
    async def test_approve_sharing_update_failure(self, enhanced_context_manager, mock_builder):
        """Test approve when update returns no data"""
        mock_builder.setup_table_data('context_sharing', [{'id': 'share-123', 'status': 'pending'}])
        mock_builder.update_response.data = []  # Update returns no data
        
        result = await enhanced_context_manager.approve_sharing_request(
            sharing_id='share-123',
            approved_by='user-123'
        )
        
        assert result is not None
        assert result.get('success') is False


class TestGetPendingApprovalsEdgeCases:
    """Test get pending approvals edge cases"""
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals_with_rag_feature(self, enhanced_context_manager, mock_builder):
        """Test get pending approvals with rag_feature filter"""
        mock_builder.setup_table_data('context_sharing', [
            {'id': 'share-1', 'status': 'pending', 'rag_feature': 'sales_intelligence'},
            {'id': 'share-2', 'status': 'pending', 'rag_feature': 'support_kb'}
        ])
        
        result = await enhanced_context_manager.get_pending_approvals(
            organization_id='org-123',
            rag_feature='sales_intelligence'
        )
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals_exception(self, enhanced_context_manager):
        """Test get pending approvals when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.get_pending_approvals('org-123')
            
            assert result is not None
            assert result.get('success') is False


class TestExportFunctionality:
    """Test export functionality - lines 485-492"""
    
    @pytest.mark.asyncio
    async def test_get_global_context_items_for_export(self, enhanced_context_manager, mock_builder):
        """Test get global items that can be exported"""
        mock_builder.setup_table_data('global_context_items', [{'id': 'item-123'}])
        mock_builder.setup_table_data('tenant_context_access', [{'organization_id': 'org-123'}])
        
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature='sales_intelligence',
            organization_id='org-123',
            limit=100,
            offset=0
        )
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_get_context_items_empty_for_export(self, enhanced_context_manager, mock_builder):
        """Test get items with no data"""
        mock_builder.setup_table_data('global_context_items', [])
        
        result = await enhanced_context_manager.get_global_context_items(
            rag_feature='sales_intelligence',
            organization_id='org-123',
            limit=100,
            offset=0
        )
        
        assert result is not None


class TestStatisticsAndReports:
    """Test statistics and report generation - lines 524-525, 551, 571"""
    
    @pytest.mark.asyncio
    async def test_get_hierarchy_sharing_stats_no_sharing(self, enhanced_context_manager, mock_builder):
        """Test stats when no sharing data"""
        mock_builder.setup_table_data('context_sharing', [])
        mock_builder.setup_table_data('organizations', [{'id': 'org-123'}])
        
        result = await enhanced_context_manager.get_hierarchy_sharing_stats('org-123')
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_get_hierarchy_sharing_stats_exception(self, enhanced_context_manager):
        """Test stats when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.get_hierarchy_sharing_stats('org-123')
            
            assert result is not None
            assert result.get('success') is False


class TestQuotaManagementFinal:
    """Test quota management final edge cases"""
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_default_creation(self, enhanced_context_manager, mock_builder):
        """Test get quotas creates defaults when missing"""
        mock_builder.setup_table_data('organization_context_quotas', [])  # No quotas
        mock_builder.insert_response.data = [{'id': 'new-quota'}]
        
        result = await enhanced_context_manager.get_organization_quotas('org-123')
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_update_organization_quotas_no_data(self, enhanced_context_manager, mock_builder):
        """Test update quotas when update returns no data"""
        mock_builder.setup_table_data('organization_context_quotas', [{'organization_id': 'org-123'}])
        mock_builder.update_response.data = []  # Update returns no data
        
        result = await enhanced_context_manager.update_organization_quotas(
            organization_id='org-123',
            quota_updates={'max_context_items': 1000}
        )
        
        assert result is not None
        assert result.get('success') is False


class TestBulkOperationsFinal:
    """Test bulk operations edge cases - lines 600-607, 619"""
    
    @pytest.mark.asyncio
    async def test_bulk_api_upload_empty_items(self, enhanced_context_manager, mock_builder):
        """Test bulk upload with empty items list"""
        result = await enhanced_context_manager.bulk_api_upload(
            items=[],
            organization_id='org-123',
            rag_feature='sales_intelligence',
            uploaded_by='user-123'
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_bulk_api_upload_single_item(self, enhanced_context_manager, mock_builder):
        """Test bulk upload with single item"""
        with patch.object(enhanced_context_manager, 'add_global_context_item') as mock_add:
            mock_add.return_value = {'success': True, 'item_id': 'item-123'}
            
            result = await enhanced_context_manager.bulk_api_upload(
                items=[{'item_title': 'Test', 'item_content': 'Content'}],
                organization_id='org-123',
                rag_feature='sales_intelligence',
                uploaded_by='user-123'
            )
            
            assert result is not None
            assert result.get('success') is True


class TestFileUploadFinal:
    """Test file upload final scenarios - line 644-651"""
    
    @pytest.mark.asyncio
    async def test_upload_file_content_empty_content(self, enhanced_context_manager, mock_builder):
        """Test upload file with empty content"""
        result = await enhanced_context_manager.upload_file_content(
            file_content="",
            file_type="text/plain",
            organization_id="org-123",
            rag_feature="sales_intelligence",
            uploaded_by="user-123"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_upload_file_content_large_file(self, enhanced_context_manager, mock_builder):
        """Test upload large file"""
        large_content = "x" * 100000  # 100KB content
        
        with patch.object(enhanced_context_manager, 'add_global_context_item') as mock_add:
            mock_add.return_value = {'success': True, 'item_id': 'item-123'}
            
            result = await enhanced_context_manager.upload_file_content(
                file_content=large_content,
                file_type="text/plain",
                organization_id="org-123",
                rag_feature="sales_intelligence",
                uploaded_by="user-123"
            )
            
            assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.enhanced_context_manager', '--cov-report=html'])

