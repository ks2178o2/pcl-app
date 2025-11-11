import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Add the parent directory to the path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.audit_service import AuditService

class TestAuditServiceFinalCoverage:
    """Additional tests to reach 95%+ coverage for AuditService"""
    
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
        
        # Chain the mocks
        mock_client.insert.return_value = mock_insert
        mock_insert.execute.return_value = Mock(data=[{"id": "audit-123"}])
        
        mock_client.select.return_value = mock_select
        mock_select.from_.return_value = mock_select
        mock_select.eq.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.range.return_value = mock_select
        mock_select.execute.return_value = Mock(data=[
            {
                "id": "audit-123",
                "user_id": "user-123",
                "action": "test_action",
                "created_at": "2024-01-01T10:00:00Z",
                "organization_id": "org-123"
            }
        ])
        
        mock_client.from_.return_value = mock_select
        
        return mock_client
    
    @pytest.fixture
    def audit_service(self, mock_supabase_client):
        """Create AuditService instance with mocked dependencies"""
        with patch('services.audit_service.get_supabase_client', return_value=mock_supabase_client):
            return AuditService()
    
    @pytest.mark.asyncio
    async def test_export_audit_logs_xlsx_format(self, audit_service, mock_supabase_client):
        """Test export audit logs in XLSX format (line 165)"""
        # Mock the filter_audit_logs method to return success
        audit_service.filter_audit_logs = AsyncMock(return_value={
            "success": True,
            "logs": [{"id": "audit-123", "action": "test"}]
        })
        
        export_config = {
            "format": "xlsx",
            "filters": {
                "user_id": "user-123",
                "organization_id": "org-123"
            }
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result["success"] is True
        assert "xlsx_data" in result
        assert result["xlsx_data"] == b"fake_excel_data"
    
    @pytest.mark.asyncio
    async def test_export_audit_logs_exception_handling(self, audit_service, mock_supabase_client):
        """Test export audit logs exception handling (lines 176-178)"""
        # Mock filter_audit_logs to raise an exception
        audit_service.filter_audit_logs = AsyncMock(side_effect=Exception("Database error"))
        
        export_config = {
            "format": "json",
            "filters": {
                "user_id": "user-123",
                "organization_id": "org-123"
            }
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result["success"] is False
        assert "error" in result
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_filter_failure(self, audit_service, mock_supabase_client):
        """Test get user activity summary when filter fails (line 236)"""
        # Mock filter_audit_logs to return failure
        audit_service.filter_audit_logs = AsyncMock(return_value={
            "success": False,
            "error": "Filter failed"
        })
        
        result = await audit_service.get_user_activity_summary(
            user_id="user-123",
            organization_id="org-123"
        )
        
        assert result["success"] is False
        assert result["error"] == "Filter failed"
    
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_empty_created_at(self, audit_service, mock_supabase_client):
        """Test get user activity summary with empty created_at (line 262->256)"""
        # Mock filter_audit_logs to return logs with empty created_at
        audit_service.filter_audit_logs = AsyncMock(return_value={
            "success": True,
            "logs": [
                {
                    "id": "audit-123",
                    "action": "test_action",
                    "created_at": "",  # Empty created_at
                    "user_id": "user-123"
                }
            ]
        })
        
        result = await audit_service.get_user_activity_summary(
            user_id="user-123",
            organization_id="org-123"
        )
        
        assert result["success"] is True
        assert result["summary"]["action_count"] == 1
        assert result["summary"]["active_days"] == 0  # Should be 0 due to empty created_at
    
    @pytest.mark.asyncio
    async def test_check_security_alerts_filter_failure(self, audit_service, mock_supabase_client):
        """Test check security alerts when filter fails (line 303)"""
        # Mock filter_audit_logs to return failure
        audit_service.filter_audit_logs = AsyncMock(return_value={
            "success": False,
            "error": "Filter failed"
        })
        
        result = await audit_service.check_security_alerts(
            organization_id="org-123",
            time_window_minutes=1440  # 24 hours
        )
        
        assert result["success"] is False
        assert result["error"] == "Filter failed"
    
    @pytest.mark.asyncio
    async def test_check_security_alerts_multiple_failed_logins(self, audit_service, mock_supabase_client):
        """Test check security alerts for multiple failed logins (line 313)"""
        # Mock filter_audit_logs to return multiple failed login attempts
        audit_service.filter_audit_logs = AsyncMock(return_value={
            "success": True,
            "logs": [
                {"id": "audit-1", "action": "login_failed", "user_id": "user-123"},
                {"id": "audit-2", "action": "login_failed", "user_id": "user-123"},
                {"id": "audit-3", "action": "login_failed", "user_id": "user-123"},
                {"id": "audit-4", "action": "login_failed", "user_id": "user-123"},
            ]
        })
        
        result = await audit_service.check_security_alerts(
            organization_id="org-123",
            time_window_minutes=1440  # 24 hours
        )
        
        assert result["success"] is True
        assert len(result["alerts"]) == 1
        assert result["alerts"][0]["alert_type"] == "multiple_failed_logins"
        assert result["alerts"][0]["count"] == 4
    
    # Note: get_performance_metrics doesn't actually call external services or use datetime.utcnow()
    # so we can't easily trigger the exception handling path. The method just returns mock data.
    # This test is skipped as the exception handling lines (374-376) are not reachable in current implementation.
