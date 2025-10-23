import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add the parent directory to the path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.tenant_isolation_service import TenantIsolationService

class TestTenantIsolationServiceAdditionalCoverage:
    """Additional tests to improve TenantIsolationService coverage to 75%+"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Create a comprehensive mock for SupabaseClientManager"""
        mock_client = Mock()
        
        # Mock the chain of methods for database operations
        mock_insert = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_order = Mock()
        mock_range = Mock()
        mock_execute = Mock()
        mock_single = Mock()
        mock_update = Mock()
        mock_delete = Mock()
        
        # Chain the mocks
        mock_client.insert.return_value = mock_insert
        mock_insert.execute.return_value = Mock(data=[{"id": "policy-123"}])
        
        mock_client.select.return_value = mock_select
        mock_select.from_.return_value = mock_select
        mock_select.eq.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.range.return_value = mock_select
        mock_select.execute.return_value = Mock(data=[
            {
                "id": "policy-123",
                "organization_id": "org-123",
                "policy_type": "data_isolation",
                "policy_name": "Test Policy"
            }
        ])
        
        mock_client.from_.return_value = mock_select
        
        return mock_client
    
    @pytest.fixture
    def tenant_isolation_service(self, mock_supabase_client):
        """Create TenantIsolationService instance with mocked dependencies"""
        with patch('services.tenant_isolation_service.get_supabase_client', return_value=mock_supabase_client):
            return TenantIsolationService()
    
    @pytest.mark.asyncio
    async def test_create_isolation_policy_missing_field(self, tenant_isolation_service, mock_supabase_client):
        """Test create isolation policy with missing required field (line 65)"""
        policy_data = {
            "organization_id": "org-123",
            "policy_type": "data_isolation",
            "policy_name": "Test Policy"
            # Missing policy_rules
        }
        
        result = await tenant_isolation_service.create_isolation_policy(policy_data)
        
        assert result["success"] is False
        assert "policy_rules is required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_isolation_policy_no_data_returned(self, tenant_isolation_service, mock_supabase_client):
        """Test create isolation policy when no data is returned (line 78)"""
        # Mock insert to return no data
        mock_supabase_client.from_.return_value.insert.return_value.execute.return_value = Mock(data=None)
        
        policy_data = {
            "organization_id": "org-123",
            "policy_type": "data_isolation",
            "policy_name": "Test Policy",
            "policy_rules": {"rule1": "value1"}
        }
        
        result = await tenant_isolation_service.create_isolation_policy(policy_data)
        
        assert result["success"] is False
        assert "Failed to create isolation policy" in result["error"]
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_quotas_failure(self, tenant_isolation_service, mock_supabase_client):
        """Test check quota limits when quotas retrieval fails (line 117)"""
        # Mock _get_organization_quotas to return failure
        tenant_isolation_service._get_organization_quotas = AsyncMock(return_value={
            "success": False,
            "error": "Failed to get quotas"
        })
        
        result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="context_items",
            quantity=10
        )
        
        assert result["success"] is False
        assert "Failed to get quotas" in result["error"]
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_context_items_exceeded(self, tenant_isolation_service, mock_supabase_client):
        """Test check quota limits when context items quota is exceeded (lines 133-146)"""
        # Mock _get_organization_quotas to return quotas
        tenant_isolation_service._get_organization_quotas = AsyncMock(return_value={
            "success": True,
            "quotas": {
                "current_context_items": 90,
                "max_context_items": 100,
                "current_file_uploads": 5,
                "max_file_uploads": 50
            }
        })
        
        result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="context_items",
            quantity=15  # This will exceed the limit (90 + 15 > 100)
        )
        
        assert result["success"] is False
        assert "quota_exceeded" in result
        assert result["quota_exceeded"] is True
        assert result["quota_type"] == "context_items"
        assert result["current"] == 90
        assert result["limit"] == 100
        assert result["requested"] == 15
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_global_access_exceeded(self, tenant_isolation_service, mock_supabase_client):
        """Test check quota limits when global access quota is exceeded"""
        # Mock _get_organization_quotas to return quotas
        tenant_isolation_service._get_organization_quotas = AsyncMock(return_value={
            "success": True,
            "quotas": {
                "current_context_items": 50,
                "max_context_items": 100,
                "current_global_access": 8,
                "max_global_access_features": 10
            }
        })
        
        result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="global_access",
            quantity=5  # This will exceed the limit (8 + 5 > 10)
        )
        
        assert result["success"] is False
        assert "quota_exceeded" in result
        assert result["quota_exceeded"] is True
        assert result["quota_type"] == "global_access"
        assert result["current"] == 8
        assert result["limit"] == 10
        assert result["requested"] == 5
    
    @pytest.mark.asyncio
    async def test_check_quota_limits_unknown_operation(self, tenant_isolation_service, mock_supabase_client):
        """Test check quota limits with unknown operation type (line 175)"""
        # Mock _get_organization_quotas to return quotas
        tenant_isolation_service._get_organization_quotas = AsyncMock(return_value={
            "success": True,
            "quotas": {
                "current_context_items": 50,
                "max_context_items": 100,
                "current_global_access": 5,
                "max_global_access_features": 10
            }
        })
        
        result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="unknown_operation",
            quantity=10
        )
        
        assert result["success"] is True
        assert "quota_check_passed" in result
        assert result["quota_check_passed"] is True
    
    @pytest.mark.asyncio
    async def test_update_quota_usage_quotas_failure(self, tenant_isolation_service, mock_supabase_client):
        """Test update quota usage when quotas retrieval fails (line 184)"""
        # Mock _get_organization_quotas to return failure
        tenant_isolation_service._get_organization_quotas = AsyncMock(return_value={
            "success": False,
            "error": "Failed to get quotas"
        })
        
        result = await tenant_isolation_service.update_quota_usage(
            organization_id="org-123",
            operation_type="context_items",
            quantity=10
        )
        
        assert result["success"] is False
        assert "Failed to get quotas" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_quota_usage_context_items_update(self, tenant_isolation_service, mock_supabase_client):
        """Test update quota usage for context items (lines 184-196)"""
        # Mock _get_organization_quotas to return quotas
        tenant_isolation_service._get_organization_quotas = AsyncMock(return_value={
            "success": True,
            "quotas": {
                "current_context_items": 50,
                "max_context_items": 100,
                "current_file_uploads": 5,
                "max_file_uploads": 50
            }
        })
        
        # Mock update to return success
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.execute.return_value = Mock(data=[{"id": "org-123"}])
        
        result = await tenant_isolation_service.update_quota_usage(
            organization_id="org-123",
            operation_type="context_items",
            quantity=10
        )
        
        assert result["success"] is True
        assert "updated_quotas" in result
    
    @pytest.mark.asyncio
    async def test_update_quota_usage_file_uploads_update(self, tenant_isolation_service, mock_supabase_client):
        """Test update quota usage for file uploads"""
        # Mock _get_organization_quotas to return quotas
        tenant_isolation_service._get_organization_quotas = AsyncMock(return_value={
            "success": True,
            "quotas": {
                "current_context_items": 50,
                "max_context_items": 100,
                "current_file_uploads": 5,
                "max_file_uploads": 50
            }
        })
        
        # Mock update to return success
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.execute.return_value = Mock(data=[{"id": "org-123"}])
        
        result = await tenant_isolation_service.update_quota_usage(
            organization_id="org-123",
            operation_type="file_uploads",
            quantity=5
        )
        
        assert result["success"] is True
        assert "updated_quotas" in result
    
    @pytest.mark.asyncio
    async def test_update_quota_usage_unknown_operation(self, tenant_isolation_service, mock_supabase_client):
        """Test update quota usage with unknown operation type (line 209)"""
        # Mock _get_organization_quotas to return quotas
        tenant_isolation_service._get_organization_quotas = AsyncMock(return_value={
            "success": True,
            "quotas": {
                "current_context_items": 50,
                "max_context_items": 100,
                "current_global_access": 5,
                "max_global_access_features": 10
            }
        })
        
        # Mock update to return no data (simulating failure)
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.execute.return_value = Mock(data=None)
        
        result = await tenant_isolation_service.update_quota_usage(
            organization_id="org-123",
            operation_type="unknown_operation",
            quantity=10
        )
        
        assert result["success"] is False
        assert "Failed to update quota usage" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_exception_handling(self, tenant_isolation_service, mock_supabase_client):
        """Test get RAG feature toggles exception handling (line 227)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await tenant_isolation_service.get_rag_feature_toggles(
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_exception_handling(self, tenant_isolation_service, mock_supabase_client):
        """Test update RAG feature toggle exception handling (line 249)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await tenant_isolation_service.update_rag_feature_toggle(
            organization_id="org-123",
            rag_feature="test_feature",
            enabled=True
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_bulk_update_rag_toggles_exception_handling(self, tenant_isolation_service, mock_supabase_client):
        """Test bulk update RAG toggles exception handling (line 270-271)"""
        # Mock update_rag_feature_toggle to return failure for all toggles
        tenant_isolation_service.update_rag_feature_toggle = AsyncMock(return_value={
            "success": False,
            "error": "Database error"
        })
        
        toggle_updates = {
            "feature1": True,
            "feature2": False
        }
        
        result = await tenant_isolation_service.bulk_update_rag_toggles(
            organization_id="org-123",
            toggle_updates=toggle_updates
        )
        
        assert result["success"] is True
        assert "updated_toggles" in result
        assert len(result["updated_toggles"]) == 0  # No successful updates
        assert "total_updated" in result
        assert result["total_updated"] == 0
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_exception_handling(self, tenant_isolation_service, mock_supabase_client):
        """Test get organization quotas exception handling (line 304)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("Database error")
        
        result = await tenant_isolation_service._get_organization_quotas(
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_organization_quotas_exception_handling(self, tenant_isolation_service, mock_supabase_client):
        """Test create organization quotas exception handling (line 317)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.insert.return_value.execute.side_effect = Exception("Database error")
        
        result = await tenant_isolation_service._create_organization_quotas(
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_organization_quotas_exception_handling(self, tenant_isolation_service, mock_supabase_client):
        """Test update organization quotas exception handling (line 340)"""
        # Mock the method to raise an exception
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        quota_updates = {
            "max_context_items": 1000,
            "max_file_uploads": 100
        }
        
        result = await tenant_isolation_service._update_organization_quotas(
            organization_id="org-123",
            quota_updates=quota_updates
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_no_data_returned(self, tenant_isolation_service, mock_supabase_client):
        """Test get organization quotas when no data is returned (line 348-350)"""
        # Mock execute to return no data
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data=None)
        
        result = await tenant_isolation_service._get_organization_quotas(
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Organization quotas not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_organization_quotas_no_data_returned(self, tenant_isolation_service, mock_supabase_client):
        """Test create organization quotas when no data is returned (line 359-363)"""
        # Mock insert to return no data
        mock_supabase_client.from_.return_value.insert.return_value.execute.return_value = Mock(data=None)
        
        result = await tenant_isolation_service._create_organization_quotas(
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Failed to create organization quotas" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_organization_quotas_no_data_returned(self, tenant_isolation_service, mock_supabase_client):
        """Test update organization quotas when no data is returned (line 368-386)"""
        # Mock update to return no data
        mock_supabase_client.from_.return_value.update.return_value.eq.return_value.execute.return_value = Mock(data=None)
        
        quota_updates = {
            "max_context_items": 1000,
            "max_file_uploads": 100
        }
        
        result = await tenant_isolation_service._update_organization_quotas(
            organization_id="org-123",
            quota_updates=quota_updates
        )
        
        assert result["success"] is False
        assert "Failed to update organization quotas" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_create_on_missing(self, tenant_isolation_service, mock_supabase_client):
        """Test get organization quotas when quotas don't exist and need to be created (line 390-419)"""
        # Mock first call to return no data (quotas don't exist)
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data=None)
        
        # Mock create to return success
        tenant_isolation_service._create_organization_quotas = AsyncMock(return_value={
            "success": True,
            "quotas": {
                "max_context_items": 100,
                "max_file_uploads": 50,
                "current_context_items": 0,
                "current_file_uploads": 0
            }
        })
        
        result = await tenant_isolation_service._get_organization_quotas(
            organization_id="org-123"
        )
        
        assert result["success"] is True
        assert "quotas" in result
    
    @pytest.mark.asyncio
    async def test_get_organization_quotas_create_failure(self, tenant_isolation_service, mock_supabase_client):
        """Test get organization quotas when create fails (line 426-465)"""
        # Mock first call to return no data (quotas don't exist)
        mock_supabase_client.from_.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(data=None)
        
        # Mock create to return failure
        tenant_isolation_service._create_organization_quotas = AsyncMock(return_value={
            "success": False,
            "error": "Failed to create quotas"
        })
        
        result = await tenant_isolation_service._get_organization_quotas(
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert "Failed to create quotas" in result["error"]
