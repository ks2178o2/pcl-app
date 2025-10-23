# apps/app-api/__tests__/test_real_database.py

import pytest
import asyncio
from datetime import datetime, timedelta
import os
import json

# Set up real environment variables for testing
# These should be set in your environment or CI/CD pipeline
# Example: export SUPABASE_URL="your_supabase_url"
# Example: export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"
# Example: export OPENAI_API_KEY="your_openai_api_key"

# For testing, use environment variables or skip if not available
if not os.environ.get('SUPABASE_URL'):
    pytest.skip("SUPABASE_URL not set - skipping real database tests")
if not os.environ.get('SUPABASE_SERVICE_ROLE_KEY'):
    pytest.skip("SUPABASE_SERVICE_ROLE_KEY not set - skipping real database tests")
if not os.environ.get('OPENAI_API_KEY'):
    pytest.skip("OPENAI_API_KEY not set - skipping real database tests")

from services.audit_service import AuditService
from services.context_manager import ContextManager
from services.supabase_client import SupabaseClientManager


class TestRealDatabase:
    """Test suite for real database operations"""
    
    @pytest.fixture
    async def audit_service(self):
        """Create audit service instance"""
        return AuditService()
    
    @pytest.fixture
    async def context_manager(self):
        """Create context manager instance"""
        return ContextManager()
    
    @pytest.fixture
    async def supabase_client(self):
        """Create Supabase client instance"""
        return SupabaseClientManager()
    
    async def test_audit_service_real_database(self, audit_service):
        """Test audit service with real database"""
        # Test creating audit log
        audit_data = {
            "user_id": "test-user-123",
            "organization_id": "test-org-123",
            "action": "test_action",
            "resource_type": "test_resource",
            "resource_id": "test-resource-123",
            "details": {"test": "data"},
            "ip_address": "127.0.0.1",
            "user_agent": "test-agent"
        }
        
        result = await audit_service.create_audit_log(audit_data)
        assert result["success"] is True
        assert "audit_id" in result
        
        # Test retrieving audit logs
        logs = await audit_service.get_audit_logs(
            user_id="test-user-123",
            limit=10
        )
        assert logs["success"] is True
        assert len(logs["logs"]) > 0
    
    async def test_context_manager_real_database(self, context_manager):
        """Test context manager with real database"""
        # Test adding context item
        context_data = {
            "organization_id": "test-org-123",
            "rag_feature": "test_feature",
            "item_id": "test-item-123",
            "item_type": "test_type",
            "item_title": "Test Item",
            "item_content": "Test content for real database",
            "priority": 1,
            "confidence_score": 0.9
        }
        
        result = await context_manager.add_context_item(context_data)
        assert result["success"] is True
        assert "item_id" in result
        
        # Test retrieving context items
        items = await context_manager.get_context_items(
            organization_id="test-org-123",
            rag_feature="test_feature"
        )
        assert items["success"] is True
        assert len(items["items"]) > 0
    
    async def test_supabase_client_real_database(self, supabase_client):
        """Test Supabase client with real database"""
        # Test basic connection
        result = await supabase_client.test_connection()
        assert result["success"] is True
        
        # Test query execution
        query_result = await supabase_client.execute_query(
            "SELECT 1 as test_value"
        )
        assert query_result["success"] is True
        assert query_result["data"][0]["test_value"] == 1


if __name__ == "__main__":
    pytest.main([__file__])