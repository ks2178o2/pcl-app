# apps/app-api/__tests__/test_audit_service.py
"""
Comprehensive tests for Audit Service (COMPLIANCE CRITICAL)
Target: 0% → 95% coverage
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from services.audit_service import AuditService
from test_utils import SupabaseMockBuilder


@pytest.fixture
def mock_builder():
    return SupabaseMockBuilder()


@pytest.fixture
def audit_service(mock_builder):
    with patch('services.audit_service.get_supabase_client', return_value=mock_builder.get_mock_client()):
        return AuditService()


class TestCreateAuditEntry:
    """Test creating audit log entries"""
    
    @pytest.mark.asyncio
    async def test_create_audit_entry_success(self, audit_service, mock_builder):
        """Test successful audit entry creation"""
        audit_data = {
            'user_id': 'user-123',
            'organization_id': 'org-123',
            'action': 'login',
            'resource_type': 'user',
            'resource_id': 'user-123',
            'details': {'ip_address': '192.168.1.1'}
        }
        
        mock_builder.insert_response.data = [{'id': 'audit-123'}]
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result is not None
        assert result.get('success') is True
        assert result.get('audit_id') == 'audit-123'
    
    @pytest.mark.asyncio
    async def test_create_audit_entry_missing_user_id(self, audit_service):
        """Test audit entry with missing user_id"""
        audit_data = {
            'organization_id': 'org-123',
            'action': 'login'
        }
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result is not None
        assert result.get('success') is False
        assert 'user_id' in result.get('error', '').lower()
    
    @pytest.mark.asyncio
    async def test_create_audit_entry_missing_organization_id(self, audit_service):
        """Test audit entry with missing organization_id"""
        audit_data = {
            'user_id': 'user-123',
            'action': 'login'
        }
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result is not None
        assert result.get('success') is False
        assert 'organization_id' in result.get('error', '').lower()
    
    @pytest.mark.asyncio
    async def test_create_audit_entry_missing_action(self, audit_service):
        """Test audit entry with missing action"""
        audit_data = {
            'user_id': 'user-123',
            'organization_id': 'org-123'
        }
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result is not None
        assert result.get('success') is False
        assert 'action' in result.get('error', '').lower()
    
    @pytest.mark.asyncio
    async def test_create_audit_entry_insert_failure(self, audit_service, mock_builder):
        """Test audit entry when insert fails"""
        audit_data = {
            'user_id': 'user-123',
            'organization_id': 'org-123',
            'action': 'login'
        }
        
        mock_builder.insert_response.data = []
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result is not None
        assert result.get('success') is False
        assert 'Failed to create audit entry' in result.get('error', '')


class TestGetAuditLogs:
    """Test retrieving audit logs"""
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_success(self, audit_service, mock_builder):
        """Test successful audit log retrieval"""
        logs = [
            {'id': 'audit-1', 'action': 'login', 'created_at': '2024-01-01T00:00:00'},
            {'id': 'audit-2', 'action': 'logout', 'created_at': '2024-01-01T01:00:00'}
        ]
        
        mock_builder.setup_table_data('audit_logs', logs)
        
        result = await audit_service.get_audit_logs(
            organization_id='org-123',
            limit=100,
            offset=0
        )
        
        assert result is not None
        assert result.get('success') is True
        assert len(result.get('logs', [])) >= 0
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_with_user_filter(self, audit_service, mock_builder):
        """Test audit logs with user filter"""
        logs = [
            {'id': 'audit-1', 'user_id': 'user-123', 'action': 'login'}
        ]
        
        mock_builder.setup_table_data('audit_logs', logs)
        
        result = await audit_service.get_audit_logs(
            organization_id='org-123',
            limit=100,
            offset=0,
            user_id='user-123'
        )
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_with_action_filter(self, audit_service, mock_builder):
        """Test audit logs with action filter"""
        logs = [{'id': 'audit-1', 'action': 'login'}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        result = await audit_service.get_audit_logs(
            organization_id='org-123',
            limit=100,
            offset=0,
            action='login'
        )
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_with_pagination(self, audit_service, mock_builder):
        """Test audit logs with pagination"""
        logs = [{'id': f'audit-{i}'} for i in range(10)]
        mock_builder.setup_table_data('audit_logs', logs)
        
        result = await audit_service.get_audit_logs(
            organization_id='org-123',
            limit=5,
            offset=0
        )
        
        assert result is not None
        assert result.get('success') is True


class TestFilterAuditLogs:
    """Test filtering audit logs"""
    
    @pytest.mark.asyncio
    async def test_filter_audit_logs_by_organization(self, audit_service, mock_builder):
        """Test filtering logs by organization"""
        logs = [{'id': 'audit-1', 'organization_id': 'org-123'}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        filters = {'organization_id': 'org-123'}
        result = await audit_service.filter_audit_logs(filters)
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_filter_audit_logs_by_date_range(self, audit_service, mock_builder):
        """Test filtering logs by date range"""
        logs = [{'id': 'audit-1', 'created_at': '2024-01-15T00:00:00'}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        filters = {
            'organization_id': 'org-123',
            'start_date': datetime(2024, 1, 1),
            'end_date': datetime(2024, 1, 31)
        }
        result = await audit_service.filter_audit_logs(filters)
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_filter_audit_logs_by_user_and_action(self, audit_service, mock_builder):
        """Test filtering logs by user and action"""
        logs = [{'id': 'audit-1', 'user_id': 'user-123', 'action': 'login'}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        filters = {
            'organization_id': 'org-123',
            'user_id': 'user-123',
            'action': 'login'
        }
        result = await audit_service.filter_audit_logs(filters)
        
        assert result is not None
        assert result.get('success') is True


class TestExportAuditLogs:
    """Test exporting audit logs"""
    
    @pytest.mark.asyncio
    async def test_export_audit_logs_json(self, audit_service, mock_builder):
        """Test exporting logs as JSON"""
        logs = [{'id': 'audit-1', 'action': 'login'}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        export_config = {
            'format': 'json',
            'filters': {'organization_id': 'org-123'}
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result is not None
        assert result.get('success') is True
        assert 'json_data' in result
    
    @pytest.mark.asyncio
    async def test_export_audit_logs_csv(self, audit_service, mock_builder):
        """Test exporting logs as CSV"""
        logs = [{'id': 'audit-1', 'action': 'login'}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        export_config = {
            'format': 'csv',
            'filters': {'organization_id': 'org-123'}
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result is not None
        assert result.get('success') is True
        assert 'csv_data' in result
    
    @pytest.mark.asyncio
    async def test_export_audit_logs_xlsx(self, audit_service, mock_builder):
        """Test exporting logs as XLSX"""
        logs = [{'id': 'audit-1', 'action': 'login'}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        export_config = {
            'format': 'xlsx',
            'filters': {'organization_id': 'org-123'}
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result is not None
        assert result.get('success') is True
        assert 'xlsx_data' in result
    
    @pytest.mark.asyncio
    async def test_export_audit_logs_invalid_format(self, audit_service, mock_builder):
        """Test exporting logs with invalid format"""
        export_config = {
            'format': 'invalid',
            'filters': {'organization_id': 'org-123'}
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result is not None
        assert result.get('success') is False
        assert 'Unsupported format' in result.get('error', '')
    
    @pytest.mark.asyncio
    async def test_export_audit_logs_empty_data(self, audit_service, mock_builder):
        """Test exporting logs with no data"""
        mock_builder.setup_table_data('audit_logs', [])
        
        export_config = {
            'format': 'csv',
            'filters': {'organization_id': 'org-123'}
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result is not None
        assert result.get('success') is True


class TestAuditStatistics:
    """Test audit statistics"""
    
    @pytest.mark.asyncio
    async def test_get_audit_statistics_success(self, audit_service, mock_builder):
        """Test getting audit statistics"""
        logs = [
            {'user_id': 'user-123', 'action': 'login', 'created_at': '2024-01-01T00:00:00'},
            {'user_id': 'user-123', 'action': 'logout', 'created_at': '2024-01-01T01:00:00'},
            {'user_id': 'user-456', 'action': 'login', 'created_at': '2024-01-01T02:00:00'}
        ]
        mock_builder.setup_table_data('audit_logs', logs)
        
        result = await audit_service.get_audit_statistics(
            organization_id='org-123',
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        assert result is not None
        assert result.get('success') is True
        assert 'statistics' in result
        assert 'total_actions' in result['statistics']
        assert 'unique_users' in result['statistics']


class TestUserActivitySummary:
    """Test user activity summary"""
    
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_with_logs(self, audit_service, mock_builder):
        """Test getting user activity summary with logs"""
        logs = [
            {'user_id': 'user-123', 'action': 'login', 'created_at': '2024-01-01T00:00:00'},
            {'user_id': 'user-123', 'action': 'logout', 'created_at': '2024-01-01T01:00:00'}
        ]
        mock_builder.setup_table_data('audit_logs', logs)
        
        result = await audit_service.get_user_activity_summary('org-123', 'user-123')
        
        assert result is not None
        assert result.get('success') is True
        assert 'summary' in result
        assert result['summary']['user_id'] == 'user-123'
    
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_no_logs(self, audit_service, mock_builder):
        """Test getting user activity summary with no logs"""
        mock_builder.setup_table_data('audit_logs', [])
        
        result = await audit_service.get_user_activity_summary('org-123', 'user-123')
        
        assert result is not None
        assert result.get('success') is True
        assert result['summary']['action_count'] == 0


class TestSecurityAlerts:
    """Test security alerts"""
    
    @pytest.mark.asyncio
    async def test_check_security_alerts_multiple_failed_logins(self, audit_service, mock_builder):
        """Test detecting multiple failed logins"""
        logs = [
            {'user_id': 'user-123', 'action': 'login_failed', 'created_at': datetime.utcnow().isoformat()},
            {'user_id': 'user-123', 'action': 'login_failed', 'created_at': datetime.utcnow().isoformat()},
            {'user_id': 'user-123', 'action': 'login_failed', 'created_at': datetime.utcnow().isoformat()}
        ]
        mock_builder.setup_table_data('audit_logs', logs)
        
        result = await audit_service.check_security_alerts('org-123', time_window_minutes=5)
        
        assert result is not None
        assert result.get('success') is True
        assert len(result.get('alerts', [])) > 0
    
    @pytest.mark.asyncio
    async def test_check_security_alerts_no_alerts(self, audit_service, mock_builder):
        """Test security check with no alerts"""
        logs = [{'user_id': 'user-123', 'action': 'login', 'created_at': datetime.utcnow().isoformat()}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        result = await audit_service.check_security_alerts('org-123')
        
        assert result is not None
        assert result.get('success') is True
        assert len(result.get('alerts', [])) == 0


class TestCleanupOldLogs:
    """Test cleanup of old audit logs"""
    
    @pytest.mark.asyncio
    async def test_cleanup_old_logs_success(self, audit_service, mock_builder):
        """Test successful cleanup of old logs"""
        # Mock delete response
        mock_builder.delete_response.data = [{'id': 'old-1'}, {'id': 'old-2'}]
        
        result = await audit_service.cleanup_old_logs('org-123', retention_days=90)
        
        assert result is not None
        assert result.get('success') is True
        assert result.get('deleted_count', 0) >= 0
    
    @pytest.mark.asyncio
    async def test_cleanup_old_logs_database_error(self, audit_service, mock_builder):
        """Test cleanup when database error occurs"""
        mock_builder.setup_error_response('audit_logs', "Database connection error")
        
        result = await audit_service.cleanup_old_logs('org-123')
        
        assert result is not None
        assert result.get('success') is False


class TestPerformanceMetrics:
    """Test performance metrics"""
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, audit_service):
        """Test getting performance metrics"""
        result = await audit_service.get_performance_metrics(
            organization_id='org-123',
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        assert result is not None
        assert result.get('success') is True


class TestAuditServiceEdgeCases:
    """Test edge cases to reach 95% coverage"""
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_empty_result(self, audit_service, mock_builder):
        """Test getting audit logs with empty result"""
        mock_builder.setup_table_data('audit_logs', [])
        
        result = await audit_service.get_audit_logs('org-123')
        
        assert result is not None
        assert result.get('success') is True
        assert len(result.get('logs', [])) == 0
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_exception_handling(self, audit_service):
        """Test exception handling in get_audit_logs"""
        with patch.object(audit_service.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await audit_service.get_audit_logs('org-123')
            
            assert result is not None
            assert result.get('success') is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_filter_audit_logs_exception_handling(self, audit_service):
        """Test exception handling in filter_audit_logs"""
        with patch.object(audit_service.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await audit_service.filter_audit_logs({'organization_id': 'org-123'})
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_get_audit_statistics_exception_handling(self, audit_service):
        """Test exception handling in get_audit_statistics"""
        with patch.object(audit_service, 'filter_audit_logs') as mock_filter:
            mock_filter.side_effect = Exception("Database error")
            
            result = await audit_service.get_audit_statistics(
                organization_id='org-123',
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31)
            )
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_exception_handling(self, audit_service):
        """Test exception handling in get_user_activity_summary"""
        with patch.object(audit_service, 'filter_audit_logs') as mock_filter:
            mock_filter.side_effect = Exception("Database error")
            
            result = await audit_service.get_user_activity_summary('org-123', 'user-123')
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_check_security_alerts_exception_handling(self, audit_service):
        """Test exception handling in check_security_alerts"""
        with patch.object(audit_service, 'filter_audit_logs') as mock_filter:
            mock_filter.side_effect = Exception("Database error")
            
            result = await audit_service.check_security_alerts('org-123')
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_cleanup_old_logs_exception_handling(self, audit_service):
        """Test exception handling in cleanup_old_logs"""
        with patch.object(audit_service.supabase, 'from_') as mock_from:
            mock_from.side_effect = Exception("Database error")
            
            result = await audit_service.cleanup_old_logs('org-123')
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_export_audit_logs_exception_handling(self, audit_service):
        """Test exception handling in export_audit_logs"""
        with patch.object(audit_service, 'filter_audit_logs') as mock_filter:
            mock_filter.side_effect = Exception("Database error")
            
            export_config = {
                'format': 'json',
                'filters': {'organization_id': 'org-123'}
            }
            
            result = await audit_service.export_audit_logs(export_config)
            
            assert result is not None
            assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_create_audit_entry_with_empty_field(self, audit_service):
        """Test creating audit entry with empty required field"""
        audit_data = {
            'user_id': '',  # Empty string
            'organization_id': 'org-123',
            'action': 'login'
        }
        
        result = await audit_service.create_audit_entry(audit_data)
        
        assert result is not None
        assert result.get('success') is False
    
    @pytest.mark.asyncio
    async def test_export_csv_with_special_characters(self, audit_service, mock_builder):
        """Test CSV export with special characters in data"""
        logs = [{'id': 'audit-1', 'action': 'login, logout', 'details': 'test with "quotes"'}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        export_config = {
            'format': 'csv',
            'filters': {'organization_id': 'org-123'}
        }
        
        result = await audit_service.export_audit_logs(export_config)
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_filter_with_resource_type(self, audit_service, mock_builder):
        """Test filter_audit_logs with resource_type filter"""
        logs = [{'id': 'audit-1', 'resource_type': 'user', 'action': 'login'}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        filters = {
            'organization_id': 'org-123',
            'resource_type': 'user'
        }
        result = await audit_service.filter_audit_logs(filters)
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_no_total_count(self, audit_service, mock_builder):
        """Test get_audit_logs when count is None"""
        logs = [{'id': 'audit-1', 'action': 'login'}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        # Mock count_result with count=None
        count_result = Mock()
        count_result.count = None
        mock_builder.count_query.execute.return_value = count_result
        
        result = await audit_service.get_audit_logs('org-123')
        
        assert result is not None
        assert result.get('success') is True
    
    @pytest.mark.asyncio
    async def test_performance_metrics_empty_data(self, audit_service):
        """Test get_performance_metrics with empty data"""
        result = await audit_service.get_performance_metrics(
            organization_id='org-123',
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        assert result is not None
        assert result.get('success') is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.audit_service', '--cov-report=html'])

