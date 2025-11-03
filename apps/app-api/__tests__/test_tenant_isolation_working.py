# apps/app-api/__tests__/test_tenant_isolation_working.py
"""
Working tests for Tenant Isolation Service
Target: 95% coverage starting from 0%
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.tenant_isolation_service import TenantIsolationService
from test_utils import SupabaseMockBuilder


class TestTenantIsolationServiceWorking:
    """Core tests for Tenant Isolation Service"""
    
    @pytest.fixture
    def mock_builder(self):
        """Create mock builder"""
        return SupabaseMockBuilder()
    
    @pytest.fixture
    def tenant_service(self, mock_builder):
        """Create tenant isolation service with mocked supabase"""
        with patch('services.tenant_isolation_service.get_supabase_client', return_value=mock_builder.get_mock_client()):
            return TenantIsolationService()
    
    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_success(self, tenant_service, mock_builder):
        """Test enforce isolation with same organization"""
        # Setup user org
        user_org = {'user_id': 'user-123', 'organization_id': 'org-123'}
        
        # Mock _get_user_organization
        with patch.object(tenant_service, '_get_user_organization', return_value=user_org):
            result = await tenant_service.enforce_tenant_isolation(
                user_id='user-123',
                organization_id='org-123',
                resource_type='context_item',
                resource_id='item-123'
            )
            
            assert result['success'] is True
            assert result['access_granted'] is True
    
    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_no_user_org(self, tenant_service):
        """Test enforce isolation when user org not found"""
        with patch.object(tenant_service, '_get_user_organization', return_value=None):
            result = await tenant_service.enforce_tenant_isolation(
                user_id='user-123',
                organization_id='org-123',
                resource_type='context_item',
                resource_id='item-123'
            )
            
            assert result['success'] is False
            assert 'User organization not found' in result['error']
    
    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_cross_tenant_allowed(self, tenant_service):
        """Test enforce isolation with cross-tenant access"""
        user_org = {'user_id': 'user-123', 'organization_id': 'org-123'}
        
        with patch.object(tenant_service, '_get_user_organization', return_value=user_org):
            with patch.object(tenant_service, '_check_cross_tenant_access', return_value=True):
                result = await tenant_service.enforce_tenant_isolation(
                    user_id='user-123',
                    organization_id='org-456',  # Different org
                    resource_type='context_item',
                    resource_id='item-123'
                )
                
                assert result['success'] is True
                assert result['access_granted'] is True
    
    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_cross_tenant_denied(self, tenant_service):
        """Test enforce isolation with cross-tenant access denied"""
        user_org = {'user_id': 'user-123', 'organization_id': 'org-123'}
        
        with patch.object(tenant_service, '_get_user_organization', return_value=user_org):
            with patch.object(tenant_service, '_check_cross_tenant_access', return_value=False):
                result = await tenant_service.enforce_tenant_isolation(
                    user_id='user-123',
                    organization_id='org-456',  # Different org
                    resource_type='context_item',
                    resource_id='item-123'
                )
                
                assert result['success'] is False
                assert result['isolation_violation'] is True
                assert 'Cross-tenant access denied' in result['error']
    
    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_exception(self, tenant_service):
        """Test enforce isolation exception handling"""
        with patch.object(tenant_service, '_get_user_organization', side_effect=Exception("DB error")):
            result = await tenant_service.enforce_tenant_isolation(
                user_id='user-123',
                organization_id='org-123',
                resource_type='context_item',
                resource_id='item-123'
            )
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_create_isolation_policy_success(self, tenant_service, mock_builder):
        """Test create isolation policy"""
        policy_data = {
            'organization_id': 'org-123',
            'policy_type': 'strict',
            'policy_name': 'Data Isolation',
            'policy_rules': {'type': 'strict'}
        }
        
        mock_builder.insert_response.data = [{'id': 'policy-123'}]
        
        result = await tenant_service.create_isolation_policy(policy_data)
        
        assert result['success'] is True
        assert result['policy_id'] == 'policy-123'
    
    @pytest.mark.asyncio
    async def test_create_isolation_policy_missing_field(self, tenant_service):
        """Test create policy with missing required field"""
        policy_data = {
            'organization_id': 'org-123',
            'policy_type': 'strict',
            'policy_name': 'Data Isolation'
            # Missing policy_rules
        }
        
        result = await tenant_service.create_isolation_policy(policy_data)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_create_isolation_policy_insert_failure(self, tenant_service, mock_builder):
        """Test create policy when insert fails"""
        mock_builder.insert_response.data = None
        
        policy_data = {
            'organization_id': 'org-123',
            'policy_type': 'strict',
            'policy_name': 'Data Isolation',
            'policy_rules': {'type': 'strict'}
        }
        
        result = await tenant_service.create_isolation_policy(policy_data)
        
        assert result['success'] is False
        assert result['error'] == 'Failed to create isolation policy'
    
    @pytest.mark.asyncio
    async def test_create_isolation_policy_exception(self, tenant_service):
        """Test create policy exception handling"""
        policy_data = {'organization_id': 'org-123'}
        tenant_service.supabase.from_.side_effect = Exception("DB error")
        
        result = await tenant_service.create_isolation_policy(policy_data)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_isolation_policies_success(self, tenant_service, mock_builder):
        """Test get isolation policies"""
        policies = [{'id': 'policy-1', 'name': 'Strict'}]
        mock_builder.setup_table_data('tenant_isolation_policies', policies)
        
        result = await tenant_service.get_isolation_policies('org-123')
        
        assert result['success'] is True
        assert len(result['policies']) == 1
    
    @pytest.mark.asyncio
    async def test_get_isolation_policies_empty(self, tenant_service, mock_builder):
        """Test get policies with empty result"""
        mock_builder.setup_table_data('tenant_isolation_policies', [])
        
        result = await tenant_service.get_isolation_policies('org-123')
        
        assert result['success'] is True
        assert result['policies'] == []
    
    @pytest.mark.asyncio
    async def test_get_isolation_policies_exception(self, tenant_service):
        """Test get policies exception handling"""
        tenant_service.supabase.from_.side_effect = Exception("DB error")
        
        result = await tenant_service.get_isolation_policies('org-123')
        
        assert result['success'] is False
        assert result['policies'] == []
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_within_quota(self, tenant_service):
        """Test check quota limits when within quota"""
        quotas = {
            'success': True,
            'quotas': {
                'current_context_items': 5,
                'max_context_items': 100,
                'current_global_access': 2,
                'max_global_access_features': 10,
                'current_sharing_requests': 5,
                'max_sharing_requests': 50
            }
        }
        
        with patch.object(tenant_service, '_get_organization_quotas', return_value=quotas):
            result = await tenant_service.check_quota_limits('org-123', 'context_items', quantity=5)
            
            assert result['success'] is True
            assert result['quota_check_passed'] is True
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_exceeded(self, tenant_service):
        """Test check quota limits when exceeded"""
        quotas = {
            'success': True,
            'quotas': {
                'current_context_items': 95,
                'max_context_items': 100,
                'current_global_access': 2,
                'max_global_access_features': 10,
                'current_sharing_requests': 5,
                'max_sharing_requests': 50
            }
        }
        
        with patch.object(tenant_service, '_get_organization_quotas', return_value=quotas):
            result = await tenant_service.check_quota_limits('org-123', 'context_items', quantity=10)
            
            assert result['success'] is False
            assert result['quota_exceeded'] is True
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_quota_not_found(self, tenant_service):
        """Test check quota when quota not found"""
        quotas = {'success': False, 'error': 'No quotas'}
        
        with patch.object(tenant_service, '_get_organization_quotas', return_value=quotas):
            result = await tenant_service.check_quota_limits('org-123', 'context_items')
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_exception(self, tenant_service):
        """Test check quota exception handling"""
        with patch.object(tenant_service, '_get_organization_quotas', side_effect=Exception("Error")):
            result = await tenant_service.check_quota_limits('org-123', 'rag_query')
            
            assert result['success'] is False
            assert 'error' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service', '--cov-report=html'])

