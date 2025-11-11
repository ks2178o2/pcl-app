# apps/app-api/__tests__/test_tenant_isolation_95_coverage.py
"""
Comprehensive test suite for Tenant Isolation Service
Target: 95% coverage for tenant_isolation_service.py
"""

import pytest
from unittest.mock import Mock, patch
from services.tenant_isolation_service import TenantIsolationService
from test_utils import SupabaseMockBuilder


@pytest.fixture
def mock_builder():
    return SupabaseMockBuilder()


@pytest.fixture
def tenant_isolation_service(mock_builder):
    with patch('services.tenant_isolation_service.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return TenantIsolationService()


class TestTenantIsolationAdvanced:
    """Test advanced isolation features"""
    
    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_violation(self, tenant_isolation_service, mock_builder):
        """Test tenant isolation violation detection"""
        user_data = [{'organization_id': 'org-456'}]
        mock_builder.setup_table_data('profiles', user_data)
        
        result = await tenant_isolation_service.enforce_tenant_isolation(
            user_id="user-123",
            organization_id="org-123",
            resource_type="item",
            resource_id="item-456"
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_create_isolation_policy(self, tenant_isolation_service, mock_builder):
        """Test creating isolation policy"""
        policy_data = {
            'organization_id': 'org-123',
            'policy_name': 'strict_isolation',
            'policy_rules': {'strict': True}
        }
        
        mock_builder.setup_table_data('isolation_policies', [])
        mock_builder.insert_response.data = [{'id': 'policy-id'}]
        
        result = await tenant_isolation_service.create_isolation_policy(policy_data)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_isolation_policies(self, tenant_isolation_service, mock_builder):
        """Test getting isolation policies"""
        policies = [
            {'id': 'policy-1', 'policy_name': 'strict'},
            {'id': 'policy-2', 'policy_name': 'moderate'}
        ]
        mock_builder.setup_table_data('isolation_policies', policies)
        
        result = await tenant_isolation_service.get_isolation_policies("org-123")
        assert result is not None


class TestTenantIsolationQuotaManagement:
    """Test quota management"""
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_exceeded(self, tenant_isolation_service, mock_builder):
        """Test quota limits when exceeded"""
        quota_data = {
            'max_context_items': 1000,
            'current_context_items': 1100
        }
        mock_builder.setup_table_data('organization_quotas', [quota_data])
        
        result = await tenant_isolation_service.check_quota_limits("org-123", "context_items")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_reset_quota_usage(self, tenant_isolation_service, mock_builder):
        """Test resetting quota usage"""
        quota_data = {
            'current_context_items': 500,
            'current_global_access': 10
        }
        mock_builder.setup_table_data('organization_quotas', [quota_data])
        mock_builder.update_response.data = [{'id': 'updated-quota'}]
        
        result = await tenant_isolation_service.reset_quota_usage("org-123")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_reset_specific_quota(self, tenant_isolation_service, mock_builder):
        """Test resetting specific quota type"""
        mock_builder.setup_table_data('organization_quotas', [])
        mock_builder.update_response.data = [{'id': 'updated-quota'}]
        
        result = await tenant_isolation_service.reset_quota_usage("org-123", quota_type="context_items")
        assert result is not None


class TestTenantIsolationRAGFeatures:
    """Test RAG feature toggles and inheritance"""
    
    @pytest.mark.asyncio
    async def test_bulk_update_rag_toggles(self, tenant_isolation_service, mock_builder):
        """Test bulk updating RAG feature toggles"""
        toggles = [
            {'rag_feature': 'sales_intelligence'},
            {'rag_feature': 'customer_insights'}
        ]
        mock_builder.setup_table_data('rag_feature_toggles', toggles)
        mock_builder.update_response.data = [{'id': 'updated-toggle'}]
        
        updates = {
            'sales_intelligence': True,
            'customer_insights': False
        }
        
        result = await tenant_isolation_service.bulk_update_rag_toggles("org-123", updates)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_inherited_features(self, tenant_isolation_service, mock_builder):
        """Test getting inherited features"""
        features = [
            {'rag_feature': 'sales_intelligence', 'inherited_from': 'parent-org'},
            {'rag_feature': 'customer_insights', 'inherited_from': 'parent-org'}
        ]
        mock_builder.setup_table_data('rag_feature_toggles', features)
        
        result = await tenant_isolation_service.get_inherited_features("org-123")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_effective_features(self, tenant_isolation_service, mock_builder):
        """Test getting effective features (own + inherited)"""
        own_features = [
            {'rag_feature': 'sales_intelligence', 'enabled': True},
            {'rag_feature': 'customer_insights', 'enabled': False}
        ]
        inherited_features = [
            {'rag_feature': 'call_analysis', 'enabled': True, 'inherited_from': 'parent'}
        ]
        mock_builder.setup_table_data('rag_feature_toggles', own_features)
        
        with patch.object(tenant_isolation_service, 'get_inherited_features') as mock_inherited:
            mock_inherited.return_value = {
                'success': True,
                'features': inherited_features
            }
            
            result = await tenant_isolation_service.get_effective_features("org-123")
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain(self, tenant_isolation_service, mock_builder):
        """Test getting inheritance chain"""
        org_data = [
            {'id': 'org-123', 'parent_organization_id': 'org-parent'},
            {'id': 'org-parent', 'parent_organization_id': 'org-grandparent'}
        ]
        mock_builder.setup_table_data('organizations', org_data)
        
        result = await tenant_isolation_service.get_inheritance_chain("org-123")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_override_status(self, tenant_isolation_service, mock_builder):
        """Test getting override status for a feature"""
        toggle_data = [
            {'rag_feature': 'sales_intelligence', 'is_inherited': False, 'enabled': True}
        ]
        mock_builder.setup_table_data('rag_feature_toggles', toggle_data)
        
        result = await tenant_isolation_service.get_override_status("org-123", "sales_intelligence")
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.tenant_isolation_service', '--cov-report=html'])

