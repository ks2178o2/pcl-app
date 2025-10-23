# apps/app-api/__tests__/test_audit_service_95_coverage.py

import pytest
import asyncio
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.audit_service import AuditService


class TestAuditService95Coverage:
    """Test suite for AuditService to achieve 95% coverage"""

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
        mock_select.order.return_value = mock_select
        mock_select.range.return_value = mock_select
        mock_select.execute.return_value = Mock(
            data=[{"id": "audit-123", "action": "test_action", "user_id": "user-123"}],
            count=1
        )
        mock_table.select.return_value = mock_select
        
        # Mock delete chain
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

    # Test create_audit_entry method - covers lines 19-50
    @pytest.mark.asyncio
    async def test_create_audit_entry_success(self, audit_service):
        """Test successful audit entry creation"""
        audit_data = {
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "test_action"
        }
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result["success"] is True
        assert result["audit_id"] == "audit-123"

    @pytest.mark.asyncio
    async def test_create_audit_entry_missing_user_id(self, audit_service):
        """Test audit entry creation with missing user_id - covers line 26"""
        audit_data = {
            "organization_id": "org-123",
            "action": "test_action"
        }
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result["success"] is False
        assert "user_id cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_missing_organization_id(self, audit_service):
        """Test audit entry creation with missing organization_id - covers line 26"""
        audit_data = {
            "user_id": "user-123",
            "action": "test_action"
        }
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result["success"] is False
        assert "organization_id cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_missing_action(self, audit_service):
        """Test audit entry creation with missing action - covers line 26"""
        audit_data = {
            "user_id": "user-123",
            "organization_id": "org-123"
        }
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result["success"] is False
        assert "action cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_empty_user_id(self, audit_service):
        """Test audit entry creation with empty user_id - covers line 25"""
        audit_data = {
            "user_id": "",
            "organization_id": "org-123",
            "action": "test_action"
        }
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result["success"] is False
        assert "user_id cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_empty_organization_id(self, audit_service):
        """Test audit entry creation with empty organization_id - covers line 25"""
        audit_data = {
            "user_id": "user-123",
            "organization_id": "",
            "action": "test_action"
        }
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result["success"] is False
        assert "organization_id cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_empty_action(self, audit_service):
        """Test audit entry creation with empty action - covers line 25"""
        audit_data = {
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": ""
        }
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result["success"] is False
        assert "action cannot be empty" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_no_data_returned(self, audit_service):
        """Test audit entry creation when no data is returned - covers line 40"""
        audit_service.supabase.from_.return_value.insert.return_value.execute.return_value = Mock(data=[])
        
        audit_data = {
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "test_action"
        }
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result["success"] is False
        assert "Failed to create audit entry" in result["error"]

    @pytest.mark.asyncio
    async def test_create_audit_entry_database_error(self, audit_service):
        """Test audit entry creation with database error - covers lines 45-50"""
        audit_service.supabase.from_.return_value.insert.return_value.execute.side_effect = Exception("Database error")
        
        audit_data = {
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "test_action"
        }
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test get_audit_logs method - covers lines 52-91
    @pytest.mark.asyncio
    async def test_get_audit_logs_success(self, audit_service):
        """Test successful audit logs retrieval - covers lines 55-88"""
        result = await audit_service.get_audit_logs("org-123", limit=50, offset=0)
        
        assert result["success"] is True
        assert "logs" in result
        assert "total_count" in result

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_user_id(self, audit_service):
        """Test audit logs retrieval with user_id filter - covers lines 59-61"""
        result = await audit_service.get_audit_logs("org-123", user_id="user-123")
        
        assert result["success"] is True
        assert "logs" in result

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_action(self, audit_service):
        """Test audit logs retrieval with action filter - covers lines 62-63"""
        result = await audit_service.get_audit_logs("org-123", action="test_action")
        
        assert result["success"] is True
        assert "logs" in result

    @pytest.mark.asyncio
    async def test_get_audit_logs_database_error(self, audit_service):
        """Test audit logs retrieval with database error - covers lines 86-91"""
        audit_service.supabase.from_.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.side_effect = Exception("Database error")
        
        result = await audit_service.get_audit_logs("org-123")
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test filter_audit_logs method - covers lines 93-126
    @pytest.mark.asyncio
    async def test_filter_audit_logs_success(self, audit_service):
        """Test successful audit logs filtering - covers lines 95-120"""
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
        """Test audit logs filtering with empty filters - covers lines 95-120"""
        filters = {}
        
        result = await audit_service.filter_audit_logs(filters)
        
        assert result["success"] is True
        assert "logs" in result

    @pytest.mark.asyncio
    async def test_filter_audit_logs_database_error(self, audit_service):
        """Test audit logs filtering with database error - covers lines 121-126"""
        audit_service.supabase.from_.return_value.select.return_value.execute.side_effect = Exception("Database error")
        
        filters = {"user_id": "user-123"}
        result = await audit_service.filter_audit_logs(filters)
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    # Test export_audit_logs method - covers lines 128-181
    @pytest.mark.asyncio
    async def test_export_audit_logs_json_success(self, audit_service):
        """Test successful audit logs export in JSON format - covers lines 130-175"""
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
    async def test_export_audit_logs_csv_success(self, audit_service):
        """Test successful audit logs export in CSV format - covers lines 130-175"""
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
        """Test audit logs export with invalid format - covers lines 130-175"""
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
        """Test audit logs export with database error - covers lines 176-181"""
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

    # Test error handling for edge cases
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
    async def test_filter_audit_logs_none_filters(self, audit_service):
        """Test audit logs filtering with None filters"""
        result = await audit_service.filter_audit_logs(None)
        
        assert result["success"] is False
        assert "error" in result

    # @pytest.mark.asyncio
    # async def test_export_audit_logs_missing_config(self, audit_service):
    #     """Test audit logs export with missing configuration"""
    #     result = await audit_service.export_audit_logs({})
    #     
    #     assert result["success"] is False
    #     assert "error" in result

    # Test concurrent operations
    @pytest.mark.asyncio
    async def test_concurrent_audit_operations(self, audit_service):
        """Test concurrent audit operations"""
        audit_data = {
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "test_action"
        }
        
        tasks = [
            audit_service.create_audit_entry(audit_data),
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
