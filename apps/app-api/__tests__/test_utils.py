# apps/app-api/__tests__/test_utils.py

"""
Test utilities for comprehensive test coverage
"""

from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List, Optional
import json

class SupabaseMockBuilder:
    """Builder class for creating comprehensive Supabase mocks"""
    
    def __init__(self):
        self.mock_client = Mock()
        self.table_mocks = {}
        self.setup_default_responses()
    
    def setup_default_responses(self):
        """Setup default mock responses for common operations"""
        # Default insert response
        self.insert_response = Mock()
        self.insert_response.data = [{'id': 'test-id-123'}]
        
        # Default select response
        self.select_response = Mock()
        self.select_response.data = []
        self.select_response.count = 0
        
        # Default update response
        self.update_response = Mock()
        self.update_response.data = [{'id': 'updated-id-123'}]
        
        # Default delete response
        self.delete_response = Mock()
        self.delete_response.data = [{'id': 'deleted-id-123'}]
        
        # Default single response
        self.single_response = Mock()
        self.single_response.data = None
        self.single_response.error = None
    
    def create_table_mock(self, table_name: str, custom_data: Optional[List[Dict]] = None):
        """Create a mock for a specific table"""
        table_mock = Mock()
        
        # Setup insert
        table_mock.insert.return_value.execute.return_value = self.insert_response
        
        # Setup select with chaining
        select_chain = Mock()
        select_chain.eq.return_value = select_chain
        select_chain.ilike.return_value = select_chain
        select_chain.order.return_value = select_chain
        select_chain.range.return_value = select_chain
        select_chain.single.return_value.execute.return_value = self.single_response
        
        if custom_data:
            select_chain.execute.return_value = Mock(data=custom_data, count=len(custom_data))
        else:
            select_chain.execute.return_value = self.select_response
            
        table_mock.select.return_value = select_chain
        
        # Setup update
        update_chain = Mock()
        update_chain.eq.return_value.execute.return_value = self.update_response
        table_mock.update.return_value = update_chain
        
        # Setup delete
        delete_chain = Mock()
        delete_chain.eq.return_value.execute.return_value = self.delete_response
        table_mock.delete.return_value = delete_chain
        
        self.table_mocks[table_name] = table_mock
        return table_mock
    
    def setup_table_data(self, table_name: str, data: List[Dict[str, Any]]):
        """Setup specific data for a table"""
        if table_name not in self.table_mocks:
            self.create_table_mock(table_name)
        
        table_mock = self.table_mocks[table_name]
        
        # Setup select chain with proper chaining
        select_chain = Mock()
        select_chain.eq.return_value = select_chain
        select_chain.ilike.return_value = select_chain
        select_chain.order.return_value = select_chain
        
        # Handle range operation properly
        def range_side_effect(start, end):
            # Simulate pagination by slicing the data
            paginated_data = data[start:end+1] if start < len(data) else []
            result = Mock()
            result.data = paginated_data if isinstance(paginated_data, list) else []
            result.count = len(data)
            return result
        
        select_chain.range.side_effect = range_side_effect
        
        # Create execute result with proper data attribute
        execute_result = Mock()
        execute_result.data = data if isinstance(data, list) else []
        execute_result.count = len(data) if isinstance(data, list) else 0
        select_chain.execute.return_value = execute_result
        
        # Setup single response
        single_chain = Mock()
        single_chain.eq.return_value = single_chain
        single_chain.single.return_value.execute.return_value = Mock(
            data=data[0] if data else None,
            error=None
        )
        
        table_mock.select.return_value = select_chain
        table_mock.select.return_value.eq.return_value.single.return_value = single_chain
        
        # Setup single response for direct single() calls
        if data:
            self.single_response.data = data[0]
            self.single_response.error = None
        else:
            self.single_response.data = None
            self.single_response.error = Mock(message="Not found")
    
    def setup_error_response(self, table_name: str, error_message: str):
        """Setup error response for a table"""
        if table_name not in self.table_mocks:
            self.create_table_mock(table_name)
        
        error_response = Mock()
        error_response.data = None
        error_response.error = Mock(message=error_message)
        
        table_mock = self.table_mocks[table_name]
        
        # Setup error responses for all operations
        table_mock.insert.return_value.execute.return_value = error_response
        table_mock.update.return_value.eq.return_value.execute.return_value = error_response
        table_mock.delete.return_value.eq.return_value.execute.return_value = error_response
        
        # Setup error for select operations
        select_error_chain = Mock()
        select_error_chain.eq.return_value = select_error_chain
        select_error_chain.ilike.return_value = select_error_chain
        select_error_chain.order.return_value = select_error_chain
        select_error_chain.range.return_value = select_error_chain
        select_error_chain.execute.return_value = error_response
        select_error_chain.single.return_value.execute.return_value = error_response
        
        table_mock.select.return_value = select_error_chain
    
    def setup_query_with_count(self, table_name: str, data: List[Dict[str, Any]], total_count: int = None):
        """Setup query chain that supports count queries for get_audit_logs"""
        if table_name not in self.table_mocks:
            self.create_table_mock(table_name)
        
        table_mock = self.table_mocks[table_name]
        
        # Create chain for the main query
        main_result = Mock()
        main_result.data = data if isinstance(data, list) else []
        
        select_chain = Mock()
        select_chain.eq.return_value = select_chain
        select_chain.order.return_value = select_chain
        
        range_result = Mock()
        range_result.data = data if isinstance(data, list) else []
        range_result.count = len(data) if isinstance(data, list) else 0
        select_chain.range = Mock(return_value=range_result)
        
        table_mock.select.return_value = select_chain
        
        # Setup count query
        count_result = Mock()
        count_result.count = total_count if total_count is not None else len(data) if isinstance(data, list) else 0
        
        # Create a separate table mock for count query
        count_table_mock = Mock()
        count_select_chain = Mock()
        count_select_chain.eq.return_value = count_select_chain
        count_select_chain.execute = Mock(return_value=count_result)
        count_table_mock.select = Mock(return_value=count_select_chain)
        
        # Store count mock
        self.count_table_mocks = getattr(self, 'count_table_mocks', {})
        self.count_table_mocks[table_name] = count_table_mock
    
    def get_mock_client(self):
        """Get the configured mock client"""
        def mock_from_side_effect(table_name):
            # Check if this is a count query (second call)
            if hasattr(self, 'count_table_mocks') and table_name in self.count_table_mocks:
                # Return count table mock for second call
                count_mock = self.count_table_mocks[table_name]
                # Don't return count mock again
                del self.count_table_mocks[table_name]
                return count_mock
            
            if table_name in self.table_mocks:
                return self.table_mocks[table_name]
            else:
                # Create default table mock
                return self.create_table_mock(table_name)
        
        self.mock_client.from_.side_effect = mock_from_side_effect
        return self.mock_client

