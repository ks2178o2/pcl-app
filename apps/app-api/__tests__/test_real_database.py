# apps/app-api/__tests__/test_real_database.py

import pytest
import asyncio
from datetime import datetime, timedelta
import os
import json

# Credentials are automatically loaded from .env.test (preferred) or .env file
# Tests should use .env.test to point to a test database, not production

# Load test environment variables (prefer .env.test over .env for tests)
try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Prefer .env.test for tests to use test database credentials
    env_paths = [
        Path(__file__).parent.parent / '.env.test',  # Test-specific credentials (preferred)
        Path(__file__).parent.parent / 'sandbox.env',  # Sandbox credentials
        Path(__file__).parent.parent / '.env',  # Development credentials (fallback)
        Path(__file__).parent.parent.parent.parent / '.env.test',  # Root .env.test
        Path(__file__).parent.parent.parent.parent / '.env',  # Root .env
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass  # dotenv not available, rely on environment

# Skip tests if credentials are not available
if not os.environ.get('SUPABASE_URL'):
    pytest.skip("SUPABASE_URL not found in .env.test or .env file - skipping real database tests", allow_module_level=True)
if not os.environ.get('SUPABASE_SERVICE_ROLE_KEY'):
    pytest.skip("SUPABASE_SERVICE_ROLE_KEY not found in .env.test or .env file - skipping real database tests", allow_module_level=True)

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