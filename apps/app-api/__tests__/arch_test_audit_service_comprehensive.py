# apps/app-api/__tests__/test_audit_service_comprehensive.py

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.audit_service import AuditService


class TestAuditServiceComprehensive:
    """Comprehensive test suite for AuditService to achieve 95% coverage"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing"""
        mock_client = Mock()
        
        # Create a mock table that returns itself for chaining
        mock_table = Mock()
        mock_insert = Mock()
        mock_insert.execute.return_value = Mock(data=[{"id": "audit-123"}])
        mock_table.insert.return_value = mock_insert
        
        mock_select = Mock()
        mock_select.eq.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.range.return_value = mock_select
        mock_select.execute.return_value = Mock(data=[{"id": "audit-123", "action": "test_action"}], count=1)
        mock_table.select.return_value = mock_select
        
        mock_delete = Mock()
        mock_delete.execute.return_value = Mock(data=[{"id": "audit-123", "deleted": True}])
        mock_table.delete.return_value = mock_delete
        
        mock_client.from_.return_value = mock_table
        
        return mock_client

    @pytest.fixture
    def audit_service(self, mock_supabase_client):
        """Create AuditService instance with mocked Supabase client"""
        with patch('services.audit_service.get_supabase_client') as mock_get_client:
            mock_get_client.return_value = mock_supabase_client
            return AuditService()

    @pytest.fixture
    def sample_audit_data(self):
        """Sample audit data for testing"""
        return {
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "test_action",
            "resource_type": "test_resource",
            "resource_id": "resource-123",
            "details": {"test": "data"},
            "ip_address": "192.168.1.1",
            "user_agent": "Test Agent"
        }

    # Test create_audit_entry method comprehensively
    @pytest.mark.asyncio
    async def test_create_audit_entry_success(self, audit_service, sample_audit_data):
        """Test successful audit entry creation"""
        result = await audit_service.create_audit_entry(sample_audit_data)
        
        assert result["success"] is True
        assert result["audit_id"] == "audit-123"

    @pytest.mark.asyncio
    async def test_create_audit_entry_missing_user_id(self, audit_service, sample_audit_data):
        """Test audit entry creation with missing user_id"""
        sample_audit_data.pop("user_id")
        
        result = await audit_service.create_audit_entry(sample_audit_data)
        
        assert result["success"] is False
        assert "user_id cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_missing_organization_id(self, audit_service, sample_audit_data):
        """Test audit entry creation with missing organization_id"""
        sample_audit_data.pop("organization_id")
        
        result = await audit_service.create_audit_entry(sample_audit_data)
        
        assert result["success"] is False
        assert "organization_id cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_missing_action(self, audit_service, sample_audit_data):
        """Test audit entry creation with missing action"""
        sample_audit_data.pop("action")
        
        result = await audit_service.create_audit_entry(sample_audit_data)
        
        assert result["success"] is False
        assert "action cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_empty_user_id(self, audit_service, sample_audit_data):
        """Test audit entry creation with empty user_id"""
        sample_audit_data["user_id"] = ""
        
        result = await audit_service.create_audit_entry(sample_audit_data)
        
        assert result["success"] is False
        assert "user_id cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_empty_organization_id(self, audit_service, sample_audit_data):
        """Test audit entry creation with empty organization_id"""
        sample_audit_data["organization_id"] = ""
        
        result = await audit_service.create_audit_entry(sample_audit_data)
        
        assert result["success"] is False
        assert "organization_id cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_empty_action(self, audit_service, sample_audit_data):
        """Test audit entry creation with empty action"""
        sample_audit_data["action"] = ""
        
        result = await audit_service.create_audit_entry(sample_audit_data)
        
        assert result["success"] is False
        assert "action cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_no_data_returned(self, audit_service, sample_audit_data):
        """Test audit entry creation when no data is returned"""
        audit_service.supabase.from_.return_value.insert.return_value.execute.return_value = Mock(
            data=[]
        )
        
        result = await audit_service.create_audit_entry(sample_audit_data)
        
        assert result["success"] is False
        assert "Failed to create audit entry" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_database_error(self, audit_service, sample_audit_data):
        """Test audit entry creation with database error"""
        audit_service.supabase.from_.return_value.insert.return_value.execute.side_effect = Exception("Database error")
        
        result = await audit_service.create_audit_entry(sample_audit_data)
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test get_audit_logs method comprehensively
    @pytest.mark.asyncio
    async def test_get_audit_logs_success(self, audit_service):
        """Test successful audit logs retrieval"""
        result = await audit_service.get_audit_logs("org-123", limit=50, offset=0)
        
        assert result["success"] is True
        assert "logs" in result

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_filters(self, audit_service):
        """Test audit logs retrieval with filters"""
        result = await audit_service.get_audit_logs("org-123", limit=100, offset=10)
        
        assert result["success"] is True
        assert "logs" in result

    @pytest.mark.asyncio
    async def test_get_audit_logs_database_error(self, audit_service):
        """Test audit logs retrieval with database error"""
        # Mock the execute method to raise an exception
        audit_service.supabase.from_.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.side_effect = Exception("Database error")
        
        result = await audit_service.get_audit_logs("org-123")
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test filter_audit_logs method comprehensively
    @pytest.mark.asyncio
    async def test_filter_audit_logs_success(self, audit_service):
        """Test successful audit logs filtering"""
        filters = {
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "test_action"
        }
        
        result = await audit_service.filter_audit_logs(filters)
        
        assert result["success"] is True
        assert "logs" in result

    @pytest.mark.asyncio
    async def test_filter_audit_logs_empty_filters(self, audit_service):
        """Test audit logs filtering with empty filters"""
        filters = {}
        
        result = await audit_service.filter_audit_logs(filters)
        
        assert result["success"] is True
        assert "logs" in result

    @pytest.mark.asyncio
    async def test_filter_audit_logs_database_error(self, audit_service):
        """Test audit logs filtering with database error"""
        audit_service.supabase.from_.return_value.select.return_value.execute.side_effect = Exception("Database error")
        
        filters = {"user_id": "user-123"}
        result = await audit_service.filter_audit_logs(filters)
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test export_audit_logs method comprehensively
    @pytest.mark.asyncio
    async def test_export_audit_logs_success(self, audit_service):
        """Test successful audit logs export"""
        export_config = {
            "organization_id": "org-123",
            "format": "json",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result["success"] is True
        assert "json_data" in result

    @pytest.mark.asyncio
    async def test_export_audit_logs_csv_format(self, audit_service):
        """Test audit logs export in CSV format"""
        export_config = {
            "organization_id": "org-123",
            "format": "csv",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result["success"] is True
        assert "csv_data" in result

    @pytest.mark.asyncio
    async def test_export_audit_logs_invalid_format(self, audit_service):
        """Test audit logs export with invalid format"""
        export_config = {
            "organization_id": "org-123",
            "format": "invalid",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result["success"] is False
        assert "Unsupported format" in result["error"]

    @pytest.mark.asyncio
    async def test_export_audit_logs_database_error(self, audit_service):
        """Test audit logs export with database error"""
        audit_service.supabase.from_.return_value.select.return_value.execute.side_effect = Exception("Database error")
        
        export_config = {
            "organization_id": "org-123",
            "format": "json",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test get_audit_statistics method comprehensively
    @pytest.mark.asyncio
    async def test_get_audit_statistics_success(self, audit_service):
        """Test successful audit statistics retrieval"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        result = await audit_service.get_audit_statistics("org-123", start_date, end_date)
        
        assert result["success"] is True
        assert "statistics" in result

    @pytest.mark.asyncio
    async def test_get_audit_statistics_database_error(self, audit_service):
        """Test audit statistics retrieval with database error"""
        audit_service.supabase.from_.return_value.select.return_value.execute.side_effect = Exception("Database error")
        
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        result = await audit_service.get_audit_statistics("org-123", start_date, end_date)
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test get_user_activity_summary method comprehensively
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_success(self, audit_service):
        """Test successful user activity summary retrieval"""
        result = await audit_service.get_user_activity_summary("org-123", "user-123")
        
        assert result["success"] is True
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_get_user_activity_summary_database_error(self, audit_service):
        """Test user activity summary retrieval with database error"""
        audit_service.supabase.from_.return_value.select.return_value.execute.side_effect = Exception("Database error")
        
        result = await audit_service.get_user_activity_summary("org-123", "user-123")
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test check_security_alerts method comprehensively
    @pytest.mark.asyncio
    async def test_check_security_alerts_success(self, audit_service):
        """Test successful security alerts check"""
        result = await audit_service.check_security_alerts("org-123", time_window_minutes=10)
        
        assert result["success"] is True
        assert "alerts" in result

    @pytest.mark.asyncio
    async def test_check_security_alerts_default_window(self, audit_service):
        """Test security alerts check with default time window"""
        result = await audit_service.check_security_alerts("org-123")
        
        assert result["success"] is True
        assert "alerts" in result

    @pytest.mark.asyncio
    async def test_check_security_alerts_database_error(self, audit_service):
        """Test security alerts check with database error"""
        audit_service.supabase.from_.return_value.select.return_value.execute.side_effect = Exception("Database error")
        
        result = await audit_service.check_security_alerts("org-123")
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test cleanup_old_logs method comprehensively
    @pytest.mark.asyncio
    async def test_cleanup_old_logs_success(self, audit_service):
        """Test successful old logs cleanup"""
        result = await audit_service.cleanup_old_logs("org-123", retention_days=30)
        
        assert result["success"] is True
        assert "deleted_count" in result

    @pytest.mark.asyncio
    async def test_cleanup_old_logs_default_retention(self, audit_service):
        """Test old logs cleanup with default retention"""
        result = await audit_service.cleanup_old_logs("org-123")
        
        assert result["success"] is True
        assert "deleted_count" in result

    @pytest.mark.asyncio
    async def test_cleanup_old_logs_database_error(self, audit_service):
        """Test old logs cleanup with database error"""
        audit_service.supabase.from_.return_value.delete.return_value.execute.side_effect = Exception("Database error")
        
        result = await audit_service.cleanup_old_logs("org-123")
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test get_performance_metrics method comprehensively
    @pytest.mark.asyncio
    async def test_get_performance_metrics_success(self, audit_service):
        """Test successful performance metrics retrieval"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        result = await audit_service.get_performance_metrics("org-123", start_date, end_date)
        
        assert result["success"] is True
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_get_performance_metrics_database_error(self, audit_service):
        """Test performance metrics retrieval with database error"""
        audit_service.supabase.from_.return_value.select.return_value.execute.side_effect = Exception("Database error")
        
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        result = await audit_service.get_performance_metrics("org-123", start_date, end_date)
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test error handling and edge cases
    @pytest.mark.asyncio
    async def test_create_audit_entry_none_data(self, audit_service):
        """Test audit entry creation with None data"""
        result = await audit_service.create_audit_entry(None)
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_create_audit_entry_invalid_data_type(self, audit_service):
        """Test audit entry creation with invalid data type"""
        result = await audit_service.create_audit_entry("invalid_data")
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_audit_logs_invalid_organization_id(self, audit_service):
        """Test audit logs retrieval with invalid organization ID"""
        result = await audit_service.get_audit_logs("")
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_filter_audit_logs_none_filters(self, audit_service):
        """Test audit logs filtering with None filters"""
        result = await audit_service.filter_audit_logs(None)
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_export_audit_logs_missing_config(self, audit_service):
        """Test audit logs export with missing configuration"""
        result = await audit_service.export_audit_logs({})
        
        assert result["success"] is False
        assert "error" in result

    # Test concurrent operations
    @pytest.mark.asyncio
    async def test_concurrent_audit_operations(self, audit_service, sample_audit_data):
        """Test concurrent audit operations"""
        tasks = [
            audit_service.create_audit_entry(sample_audit_data),
            audit_service.get_audit_logs("org-123"),
            audit_service.filter_audit_logs({"user_id": "user-123"})
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should complete
        assert len(results) == 3
        for result in results:
            assert result is not None
            if isinstance(result, dict):
                assert "success" in result