class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_global_context_item(overrides: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a global context item for testing"""
        default_item = {
            "id": "global-123",
            "rag_feature": "best_practice_kb",
            "item_id": "global-knowledge-123",
            "item_type": "knowledge_chunk",
            "item_title": "Global Best Practice",
            "item_content": "This is global knowledge content",
            "status": "active",
            "priority": 1,
            "confidence_score": 0.9,
            "source": "test_source",
            "tags": ["sales", "best-practice"],
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
        
        if overrides:
            default_item.update(overrides)
        
        return default_item
    
    @staticmethod
    def create_tenant_access(overrides: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a tenant access record for testing"""
        default_access = {
            "id": "access-123",
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            "access_level": "read",
            "enabled": True,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
        
        if overrides:
            default_access.update(overrides)
        
        return default_access
    
    @staticmethod
    def create_context_sharing(overrides: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a context sharing record for testing"""
        default_sharing = {
            "id": "sharing-123",
            "source_organization_id": "org-123",
            "target_organization_id": "org-456",
            "rag_feature": "best_practice_kb",
            "item_id": "knowledge-123",
            "sharing_type": "read_only",
            "status": "pending",
            "shared_by": "user-123",
            "approved_by": None,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
        
        if overrides:
            default_sharing.update(overrides)
        
        return default_sharing
    
    @staticmethod
    def create_organization_quotas(overrides: Optional[Dict] = None) -> Dict[str, Any]:
        """Create organization quotas for testing"""
        default_quotas = {
            "id": "quota-123",
            "organization_id": "org-123",
            "max_context_items": 1000,
            "max_global_access_features": 10,
            "max_sharing_requests": 50,
            "current_context_items": 100,
            "current_global_access": 2,
            "current_sharing_requests": 5,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
        
        if overrides:
            default_quotas.update(overrides)
        
        return default_quotas
    
    @staticmethod
    def create_rag_toggle(overrides: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a RAG feature toggle for testing"""
        default_toggle = {
            "id": "toggle-123",
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            "enabled": True,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
        
        if overrides:
            default_toggle.update(overrides)
        
        return default_toggle
    
    @staticmethod
    def create_audit_log(overrides: Optional[Dict] = None) -> Dict[str, Any]:
        """Create an audit log entry for testing"""
        default_log = {
            "id": "audit-123",
            "user_id": "user-123",
            "organization_id": "org-123",
            "action": "test_action",
            "resource_type": "test_resource",
            "resource_id": "resource-123",
            "details": {"test": "data"},
            "ip_address": "192.168.1.1",
            "user_agent": "Test Agent",
            "created_at": "2024-01-15T10:00:00Z"
        }
        
        if overrides:
            default_log.update(overrides)
        
        return default_log
    
    @staticmethod
    def create_context_item(overrides: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a context item for testing"""
        default_item = {
            "id": "context-123",
            "organization_id": "org-123",
            "rag_feature": "best_practice_kb",
            "item_id": "knowledge_123",
            "item_type": "knowledge_chunk",
            "item_title": "Test Knowledge",
            "item_content": "Test content",
            "status": "included",
            "priority": 1,
            "confidence_score": 0.9,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
        
        if overrides:
            default_item.update(overrides)
        
        return default_item

class MockResponseBuilder:
    """Builder for creating mock responses with different scenarios"""
    
    @staticmethod
    def success_response(data: Any = None) -> Mock:
        """Create a successful response"""
        response = Mock()
        response.data = data or [{'id': 'success-id'}]
        response.error = None
        return response
    
    @staticmethod
    def error_response(error_message: str) -> Mock:
        """Create an error response"""
        response = Mock()
        response.data = None
        response.error = Mock(message=error_message)
        return response
    
    @staticmethod
    def empty_response() -> Mock:
        """Create an empty response"""
        response = Mock()
        response.data = []
        response.count = 0
        response.error = None
        return response
    
    @staticmethod
    def paginated_response(data: List[Dict], total_count: int) -> Mock:
        """Create a paginated response"""
        response = Mock()
        response.data = data
        response.count = total_count
        response.error = None
        return response
