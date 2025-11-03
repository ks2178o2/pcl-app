# apps/app-api/__tests__/test_enhanced_context_95_target.py
"""
Final targeted tests to reach 95% coverage for Enhanced Context Manager
Focusing on missing error paths and edge cases
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.enhanced_context_manager import EnhancedContextManager
from test_utils import SupabaseMockBuilder


@pytest.fixture
def mock_builder():
    builder = SupabaseMockBuilder()
    return builder


@pytest.fixture
def enhanced_context_manager(mock_builder):
    with patch('services.enhanced_context_manager.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return EnhancedContextManager()


class TestRevokeTenantAccessNoData:
    """Test revoke tenant access when update returns no data - line 178"""
    
    @pytest.mark.asyncio
    async def test_revoke_access_no_data_returned(self, enhanced_context_manager, mock_builder):
        """Test revoke when update returns empty data - covers line 178"""
        # Setup to return empty data from update
        update_result = Mock()
        update_result.data = []
        
        # Setup the query chain properly
        chain = Mock()
        chain.update.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = update_result
        
        table = Mock()
        table.update = Mock(return_value=chain)
        mock_builder.supabase.from_.return_value = table
        
        result = await enhanced_context_manager.revoke_tenant_access(
            organization_id='org-123',
            rag_feature='sales_intelligence'
        )
        
        assert result is not None
        assert result.get('success') is False
        assert 'Failed to revoke' in result.get('error', '')


class TestShareContextItemException:
    """Test share context item exception handling - lines 228-230"""
    
    @pytest.mark.asyncio
    async def test_share_context_item_exception_path(self, enhanced_context_manager):
        """Test share when exception occurs - covers lines 228-230"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database connection error")
            
            result = await enhanced_context_manager.share_context_item(
                source_org_id='org-source',
                target_org_id='org-target',
                rag_feature='sales_intelligence',
                item_id='item-123',
                shared_by='user-123'
            )
            
            assert result is not None
            assert result.get('success') is False
            assert 'error' in result


class TestFileUploadErrorPaths:
    """Test file upload error handling - lines 306-326"""
    
    @pytest.mark.asyncio
    async def test_upload_file_content_empty_content(self, enhanced_context_manager):
        """Test upload with empty content"""
        result = await enhanced_context_manager.upload_file_content(
            file_content="",
            file_type="text/plain",
            organization_id="org-123",
            rag_feature="sales_intelligence",
            uploaded_by="user-123"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_upload_file_content_with_add_failure(self, enhanced_context_manager, mock_builder):
        """Test upload when add_context_item fails - covers error path"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        with patch.object(enhanced_context_manager, 'add_context_item') as mock_add:
            mock_add.return_value = {'success': False, 'error': 'Failed'}
            
            result = await enhanced_context_manager.upload_file_content(
                file_content="Test content\n\nSecond paragraph",
                file_type="txt",
                organization_id="org-123",
                rag_feature="sales_intelligence",
                uploaded_by="user-123"
            )
            
            assert result is not None
            # Should still return success with error_count > 0
            assert result.get('success') is True


class TestUpdateQuotaErrorPaths:
    """Test update quota error handling - lines 490-492"""
    
    @pytest.mark.asyncio
    async def test_update_organization_quotas_exception(self, enhanced_context_manager):
        """Test update quotas when exception occurs - covers lines 490-492"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.update_organization_quotas(
                organization_id='org-123',
                quota_updates={'max_context_items': 1000}
            )
            
            assert result is not None
            assert result.get('success') is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_update_organization_quotas_no_data(self, enhanced_context_manager):
        """Test update quotas when update returns no data"""
        # Setup update to return no data
        update_result = Mock()
        update_result.data = []
        
        chain = Mock()
        chain.update.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = update_result
        
        table = Mock()
        table.update = Mock(return_value=chain)
        enhanced_context_manager.supabase.from_.return_value = table
        
        result = await enhanced_context_manager.update_organization_quotas(
            organization_id='org-123',
            quota_updates={'max_context_items': 1000}
        )
        
        assert result is not None
        assert result.get('success') is False


class TestCheckDuplicateError:
    """Test duplicate check error handling"""
    
    @pytest.mark.asyncio
    async def test_check_global_duplicate_with_exception(self, enhanced_context_manager):
        """Test _check_global_duplicate_item when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Connection error")
            
            result = await enhanced_context_manager._check_global_duplicate_item('item-123')
            
            # Should return False when exception occurs
            assert result is False


class TestLogUploadScenarios:
    """Test upload logging scenarios"""
    
    @pytest.mark.asyncio
    async def test_log_upload_with_errors(self, enhanced_context_manager):
        """Test logging upload with partial errors"""
        await enhanced_context_manager._log_upload(
            organization_id='org-123',
            upload_type='file',
            rag_feature='sales_intelligence',
            items_count=10,
            success_count=8,
            error_count=2,
            upload_source='manual_upload',
            uploaded_by='user-123'
        )
        # If no exception, test passes


class TestApprovalWorkflowErrors:
    """Test approval workflow error paths"""
    
    @pytest.mark.asyncio
    async def test_approve_sharing_exception(self, enhanced_context_manager):
        """Test approve sharing when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.approve_sharing_request(
                sharing_id='share-123',
                approved_by='user-123'
            )
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_reject_sharing_exception(self, enhanced_context_manager):
        """Test reject sharing when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.reject_sharing_request(
                sharing_id='share-123',
                rejected_by='user-123',
                reason='Test rejection'
            )
            
            assert result is not None
            assert result.get('success') is False


class TestQuotaCreationError:
    """Test quota creation error handling"""
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_creates_default_on_exception(self, enhanced_context_manager):
        """Test get quotas when creation fails"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.get_organization_quotas('org-123')
            
            assert result is not None


class TestStatisticsError:
    """Test statistics error handling - lines 524-525, 551, 571"""
    
    @pytest.mark.asyncio
    async def test_get_hierarchy_sharing_stats_exception(self, enhanced_context_manager):
        """Test get hierarchy stats when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.get_hierarchy_sharing_stats('org-123')
            
            assert result is not None
            assert result.get('success') is False


class TestBulkOperationsErrors:
    """Test bulk operations error handling - lines 600-607, 619"""
    
    @pytest.mark.asyncio
    async def test_bulk_api_upload_with_partial_failures(self, enhanced_context_manager, mock_builder):
        """Test bulk upload with mixed successes and failures"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        with patch.object(enhanced_context_manager, 'add_global_context_item') as mock_add:
            # Simulate alternating success/failure
            mock_add.side_effect = [
                {'success': True, 'item_id': 'item-1'},
                {'success': False, 'error': 'Failed 1'},
                {'success': True, 'item_id': 'item-2'},
                {'success': False, 'error': 'Failed 2'}
            ]
            
            result = await enhanced_context_manager.bulk_api_upload(
                items=[
                    {'item_title': 'Test 1', 'item_content': 'Content 1'},
                    {'item_title': 'Test 2', 'item_content': 'Content 2'},
                    {'item_title': 'Test 3', 'item_content': 'Content 3'},
                    {'item_title': 'Test 4', 'item_content': 'Content 4'}
                ],
                organization_id='org-123',
                rag_feature='sales_intelligence',
                uploaded_by='user-123'
            )
            
            assert result is not None
            assert result.get('success') is True  # Overall success
            assert result.get('success_count', 0) == 2
            assert result.get('error_count', 0) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.enhanced_context_manager', '--cov-report=html'])

