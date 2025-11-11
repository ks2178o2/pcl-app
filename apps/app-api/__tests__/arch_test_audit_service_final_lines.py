# apps/app-api/__tests__/test_audit_service_final_lines.py
"""
Tests for final missing lines in Audit Service
Lines: 121-123, 136, 176-178, 218-220, 236, 280-282, 303, 326-328, 349-351, 374-376
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from services.audit_service import AuditService


class TestAuditServiceFinalLines:
    """Tests for remaining coverage gaps"""
    
    @pytest.fixture
    def audit_service(self):
        """Create audit service with mocked supabase"""
        with patch('services.audit_service.get_supabase_client') as mock_get:
            mock_client = Mock()
            
            table_mock = Mock()
            insert_result = Mock()
            insert_result.data = [{'id': 'audit-123'}]
            table_mock.insert.return_value.execute.return_value = insert_result
            
            select_chain = Mock()
            select_result = Mock()
            select_result.data = []
            select_result.count = 0
            select_chain.execute.return_value = select_result
            select_chain.eq.return_value = select_chain
            select_chain.order.return_value = select_chain
            select_chain.range.return_value = select_result
            table_mock.select.return_value = select_chain
            
            table_mock.delete.return_value = table_mock
            table_mock.lt.return_value = table_mock
            
            mock_client.from_.return_value = table_mock
            mock_get.return_value = mock_client
            
            return AuditService()
    
    @pytest.mark.asyncio
    async def test_filter_audit_logs_exception(self, audit_service):
        """Test filter_audit_logs exception handling - lines 121-125"""
        # Force exception
        audit_service.supabase.from_.return_value.select.side_effect = Exception("DB error")
        
        result = await audit_service.filter_audit_logs({
            'organization_id': 'org-123'
        })
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_export_audit_logs_filter_failure(self, audit_service):
        """Test export when filter fails - lines 134-136"""
        with patch.object(audit_service, 'filter_audit_logs', return_value={
            'success': False,
            'error': 'Filter failed'
        }):
            result = await audit_service.export_audit_logs({
                'filters': {'organization_id': 'org-123'},
                'format': 'json'
            })
            
            assert result['success'] is False
            assert result['error'] == 'Filter failed'
    
    @pytest.mark.asyncio
    async def test_export_audit_logs_exception(self, audit_service):
        """Test export exception handling - lines 176-180"""
        with patch.object(audit_service, 'filter_audit_logs', side_effect=Exception("Export error")):
            result = await audit_service.export_audit_logs({
                'filters': {'organization_id': 'org-123'},
                'format': 'json'
            })
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_audit_statistics_exception(self, audit_service):
        """Test get_audit_statistics exception handling - lines 218-222"""
        with patch.object(audit_service, 'filter_audit_logs', side_effect=Exception("Stats error")):
            result = await audit_service.get_audit_statistics(
                organization_id='org-123',
                start_date=datetime.utcnow() - timedelta(days=7),
                end_date=datetime.utcnow()
            )
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_no_logs_more_check(self, audit_service):
        """Test activity summary with no logs - covers line 236"""
        with patch.object(audit_service, 'filter_audit_logs', return_value={
            'success': True,
            'logs': []
        }):
            result = await audit_service.get_user_activity_summary(
                organization_id='org-123',
                user_id='user-123'
            )
            
            assert result['success'] is True
            assert result['summary']['action_count'] == 0
    
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_exception(self, audit_service):
        """Test get_user_activity_summary exception handling - lines 280-284"""
        with patch.object(audit_service, 'filter_audit_logs', side_effect=Exception("Summary error")):
            result = await audit_service.get_user_activity_summary(
                organization_id='org-123',
                user_id='user-123'
            )
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_check_security_alerts_filter_failure(self, audit_service):
        """Test security alerts when filter fails - lines 300-303"""
        with patch.object(audit_service, 'filter_audit_logs', return_value={
            'success': False,
            'error': 'Filter failed'
        }):
            result = await audit_service.check_security_alerts(
                organization_id='org-123',
                time_window_minutes=5
            )
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_check_security_alerts_exception(self, audit_service):
        """Test check_security_alerts exception handling - lines 326-330"""
        with patch.object(audit_service, 'filter_audit_logs', side_effect=Exception("Alerts error")):
            result = await audit_service.check_security_alerts(
                organization_id='org-123',
                time_window_minutes=5
            )
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_cleanup_old_logs_exception(self, audit_service):
        """Test cleanup exception handling - lines 349-353"""
        # Force exception
        audit_service.supabase.from_.return_value.delete.side_effect = Exception("Cleanup error")
        
        result = await audit_service.cleanup_old_logs(
            organization_id='org-123',
            retention_days=90
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics_exception(self, audit_service):
        """Test get_performance_metrics exception handling - lines 374-378"""
        # Force exception by making datetime calls fail
        with patch('datetime.datetime') as mock_dt:
            mock_dt.utcnow.side_effect = Exception("Metrics error")
            
            result = await audit_service.get_performance_metrics(
                organization_id='org-123',
                start_date=datetime.utcnow() - timedelta(days=7),
                end_date=datetime.utcnow()
            )
            
            assert result['success'] is False
            assert 'error' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.audit_service', '--cov-report=html'])

