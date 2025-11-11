# apps/app-api/__tests__/test_audit_service_edge_cases.py
"""
Edge case tests for remaining coverage gaps
Lines: 236, 262-264
"""

import pytest
from unittest.mock import Mock, patch
from services.audit_service import AuditService


class TestAuditServiceEdgeCases:
    """Edge case tests for remaining lines"""
    
    @pytest.fixture
    def audit_service(self):
        """Create audit service with mocked supabase"""
        with patch('services.audit_service.get_supabase_client') as mock_get:
            mock_client = Mock()
            table_mock = Mock()
            insert_result = Mock()
            insert_result.data = [{'id': 'audit-123'}]
            table_mock.insert.return_value.execute.return_value = insert_result
            table_mock.select.return_value = Mock()
            mock_client.from_.return_value = table_mock
            mock_get.return_value = mock_client
            
            return AuditService()
    
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_filter_failure(self, audit_service):
        """Test activity summary when filter fails - line 236"""
        with patch.object(audit_service, 'filter_audit_logs', return_value={
            'success': False,
            'error': 'Filter failed'
        }):
            result = await audit_service.get_user_activity_summary(
                organization_id='org-123',
                user_id='user-123'
            )
            
            assert result['success'] is False
            assert result['error'] == 'Filter failed'
    
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_with_created_at(self, audit_service):
        """Test activity summary with created_at timestamps - lines 261-264"""
        logs = [
            {'action': 'login', 'user_id': 'user-123', 'created_at': '2024-01-01T12:00:00'},
            {'action': 'logout', 'user_id': 'user-123', 'created_at': '2024-01-02T12:00:00'},
            {'action': 'login', 'user_id': 'user-123', 'created_at': '2024-01-02T13:00:00'}  # Same day
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
            assert result['summary']['action_count'] == 3
            assert result['summary']['active_days'] == 2  # 2 unique days
            assert result['summary']['most_common_action'] == 'login'
    
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_without_created_at(self, audit_service):
        """Test activity summary without created_at - line 262"""
        logs = [
            {'action': 'login', 'user_id': 'user-123', 'created_at': ''},  # Empty
            {'action': 'logout', 'user_id': 'user-123'}  # Missing key
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
            assert result['summary']['active_days'] == 0  # No valid dates
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics_implementation(self, audit_service):
        """Test get_performance_metrics returns mock data"""
        from datetime import datetime, timedelta
        
        result = await audit_service.get_performance_metrics(
            organization_id='org-123',
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        
        assert result['success'] is True
        assert 'metrics' in result
        assert 'rag_query' in result['metrics']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.audit_service', '--cov-report=html'])

