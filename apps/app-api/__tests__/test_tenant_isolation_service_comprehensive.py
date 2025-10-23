# apps/app-api/__tests__/test_tenant_isolation_service_comprehensive.py

import pytest
import asyncio
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
import json

from services.tenant_isolation_service import TenantIsolationService
from test_utils import SupabaseMockBuilder, TestDataFactory, MockResponseBuilder

class TestTenantIsolationServiceComprehensive:
    """Comprehensive test suite for Tenant Isolation Service with 95% coverage"""

    @pytest.fixture
    def mock_builder(self):
        """Create mock builder for Supabase client"""
        return SupabaseMockBuilder()

    @pytest.fixture
    def tenant_isolation_service(self, mock_builder):
        """Create TenantIsolationService with mocked Supabase client"""
        with patch('services.tenant_isolation_service.get_supabase_client', return_value=mock_builder.get_mock_client()):
            return TenantIsolationService()

    # ==================== TENANT ISOLATION TESTS ====================

    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_success(self, tenant_isolation_service, mock_builder):
        """Test successful tenant isolation enforcement"""
        # Mock user belongs to organization
        user_profile = {
            "user_id": "user-123",
            "organization_id": "org-123",
            "role": "salesperson"
        }
        mock_builder.setup_table_data('profiles', [user_profile])
        
        result = await tenant_isolation_service.enforce_tenant_isolation(
            user_id="user-123",
            organization_id="org-123",
            resource_type="context_item",
            resource_id="item-123"
        )
        
        assert result["success"] is True
        assert result["access_granted"] is True

    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_user_not_found(self, tenant_isolation_service, mock_builder):
        """Test tenant isolation when user not found"""
        mock_builder.setup_table_data('profiles', [])
        
        result = await tenant_isolation_service.enforce_tenant_isolation(
            user_id="non-existent-user",
            organization_id="org-123",
            resource_type="context_item",
            resource_id="item-123"
        )
        
        assert result["success"] is False
        assert "User not found" in result["error"]

    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_wrong_organization(self, tenant_isolation_service, mock_builder):
        """Test tenant isolation when user belongs to different organization"""
        user_profile = {
            "user_id": "user-123",
            "organization_id": "org-456",  # Different org
            "role": "salesperson"
        }
        mock_builder.setup_table_data('profiles', [user_profile])
        
        result = await tenant_isolation_service.enforce_tenant_isolation(
            user_id="user-123",
            organization_id="org-123",  # Trying to access this org
            resource_type="context_item",
            resource_id="item-123"
        )
        
        assert result["success"] is False
        assert "Access denied" in result["error"]

    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_system_admin(self, tenant_isolation_service, mock_builder):
        """Test tenant isolation with system admin (should have access)"""
        user_profile = {
            "user_id": "user-123",
            "organization_id": "org-456",
            "role": "system_admin"  # System admin can access any org
        }
        mock_builder.setup_table_data('profiles', [user_profile])
        
        result = await tenant_isolation_service.enforce_tenant_isolation(
            user_id="user-123",
            organization_id="org-123",  # Different org, but system admin
            resource_type="context_item",
            resource_id="item-123"
        )
        
        assert result["success"] is True
        assert result["access_granted"] is True

    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_database_error(self, tenant_isolation_service, mock_builder):
        """Test tenant isolation with database error"""
        mock_builder.setup_error_response('profiles', 'Database connection failed')
        
        result = await tenant_isolation_service.enforce_tenant_isolation(
            user_id="user-123",
            organization_id="org-123",
            resource_type="context_item",
            resource_id="item-123"
        )
        
        assert result["success"] is False
        assert "Database connection failed" in result["error"]

    # ==================== QUOTA MANAGEMENT TESTS ====================

    @pytest.mark.asyncio
    async def test_check_quota_limits_within_quota(self, tenant_isolation_service, mock_builder):
        """Test quota limits check when within quota"""
        quotas = TestDataFactory.create_organization_quotas({
            "max_context_items": 1000,
            "current_context_items": 100
        })
        mock_builder.setup_table_data('organization_context_quotas', [quotas])
        
        result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="context_items",
            quantity=50
        )
        
        assert result["success"] is True
        assert result["within_quota"] is True
        assert result["remaining_quota"] == 850

    @pytest.mark.asyncio
    async def test_check_quota_limits_exceeds_quota(self, tenant_isolation_service, mock_builder):
        """Test quota limits check when exceeds quota"""
        quotas = TestDataFactory.create_organization_quotas({
            "max_context_items": 1000,
            "current_context_items": 950
        })
        mock_builder.setup_table_data('organization_context_quotas', [quotas])
        
        result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="context_items",
            quantity=100  # Would exceed quota
        )
        
        assert result["success"] is True
        assert result["within_quota"] is False
        assert result["remaining_quota"] == 50

    @pytest.mark.asyncio
    async def test_check_quota_limits_create_default(self, tenant_isolation_service, mock_builder):
        """Test quota limits check when quotas don't exist (create default)"""
        mock_builder.setup_table_data('organization_context_quotas', [])
        
        result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="context_items",
            quantity=10
        )
        
        assert result["success"] is True
        assert result["within_quota"] is True

    @pytest.mark.asyncio
    async def test_check_quota_limits_database_error(self, tenant_isolation_service, mock_builder):
        """Test quota limits check with database error"""
        mock_builder.setup_error_response('organization_context_quotas', 'Query failed')
        
        result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="context_items",
            quantity=10
        )
        
        assert result["success"] is False
        assert "Query failed" in result["error"]

    @pytest.mark.asyncio
    async def test_update_quota_usage_success(self, tenant_isolation_service, mock_builder):
        """Test successful quota usage update"""
        quotas = TestDataFactory.create_organization_quotas({
            "current_context_items": 100
        })
        mock_builder.setup_table_data('organization_context_quotas', [quotas])
        
        result = await tenant_isolation_service.update_quota_usage(
            organization_id="org-123",
            operation_type="context_items",
            quantity=5
        )
        
        assert result["success"] is True
        assert "updated_quotas" in result

    @pytest.mark.asyncio
    async def test_update_quota_usage_database_error(self, tenant_isolation_service, mock_builder):
        """Test quota usage update with database error"""
        mock_builder.setup_error_response('organization_context_quotas', 'Update failed')
        
        result = await tenant_isolation_service.update_quota_usage(
            organization_id="org-123",
            operation_type="context_items",
            quantity=5
        )
        
        assert result["success"] is False
        assert "Update failed" in result["error"]

    @pytest.mark.asyncio
    async def test_reset_quota_usage_success(self, tenant_isolation_service, mock_builder):
        """Test successful quota usage reset"""
        result = await tenant_isolation_service.reset_quota_usage(
            organization_id="org-123",
            operation_type="context_items"
        )
        
        assert result["success"] is True
        assert "reset_quotas" in result

    @pytest.mark.asyncio
    async def test_reset_quota_usage_database_error(self, tenant_isolation_service, mock_builder):
        """Test quota usage reset with database error"""
        mock_builder.setup_error_response('organization_context_quotas', 'Reset failed')
        
        result = await tenant_isolation_service.reset_quota_usage(
            organization_id="org-123",
            operation_type="context_items"
        )
        
        assert result["success"] is False
        assert "Reset failed" in result["error"]

    # ==================== RAG FEATURE TOGGLES TESTS ====================

    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_success(self, tenant_isolation_service, mock_builder):
        """Test successful retrieval of RAG feature toggles"""
        toggles = [
            TestDataFactory.create_rag_toggle({"rag_feature": "best_practice_kb", "enabled": True}),
            TestDataFactory.create_rag_toggle({"rag_feature": "customer_insight_rag", "enabled": False})
        ]
        mock_builder.setup_table_data('organization_rag_toggles', toggles)
        
        result = await tenant_isolation_service.get_rag_feature_toggles("org-123")
        
        assert result["success"] is True
        assert len(result["toggles"]) == 2
        assert result["toggles"]["best_practice_kb"] is True
        assert result["toggles"]["customer_insight_rag"] is False

    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_create_default(self, tenant_isolation_service, mock_builder):
        """Test creating default toggles when none exist"""
        mock_builder.setup_table_data('organization_rag_toggles', [])
        
        result = await tenant_isolation_service.get_rag_feature_toggles("org-123")
        
        assert result["success"] is True
        assert "toggles" in result

    @pytest.mark.asyncio
    async def test_get_rag_feature_toggles_database_error(self, tenant_isolation_service, mock_builder):
        """Test retrieving RAG feature toggles with database error"""
        mock_builder.setup_error_response('organization_rag_toggles', 'Query failed')
        
        result = await tenant_isolation_service.get_rag_feature_toggles("org-123")
        
        assert result["success"] is False
        assert "Query failed" in result["error"]

    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_success(self, tenant_isolation_service, mock_builder):
        """Test successful update of RAG feature toggle"""
        result = await tenant_isolation_service.update_rag_feature_toggle(
            organization_id="org-123",
            rag_feature="best_practice_kb",
            enabled=True
        )
        
        assert result["success"] is True
        assert "updated_toggle" in result

    @pytest.mark.asyncio
    async def test_update_rag_feature_toggle_database_error(self, tenant_isolation_service, mock_builder):
        """Test updating RAG feature toggle with database error"""
        mock_builder.setup_error_response('organization_rag_toggles', 'Update failed')
        
        result = await tenant_isolation_service.update_rag_feature_toggle(
            organization_id="org-123",
            rag_feature="best_practice_kb",
            enabled=True
        )
        
        assert result["success"] is False
        assert "Update failed" in result["error"]

    @pytest.mark.asyncio
    async def test_bulk_update_rag_feature_toggles_success(self, tenant_isolation_service, mock_builder):
        """Test successful bulk update of RAG feature toggles"""
        toggle_updates = {
            "best_practice_kb": True,
            "customer_insight_rag": False,
            "performance_improvement_rag": True
        }
        
        result = await tenant_isolation_service.bulk_update_rag_feature_toggles(
            organization_id="org-123",
            toggle_updates=toggle_updates
        )
        
        assert result["success"] is True
        assert result["updated_count"] == 3

    @pytest.mark.asyncio
    async def test_bulk_update_rag_feature_toggles_database_error(self, tenant_isolation_service, mock_builder):
        """Test bulk update of RAG feature toggles with database error"""
        mock_builder.setup_error_response('organization_rag_toggles', 'Bulk update failed')
        
        toggle_updates = {"best_practice_kb": True}
        
        result = await tenant_isolation_service.bulk_update_rag_feature_toggles(
            organization_id="org-123",
            toggle_updates=toggle_updates
        )
        
        assert result["success"] is False
        assert "Bulk update failed" in result["error"]

    @pytest.mark.asyncio
    async def test_is_rag_feature_enabled_success(self, tenant_isolation_service, mock_builder):
        """Test checking if RAG feature is enabled"""
        toggle = TestDataFactory.create_rag_toggle({"enabled": True})
        mock_builder.setup_table_data('organization_rag_toggles', [toggle])
        
        result = await tenant_isolation_service.is_rag_feature_enabled(
            organization_id="org-123",
            rag_feature="best_practice_kb"
        )
        
        assert result["success"] is True
        assert result["enabled"] is True

    @pytest.mark.asyncio
    async def test_is_rag_feature_enabled_disabled(self, tenant_isolation_service, mock_builder):
        """Test checking if RAG feature is disabled"""
        toggle = TestDataFactory.create_rag_toggle({"enabled": False})
        mock_builder.setup_table_data('organization_rag_toggles', [toggle])
        
        result = await tenant_isolation_service.is_rag_feature_enabled(
            organization_id="org-123",
            rag_feature="best_practice_kb"
        )
        
        assert result["success"] is True
        assert result["enabled"] is False

    @pytest.mark.asyncio
    async def test_is_rag_feature_enabled_not_found(self, tenant_isolation_service, mock_builder):
        """Test checking RAG feature when toggle not found"""
        mock_builder.setup_table_data('organization_rag_toggles', [])
        
        result = await tenant_isolation_service.is_rag_feature_enabled(
            organization_id="org-123",
            rag_feature="non_existent_feature"
        )
        
        assert result["success"] is True
        assert result["enabled"] is False  # Default to disabled

    @pytest.mark.asyncio
    async def test_is_rag_feature_enabled_database_error(self, tenant_isolation_service, mock_builder):
        """Test checking RAG feature with database error"""
        mock_builder.setup_error_response('organization_rag_toggles', 'Query failed')
        
        result = await tenant_isolation_service.is_rag_feature_enabled(
            organization_id="org-123",
            rag_feature="best_practice_kb"
        )
        
        assert result["success"] is False
        assert "Query failed" in result["error"]

    # ==================== SECURITY POLICY TESTS ====================

    @pytest.mark.asyncio
    async def test_validate_cross_tenant_access_allowed(self, tenant_isolation_service, mock_builder):
        """Test cross-tenant access validation when allowed"""
        sharing_record = TestDataFactory.create_context_sharing({
            "status": "approved",
            "target_organization_id": "org-456"
        })
        mock_builder.setup_table_data('context_sharing', [sharing_record])
        
        result = await tenant_isolation_service.validate_cross_tenant_access(
            user_org_id="org-456",
            target_org_id="org-123",
            resource_type="context_item",
            resource_id="item-123"
        )
        
        assert result["success"] is True
        assert result["access_allowed"] is True

    @pytest.mark.asyncio
    async def test_validate_cross_tenant_access_denied(self, tenant_isolation_service, mock_builder):
        """Test cross-tenant access validation when denied"""
        mock_builder.setup_table_data('context_sharing', [])  # No sharing record
        
        result = await tenant_isolation_service.validate_cross_tenant_access(
            user_org_id="org-456",
            target_org_id="org-123",
            resource_type="context_item",
            resource_id="item-123"
        )
        
        assert result["success"] is True
        assert result["access_allowed"] is False

    @pytest.mark.asyncio
    async def test_validate_cross_tenant_access_pending(self, tenant_isolation_service, mock_builder):
        """Test cross-tenant access validation with pending sharing"""
        sharing_record = TestDataFactory.create_context_sharing({
            "status": "pending",
            "target_organization_id": "org-456"
        })
        mock_builder.setup_table_data('context_sharing', [sharing_record])
        
        result = await tenant_isolation_service.validate_cross_tenant_access(
            user_org_id="org-456",
            target_org_id="org-123",
            resource_type="context_item",
            resource_id="item-123"
        )
        
        assert result["success"] is True
        assert result["access_allowed"] is False

    @pytest.mark.asyncio
    async def test_validate_cross_tenant_access_database_error(self, tenant_isolation_service, mock_builder):
        """Test cross-tenant access validation with database error"""
        mock_builder.setup_error_response('context_sharing', 'Query failed')
        
        result = await tenant_isolation_service.validate_cross_tenant_access(
            user_org_id="org-456",
            target_org_id="org-123",
            resource_type="context_item",
            resource_id="item-123"
        )
        
        assert result["success"] is False
        assert "Query failed" in result["error"]

    @pytest.mark.asyncio
    async def test_log_security_violation_success(self, tenant_isolation_service, mock_builder):
        """Test successful security violation logging"""
        result = await tenant_isolation_service.log_security_violation(
            user_id="user-123",
            organization_id="org-123",
            violation_type="unauthorized_access",
            resource_type="context_item",
            resource_id="item-123",
            details={"attempted_action": "read", "ip_address": "192.168.1.1"}
        )
        
        assert result["success"] is True
        assert "violation_id" in result

    @pytest.mark.asyncio
    async def test_log_security_violation_database_error(self, tenant_isolation_service, mock_builder):
        """Test security violation logging with database error"""
        mock_builder.setup_error_response('security_violations', 'Insert failed')
        
        result = await tenant_isolation_service.log_security_violation(
            user_id="user-123",
            organization_id="org-123",
            violation_type="unauthorized_access",
            resource_type="context_item",
            resource_id="item-123",
            details={"attempted_action": "read"}
        )
        
        assert result["success"] is False
        assert "Insert failed" in result["error"]

    # ==================== HELPER METHOD TESTS ====================

    @pytest.mark.asyncio
    async def test_get_user_organization_success(self, tenant_isolation_service, mock_builder):
        """Test successful user organization retrieval"""
        user_profile = {
            "user_id": "user-123",
            "organization_id": "org-123",
            "role": "salesperson"
        }
        mock_builder.setup_table_data('profiles', [user_profile])
        
        result = await tenant_isolation_service._get_user_organization("user-123")
        
        assert result["success"] is True
        assert result["organization_id"] == "org-123"

    @pytest.mark.asyncio
    async def test_get_user_organization_not_found(self, tenant_isolation_service, mock_builder):
        """Test user organization retrieval when user not found"""
        mock_builder.setup_table_data('profiles', [])
        
        result = await tenant_isolation_service._get_user_organization("non-existent-user")
        
        assert result["success"] is False
        assert "User not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_user_organization_database_error(self, tenant_isolation_service, mock_builder):
        """Test user organization retrieval with database error"""
        mock_builder.setup_error_response('profiles', 'Query failed')
        
        result = await tenant_isolation_service._get_user_organization("user-123")
        
        assert result["success"] is False
        assert "Query failed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_organization_quotas_success(self, tenant_isolation_service, mock_builder):
        """Test successful organization quotas retrieval"""
        quotas = TestDataFactory.create_organization_quotas()
        mock_builder.setup_table_data('organization_context_quotas', [quotas])
        
        result = await tenant_isolation_service._get_organization_quotas("org-123")
        
        assert result["success"] is True
        assert result["quotas"]["organization_id"] == "org-123"

    @pytest.mark.asyncio
    async def test_get_organization_quotas_not_found(self, tenant_isolation_service, mock_builder):
        """Test organization quotas retrieval when not found"""
        mock_builder.setup_table_data('organization_context_quotas', [])
        
        result = await tenant_isolation_service._get_organization_quotas("org-123")
        
        assert result["success"] is True
        assert result["quotas"] is None

    @pytest.mark.asyncio
    async def test_get_organization_quotas_database_error(self, tenant_isolation_service, mock_builder):
        """Test organization quotas retrieval with database error"""
        mock_builder.setup_error_response('organization_context_quotas', 'Query failed')
        
        result = await tenant_isolation_service._get_organization_quotas("org-123")
        
        assert result["success"] is False
        assert "Query failed" in result["error"]

    @pytest.mark.asyncio
    async def test_create_default_quotas_success(self, tenant_isolation_service, mock_builder):
        """Test successful creation of default quotas"""
        result = await tenant_isolation_service._create_default_quotas("org-123")
        
        assert result["success"] is True
        assert "quotas" in result

    @pytest.mark.asyncio
    async def test_create_default_quotas_database_error(self, tenant_isolation_service, mock_builder):
        """Test creation of default quotas with database error"""
        mock_builder.setup_error_response('organization_context_quotas', 'Insert failed')
        
        result = await tenant_isolation_service._create_default_quotas("org-123")
        
        assert result["success"] is False
        assert "Insert failed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_default_rag_toggles(self, tenant_isolation_service):
        """Test getting default RAG feature toggles"""
        toggles = tenant_isolation_service._get_default_rag_toggles()
        
        assert isinstance(toggles, dict)
        assert len(toggles) > 0
        # Check that all values are boolean
        for enabled in toggles.values():
            assert isinstance(enabled, bool)

    @pytest.mark.asyncio
    async def test_get_default_quotas(self, tenant_isolation_service):
        """Test getting default quotas"""
        quotas = tenant_isolation_service._get_default_quotas()
        
        assert isinstance(quotas, dict)
        assert "max_context_items" in quotas
        assert "max_global_access_features" in quotas
        assert "max_sharing_requests" in quotas
        # Check that all values are positive integers
        for value in quotas.values():
            assert isinstance(value, int)
            assert value > 0

    # ==================== EDGE CASE TESTS ====================

    @pytest.mark.asyncio
    async def test_enforce_tenant_isolation_empty_parameters(self, tenant_isolation_service):
        """Test tenant isolation with empty parameters"""
        result = await tenant_isolation_service.enforce_tenant_isolation(
            user_id="",
            organization_id="",
            resource_type="",
            resource_id=""
        )
        
        assert result["success"] is False
        assert "cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_check_quota_limits_negative_quantity(self, tenant_isolation_service, mock_builder):
        """Test quota limits check with negative quantity"""
        quotas = TestDataFactory.create_organization_quotas()
        mock_builder.setup_table_data('organization_context_quotas', [quotas])
        
        result = await tenant_isolation_service.check_quota_limits(
            organization_id="org-123",
            operation_type="context_items",
            quantity=-10
        )
        
        assert result["success"] is False
        assert "Quantity must be positive" in result["error"]

    @pytest.mark.asyncio
    async def test_update_quota_usage_zero_quantity(self, tenant_isolation_service, mock_builder):
        """Test quota usage update with zero quantity"""
        quotas = TestDataFactory.create_organization_quotas()
        mock_builder.setup_table_data('organization_context_quotas', [quotas])
        
        result = await tenant_isolation_service.update_quota_usage(
            organization_id="org-123",
            operation_type="context_items",
            quantity=0
        )
        
        assert result["success"] is True  # Zero quantity should be allowed

    @pytest.mark.asyncio
    async def test_bulk_update_rag_feature_toggles_empty(self, tenant_isolation_service):
        """Test bulk update of RAG feature toggles with empty updates"""
        result = await tenant_isolation_service.bulk_update_rag_feature_toggles(
            organization_id="org-123",
            toggle_updates={}
        )
        
        assert result["success"] is True
        assert result["updated_count"] == 0
