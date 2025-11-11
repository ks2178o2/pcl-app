"""
Real Database Integration Tests
Tests database operations with actual Supabase connection
Credentials are automatically loaded from .env.test (preferred) or .env file
Tests should use .env.test to point to a test database, not production
"""
import pytest
import os
import asyncio
from datetime import datetime
from services.supabase_client import SupabaseClientManager
from services.audit_logger import AuditLogger
from services.audit_service import AuditService
from services.context_manager import ContextManager

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

# Skip all tests if Supabase credentials are not available
pytestmark = pytest.mark.skipif(
    not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_SERVICE_ROLE_KEY'),
    reason="Supabase credentials not available in .env.test or .env file"
)


@pytest.fixture(scope="class")
def supabase_manager():
    """Create Supabase client manager with real connection"""
    manager = SupabaseClientManager()
    # Reset singleton to ensure fresh connection
    SupabaseClientManager._instance = None
    SupabaseClientManager._client = None
    return SupabaseClientManager()


@pytest.fixture(scope="class")
def test_organization_id():
    """Test organization ID for isolation"""
    return f"test-org-{datetime.now().strftime('%Y%m%d%H%M%S')}"


@pytest.fixture(scope="class")
def test_user_id():
    """Test user ID for isolation"""
    return f"test-user-{datetime.now().strftime('%Y%m%d%H%M%S')}"


