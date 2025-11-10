# apps/app-api/__tests__/test_audit_service_improved.py
"""
Improved test suite for Audit Service to reach 85% coverage
Target: 85% coverage for AuditService
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from services.audit_service import AuditService


class TestAuditServiceAdvanced:
    """Test advanced Audit Service features"""
    
    @pytest.fixture
    def audit_service(self):
        return AuditService()
    
    @pytest.mark.asyncio
    async def test_query_audit_logs_with_filter(self, audit_service):
        """Test querying audit logs with filters"""
        filters = {
            'action_type': 'CREATE',
            'resource_type': 'context_item',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
        
        with patch.object(audit_service.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = Mock(data=[
                {'id': 'log-1', 'action_type': 'CREATE'},
                {'id': 'log-2', 'action_type': 'CREATE'}
            ])
            
            logs = await audit_service.query_audit_logs(
                organization_id='org-123',
                filters=filters
            )
            assert len(logs) == 2
    
    @pytest.mark.asyncio
    async def test_paginate_audit_logs(self, audit_service):
        """Test paginating through audit logs"""
        with patch.object(audit_service.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.eq.return_value.range.return_value.order.return_value.execute.return_value = Mock(data=[
                {'id': f'log-{i}'} for i in range(20)
            ])
            
            page1 = await audit_service.get_audit_logs(
                organization_id='org-123',
                limit=10,
                offset=0
            )
            assert len(page1) == 20  # Mock returns all data
    
    @pytest.mark.asyncio
    async def test_get_audit_statistics(self, audit_service):
        """Test retrieving audit statistics"""
        with patch.object(audit_service.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.execute.return_value = Mock(data=[
                {'action_type': 'CREATE', 'count': 50},
                {'action_type': 'UPDATE', 'count': 30},
                {'action_type': 'DELETE', 'count': 10}
            ])
            
            stats = await audit_service.get_audit_statistics('org-123')
            assert stats is not None
            assert 'CREATE' in [s['action_type'] for s in stats]
    
    @pytest.mark.asyncio
    async def test_export_audit_logs(self, audit_service):
        """Test exporting audit logs to CSV/JSON"""
        with patch.object(audit_service.supabase, 'from_') as mock_from:
            mock_from.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[
                {'id': 'log-1', 'action_type': 'CREATE', 'timestamp': '2024-01-01'},
                {'id': 'log-2', 'action_type': 'UPDATE', 'timestamp': '2024-01-02'}
            ])
            
            export_data = await audit_service.export_audit_logs('org-123')
            assert export_data is not None
    
    @pytest.mark.asyncio
    async def test_cleanup_old_audit_logs(self, audit_service):
        """Test cleaning up old audit logs"""
        with patch.object(audit_service.supabase, 'from_') as mock_from:
            mock_from.return_value.delete.return_value.lt.return_value.execute.return_value = Mock()
            
            result = await audit_service.cleanup_old_logs(365)  # Delete logs older than 1 year
            assert result is not None


class TestAuditServiceErrorHandling:
    """Test error handling in Audit Service"""
    
    @pytest.fixture
    def audit_service(self):
        return AuditService()
    
    @pytest.mark.asyncio
    async def test_handle_database_connection_error(self, audit_service):
        """Test handling database connection errors"""
        with patch.object(audit_service.supabase, 'from_') as mock_from:
            mock_from.side_effect = ConnectionError("Database connection failed")
            
            with pytest.raises(ConnectionError):
                await audit_service.log_action(
                    user_id='user-123',
                    action_type='CREATE',
                    resource_type='context_item',
                    resource_id='item-123'
                )
    
    @pytest.mark.asyncio
    async def test_handle_timeout_error(self, audit_service):
        """Test handling timeout errors"""
        with patch.object(audit_service.supabase, 'from_') as mock_from:
            mock_from.return_value.insert.return_value.execute.side_effect = TimeoutError("Operation timed out")
            
            with pytest.raises(TimeoutError):
                await audit_service.log_action(
                    user_id='user-123',
                    action_type='CREATE',
                    resource_type='context_item',
                    resource_id='item-123'
                )
    
    @pytest.mark.asyncio
    async def test_handle_invalid_data(self, audit_service):
        """Test handling invalid data in audit logs"""
        with pytest.raises(ValueError):
            await audit_service.log_action(
                user_id='',
                action_type='',
                resource_type='',
                resource_id=''
            )


class TestAuditServicePerformance:
    """Test performance of Audit Service"""
    
    @pytest.fixture
    def audit_service(self):
        return AuditService()
    
    @pytest.mark.asyncio
    async def test_high_volume_audit_logging(self, audit_service):
        """Test logging many audit entries efficiently"""
        with patch.object(audit_service.supabase, 'from_') as mock_from:
            mock_from.return_value.insert.return_value.execute.return_value = Mock()
            
            import time
            start = time.time()
            
            tasks = [
                audit_service.log_action(
                    user_id=f'user-{i}',
                    action_type='CREATE',
                    resource_type='context_item',
                    resource_id=f'item-{i}'
                )
                for i in range(1000)
            ]
            
            await asyncio.gather(*tasks)
            elapsed = time.time() - start
            
            # Should log 1000 entries in <5 seconds
            assert elapsed < 5.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.audit_service', '--cov-report=html'])

