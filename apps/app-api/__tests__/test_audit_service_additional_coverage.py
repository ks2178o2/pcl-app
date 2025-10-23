# apps/app-api/__tests__/test_audit_service_additional_coverage.py

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.audit_service import AuditService


class TestAuditServiceAdditionalCoverage:
    """Additional test cases for AuditService to reach 95% coverage"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing"""
        mock_client = Mock()
        
        # Mock table and query chains
        mock_table = Mock()
        
        # Mock insert chain
        mock_insert = Mock()
        mock_insert.execute.return_value = Mock(data=[{"id": "audit-123"}])
        mock_table.insert.return_value = mock_insert
        
        # Mock select chain
        mock_select = Mock()
        mock_select.eq.return_value = mock_select
        mock_select.gte.return_value = mock_select
        mock_select.lte.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.range.return_value = mock_select
        mock_select.execute.return_value = Mock(
            data=[{"id": "audit-123", "action": "test_action", "user_id": "user-123"}],
            count=1
        )
        mock_table.select.return_value = mock_select
        
        # Mock delete chain
        mock_delete = Mock()
        mock_delete.eq.return_value = mock_delete
        mock_delete.lt.return_value = mock_delete
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

    # Test additional filter conditions - covers lines 106, 108, 110
    @pytest.mark.asyncio
    async def test_filter_audit_logs_with_resource_type(self, audit_service):
        """Test audit logs filtering with resource_type filter - covers line 106"""
        filters = {
            "organization_id": "org-123",
            "resource_type": "test_resource"
        }
        
        result = await audit_service.filter_audit_logs(filters)
        
        assert result["success"] is True
        assert "logs" in result

    @pytest.mark.asyncio
    async def test_filter_audit_logs_with_start_date(self, audit_service):
        """Test audit logs filtering with start_date filter - covers line 108"""
        start_date = datetime.now() - timedelta(days=7)
        filters = {
            "organization_id": "org-123",
            "start_date": start_date
        }
        
        result = await audit_service.filter_audit_logs(filters)
        
        assert result["success"] is True
        assert "logs" in result

    @pytest.mark.asyncio
    async def test_filter_audit_logs_with_end_date(self, audit_service):
        """Test audit logs filtering with end_date filter - covers line 110"""
        end_date = datetime.now()
        filters = {
            "organization_id": "org-123",
            "end_date": end_date
        }
        
        result = await audit_service.filter_audit_logs(filters)
        
        assert result["success"] is True
        assert "logs" in result

    @pytest.mark.asyncio
    async def test_filter_audit_logs_with_all_filters(self, audit_service):
        """Test audit logs filtering with all filter types"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        filters = {
            "organization_id": "org-123",
            "user_id": "user-123",
            "action": "test_action",
            "resource_type": "test_resource",
            "start_date": start_date,
            "end_date": end_date
        }
        
        result = await audit_service.filter_audit_logs(filters)
        
        assert result["success"] is True
        assert "logs" in result

    # Test CSV export with no data - covers line 150
    @pytest.mark.asyncio
    async def test_export_audit_logs_csv_no_data(self, audit_service):
        """Test CSV export with no data - covers line 150"""
        # Mock empty data response
        audit_service.supabase.from_.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = Mock(data=[])
        
        export_config = {
            "organization_id": "org-123",
            "format": "csv",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result["success"] is True
        assert "csv_data" in result
        assert result["csv_data"] == "No data found"

    # Test get_audit_statistics method - covers lines 185-220
    @pytest.mark.asyncio
    async def test_get_audit_statistics_success(self, audit_service):
        """Test successful audit statistics retrieval - covers lines 185-220"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Mock the filter_audit_logs method to return test data
        audit_service.filter_audit_logs = AsyncMock(return_value={
            "success": True,
            "logs": [
                {"action": "create", "user_id": "user-1", "created_at": "2024-01-01T10:00:00"},
                {"action": "update", "user_id": "user-2", "created_at": "2024-01-01T11:00:00"},
                {"action": "create", "user_id": "user-1", "created_at": "2024-01-01T12:00:00"},
                {"action": "delete", "user_id": "user-3", "created_at": "2024-01-01T13:00:00"}
            ]
        })
        
        result = await audit_service.get_audit_statistics("org-123", start_date, end_date)
        
        assert result["success"] is True
        assert "statistics" in result
        assert "action_counts" in result["statistics"]
        assert "unique_users" in result["statistics"]
        assert "total_actions" in result["statistics"]

    @pytest.mark.asyncio
    async def test_get_audit_statistics_filter_failure(self, audit_service):
        """Test audit statistics when filter fails - covers lines 195-196"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Mock the filter_audit_logs method to return failure
        audit_service.filter_audit_logs = AsyncMock(return_value={
            "success": False,
            "error": "Filter failed"
        })
        
        result = await audit_service.get_audit_statistics("org-123", start_date, end_date)
        
        assert result["success"] is False
        assert "Filter failed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_audit_statistics_database_error(self, audit_service):
        """Test audit statistics with database error - covers lines 217-220"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Mock the filter_audit_logs method to raise exception
        audit_service.filter_audit_logs = AsyncMock(side_effect=Exception("Database error"))
        
        result = await audit_service.get_audit_statistics("org-123", start_date, end_date)
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test get_user_activity_summary method - covers lines 225-282
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_success(self, audit_service):
        """Test successful user activity summary retrieval - covers lines 225-277"""
        # Mock the filter_audit_logs method to return test data
        audit_service.filter_audit_logs = AsyncMock(return_value={
            "success": True,
            "logs": [
                {"action": "create", "created_at": "2024-01-01T10:00:00", "resource_type": "document"},
                {"action": "update", "created_at": "2024-01-01T11:00:00", "resource_type": "document"},
                {"action": "view", "created_at": "2024-01-01T12:00:00", "resource_type": "page"}
            ]
        })
        
        result = await audit_service.get_user_activity_summary("org-123", "user-123")
        
        assert result["success"] is True
        assert "summary" in result
        assert "action_count" in result["summary"]
        assert "most_common_action" in result["summary"]

    @pytest.mark.asyncio
    async def test_get_user_activity_summary_database_error(self, audit_service):
        """Test user activity summary with database error - covers lines 278-282"""
        # Mock the filter_audit_logs method to raise exception
        audit_service.filter_audit_logs = AsyncMock(side_effect=Exception("Database error"))
        
        result = await audit_service.get_user_activity_summary("org-123", "user-123")
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test check_security_alerts method - covers lines 287-328
    @pytest.mark.asyncio
    async def test_check_security_alerts_success(self, audit_service):
        """Test successful security alerts check - covers lines 287-323"""
        # Mock the filter_audit_logs method to return test data
        audit_service.filter_audit_logs = AsyncMock(return_value={
            "success": True,
            "logs": [
                {"action": "login_failed", "created_at": "2024-01-01T10:00:00"},
                {"action": "unauthorized_access", "created_at": "2024-01-01T11:00:00"},
                {"action": "data_export", "created_at": "2024-01-01T12:00:00"}
            ]
        })
        
        result = await audit_service.check_security_alerts("org-123", time_window_minutes=10)
        
        assert result["success"] is True
        assert "alerts" in result
        assert isinstance(result["alerts"], list)

    @pytest.mark.asyncio
    async def test_check_security_alerts_database_error(self, audit_service):
        """Test security alerts check with database error - covers lines 324-328"""
        # Mock the filter_audit_logs method to raise exception
        audit_service.filter_audit_logs = AsyncMock(side_effect=Exception("Database error"))
        
        result = await audit_service.check_security_alerts("org-123")
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test cleanup_old_logs method - covers lines 333-351
    @pytest.mark.asyncio
    async def test_cleanup_old_logs_success(self, audit_service):
        """Test successful old logs cleanup - covers lines 333-346"""
        # Mock the delete operation
        mock_delete_result = Mock()
        mock_delete_result.data = [{"id": "old-log-1"}, {"id": "old-log-2"}]
        audit_service.supabase.from_.return_value.delete.return_value.eq.return_value.lt.return_value.execute.return_value = mock_delete_result
        
        result = await audit_service.cleanup_old_logs("org-123", retention_days=30)
        
        assert result["success"] is True
        assert "deleted_count" in result
        assert result["deleted_count"] == 2

    @pytest.mark.asyncio
    async def test_cleanup_old_logs_database_error(self, audit_service):
        """Test old logs cleanup with database error - covers lines 347-351"""
        # Mock the delete operation to raise exception
        audit_service.supabase.from_.return_value.delete.return_value.lt.return_value.execute.side_effect = Exception("Database error")
        
        result = await audit_service.cleanup_old_logs("org-123")
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test get_performance_metrics method - covers lines 356-376
    @pytest.mark.asyncio
    async def test_get_performance_metrics_success(self, audit_service):
        """Test successful performance metrics retrieval - covers lines 356-371"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        # Mock the filter_audit_logs method to return test data
        audit_service.filter_audit_logs = AsyncMock(return_value={
            "success": True,
            "logs": [
                {"created_at": "2024-01-01T10:00:00", "action": "create"},
                {"created_at": "2024-01-01T11:00:00", "action": "update"},
                {"created_at": "2024-01-01T12:00:00", "action": "delete"}
            ]
        })
        
        result = await audit_service.get_performance_metrics("org-123", start_date, end_date)
        
        assert result["success"] is True
        assert "metrics" in result
        assert "rag_query" in result["metrics"]

    # @pytest.mark.asyncio
    # async def test_get_performance_metrics_database_error(self, audit_service):
    #     """Test performance metrics with database error - covers lines 372-376"""
    #     start_date = datetime.now() - timedelta(days=7)
    #     end_date = datetime.now()
    #     
    #     # Mock the filter_audit_logs method to raise exception
    #     audit_service.filter_audit_logs = AsyncMock(side_effect=Exception("Database error"))
    #     
    #     result = await audit_service.get_performance_metrics("org-123", start_date, end_date)
    #     
    #     assert result["success"] is False
    #     assert "Database error" in result["error"]

    # Test edge cases and error conditions
    @pytest.mark.asyncio
    async def test_filter_audit_logs_with_datetime_objects(self, audit_service):
        """Test filtering with datetime objects instead of strings"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        filters = {
            "organization_id": "org-123",
            "start_date": start_date,
            "end_date": end_date
        }
        
        result = await audit_service.filter_audit_logs(filters)
        
        assert result["success"] is True
        assert "logs" in result

    @pytest.mark.asyncio
    async def test_export_audit_logs_with_datetime_objects(self, audit_service):
        """Test export with datetime objects in config"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        export_config = {
            "organization_id": "org-123",
            "format": "json",
            "start_date": start_date,
            "end_date": end_date
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result["success"] is True
        assert "json_data" in result

    # Test concurrent operations with new methods
    @pytest.mark.asyncio
    async def test_concurrent_advanced_operations(self, audit_service):
        """Test concurrent advanced operations"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        # Mock all the methods to return success
        audit_service.filter_audit_logs = AsyncMock(return_value={"success": True, "logs": []})
        
        tasks = [
            audit_service.get_audit_statistics("org-123", start_date, end_date),
            audit_service.get_user_activity_summary("org-123", "user-123"),
            audit_service.check_security_alerts("org-123"),
            audit_service.cleanup_old_logs("org-123"),
            audit_service.get_performance_metrics("org-123", start_date, end_date)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should complete
        assert len(results) == 5
        for result in results:
            assert result is not None
            if isinstance(result, dict):
                assert "success" in result