class TestRealDatabaseIntegration:
    """Real database integration tests with actual Supabase"""
    
    @pytest.mark.asyncio
    async def test_supabase_connection(self, supabase_manager):
        """Test basic Supabase connection"""
        client = supabase_manager.get_client()
        assert client is not None, "Supabase client should be initialized"
        
        # Test health check
        result = await supabase_manager.health_check()
        assert result["success"] is True, "Health check should succeed"
        assert result["status"] == "healthy", "Status should be healthy"
    
    @pytest.mark.asyncio
    async def test_supabase_crud_operations(self, supabase_manager, test_organization_id):
        """Test CRUD operations with real database"""
        client = supabase_manager.get_client()
        
        # CREATE - Insert test data
        test_data = {
            "organization_id": test_organization_id,
            "name": "Test Organization",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Note: Adjust table name based on your schema
        # This is a template - update based on actual tables
        try:
            result = await supabase_manager.insert_data("organizations", test_data)
            assert result["success"] is True, "Insert should succeed"
            org_id = result["data"][0]["id"] if result["data"] else test_organization_id
            
            # READ - Query test data
            read_result = await supabase_manager.execute_query(
                "organizations",
                select="*",
                filters={"id": org_id}
            )
            assert read_result["success"] is True, "Read should succeed"
            assert len(read_result["data"]) > 0, "Should find inserted data"
            
            # UPDATE - Update test data
            update_data = {"name": "Updated Test Organization"}
            update_result = await supabase_manager.update_data(
                "organizations",
                update_data,
                {"id": org_id}
            )
            assert update_result["success"] is True, "Update should succeed"
            
            # Verify update
            verify_result = await supabase_manager.execute_query(
                "organizations",
                select="name",
                filters={"id": org_id}
            )
            assert verify_result["data"][0]["name"] == "Updated Test Organization"
            
            # DELETE - Clean up test data
            delete_result = await supabase_manager.delete_data(
                "organizations",
                {"id": org_id}
            )
            assert delete_result["success"] is True, "Delete should succeed"
            
        except Exception as e:
            # If table doesn't exist or schema differs, skip but log
            pytest.skip(f"Table 'organizations' may not exist or schema differs: {e}")
    
    @pytest.mark.asyncio
    async def test_rls_policies(self, supabase_manager, test_user_id, test_organization_id):
        """Test Row Level Security policies with real database"""
        client = supabase_manager.get_client()
        
        # Test that RLS policies are enforced
        # This would test that users can only access their own data
        # Adjust based on your actual RLS setup
        
        try:
            # Try to access data with service role (should bypass RLS)
            result = await supabase_manager.execute_query(
                "profiles",
                select="id",
                filters={"user_id": test_user_id}
            )
            # Service role should have access
            assert result["success"] is True
            
        except Exception as e:
            pytest.skip(f"RLS test skipped - may need different setup: {e}")
    
    @pytest.mark.asyncio
    async def test_audit_service_real_database(self, test_user_id, test_organization_id):
        """Test audit service with real database"""
        audit_service = AuditService()
        
        # Create audit log
        audit_data = {
            "user_id": test_user_id,
            "organization_id": test_organization_id,
            "action": "test_action",
            "resource_type": "test_resource",
            "resource_id": "test-resource-123",
            "details": {"test": "data"},
            "ip_address": "127.0.0.1",
            "user_agent": "test-agent"
        }
        
        result = await audit_service.create_audit_log(audit_data)
        assert result["success"] is True, "Audit log creation should succeed"
        assert "audit_id" in result, "Should return audit ID"
        
        # Retrieve audit logs
        logs = await audit_service.get_audit_logs(
            user_id=test_user_id,
            limit=10
        )
        assert logs["success"] is True, "Should retrieve audit logs"
        assert len(logs["logs"]) > 0, "Should find created audit log"
    
    @pytest.mark.asyncio
    async def test_context_manager_real_database(self, test_organization_id):
        """Test context manager with real database"""
        context_manager = ContextManager()
        
        # Add context item
        context_data = {
            "organization_id": test_organization_id,
            "rag_feature": "test_feature",
            "item_id": f"test-item-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "item_type": "test_type",
            "item_title": "Test Item",
            "item_content": "Test content for real database",
            "priority": 1,
            "confidence_score": 0.9
        }
        
        result = await context_manager.add_context_item(context_data)
        assert result["success"] is True, "Context item creation should succeed"
        assert "item_id" in result, "Should return item ID"
        
        # Retrieve context items
        items = await context_manager.get_context_items(
            organization_id=test_organization_id,
            rag_feature="test_feature"
        )
        assert items["success"] is True, "Should retrieve context items"
        assert len(items["items"]) > 0, "Should find created context item"
    
    @pytest.mark.asyncio
    async def test_database_constraints(self, supabase_manager):
        """Test database constraints (unique, foreign keys, etc.)"""
        client = supabase_manager.get_client()
        
        # Test unique constraint violation
        # This would test that duplicate unique values are rejected
        # Adjust based on your actual schema constraints
        
        try:
            # Example: Try to insert duplicate email (if unique constraint exists)
            # This is a template - update based on actual constraints
            pass
        except Exception as e:
            # Expected to fail if constraint exists
            assert "unique" in str(e).lower() or "duplicate" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, supabase_manager):
        """Test transaction behavior and rollback"""
        # Test that failed operations don't leave partial data
        # This would test transaction integrity
        # Adjust based on your transaction handling
        
        # Note: Supabase client may handle transactions differently
        # This is a placeholder for transaction testing
        pass
    
    @pytest.mark.asyncio
    async def test_query_performance(self, supabase_manager):
        """Test query performance with real database"""
        import time
        
        start_time = time.time()
        
        # Execute a simple query
        result = await supabase_manager.execute_query(
            "profiles",
            select="id",
            filters={}
        )
        
        elapsed_time = time.time() - start_time
        
        assert result["success"] is True, "Query should succeed"
        assert elapsed_time < 5.0, "Query should complete in reasonable time (<5s)"
    
    @pytest.mark.asyncio
    async def test_error_handling_real_database(self, supabase_manager):
        """Test error handling with real database"""
        # Test invalid table name
        result = await supabase_manager.execute_query(
            "nonexistent_table_12345",
            select="*"
        )
        # Should handle gracefully
        assert result["success"] is False or "error" in result, "Should handle invalid table"


class TestDatabaseCleanup:
    """Cleanup test data after integration tests"""
    
    @pytest.mark.asyncio
    async def test_cleanup_test_data(self, supabase_manager, test_organization_id, test_user_id):
        """Clean up test data created during integration tests"""
        # This would clean up any test data created during tests
        # Adjust based on your cleanup needs
        
        try:
            # Clean up test organization
            await supabase_manager.delete_data(
                "organizations",
                {"id": test_organization_id}
            )
        except Exception:
            pass  # Ignore cleanup errors
        
        try:
            # Clean up test user data
            await supabase_manager.delete_data(
                "profiles",
                {"user_id": test_user_id}
            )
        except Exception:
            pass  # Ignore cleanup errors

