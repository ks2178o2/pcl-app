# apps/app-api/__tests__/test_audit_logger.py

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


class TestAuditLogger:
    """Test suite for AuditLogger service"""

    @pytest.fixture
    def mock_audit_logger(self):
        """Mock AuditLogger for testing"""
        mock_logger = Mock()
        mock_logger.log_user_action = AsyncMock(return_value={
            "success": True,
            "audit_id": "audit-123"
        })
        return mock_logger

    @pytest.fixture
    def sample_audit_entry(self):
        """Sample audit entry for testing"""
        return {
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "test_action",
            "resource_type": "test_resource",
            "resource_id": "resource-123",
            "details": {"test": "data"},
            "ip_address": "192.168.1.1",
            "user_agent": "Test Agent",
            "timestamp": datetime.now()
        }

    @pytest.mark.asyncio
    async def test_log_user_action_success(self, mock_audit_logger, sample_audit_entry):
        """Test successful user action logging"""
        result = await mock_audit_logger.log_user_action(sample_audit_entry)
        
        assert result["success"] is True
        assert result["audit_id"] == "audit-123"

    @pytest.mark.asyncio
    async def test_log_user_action_with_metadata(self, mock_audit_logger):
        """Test logging user action with complex metadata"""
        entry = {
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "rag_query",
            "resource_type": "knowledge_base",
            "resource_id": "kb-123",
            "details": {
                "query": "test query",
                "feature": "best_practice_kb",
                "results_count": 5,
                "response_time": 150
            },
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0 Test Browser",
            "timestamp": datetime.now()
        }
        
        result = await mock_audit_logger.log_user_action(entry)
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_log_user_action_error_handling(self, mock_audit_logger):
        """Test error handling in user action logging"""
        # Mock error response
        mock_audit_logger.log_user_action = AsyncMock(return_value={
            "success": False,
            "error": "Database connection failed"
        })
        
        entry = {
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "test_action",
            "resource_type": "test_resource",
            "resource_id": "resource-123",
            "details": {},
            "ip_address": "192.168.1.1",
            "user_agent": "Test Agent",
            "timestamp": datetime.now()
        }
        
        result = await mock_audit_logger.log_user_action(entry)
        
        assert result["success"] is False
        assert "Database connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_user_ip_address(self, mock_audit_logger):
        """Test IP address extraction from request"""
        mock_request = Mock()
        mock_request.headers = {"x-forwarded-for": "203.0.113.195, 70.41.3.18, 150.172.238.178"}
        
        # Mock the method
        mock_audit_logger.get_user_ip_address = Mock(return_value="203.0.113.195")
        
        ip_address = mock_audit_logger.get_user_ip_address(mock_request)
        
        assert ip_address == "203.0.113.195"

    @pytest.mark.asyncio
    async def test_get_user_ip_address_direct(self, mock_audit_logger):
        """Test IP address extraction from direct connection"""
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.100"
        
        # Mock the method
        mock_audit_logger.get_user_ip_address = Mock(return_value="192.168.1.100")
        
        ip_address = mock_audit_logger.get_user_ip_address(mock_request)
        
        assert ip_address == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_get_user_agent_info(self, mock_audit_logger):
        """Test user agent information extraction"""
        mock_request = Mock()
        mock_request.headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        # Mock the method
        mock_audit_logger.get_user_agent_info = Mock(return_value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        user_agent = mock_audit_logger.get_user_agent_info(mock_request)
        
        assert "Mozilla/5.0" in user_agent
        assert "Windows NT 10.0" in user_agent

    @pytest.mark.asyncio
    async def test_format_audit_log_entry(self, mock_audit_logger, sample_audit_entry):
        """Test audit log entry formatting"""
        # Mock the method
        mock_audit_logger.format_audit_log_entry = Mock(return_value={
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "test_action",
            "resource_type": "test_resource",
            "resource_id": "resource-123",
            "details": {"test": "data"},
            "timestamp": datetime.now().isoformat()
        })
        
        formatted = mock_audit_logger.format_audit_log_entry(sample_audit_entry)
        
        assert formatted["user_id"] == "user-123"
        assert formatted["organization_id"] == "org-123"
        assert formatted["action"] == "test_action"
        assert formatted["resource_type"] == "test_resource"
        assert formatted["resource_id"] == "resource-123"
        assert formatted["details"] == {"test": "data"}
        assert "timestamp" in formatted

    @pytest.mark.asyncio
    async def test_audit_log_validation(self, mock_audit_logger):
        """Test audit log entry validation"""
        # Mock validation error
        mock_audit_logger.log_user_action = AsyncMock(side_effect=ValueError("User ID cannot be empty"))
        
        invalid_entry = {
            "user_id": "",  # Empty user_id should fail validation
            "organization_id": "org-123",
            "action": "test_action",
            "resource_type": "test_resource",
            "resource_id": "resource-123",
            "details": {},
            "ip_address": "192.168.1.1",
            "user_agent": "Test Agent",
            "timestamp": datetime.now()
        }
        
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            await mock_audit_logger.log_user_action(invalid_entry)

    @pytest.mark.asyncio
    async def test_audit_log_batch_insertion(self, mock_audit_logger):
        """Test batch insertion of audit logs"""
        entries = [
            {
                "user_id": "user-123",
                "organization_id": "org-123",
                "action": "action1",
                "resource_type": "resource1",
                "resource_id": "id1",
                "details": {},
                "ip_address": "192.168.1.1",
                "user_agent": "Test Agent",
                "timestamp": datetime.now()
            },
            {
                "user_id": "user-456",
                "organization_id": "org-123",
                "action": "action2",
                "resource_type": "resource2",
                "resource_id": "id2",
                "details": {},
                "ip_address": "192.168.1.2",
                "user_agent": "Test Agent",
                "timestamp": datetime.now()
            }
        ]
        
        # Mock batch method
        mock_audit_logger.log_user_actions_batch = AsyncMock(return_value={
            "success": True,
            "inserted_count": 2
        })
        
        result = await mock_audit_logger.log_user_actions_batch(entries)
        
        assert result["success"] is True
        assert result["inserted_count"] == 2

    @pytest.mark.asyncio
    async def test_audit_log_performance_metrics(self, mock_audit_logger):
        """Test audit logging with performance metrics"""
        entry = {
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "rag_query",
            "resource_type": "knowledge_base",
            "resource_id": "kb-123",
            "details": {
                "query_time": 150,
                "embedding_time": 50,
                "search_time": 80,
                "llm_time": 20,
                "total_results": 5
            },
            "ip_address": "192.168.1.1",
            "user_agent": "Test Agent",
            "timestamp": datetime.now()
        }
        
        result = await mock_audit_logger.log_user_action(entry)
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_audit_log_search_and_filter(self, mock_audit_logger):
        """Test audit log search and filtering"""
        # Mock search method
        mock_audit_logger.search_audit_logs = AsyncMock(return_value={
            "success": True,
            "logs": [
                {
                    "id": "audit-1",
                    "user_id": "user-123",
                    "action": "rag_query",
                    "created_at": "2024-01-15T10:00:00Z"
                }
            ]
        })
        
        filters = {
            "user_id": "user-123",
            "action": "rag_query",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }
        
        result = await mock_audit_logger.search_audit_logs(filters)
        
        assert result["success"] is True
        assert len(result["logs"]) == 1
        assert result["logs"][0]["action"] == "rag_query"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])