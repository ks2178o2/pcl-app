# apps/app-api/__tests__/test_enhanced_context_95_final.py
"""
Final tests to reach 95% coverage for Enhanced Context Manager
Target: Complete all remaining missing paths
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


class TestGrantTenantAccessEdgeCases:
    """Test grant tenant access edge cases"""
    
    @pytest.mark.asyncio
    async def test_grant_tenant_access_update_failure(self, enhanced_context_manager, mock_builder):
        """Test grant access when update returns no data"""
        # Setup existing access
        mock_builder.setup_table_data('tenant_context_access', [{'organization_id': 'org-123', 'rag_feature': 'sales_intelligence'}])
        mock_builder.update_response.data = []
        
        result = await enhanced_context_manager.grant_tenant_access(
            organization_id='org-123',
            rag_feature='sales_intelligence',
            access_level='read'
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_grant_tenant_access_create_failure(self, enhanced_context_manager, mock_builder):
        """Test grant access when create returns no data"""
        # No existing access
        mock_builder.setup_table_data('tenant_context_access', [])
        mock_builder.insert_response.data = []
        
        result = await enhanced_context_manager.grant_tenant_access(
            organization_id='org-123',
            rag_feature='sales_intelligence',
            access_level='read'
        )
        
        assert result is not None
        assert result.get('success') is False


class TestRevokeTenantAccessEdgeCases:
    """Test revoke tenant access edge cases"""
    
    @pytest.mark.asyncio
    async def test_revoke_tenant_access_no_data(self, enhanced_context_manager, mock_builder):
        """Test revoke when update returns no data"""
        mock_builder.setup_table_data('tenant_context_access', [{'organization_id': 'org-123'}])
        mock_builder.update_response.data = []
        
        result = await enhanced_context_manager.revoke_tenant_access(
            organization_id='org-123',
            rag_feature='sales_intelligence'
        )
        
        assert result is not None
        assert result.get('success') is False


class TestShareContextItemErrorPaths:
    """Test share context item error handling"""
    
    @pytest.mark.asyncio
    async def test_share_context_item_no_insert_data(self, enhanced_context_manager, mock_builder):
        """Test share when insert returns no data"""
        mock_builder.setup_table_data('global_context_items', [{'id': 'item-123'}])
        mock_builder.insert_response.data = []
        
        result = await enhanced_context_manager.share_context_item(
            item_id='item-123',
            target_organization_id='org-target',
            shared_by='user-123',
            reason='Test'
        )
        
        assert result is not None
        assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_share_context_item_exception(self, enhanced_context_manager, mock_builder):
        """Test share when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.share_context_item(
                item_id='item-123',
                target_organization_id='org-target',
                shared_by='user-123',
                reason='Test'
            )
            
            assert result is not None
            assert result.get('success') is False


class TestWebScrapingAdvanced:
    """Test advanced web scraping scenarios"""
    
    @pytest.mark.asyncio
    async def test_scrape_web_content_invalid_url(self, enhanced_context_manager, mock_builder):
        """Test scraping with invalid URL"""
        mock_builder.setup_table_data('rag_context_items', [])
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Invalid URL")
            
            result = await enhanced_context_manager.scrape_web_content(
                url="not-a-valid-url",
                organization_id="org-123",
                rag_feature="sales_intelligence",
                uploaded_by="user-123"
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_bulk_api_upload_exception_handling(self, enhanced_context_manager, mock_builder):
        """Test bulk upload exception handling"""
        with patch.object(enhanced_context_manager, 'add_global_context_item') as mock_add:
            mock_add.side_effect = Exception("Upload error")
            
            result = await enhanced_context_manager.bulk_api_upload(
                items=[{'item_title': 'Test', 'item_content': 'Content'}],
                organization_id='org-123',
                rag_feature='sales_intelligence',
                uploaded_by='user-123'
            )
            
            assert result is not None


class TestQuotaManagementAdvanced:
    """Test advanced quota management"""
    
    @pytest.mark.asyncio
    async def test_update_organization_quotas_exception(self, enhanced_context_manager, mock_builder):
        """Test update quotas when exception occurs"""
        mock_builder.setup_table_data('organization_quotas', [])
        
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.update_organization_quotas(
                organization_id='org-123',
                quotas={'max_context_items': 1000}
            )
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_exception(self, enhanced_context_manager):
        """Test get quotas when exception occurs"""
        with patch.object(enhanced_context_manager.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await enhanced_context_manager.get_organization_quotas('org-123')
            
            assert result is not None
            assert result.get('success') is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.enhanced_context_manager', '--cov-report=html'])

