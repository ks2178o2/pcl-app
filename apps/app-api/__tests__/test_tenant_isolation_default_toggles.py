# apps/app-api/__tests__/test_tenant_isolation_default_toggles.py
"""
Tests for default toggle creation and remaining coverage
Lines: 681-720
"""

import pytest
from unittest.mock import Mock, patch
from services.tenant_isolation_service import TenantIsolationService


class TestTenantIsolationDefaultToggles:
    """Tests for default toggle creation"""
    
    @pytest.fixture
    def tenant_service(self):
        """Create tenant isolation service"""
        with patch('services.tenant_isolation_service.get_supabase_client'):
            return TenantIsolationService()
    
    @pytest.mark.asyncio
    async def test_create_default_rag_toggles_success(self, tenant_service):
        """Test create default toggles - lines 680-716"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            table = Mock()
            insert_result = Mock()
            insert_result.data = [{'id': f'toggle-{i}', 'rag_feature': f'feature{i}'} for i in range(20)]
            
            insert_chain = Mock()
            insert_chain.execute.return_value = insert_result
            
            table.insert.return_value = insert_chain
            mock_supabase.from_.return_value = table
            
            result = await tenant_service._create_default_rag_toggles('org-123')
            
            assert len(result) == 20
            assert all('rag_feature' in toggle for toggle in result)
    
    @pytest.mark.asyncio
    async def test_create_default_rag_toggles_exception(self, tenant_service):
        """Test create default toggles exception - lines 718-720"""
        with patch.object(tenant_service, 'supabase') as mock_supabase:
            mock_supabase.from_.side_effect = Exception("Insert error")
            
            result = await tenant_service._create_default_rag_toggles('org-123')
            
            assert result == []


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service'])



