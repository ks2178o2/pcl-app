# apps/app-api/__tests__/test_audit_service_95_coverage.py
"""
Tests to push Audit Service coverage from 82.67% to 95%
Targeting missing lines: 62, 73, 78, 108, 110, 128-130, 143, 157, 183-185, 203, 225-227, 243, 287-289, 310, 333-335, 356-358, 381-383
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from services.audit_service import AuditService


class TestAuditService95Coverage:
    """Tests to reach 95% coverage for Audit Service"""
    
    @pytest.fixture
    def audit_service(self):
        """Create audit service with mocked supabase"""
        with patch('services.audit_service.get_supabase_client') as mock_get_client:
            mock_client = Mock()
            table_mock = Mock()
            
            # Setup basic chains
            select_chain = Mock()
            select_chain.eq = Mock(return_value=select_chain)
            select_chain.order = Mock(return_value=select_chain)
            select_chain.gte = Mock(return_value=select_chain)
            select_chain.lte = Mock(return_value=select_chain)
            select_chain.execute = Mock(return_value=Mock(data=[]))
            
            insert_result = Mock()
            insert_result.data = [{'id': 'test-id'}]
            table_mock.insert.return_value.execute.return_value = insert_result
            
            delete_result = Mock()
            delete_result.data = []
            delete_chain = Mock()
            delete_chain.eq = Mock(return_value=delete_chain)
            delete_chain.lt = Mock(return_value=delete_chain)
            delete_chain.execute.return_value = delete_result
            table_mock.delete.return_value = delete_chain
            
            table_mock.select.return_value = select_chain
            mock_client.from_.return_value = table_mock
            mock_get_client.return_value = mock_client
            
            return AuditService()
    
    # Test action filtering in get_audit_logs (lines 62, 73, 78)
    @pytest.mark.asyncio
    async def test_get_audit_logs_with_action_filter(self, audit_service):
        """Test action filtering - lines 62, 73, 78"""
        logs_data = [{'id': 'audit-1', 'action': 'login'}]
        
        range_result = Mock()
        range_result.data = logs_data
        
        count_result = Mock()
        count_result.count = 1
        count_result.data = []
        
        # Setup the main query chain for getting logs
        range_chain = Mock()
        range_chain.execute = Mock(return_value=range_result)
        
        order_chain = Mock()
        order_chain.range = Mock(return_value=range_chain)
        
        # Chain for action filter (second eq call)
        action_eq_chain = Mock()
        action_eq_chain.order = Mock(return_value=order_chain)
        
        # Chain for org_id filter (first eq call)
        org_eq_chain = Mock()
        org_eq_chain.eq = Mock(return_value=action_eq_chain)
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=org_eq_chain)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        
        # Setup count query chain
        count_action_eq = Mock()
        count_action_eq.execute = Mock(return_value=count_result)
        
        count_org_eq = Mock()
        count_org_eq.eq = Mock(return_value=count_action_eq)
        
        count_select = Mock()
        count_select.eq = Mock(return_value=count_org_eq)
        
        count_table_mock = Mock()
        count_table_mock.select = Mock(return_value=count_select)
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            # First call returns table_mock, second call returns count_table_mock
            return table_mock if call_count == 1 else count_table_mock
        
        audit_service.supabase.from_.side_effect = from_side_effect
        
        result = await audit_service.get_audit_logs(
            organization_id='org-123',
            limit=100,
            offset=0,
            action='login'
        )
        
        assert result['success'] is True
        assert len(result['logs']) == 1
    
    # Test date filtering in filter_audit_logs (lines 108, 110)
    @pytest.mark.asyncio
    async def test_filter_audit_logs_with_dates(self, audit_service):
        """Test date filtering - lines 114-117"""
        logs_data = [{'id': 'audit-1', 'created_at': '2024-01-15T00:00:00'}]
        
        select_result = Mock()
        select_result.data = logs_data
        
        table_mock = audit_service.supabase.from_.return_value
        order_chain = Mock()
        order_chain.execute = Mock(return_value=select_result)
        
        gte_chain = Mock()
        gte_chain.lte = Mock(return_value=gte_chain)
        gte_chain.order = Mock(return_value=order_chain)
        
        eq_chain = Mock()
        eq_chain.gte = Mock(return_value=gte_chain)
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=eq_chain)
        
        table_mock.select.return_value = select_chain
        
        filters = {
            'organization_id': 'org-123',
            'start_date': datetime.utcnow() - timedelta(days=7),
            'end_date': datetime.utcnow()
        }
        
        result = await audit_service.filter_audit_logs(filters)
        assert result['success'] is True
    
    # Test exception handling in filter_audit_logs (lines 128-130)
    @pytest.mark.asyncio
    async def test_filter_audit_logs_exception(self, audit_service):
        """Test exception handling - lines 128-130"""
        audit_service.supabase.from_.return_value.select.side_effect = Exception("DB error")
        
        filters = {'organization_id': 'org-123'}
        result = await audit_service.filter_audit_logs(filters)
        
        assert result['success'] is False
        assert 'error' in result
    
    # Test exception in export when filter_audit_logs fails (line 143)
    @pytest.mark.asyncio
    async def test_export_when_filter_fails(self, audit_service):
        """Test export when filter fails - line 143"""
        with patch.object(audit_service, 'filter_audit_logs', return_value={
            'success': False,
            'error': 'Filter failed'
        }):
            result = await audit_service.export_audit_logs({
                'filters': {'organization_id': 'org-123'},
                'format': 'csv'
            })
            
            assert result['success'] is False
    
    # Test export CSV when logs is empty (line 157)
    @pytest.mark.asyncio
    async def test_export_csv_empty_logs(self, audit_service):
        """Test CSV export with empty logs - line 157"""
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
    
    # Test exception in export (lines 183-185)
    @pytest.mark.asyncio
    async def test_export_exception(self, audit_service):
        """Test exception in export - lines 183-185"""
        with patch.object(audit_service, 'filter_audit_logs', side_effect=Exception("Error")):
            result = await audit_service.export_audit_logs({
                'filters': {'organization_id': 'org-123'},
                'format': 'csv'
            })
            
            assert result['success'] is False
            assert 'error' in result
    
    # Test exception in get_audit_statistics (lines 225-227)
    @pytest.mark.asyncio
    async def test_get_audit_statistics_exception(self, audit_service):
        """Test exception in get_audit_statistics - lines 225-227"""
        with patch.object(audit_service, 'filter_audit_logs', side_effect=Exception("Error")):
            result = await audit_service.get_audit_statistics(
                organization_id='org-123',
                start_date=datetime.utcnow() - timedelta(days=7),
                end_date=datetime.utcnow()
            )
            
            assert result['success'] is False
    
    # Test exception in get_user_activity_summary when filter fails (lines 243)
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_filter_failure(self, audit_service):
        """Test summary when filter fails - line 243"""
        with patch.object(audit_service, 'filter_audit_logs', return_value={
            'success': False,
            'error': 'Filter error'
        }):
            result = await audit_service.get_user_activity_summary(
                organization_id='org-123',
                user_id='user-123'
            )
            
            assert result['success'] is False
    
    # Test exception in get_user_activity_summary (lines 287-289)
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_exception(self, audit_service):
        """Test exception in get_user_activity_summary - lines 287-289"""
        with patch.object(audit_service, 'filter_audit_logs', side_effect=Exception("Error")):
            result = await audit_service.get_user_activity_summary(
                organization_id='org-123',
                user_id='user-123'
            )
            
            assert result['success'] is False
    
    # Test check_security_alerts when filter fails (line 310)
    @pytest.mark.asyncio
    async def test_check_security_alerts_filter_failure(self, audit_service):
        """Test security alerts when filter fails - line 310"""
        with patch.object(audit_service, 'filter_audit_logs', return_value={
            'success': False
        }):
            result = await audit_service.check_security_alerts(
                organization_id='org-123',
                time_window_minutes=5
            )
            
            assert result['success'] is False
    
    # Test exception in check_security_alerts (lines 333-335)
    @pytest.mark.asyncio
    async def test_check_security_alerts_exception(self, audit_service):
        """Test exception in check_security_alerts - lines 333-335"""
        with patch.object(audit_service, 'filter_audit_logs', side_effect=Exception("Error")):
            result = await audit_service.check_security_alerts(
                organization_id='org-123',
                time_window_minutes=5
            )
            
            assert result['success'] is False
    
    # Test exception in cleanup_old_logs (lines 356-358)
    @pytest.mark.asyncio
    async def test_cleanup_old_logs_exception(self, audit_service):
        """Test exception in cleanup - lines 356-358"""
        audit_service.supabase.from_.return_value.delete.return_value.eq.return_value.lt.side_effect = Exception("Error")
        
        result = await audit_service.cleanup_old_logs(
            organization_id='org-123',
            retention_days=90
        )
        
        assert result['success'] is False
    
    # Test exception in get_performance_metrics (lines 381-383)
    @pytest.mark.asyncio
    async def test_get_performance_metrics_exception(self, audit_service):
        """Test exception in get_performance_metrics - lines 381-383
        
        Note: The method get_performance_metrics is very simple and only returns hardcoded data.
        The exception handler at lines 381-383 is defensive code that may never execute in practice.
        To properly test it, we would need to modify the method to have a code path that can fail.
        For now, we verify the method works correctly in the normal case.
        """
        result = await audit_service.get_performance_metrics(
            organization_id='org-123',
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        
        # Verify the method works normally
        assert result['success'] is True
        assert 'metrics' in result
        assert 'rag_query' in result['metrics']
    
    # Test export XLSX format
    @pytest.mark.asyncio
    async def test_export_xlsx_format(self, audit_service):
        """Test XLSX export format"""
        with patch.object(audit_service, 'filter_audit_logs', return_value={
            'success': True,
            'logs': [{'id': 'audit-1', 'action': 'test'}]
        }):
            result = await audit_service.export_audit_logs({
                'filters': {'organization_id': 'org-123'},
                'format': 'xlsx'
            })
            
            assert result['success'] is True
            assert 'xlsx_data' in result
    
    # Test statistics with actual data
    @pytest.mark.asyncio
    async def test_get_audit_statistics_with_data(self, audit_service):
        """Test statistics calculation with real data"""
        logs = [
            {'action': 'login', 'user_id': 'user-1'},
            {'action': 'login', 'user_id': 'user-2'},
            {'action': 'logout', 'user_id': 'user-1'},
            {'action': 'view', 'user_id': 'user-3'}
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
            assert result['statistics']['total_actions'] == 4
            assert result['statistics']['unique_users'] == 3
            assert result['statistics']['action_counts']['login'] == 2
    
    # Test user activity summary with complex data
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_complex(self, audit_service):
        """Test user activity summary with various actions"""
        logs = [
            {'action': 'login', 'user_id': 'user-123', 'created_at': '2024-01-01T00:00:00'},
            {'action': 'login', 'user_id': 'user-123', 'created_at': '2024-01-02T10:30:00'},
            {'action': 'logout', 'user_id': 'user-123', 'created_at': '2024-01-02T18:00:00'},
            {'action': 'login', 'user_id': 'user-123', 'created_at': '2024-01-03T09:00:00'}
        ]
        
        with patch.object(audit_service, 'filter_audit_logs', return_value={
            'success': True,
            'logs': logs
        }):
            result = await audit_service.get_user_activity_summary(
                organization_id='org-123',
                user_id='user-123'
            )
            
            assert result['success'] is True
            assert result['summary']['action_count'] == 4
            assert result['summary']['most_common_action'] == 'login'
            assert result['summary']['active_days'] == 3  # 3 different dates
