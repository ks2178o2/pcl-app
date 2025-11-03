# apps/app-api/__tests__/test_enhanced_context_95_ultimate.py
"""
Ultimate test to reach 95% coverage
Target: Lines 178, 426-428, 619, 644-651, 735-742, 764-771
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


class TestRevokeTenantAccessLine178:
    """Test revoke tenant access - line 178"""
    
    @pytest.mark.asyncio
    async def test_revoke_tenant_access_update_returns_empty(self, enhanced_context_manager):
        """Test revoke when update returns no data - MUST cover line 178"""
        # Setup the update query to return empty data
        update_result = Mock()
        update_result.data = []  # Empty data triggers line 178
        
        # Build the query chain correctly
        chain = Mock()
        chain.update.return_value = chain
        chain.eq.return_value = chain  # chain.eq() returns chain
        chain.execute.return_value = update_result
        
        table = Mock()
        table.update.return_value = chain
        enhanced_context_manager.supabase.from_.return_value = table
        
        result = await enhanced_context_manager.revoke_tenant_access(
            organization_id='org-123',
            rag_feature='sales_intelligence'
        )
        
        # Verify we hit the error path on line 178
        assert result is not None
        assert result.get('success') is False
        assert 'Failed to revoke' in result.get('error', '')
        # Key test: this should trigger the else block at line 178


class TestBulkUploadLines426428:
    """Test bulk upload exception - lines 426-428"""
    
    @pytest.mark.asyncio
    async def test_bulk_api_upload_top_level_exception(self, enhanced_context_manager):
        """Test bulk upload when top-level exception occurs - covers 426-428"""
        # Force exception in the entire bulk operation
        with patch.object(enhanced_context_manager, 'add_global_context_item', side_effect=Exception("Critical error")):
            result = await enhanced_context_manager.bulk_api_upload(
                items=[{'item_title': 'Test', 'item_content': 'Content'}],
                organization_id='org-123',
                rag_feature='sales_intelligence',
                uploaded_by='user-123'
            )
            
            assert result is not None
            assert result.get('success') is False
            assert 'error' in result


class TestApprovalWorkflowLine619:
    """Test approval workflow - line 619"""
    
    @pytest.mark.asyncio
    async def test_reject_sharing_request_no_data(self, enhanced_context_manager):
        """Test reject sharing when update returns no data"""
        # Setup update to return empty data
        update_result = Mock()
        update_result.data = []
        
        chain = Mock()
        chain.update.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = update_result
        
        table = Mock()
        table.update.return_value = chain
        enhanced_context_manager.supabase.from_.return_value = table
        
        result = await enhanced_context_manager.reject_sharing_request(
            sharing_id='share-123',
            rejected_by='user-123',
            reason='Test rejection'
        )
        
        assert result is not None
        assert result.get('success') is False


class TestShareToParentLines644651:
    """Test share to parent - lines 644-651"""
    
    @pytest.mark.asyncio
    async def test_share_to_parent_exception_during_insert(self, enhanced_context_manager):
        """Test share to parent when exception occurs during insert"""
        # Setup parent to exist
        parent_result = Mock()
        parent_result.data = {'id': 'parent-123'}
        parent_result.single.return_value.execute.return_value = parent_result
        
        # Setup org table to return parent
        org_table = Mock()
        org_table.select.return_value.eq.return_value.single.return_value.execute.return_value = parent_result
        
        # Setup share table to raise exception
        def share_insert_side_effect(*args):
            raise Exception("Insert failed")
        
        share_table = Mock()
        share_table.insert.return_value.execute.return_value = Mock(side_effect=share_insert_side_effect)
        
        def from_side_effect(table_name):
            if table_name == 'organizations':
                return org_table
            elif table_name == 'context_sharing':
                return share_table
        
        enhanced_context_manager.supabase.from_ = Mock(side_effect=from_side_effect)
        
        result = await enhanced_context_manager.share_to_parent_organization(
            organization_id='org-123',
            rag_feature='sales_intelligence',
            item_id='item-123',
            shared_by='user-123'
        )
        
        assert result is not None
        assert result.get('success') is False


class TestShareToChildrenLines735742:
    """Test share to children - lines 735-742"""
    
    @pytest.mark.asyncio
    async def test_share_to_children_exception_in_insert(self, enhanced_context_manager):
        """Test share to children when exception in bulk insert"""
        # Setup children to exist
        children_result = Mock()
        children_result.data = [{'id': 'child-1'}, {'id': 'child-2'}]
        
        children_chain = Mock()
        children_chain.select.return_value = children_chain
        children_chain.eq.return_value = children_chain
        children_chain.execute.return_value = children_result
        
        org_table = Mock()
        org_table.select.return_value = children_chain
        
        # Setup insert to raise exception
        share_table = Mock()
        
        def insert_side_effect(*args):
            chain = Mock()
            chain.insert.return_value = chain
            chain.execute.side_effect = Exception("Bulk insert failed")
            return chain
        
        share_table.insert = Mock(side_effect=insert_side_effect)
        
        def from_side_effect(table_name):
            if table_name == 'organizations':
                return org_table
            else:
                return share_table
        
        enhanced_context_manager.supabase.from_ = Mock(side_effect=from_side_effect)
        
        result = await enhanced_context_manager.share_to_children(
            source_org_id='org-123',
            item_id='item-123',
            rag_feature='sales_intelligence',
            shared_by='user-123'
        )
        
        assert result is not None
        assert result.get('success') is False


class TestGetPendingApprovalsLines764771:
    """Test get pending approvals - lines 764-771"""
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals_with_rag_filter_exception(self, enhanced_context_manager):
        """Test get pending with rag feature filter when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_', side_effect=Exception("Query error")):
            result = await enhanced_context_manager.get_pending_approvals('org-123', rag_feature='sales_intelligence')
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals_exception_handling(self, enhanced_context_manager):
        """Test get pending with basic exception"""
        with patch.object(enhanced_context_manager.supabase, 'from_', side_effect=Exception("Database error")):
            result = await enhanced_context_manager.get_pending_approvals('org-123')
            
            assert result is not None
            assert result.get('success') is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.enhanced_context_manager', '--cov-report=html'])

