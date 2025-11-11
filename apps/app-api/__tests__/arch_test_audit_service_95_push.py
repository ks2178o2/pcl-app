# apps/app-api/__tests__/test_audit_service_95_push.py
"""
Push Audit Service coverage to 95%
Fix remaining mock issues and add tests for missing lines
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from services.audit_service import AuditService
from test_utils import SupabaseMockBuilder


class TestAuditService95Push:
    """Tests to push coverage to 95%"""
    
    @pytest.fixture
    def mock_builder(self):
        """Create mock builder"""
        return SupabaseMockBuilder()
    
    @pytest.fixture
    def audit_service(self, mock_builder):
        """Create audit service with mocked supabase"""
        with patch('services.audit_service.get_supabase_client', return_value=mock_builder.get_mock_client()):
            return AuditService()
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_success_fixed(self, audit_service, mock_builder):
        """Test getting audit logs - fixed mock"""
        logs = [
            {'id': 'audit-1', 'user_id': 'user-123', 'action': 'login'},
            {'id': 'audit-2', 'user_id': 'user-123', 'action': 'logout'}
        ]
        
        # Setup the table mock with proper chain
        table_mock = mock_builder.create_table_mock('audit_logs', logs)
        
        # Create proper chain for get_audit_logs
        mock_builder.setup_query_with_count('audit_logs', logs, total_count=2)
        
        result = await audit_service.get_audit_logs('org-123', limit=100, offset=0)
        
        assert result['success'] is True
        assert len(result['logs']) == 2
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_with_filters_fixed(self, audit_service, mock_builder):
        """Test get_audit_logs with user and action filters"""
        logs = [{'id': 'audit-1', 'action': 'login'}]
        mock_builder.setup_query_with_count('audit_logs', logs, total_count=1)
        
        result = await audit_service.get_audit_logs(
            organization_id='org-123',
            limit=100,
            offset=0,
            user_id='user-123',
            action='login'
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_pagination_fixed(self, audit_service, mock_builder):
        """Test pagination with has_more"""
        logs = [{'id': f'audit-{i}'} for i in range(10)]
        mock_builder.setup_query_with_count('audit_logs', logs, total_count=25)
        
        result = await audit_service.get_audit_logs('org-123', limit=10, offset=0)
        
        assert result['success'] is True
        assert result['total_count'] == 25
        assert result['has_more'] is True  # 10 < 25
    
    @pytest.mark.asyncio
    async def test_filter_audit_logs_fixed(self, audit_service, mock_builder):
        """Test filter_audit_logs with all filters"""
        logs = [{'id': 'audit-1', 'action': 'login'}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        filters = {
            'organization_id': 'org-123',
            'user_id': 'user-123',
            'action': 'login',
            'resource_type': 'context_item',
            'start_date': datetime.utcnow() - timedelta(days=1),
            'end_date': datetime.utcnow()
        }
        
        result = await audit_service.filter_audit_logs(filters)
        
        assert result['success'] is True
        assert len(result['logs']) == 1
    
    @pytest.mark.asyncio
    async def test_export_audit_logs_empty(self, audit_service):
        """Test export with empty logs - line 149"""
        with patch.object(audit_service, 'filter_audit_logs', return_value={
            'success': True,
            'logs': []
        }):
            result = await audit_service.export_audit_logs({
                'filters': {'organization_id': 'org-123'},
                'format': 'csv'
            })
            
            assert result['success'] is True
            assert result['csv_data'] == "No data found"
    
    @pytest.mark.asyncio
    async def test_filter_audit_logs_date_filters(self, audit_service, mock_builder):
        """Test filter with date range - lines 107-110"""
        logs = [{'id': 'audit-1', 'created_at': '2024-01-01T00:00:00'}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        filters = {
            'organization_id': 'org-123',
            'start_date': datetime(2024, 1, 1),
            'end_date': datetime(2024, 1, 2)
        }
        
        result = await audit_service.filter_audit_logs(filters)
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_filter_audit_logs_no_filters(self, audit_service, mock_builder):
        """Test filter with no filters"""
        logs = []
        mock_builder.setup_table_data('audit_logs', logs)
        
        result = await audit_service.filter_audit_logs({})
        
        assert result['success'] is True
        assert result['logs'] == []
    
    @pytest.mark.asyncio
    async def test_filter_audit_logs_resource_type(self, audit_service, mock_builder):
        """Test filter with resource_type - line 105"""
        logs = [{'id': 'audit-1', 'resource_type': 'context_item'}]
        mock_builder.setup_table_data('audit_logs', logs)
        
        filters = {
            'organization_id': 'org-123',
            'resource_type': 'context_item'
        }
        
        result = await audit_service.filter_audit_logs(filters)
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_get_audit_statistics_empty_logs(self, audit_service):
        """Test statistics with no logs - line 196"""
        with patch.object(audit_service, 'filter_audit_logs', return_value={
            'success': False,
            'error': 'No logs found'
        }):
            result = await audit_service.get_audit_statistics(
                organization_id='org-123',
                start_date=datetime.utcnow() - timedelta(days=7),
                end_date=datetime.utcnow()
            )
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_audit_statistics_no_unique_users(self, audit_service):
        """Test statistics with no unique users"""
        logs = [
            {'action': 'login', 'user_id': None}
        ]
        
        with patch.object(audit_service, 'filter_audit_logs', return_value={
            'success': True,
            'logs': logs
        }):
            result = await audit_service.get_audit_statistics(
                organization_id='org-123',
                start_date=datetime.utcnow() - timedelta(days=7),
                end_date=datetime.utcnow()
            )
            
            assert result['success'] is True
            # None should not be added to unique_users set
            assert result['statistics']['unique_users'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.audit_service', '--cov-report=html'])

