# apps/app-api/__tests__/test_enhanced_context_manager_working.py

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from services.enhanced_context_manager import EnhancedContextManager


class TestEnhancedContextManagerWorking:
    """Working tests for Enhanced Context Manager"""
    
    @pytest.fixture
    def enhanced_manager(self):
        """Create enhanced manager with mocked supabase"""
        with patch('services.enhanced_context_manager.get_supabase_client', return_value=Mock()):
            return EnhancedContextManager()
    
    @pytest.mark.asyncio
    async def test_add_global_context_item_success(self, enhanced_manager):
        """Test successful addition of global context item"""
        # Mock duplicate check returning empty
        mock_check_result = Mock()
        mock_check_result.data = []
        
        # Mock insert result
        mock_insert_result = Mock()
        mock_insert_result.data = [{'id': 'global-123', 'item_id': 'test-item-123'}]
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if table_name == 'global_context_items':
                if call_count == 1:  # duplicate check
                    mock_select = Mock()
                    mock_eq = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = mock_check_result
                    
                    mock_table.select = Mock(return_value=mock_select)
                    mock_select.eq = Mock(return_value=mock_eq)
                    mock_eq.execute = mock_execute
                else:  # insert
                    mock_insert = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = mock_insert_result
                    
                    mock_table.insert = Mock(return_value=mock_insert)
                    mock_insert.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        context_data = {
            'rag_feature': 'best_practice_kb',
            'item_id': 'test-item-123',
            'item_type': 'knowledge_chunk',
            'item_title': 'Test Title',
            'item_content': 'Test Content',
            'confidence_score': 0.8
        }
        
        result = await enhanced_manager.add_global_context_item(context_data)
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_add_global_context_item_invalid_confidence(self, enhanced_manager):
        """Test validation of confidence score"""
        context_data = {
            'rag_feature': 'best_practice_kb',
            'item_id': 'test-item-123',
            'item_type': 'knowledge_chunk',
            'item_title': 'Test Title',
            'item_content': 'Test Content',
            'confidence_score': 1.5  # Invalid > 1
        }
        
        result = await enhanced_manager.add_global_context_item(context_data)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_add_global_context_item_duplicate(self, enhanced_manager):
        """Test adding duplicate global item"""
        # Mock duplicate check returning existing item
        mock_check_result = Mock()
        mock_check_result.data = [{'id': 'existing-123'}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = mock_check_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        context_data = {
            'rag_feature': 'best_practice_kb',
            'item_id': 'existing-item-123',
            'item_type': 'knowledge_chunk',
            'item_title': 'Test Title',
            'item_content': 'Test Content'
        }
        
        result = await enhanced_manager.add_global_context_item(context_data)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_global_context_items_basic(self, enhanced_manager):
        """Test getting global context items without filters"""
        mock_result = Mock()
        mock_result.data = [
            {'id': 'global-1', 'item_id': 'item-1', 'rag_feature': 'best_practice_kb'},
            {'id': 'global-2', 'item_id': 'item-2', 'rag_feature': 'best_practice_kb'}
        ]
        mock_result.count = 2
        
        # Create proper mock chain
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_order1 = Mock()
        mock_order2 = Mock()
        mock_range = Mock()
        mock_execute = Mock()
        mock_execute.return_value = mock_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_eq.order = Mock(return_value=mock_order1)
        mock_order1.order = Mock(return_value=mock_order2)
        mock_order2.range = Mock(return_value=mock_range)
        mock_range.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.get_global_context_items()
        
        assert result['success'] is True
        assert len(result['items']) == 2
    
    @pytest.mark.asyncio
    async def test_get_global_context_items_with_feature_filter(self, enhanced_manager):
        """Test getting global context items with RAG feature filter"""
        mock_result = Mock()
        mock_result.data = [
            {'id': 'global-1', 'rag_feature': 'best_practice_kb'}
        ]
        mock_result.count = 1
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_order1 = Mock()
        mock_order2 = Mock()
        mock_range = Mock()
        mock_execute = Mock()
        mock_execute.return_value = mock_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.order = Mock(return_value=mock_order1)
        mock_order1.order = Mock(return_value=mock_order2)
        mock_order2.range = Mock(return_value=mock_range)
        mock_range.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.get_global_context_items(rag_feature='best_practice_kb')
        
        assert result['success'] is True
        assert len(result['items']) == 1
    
    @pytest.mark.asyncio
    async def test_get_global_context_items_no_access(self, enhanced_manager):
        """Test getting global items when org has no access"""
        # Setup access check returning empty
        access_check = Mock()
        access_check.data = []  # No access
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_eq3 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = access_check
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.eq = Mock(return_value=mock_eq3)
        mock_eq3.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.get_global_context_items(
            rag_feature='best_practice_kb',
            organization_id='org-123'
        )
        
        assert result['success'] is True
        assert len(result['items']) == 0
        assert 'No access' in result.get('message', '')
    
    @pytest.mark.asyncio
    async def test_grant_tenant_access_new(self, enhanced_manager):
        """Test granting tenant access when no existing access"""
        # Mock select returning empty (no existing access)
        select_result = Mock()
        select_result.data = []
        
        # Mock insert result
        insert_result = Mock()
        insert_result.data = [{'id': 'access-123', 'organization_id': 'org-123', 'rag_feature': 'best_practice_kb'}]
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if table_name == 'tenant_context_access':
                if call_count == 1:  # select
                    mock_select = Mock()
                    mock_eq1 = Mock()
                    mock_eq2 = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = select_result
                    
                    mock_table.select = Mock(return_value=mock_select)
                    mock_select.eq = Mock(return_value=mock_eq1)
                    mock_eq1.eq = Mock(return_value=mock_eq2)
                    mock_eq2.execute = mock_execute
                else:  # insert
                    mock_insert = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = insert_result
                    
                    mock_table.insert = Mock(return_value=mock_insert)
                    mock_insert.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.grant_tenant_access('org-123', 'best_practice_kb')
        
        assert result['success'] is True
        assert 'access_id' in result
    
    @pytest.mark.asyncio
    async def test_grant_tenant_access_update_existing(self, enhanced_manager):
        """Test granting tenant access when access already exists"""
        # Mock select returning existing access
        select_result = Mock()
        select_result.data = [{'id': 'access-123', 'enabled': False}]
        
        # Mock update result
        update_result = Mock()
        update_result.data = [{'id': 'access-123', 'enabled': True}]
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if table_name == 'tenant_context_access':
                if call_count == 1:  # select
                    mock_select = Mock()
                    mock_eq1 = Mock()
                    mock_eq2 = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = select_result
                    
                    mock_table.select = Mock(return_value=mock_select)
                    mock_select.eq = Mock(return_value=mock_eq1)
                    mock_eq1.eq = Mock(return_value=mock_eq2)
                    mock_eq2.execute = mock_execute
                else:  # update
                    mock_update = Mock()
                    mock_eq1 = Mock()
                    mock_eq2 = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = update_result
                    
                    mock_table.update = Mock(return_value=mock_update)
                    mock_update.eq = Mock(return_value=mock_eq1)
                    mock_eq1.eq = Mock(return_value=mock_eq2)
                    mock_eq2.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.grant_tenant_access('org-123', 'best_practice_kb', 'write')
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_revoke_tenant_access(self, enhanced_manager):
        """Test revoking tenant access"""
        update_result = Mock()
        update_result.data = [{'id': 'access-123', 'enabled': False}]
        
        mock_table = Mock()
        mock_update = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = update_result
        
        mock_table.update = Mock(return_value=mock_update)
        mock_update.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.revoke_tenant_access('org-123', 'best_practice_kb')
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_share_context_item(self, enhanced_manager):
        """Test sharing context item with another org"""
        # Mock select for duplicate check (return empty)
        select_result = Mock()
        select_result.data = []
        
        # Mock insert result
        insert_result = Mock()
        insert_result.data = [{'id': 'sharing-123'}]
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if table_name == 'context_sharing':
                if call_count == 1:  # select
                    mock_select = Mock()
                    mock_eq1 = Mock()
                    mock_eq2 = Mock()
                    mock_eq3 = Mock()
                    mock_eq4 = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = select_result
                    
                    mock_table.select = Mock(return_value=mock_select)
                    mock_select.eq = Mock(return_value=mock_eq1)
                    mock_eq1.eq = Mock(return_value=mock_eq2)
                    mock_eq2.eq = Mock(return_value=mock_eq3)
                    mock_eq3.eq = Mock(return_value=mock_eq4)
                    mock_eq4.execute = mock_execute
                else:  # insert
                    mock_insert = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = insert_result
                    
                    mock_table.insert = Mock(return_value=mock_insert)
                    mock_insert.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.share_context_item(
            'org-123', 'org-456', 'best_practice_kb', 'item-123', 'user-123', 'read_only'
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_approve_sharing_request(self, enhanced_manager):
        """Test approving sharing request"""
        update_result = Mock()
        update_result.data = [{'id': 'request-123', 'status': 'approved'}]
        
        mock_table = Mock()
        mock_update = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = update_result
        
        mock_table.update = Mock(return_value=mock_update)
        mock_update.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.approve_sharing_request('request-123', 'user-123')
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_get_shared_context_items(self, enhanced_manager):
        """Test getting shared context items"""
        mock_result = Mock()
        mock_result.data = [
            {'id': 'shared-1', 'source_organization_id': 'org-123'},
            {'id': 'shared-2', 'source_organization_id': 'org-456'}
        ]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = mock_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.get_shared_context_items('org-789')
        
        assert result['success'] is True
        assert len(result['shared_items']) == 2
    
    @pytest.mark.asyncio
    async def test_upload_file_content_txt(self, enhanced_manager):
        """Test uploading TXT file content"""
        file_content = "Line 1\n\nLine 2"  # Needs double newline for splitting
        file_type = "txt"
        
        # Mock add_context_item success
        with patch.object(enhanced_manager, 'add_context_item', return_value={'success': True, 'item_id': 'item-123'}):
            with patch.object(enhanced_manager, '_log_upload', return_value=None):
                result = await enhanced_manager.upload_file_content(
                    file_content, file_type, 'org-123', 'best_practice_kb', 'user-123'
                )
                
                assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_upload_file_content_md(self, enhanced_manager):
        """Test uploading MD file content"""
        file_content = "# Header\n\nParagraph 1\n\nParagraph 2"
        file_type = "md"
        
        with patch.object(enhanced_manager, 'add_context_item', return_value={'success': True, 'item_id': 'item-123'}):
            result = await enhanced_manager.upload_file_content(
                file_content, file_type, 'org-123', 'best_practice_kb', 'user-123'
            )
            
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_scrape_web_content(self, enhanced_manager):
        """Test scraping web content"""
        url = "https://example.com/article"
        
        with patch.object(enhanced_manager, 'add_context_item', return_value={'success': True, 'item_id': 'item-123'}):
            with patch.object(enhanced_manager, '_log_upload', return_value=None):
                result = await enhanced_manager.scrape_web_content(
                    url, 'org-123', 'best_practice_kb', 'user-123'
                )
                
                assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_bulk_api_upload(self, enhanced_manager):
        """Test bulk API upload"""
        api_data = [
            {'item_id': 'bulk-1', 'item_title': 'Title 1', 'item_content': 'Content 1'},
            {'item_id': 'bulk-2', 'item_title': 'Title 2', 'item_content': 'Content 2'}
        ]
        
        with patch.object(enhanced_manager, 'add_context_item', return_value={'success': True, 'item_id': 'item-123'}):
            with patch.object(enhanced_manager, '_log_upload', return_value=None):
                result = await enhanced_manager.bulk_api_upload(
                    api_data, 'org-123', 'best_practice_kb', 'user-123'
                )
                
                assert result['success'] is True
                assert result['success_count'] == 2
    
    @pytest.mark.asyncio
    async def test_add_context_item_legacy(self, enhanced_manager):
        """Test legacy add_context_item method"""
        insert_result = Mock()
        insert_result.data = [{'id': 'legacy-123'}]
        
        mock_table = Mock()
        mock_insert = Mock()
        mock_execute = Mock()
        mock_execute.return_value = insert_result
        
        mock_table.insert = Mock(return_value=mock_insert)
        mock_insert.execute = mock_execute
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        context_data = {
            'organization_id': 'org-123',
            'rag_feature': 'best_practice_kb',
            'item_id': 'legacy-item-123',
            'item_type': 'knowledge_chunk',
            'item_title': 'Legacy Title',
            'item_content': 'Legacy Content'
        }
        
        result = await enhanced_manager.add_context_item(context_data)
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_share_to_children(self, enhanced_manager):
        """Test sharing to child organizations"""
        # Mock children query result
        children_result = Mock()
        children_result.data = [
            {'id': 'child-1'},
            {'id': 'child-2'}
        ]
        
        # Mock insert result
        insert_result = Mock()
        insert_result.data = [
            {'id': 'sharing-1'},
            {'id': 'sharing-2'}
        ]
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if table_name == 'organizations':
                mock_select = Mock()
                mock_eq = Mock()
                mock_execute = Mock()
                mock_execute.return_value = children_result
                
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_eq.execute = mock_execute
            elif table_name == 'context_sharing':
                mock_insert = Mock()
                mock_execute = Mock()
                mock_execute.return_value = insert_result
                
                mock_table.insert = Mock(return_value=mock_insert)
                mock_insert.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.share_to_children(
            'org-123', 'item-123', 'best_practice_kb', 'user-123'
        )
        
        assert result['success'] is True
        assert result['shared_count'] == 2
    
    @pytest.mark.asyncio
    async def test_get_global_context_items_with_rag_feature_filter(self, enhanced_manager):
        """Test getting global items with RAG feature filter and pagination"""
        mock_result = Mock()
        mock_result.data = [{'id': 'global-1', 'rag_feature': 'best_practice_kb'}]
        mock_result.count = 1
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_order1 = Mock()
        mock_order2 = Mock()
        mock_range = Mock()
        mock_execute = Mock()
        mock_execute.return_value = mock_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.order = Mock(return_value=mock_order1)
        mock_order1.order = Mock(return_value=mock_order2)
        mock_order2.range = Mock(return_value=mock_range)
        mock_range.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.get_global_context_items(
            rag_feature='best_practice_kb', limit=50, offset=0
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_get_global_context_items_exception(self, enhanced_manager):
        """Test exception handling in get_global_context_items"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await enhanced_manager.get_global_context_items()
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_grant_tenant_access_exception(self, enhanced_manager):
        """Test exception handling in grant_tenant_access"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await enhanced_manager.grant_tenant_access('org-123', 'best_practice_kb')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_revoke_tenant_access_exception(self, enhanced_manager):
        """Test exception handling in revoke_tenant_access"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await enhanced_manager.revoke_tenant_access('org-123', 'best_practice_kb')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_add_global_context_item_exception(self, enhanced_manager):
        """Test exception handling in add_global_context_item"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        context_data = {
            'rag_feature': 'best_practice_kb',
            'item_id': 'test-123',
            'item_type': 'knowledge_chunk',
            'item_title': 'Test',
            'item_content': 'Content'
        }
        
        result = await enhanced_manager.add_global_context_item(context_data)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_add_global_context_item_insert_fails(self, enhanced_manager):
        """Test when insert fails - line 60-64"""
        mock_check_result = Mock()
        mock_check_result.data = []  # No duplicate
        
        insert_result = Mock()
        insert_result.data = []  # No data returned
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if table_name == 'global_context_items':
                if call_count == 1:  # duplicate check
                    mock_select = Mock()
                    mock_eq = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = mock_check_result
                    
                    mock_table.select = Mock(return_value=mock_select)
                    mock_select.eq = Mock(return_value=mock_eq)
                    mock_eq.execute = mock_execute
                else:  # insert
                    mock_insert = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = insert_result
                    
                    mock_table.insert = Mock(return_value=mock_insert)
                    mock_insert.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        context_data = {
            'rag_feature': 'best_practice_kb',
            'item_id': 'test-123',
            'item_type': 'knowledge_chunk',
            'item_title': 'Test',
            'item_content': 'Content'
        }
        
        result = await enhanced_manager.add_global_context_item(context_data)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_share_context_item_already_exists(self, enhanced_manager):
        """Test sharing when item already exists - line 200-204"""
        select_result = Mock()
        select_result.data = [{'id': 'existing-sharing'}]  # Already exists
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_eq3 = Mock()
        mock_eq4 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = select_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.eq = Mock(return_value=mock_eq3)
        mock_eq3.eq = Mock(return_value=mock_eq4)
        mock_eq4.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.share_context_item(
            'org-123', 'org-456', 'best_practice_kb', 'item-123', 'user-123', 'read_only'
        )
        
        assert result['success'] is False
        assert 'Sharing already exists' in result['error']
    
    @pytest.mark.asyncio
    async def test_approve_sharing_request_fails(self, enhanced_manager):
        """Test approve sharing request when update fails - line 249-253"""
        update_result = Mock()
        update_result.data = []
        
        mock_table = Mock()
        mock_update = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = update_result
        
        mock_table.update = Mock(return_value=mock_update)
        mock_update.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.approve_sharing_request('request-123', 'user-123')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_shared_context_items_with_feature(self, enhanced_manager):
        """Test get shared items with RAG feature filter - line 270"""
        mock_result = Mock()
        mock_result.data = [
            {'id': 'shared-1', 'rag_feature': 'best_practice_kb'}
        ]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_eq3 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = mock_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.eq = Mock(return_value=mock_eq3)
        mock_eq3.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.get_shared_context_items('org-123', rag_feature='best_practice_kb')
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_share_to_parent(self, enhanced_manager):
        """Test sharing to parent organization"""
        # Mock org result with parent
        org_result = Mock()
        org_result.data = [{'parent_organization_id': 'org-parent'}]
        
        # Mock insert result
        insert_result = Mock()
        insert_result.data = [{'id': 'sharing-to-parent'}]
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if table_name == 'organizations':
                mock_select = Mock()
                mock_eq = Mock()
                mock_execute = Mock()
                mock_execute.return_value = org_result
                
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_eq.execute = mock_execute
            elif table_name == 'context_sharing':
                mock_insert = Mock()
                mock_execute = Mock()
                mock_execute.return_value = insert_result
                
                mock_table.insert = Mock(return_value=mock_insert)
                mock_insert.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.share_to_parent('org-child', 'item-123', 'best_practice_kb', 'user-123')
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_share_to_parent_no_parent(self, enhanced_manager):
        """Test share to parent when no parent exists - line 618-622"""
        org_result = Mock()
        org_result.data = []  # No parent
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = org_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.share_to_parent('org-123', 'item-123', 'best_practice_kb', 'user-123')
        
        assert result['success'] is False
        assert 'No parent organization found' in result['error']
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals(self, enhanced_manager):
        """Test getting pending approvals"""
        mock_result = Mock()
        mock_result.data = [
            {'id': 'pending-1', 'source_organization_id': 'org-123'},
            {'id': 'pending-2', 'source_organization_id': 'org-456'}
        ]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = mock_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.get_pending_approvals('org-123')
        
        assert result['success'] is True
        assert result['count'] == 2
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals_empty(self, enhanced_manager):
        """Test getting pending approvals when empty - line 667-672"""
        mock_result = Mock()
        mock_result.data = []
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = mock_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.get_pending_approvals('org-123')
        
        assert result['success'] is True
        assert result['count'] == 0
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals_exception(self, enhanced_manager):
        """Test exception in get_pending_approvals - line 674-680"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await enhanced_manager.get_pending_approvals('org-123')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_share_to_children_no_children(self, enhanced_manager):
        """Test share to children when no children exist - line 570-575"""
        children_result = Mock()
        children_result.data = []
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = children_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.share_to_children('org-123', 'item-123', 'best_practice_kb', 'user-123')
        
        assert result['success'] is True
        assert result['shared_count'] == 0
    
    @pytest.mark.asyncio
    async def test_approve_shared_item_success(self, enhanced_manager):
        """Test approving shared item with full item copy - lines 682-745"""
        sharing_update = Mock()
        sharing_update.data = [{
            'id': 'sharing-123',
            'item_id': 'item-123',
            'target_organization_id': 'org-456',
            'source_organization_id': 'org-123',
            'rag_feature': 'best_practice_kb'
        }]
        
        original_item = Mock()
        original_item.data = [{
            'title': 'Original Title',
            'content': 'Original Content',
            'item_type': 'knowledge_chunk'
        }]
        
        insert_result = Mock()
        insert_result.data = [{'id': 'new-item-456'}]
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if table_name == 'context_sharing':
                if call_count == 1:  # update
                    mock_update = Mock()
                    mock_eq = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = sharing_update
                    
                    mock_table.update = Mock(return_value=mock_update)
                    mock_update.eq = Mock(return_value=mock_eq)
                    mock_eq.execute = mock_execute
                else:  # select
                    mock_select = Mock()
                    mock_eq = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = Mock(data=[])
                    
                    mock_table.select = Mock(return_value=mock_select)
                    mock_select.eq = Mock(return_value=mock_eq)
                    mock_eq.execute = mock_execute
            elif table_name == 'context_items':
                if call_count == 2:  # select original
                    mock_select = Mock()
                    mock_eq = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = original_item
                    
                    mock_table.select = Mock(return_value=mock_select)
                    mock_select.eq = Mock(return_value=mock_eq)
                    mock_eq.execute = mock_execute
                else:  # insert
                    mock_insert = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = insert_result
                    
                    mock_table.insert = Mock(return_value=mock_insert)
                    mock_insert.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.approve_shared_item('sharing-123', 'user-456')
        
        assert result['success'] is True
        assert 'new_item_id' in result
    
    @pytest.mark.asyncio
    async def test_approve_shared_item_no_data(self, enhanced_manager):
        """Test approve shared item when update has no data - line 734-738"""
        update_result = Mock()
        update_result.data = []
        
        mock_table = Mock()
        mock_update = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = update_result
        
        mock_table.update = Mock(return_value=mock_update)
        mock_update.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.approve_shared_item('sharing-123', 'user-456')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_reject_shared_item(self, enhanced_manager):
        """Test rejecting shared item - lines 747-774"""
        update_result = Mock()
        update_result.data = [{'id': 'sharing-123', 'status': 'rejected'}]
        
        mock_table = Mock()
        mock_update = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = update_result
        
        mock_table.update = Mock(return_value=mock_update)
        mock_update.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.reject_shared_item('sharing-123', 'user-456', 'Not interested')
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_reject_shared_item_fails(self, enhanced_manager):
        """Test reject shared item when update fails - line 763-767"""
        update_result = Mock()
        update_result.data = []
        
        mock_table = Mock()
        mock_update = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = update_result
        
        mock_table.update = Mock(return_value=mock_update)
        mock_update.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.reject_shared_item('sharing-123', 'user-456')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_hierarchy_sharing_stats(self, enhanced_manager):
        """Test getting hierarchy sharing stats - lines 776-807"""
        outgoing = Mock()
        outgoing.count = 5
        
        incoming = Mock()
        incoming.count = 3
        
        pending = Mock()
        pending.count = 2
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if call_count == 1:  # outgoing
                mock_select = Mock()
                mock_eq1 = Mock()
                mock_eq2 = Mock()
                mock_execute = Mock()
                mock_execute.return_value = outgoing
                
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq1)
                mock_eq1.eq = Mock(return_value=mock_eq2)
                mock_eq2.execute = mock_execute
            elif call_count == 2:  # incoming
                mock_select = Mock()
                mock_eq1 = Mock()
                mock_eq2 = Mock()
                mock_execute = Mock()
                mock_execute.return_value = incoming
                
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq1)
                mock_eq1.eq = Mock(return_value=mock_eq2)
                mock_eq2.execute = mock_execute
            else:  # pending
                mock_select = Mock()
                mock_eq1 = Mock()
                mock_eq2 = Mock()
                mock_execute = Mock()
                mock_execute.return_value = pending
                
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq1)
                mock_eq1.eq = Mock(return_value=mock_eq2)
                mock_eq2.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.get_hierarchy_sharing_stats('org-123')
        
        assert result['success'] is True
        assert result['stats']['outgoing_shares'] == 5
        assert result['stats']['incoming_shares'] == 3
        assert result['stats']['pending_approvals'] == 2
    
    @pytest.mark.asyncio
    async def test_get_hierarchy_sharing_stats_exception(self, enhanced_manager):
        """Test exception in get_hierarchy_sharing_stats - line 797-807"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await enhanced_manager.get_hierarchy_sharing_stats('org-123')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_approve_shared_item_insert_fails(self, enhanced_manager):
        """Test approve shared item when insert fails - lines 725-728"""
        sharing_update = Mock()
        sharing_update.data = [{
            'id': 'sharing-123',
            'item_id': 'item-123',
            'target_organization_id': 'org-456',
            'source_organization_id': 'org-123',
            'rag_feature': 'best_practice_kb'
        }]
        
        original_item = Mock()
        original_item.data = [{
            'title': 'Original Title',
            'content': 'Original Content',
            'item_type': 'knowledge_chunk'
        }]
        
        insert_result = Mock()
        insert_result.data = []  # Insert fails
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if table_name == 'context_sharing':
                mock_update = Mock()
                mock_eq = Mock()
                mock_execute = Mock()
                mock_execute.return_value = sharing_update
                
                mock_table.update = Mock(return_value=mock_update)
                mock_update.eq = Mock(return_value=mock_eq)
                mock_eq.execute = mock_execute
            elif table_name == 'context_items':
                if call_count == 2:  # select
                    mock_select = Mock()
                    mock_eq = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = original_item
                    
                    mock_table.select = Mock(return_value=mock_select)
                    mock_select.eq = Mock(return_value=mock_eq)
                    mock_eq.execute = mock_execute
                else:  # insert fails
                    mock_insert = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = insert_result
                    
                    mock_table.insert = Mock(return_value=mock_insert)
                    mock_insert.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.approve_shared_item('sharing-123', 'user-456')
        
        assert result['success'] is False
        assert 'Failed to copy item' in result['error']
    
    @pytest.mark.asyncio
    async def test_approve_shared_item_no_original(self, enhanced_manager):
        """Test approve shared item when original not found - lines 729-733"""
        sharing_update = Mock()
        sharing_update.data = [{
            'id': 'sharing-123',
            'item_id': 'item-123',
            'target_organization_id': 'org-456',
            'source_organization_id': 'org-123',
            'rag_feature': 'best_practice_kb'
        }]
        
        original_item = Mock()
        original_item.data = []  # No original item
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if table_name == 'context_sharing':
                mock_update = Mock()
                mock_eq = Mock()
                mock_execute = Mock()
                mock_execute.return_value = sharing_update
                
                mock_table.update = Mock(return_value=mock_update)
                mock_update.eq = Mock(return_value=mock_eq)
                mock_eq.execute = mock_execute
            elif table_name == 'context_items':
                mock_select = Mock()
                mock_eq = Mock()
                mock_execute = Mock()
                mock_execute.return_value = original_item
                
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_eq.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.approve_shared_item('sharing-123', 'user-456')
        
        assert result['success'] is False
        assert 'Original item not found' in result['error']
    
    @pytest.mark.asyncio
    async def test_reject_shared_item_exception(self, enhanced_manager):
        """Test exception in reject shared item - line 769-774"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await enhanced_manager.reject_shared_item('sharing-123', 'user-456', 'Not needed')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_exists(self, enhanced_manager):
        """Test get organization quotas when they exist - lines 435-469"""
        mock_result = Mock()
        mock_result.data = {'max_context_items': 1000, 'current_context_items': 50}
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_single = Mock()
        mock_execute = Mock()
        mock_execute.return_value = mock_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_single)
        mock_single.single = Mock(return_value=mock_execute)
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.get_organization_quotas('org-123')
        
        assert result['success'] is True
        assert 'quotas' in result
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_create_default(self, enhanced_manager):
        """Test get organization quotas creates default - lines 446-462"""
        # First call returns empty
        mock_result = Mock()
        mock_result.data = None
        
        insert_result = Mock()
        insert_result.data = [{'max_context_items': 1000, 'organization_id': 'org-123'}]
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if call_count == 1:  # select
                mock_select = Mock()
                mock_eq = Mock()
                mock_single = Mock()
                mock_execute = Mock()
                mock_execute.return_value = mock_result
                
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_single)
                mock_single.single = Mock(return_value=mock_execute)
            else:  # insert
                mock_insert = Mock()
                mock_execute = Mock()
                mock_execute.return_value = insert_result
                
                mock_table.insert = Mock(return_value=mock_insert)
                mock_insert.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.get_organization_quotas('org-123')
        
        assert result['success'] is True
        assert 'quotas' in result
    
    @pytest.mark.asyncio
    async def test_update_organization_quotas_success(self, enhanced_manager):
        """Test update organization quotas successfully - lines 471-489"""
        update_result = Mock()
        update_result.data = [{'max_context_items': 1500, 'organization_id': 'org-123'}]
        
        mock_table = Mock()
        mock_update = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = update_result
        
        mock_table.update = Mock(return_value=mock_update)
        mock_update.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.update_organization_quotas('org-123', {'max_context_items': 1500})
        
        assert result['success'] is True
        assert 'updated_quotas' in result
    
    @pytest.mark.asyncio
    async def test_update_organization_quotas_fails(self, enhanced_manager):
        """Test update organization quotas when fails - lines 484-488"""
        update_result = Mock()
        update_result.data = []
        
        mock_table = Mock()
        mock_update = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = update_result
        
        mock_table.update = Mock(return_value=mock_update)
        mock_update.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.update_organization_quotas('org-123', {'max_context_items': 1500})
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_add_global_context_item_missing_required_field(self, enhanced_manager):
        """Test add global context item with missing required field - line 30"""
        context_data = {
            'rag_feature': 'best_practice_kb',
            'item_id': 'test-123',
            # Missing item_type
            'item_title': 'Test Title',
            'item_content': 'Content'
        }
        
        result = await enhanced_manager.add_global_context_item(context_data)
        
        assert result['success'] is False
        assert 'cannot be empty' in result['error']
    
    @pytest.mark.asyncio
    async def test_grant_tenant_access_fails_no_data(self, enhanced_manager):
        """Test grant tenant access when result has no data - lines 151-155"""
        select_result = Mock()
        select_result.data = []
        
        insert_result = Mock()
        insert_result.data = []  # Insert returns no data
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if table_name == 'tenant_context_access':
                if call_count == 1:  # select
                    mock_select = Mock()
                    mock_eq1 = Mock()
                    mock_eq2 = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = select_result
                    
                    mock_table.select = Mock(return_value=mock_select)
                    mock_select.eq = Mock(return_value=mock_eq1)
                    mock_eq1.eq = Mock(return_value=mock_eq2)
                    mock_eq2.execute = mock_execute
                else:  # insert
                    mock_insert = Mock()
                    mock_execute = Mock()
                    mock_execute.return_value = insert_result
                    
                    mock_table.insert = Mock(return_value=mock_insert)
                    mock_insert.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.grant_tenant_access('org-123', 'best_practice_kb')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_revoke_tenant_access_fails_no_data(self, enhanced_manager):
        """Test revoke tenant access when update has no data - lines 176-181"""
        update_result = Mock()
        update_result.data = []
        
        mock_table = Mock()
        mock_update = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = update_result
        
        mock_table.update = Mock(return_value=mock_update)
        mock_update.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager.revoke_tenant_access('org-123', 'best_practice_kb')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_share_context_item_exception(self, enhanced_manager):
        """Test exception in share_context_item - lines 228-233"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await enhanced_manager.share_context_item(
            'org-123', 'org-456', 'best_practice_kb', 'item-123', 'user-123', 'read_only'
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_approve_sharing_request_exception(self, enhanced_manager):
        """Test exception in approve_sharing_request - lines 255-260"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await enhanced_manager.approve_sharing_request('request-123', 'user-123')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_shared_context_items_exception(self, enhanced_manager):
        """Test exception in get_shared_context_items - lines 280-286"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await enhanced_manager.get_shared_context_items('org-123')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_upload_file_content_exception(self, enhanced_manager):
        """Test exception in upload_file_content - lines 341-346"""
        with patch.object(enhanced_manager, 'add_context_item', side_effect=Exception("DB error")):
            result = await enhanced_manager.upload_file_content(
                "Content\n\nMore", "txt", 'org-123', 'best_practice_kb', 'user-123'
            )
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_scrape_web_content_exception(self, enhanced_manager):
        """Test exception in scrape_web_content - lines 385-390"""
        with patch.object(enhanced_manager, 'add_context_item', side_effect=Exception("DB error")):
            with patch.object(enhanced_manager, '_log_upload', return_value=None):
                result = await enhanced_manager.scrape_web_content(
                    "https://example.com", 'org-123', 'best_practice_kb', 'user-123'
                )
                
                assert result['success'] is False
                assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_bulk_api_upload_exception(self, enhanced_manager):
        """Test exception in bulk_api_upload - lines 426-431"""
        api_data = [{'item_id': 'test-1'}]
        
        with patch.object(enhanced_manager, 'add_context_item', side_effect=Exception("DB error")):
            with patch.object(enhanced_manager, '_log_upload', return_value=None):
                result = await enhanced_manager.bulk_api_upload(
                    api_data, 'org-123', 'best_practice_kb', 'user-123'
                )
                
                assert result['success'] is False
                assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_exception(self, enhanced_manager):
        """Test exception in get_organization_quotas - lines 464-469"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await enhanced_manager.get_organization_quotas('org-123')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_update_organization_quotas_exception(self, enhanced_manager):
        """Test exception in update_organization_quotas - lines 490-495"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await enhanced_manager.update_organization_quotas('org-123', {'max_context_items': 1500})
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_check_global_duplicate_item(self, enhanced_manager):
        """Test _check_global_duplicate_item helper - lines 499-505"""
        mock_result = Mock()
        mock_result.data = [{'id': 'existing-123'}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = mock_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        result = await enhanced_manager._check_global_duplicate_item('test-123')
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_log_upload_exception(self, enhanced_manager):
        """Test exception in _log_upload - lines 524-525"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        # Should not raise, just log
        await enhanced_manager._log_upload('org-123', 'file', 'best_practice_kb', 10, 10, 0, 'source', 'user-123')
        
        # No assertion needed - just that it doesn't raise
    
    @pytest.mark.asyncio
    async def test_add_context_item_exception(self, enhanced_manager):
        """Test exception in add_context_item legacy - lines 555-560"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        context_data = {
            'organization_id': 'org-123',
            'rag_feature': 'best_practice_kb',
            'item_id': 'test-123',
            'item_type': 'knowledge_chunk',
            'item_title': 'Test',
            'item_content': 'Content'
        }
        
        result = await enhanced_manager.add_context_item(context_data)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_share_to_children_exception(self, enhanced_manager):
        """Test exception in share_to_children - lines 605-610"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await enhanced_manager.share_to_children('org-123', 'item-123', 'best_practice_kb', 'user-123')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_share_to_parent_exception(self, enhanced_manager):
        """Test exception in share_to_parent - lines 649-654"""
        enhanced_manager.supabase.from_.side_effect = Exception("DB error")
        
        result = await enhanced_manager.share_to_parent('org-123', 'item-123', 'best_practice_kb', 'user-123')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_add_context_item_missing_field(self, enhanced_manager):
        """Test add_context_item with missing field - line 537"""
        context_data = {
            'organization_id': 'org-123',
            'rag_feature': 'best_practice_kb',
            'item_id': 'test-123',
            # Missing item_type
            'item_title': 'Test',
            'item_content': 'Content'
        }
        
        result = await enhanced_manager.add_context_item(context_data)
        
        assert result['success'] is False
        assert 'cannot be empty' in result['error']
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_insert_no_data(self, enhanced_manager):
        """Test get quotas when insert returns no data - line 461"""
        mock_result = Mock()
        mock_result.data = None
        
        insert_result = Mock()
        insert_result.data = []  # No data returned
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if call_count == 1:  # select
                mock_select = Mock()
                mock_eq = Mock()
                mock_single = Mock()
                mock_execute = Mock()
                mock_execute.return_value = mock_result
                
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_single)
                mock_single.single = Mock(return_value=mock_execute)
            else:  # insert
                mock_insert = Mock()
                mock_execute = Mock()
                mock_execute.return_value = insert_result
                
                mock_table.insert = Mock(return_value=mock_insert)
                mock_insert.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.get_organization_quotas('org-123')
        
        assert result['success'] is True
        assert 'quotas' in result
    
    @pytest.mark.asyncio
    async def test_bulk_api_upload_partial_failures(self, enhanced_manager):
        """Test bulk API upload with partial failures - line 411"""
        api_data = [
            {'item_id': 'bulk-1', 'item_title': 'Title 1', 'item_content': 'Content 1'},
            {'item_id': 'bulk-2', 'item_title': 'Title 2', 'item_content': 'Content 2'}
        ]
        
        call_count = 0
        async def add_context_side_effect(item_data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {'success': True, 'item_id': 'success-1'}
            else:
                return {'success': False, 'error': 'Failed'}
        
        with patch.object(enhanced_manager, 'add_context_item', side_effect=add_context_side_effect):
            with patch.object(enhanced_manager, '_log_upload', return_value=None):
                result = await enhanced_manager.bulk_api_upload(
                    api_data, 'org-123', 'best_practice_kb', 'user-123'
                )
                
                assert result['success'] is True
                assert result['success_count'] == 1
                assert result['error_count'] == 1
    
    @pytest.mark.asyncio
    async def test_add_context_item_insert_fails(self, enhanced_manager):
        """Test add_context_item when insert fails - lines 550-554"""
        insert_result = Mock()
        insert_result.data = []  # No data
        
        mock_table = Mock()
        mock_insert = Mock()
        mock_execute = Mock()
        mock_execute.return_value = insert_result
        
        mock_table.insert = Mock(return_value=mock_insert)
        mock_insert.execute = mock_execute
        enhanced_manager.supabase.from_ = Mock(return_value=mock_table)
        
        context_data = {
            'organization_id': 'org-123',
            'rag_feature': 'best_practice_kb',
            'item_id': 'test-123',
            'item_type': 'knowledge_chunk',
            'item_title': 'Test',
            'item_content': 'Content'
        }
        
        result = await enhanced_manager.add_context_item(context_data)
        
        assert result['success'] is False
        assert 'Failed to create context item' in result['error']
    
    @pytest.mark.asyncio
    async def test_share_to_children_insert_fails(self, enhanced_manager):
        """Test share to children when insert fails - lines 599-603"""
        children_result = Mock()
        children_result.data = [{'id': 'child-1'}]
        
        insert_result = Mock()
        insert_result.data = []  # Insert fails
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if table_name == 'organizations':
                mock_select = Mock()
                mock_eq = Mock()
                mock_execute = Mock()
                mock_execute.return_value = children_result
                
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_eq.execute = mock_execute
            elif table_name == 'context_sharing':
                mock_insert = Mock()
                mock_execute = Mock()
                mock_execute.return_value = insert_result
                
                mock_table.insert = Mock(return_value=mock_insert)
                mock_insert.execute = mock_execute
            
            return mock_table
        
        enhanced_manager.supabase.from_.side_effect = from_side_effect
        
        result = await enhanced_manager.share_to_children('org-123', 'item-123', 'best_practice_kb', 'user-123')
        
        assert result['success'] is False
        assert 'error' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.enhanced_context_manager', '--cov-report=html'])

