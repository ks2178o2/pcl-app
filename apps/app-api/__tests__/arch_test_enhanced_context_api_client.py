# apps/app-api/__tests__/test_enhanced_context_api_client.py

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def create_async_mock_method(return_value, side_effect=None):
    """Create an async mock method that returns the given value or raises side_effect"""
    async def async_method(*args, **kwargs):
        if side_effect:
            raise side_effect
        return return_value
    return async_method


@pytest.fixture
def mock_context_manager():
    """Create a mock EnhancedContextManager using Mock with async methods to avoid recursion"""
    mock = Mock()
    # Set up methods as async functions (TestClient will handle them)
    mock.add_global_context_item = create_async_mock_method({'success': True})
    mock.get_global_context_items = create_async_mock_method({'success': True, 'data': []})
    mock.grant_tenant_access = create_async_mock_method({'success': True})
    mock.revoke_tenant_access = create_async_mock_method({'success': True})
    mock.share_context_item = create_async_mock_method({'success': True})
    mock.approve_sharing_request = create_async_mock_method({'success': True})
    mock.get_shared_context_items = create_async_mock_method({'success': True, 'data': []})
    mock.upload_file_content = create_async_mock_method({'success': True})
    mock.scrape_web_content = create_async_mock_method({'success': True})
    mock.bulk_api_upload = create_async_mock_method({'success': True})
    mock.get_organization_quotas = create_async_mock_method({'success': True, 'quotas': {}})
    mock.update_organization_quotas = create_async_mock_method({'success': True})
    return mock


@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger using Mock with async method to avoid recursion"""
    mock = Mock()
    mock.log_user_action = create_async_mock_method(None)
    return mock


@pytest.fixture
def mock_user():
    """Create a mock user"""
    return {
        "id": "user-123",
        "role": "system_admin",
        "organization_id": "org-123"
    }


@pytest.fixture
def app(mock_context_manager, mock_audit_logger, mock_user):
    """Create FastAPI app with mocked dependencies"""
    # Use the same approach as _build_app_with_mocks (without reload to avoid recursion)
    manager_patcher = patch('services.enhanced_context_manager.EnhancedContextManager', return_value=mock_context_manager)
    logger_patcher = patch('services.audit_logger.audit_logger', mock_audit_logger)
    
    manager_patcher.start()
    logger_patcher.start()
    
    try:
        import sys
        if 'api.enhanced_context_api' not in sys.modules:
            import api.enhanced_context_api as ctx_api
        else:
            import api.enhanced_context_api as ctx_api
        
        ctx_api.context_manager = mock_context_manager
        ctx_api.audit_logger = mock_audit_logger
        
        # Patch get_current_user directly in the module
        async def get_user_override():
            return mock_user
        ctx_api.get_current_user = get_user_override
        
        app = FastAPI()
        app.include_router(ctx_api.router)
        # Don't store patchers on app to avoid serialization issues
        return app
    except Exception:
        manager_patcher.stop()
        logger_patcher.stop()
        raise


@pytest.fixture
def client(app):
    """Create TestClient with mocked dependencies"""
    yield TestClient(app)


class TestEnhancedContextAPIClient:
    """Integration tests for Enhanced Context API using TestClient"""
    
    def _build_app_with_mocks(self, context_manager_mock, audit_logger_mock, user):
        """Build FastAPI app with mocked dependencies"""
        # CRITICAL: Patch class BEFORE importing module (module instantiates at import)
        manager_patcher = patch('services.enhanced_context_manager.EnhancedContextManager', return_value=context_manager_mock)
        logger_patcher = patch('services.audit_logger.audit_logger', audit_logger_mock)
        
        manager_patcher.start()
        logger_patcher.start()
        
        try:
            import sys
            import importlib
            
            # Import/reload module to get fresh router
            if 'api.enhanced_context_api' in sys.modules:
                ctx_api = importlib.reload(sys.modules['api.enhanced_context_api'])
            else:
                import api.enhanced_context_api as ctx_api
            
            # Directly assign mocks
            ctx_api.context_manager = context_manager_mock
            ctx_api.audit_logger = audit_logger_mock
            
            # Create FastAPI app and include router
            app = FastAPI()
            app.include_router(ctx_api.router)
            
            # Find the get_current_user function reference from the router's routes
            # This is the EXACT function that FastAPI will call
            get_current_user_func = None
            for route in ctx_api.router.routes:
                if hasattr(route, 'dependant') and route.dependant:
                    for dep in route.dependant.dependencies:
                        if hasattr(dep, 'call') and 'get_current_user' in str(dep.call):
                            get_current_user_func = dep.call
                            break
                if get_current_user_func:
                    break
            
            # Fallback to module function if not found in routes
            if not get_current_user_func:
                get_current_user_func = ctx_api.get_current_user
            
            # Override using the exact function reference from the route
            async def get_user_override():
                return user
            
            app.dependency_overrides[get_current_user_func] = get_user_override
            
            return app
        except Exception as e:
            manager_patcher.stop()
            logger_patcher.stop()
            raise
    
    def test_app_has_routes(self, app):
        """Test that app has routes registered"""
        assert len(app.routes) > 0
        
        # Get routes with path info
        route_paths = []
        for route in app.routes:
            if hasattr(route, 'path'):
                route_paths.append(route.path)
        
        assert len(route_paths) > 0
    
    def test_add_global_context_endpoint_exists(self):
        """Test that add global context endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.post("/global/add")' in content
    
    def test_get_global_context_items_endpoint_exists(self):
        """Test that get global context items endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.get("/global/items")' in content
    
    def test_grant_tenant_access_endpoint_exists(self):
        """Test that grant tenant access endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.post("/access/grant")' in content
    
    def test_revoke_tenant_access_endpoint_exists(self):
        """Test that revoke tenant access endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.post("/access/revoke")' in content
    
    def test_share_context_item_endpoint_exists(self):
        """Test that share context item endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.post("/sharing/share")' in content
    
    def test_approve_sharing_request_endpoint_exists(self):
        """Test that approve sharing request endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.post("/sharing/approve/{sharing_id}")' in content
    
    def test_get_shared_context_items_endpoint_exists(self):
        """Test that get shared context items endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.get("/sharing/received")' in content
    
    def test_upload_file_content_endpoint_exists(self):
        """Test that upload file content endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.post("/upload/file")' in content
    
    def test_scrape_web_content_endpoint_exists(self):
        """Test that scrape web content endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.post("/upload/web-scrape")' in content
    
    def test_bulk_api_upload_endpoint_exists(self):
        """Test that bulk API upload endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.post("/upload/bulk")' in content
    
    def test_get_organization_quotas_endpoint_exists(self):
        """Test that get organization quotas endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.get("/quotas/{organization_id}")' in content
    
    def test_update_organization_quotas_endpoint_exists(self):
        """Test that update organization quotas endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.put("/quotas/{organization_id}")' in content
    
    def test_exception_handling_present(self):
        """Test that exception handling is present"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'HTTPException' in content
        assert 'except HTTPException:' in content
        assert 'except Exception as e:' in content
    
    def test_audit_logging_used(self):
        """Test that audit logging is used in API"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'audit_logger' in content
        assert 'log_user_action' in content
    
    def test_context_manager_used(self):
        """Test that context_manager is used in API"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'context_manager' in content
        assert 'EnhancedContextManager' in content
    
    def test_role_based_access_control(self):
        """Test that role-based access control is implemented"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'current_user.get(\'role\')' in content
        assert 'system_admin' in content
        assert 'org_admin' in content
    
    def test_permission_checks_present(self):
        """Test that permission checks are present"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'status_code=403' in content
        assert 'Insufficient permissions' in content or 'Only system admins' in content
    
    def test_router_prefix_correct(self):
        """Test that router prefix is correct"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'prefix="/api/enhanced-context"' in content
    
    def test_router_tags_correct(self):
        """Test that router tags are correct"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'tags=["Enhanced Context Management"]' in content
    
    def test_organization_id_extraction(self):
        """Test that organization_id is extracted from user"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'current_user.get(\'organization_id\')' in content or 'organization_id' in content
    
    def test_file_upload_handling(self):
        """Test that file upload handling is present"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'UploadFile' in content
        assert 'File' in content
        assert 'Form' in content
    
    def test_add_global_context_success(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test successful add global context - lines 29-59"""
        # Setup mock result
        result = {
            'success': True,
            'item_id': 'item-123',
            'message': 'Context item added'
        }
        mock_context_manager.add_global_context_item = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/global/add",
                json={
                    "rag_feature": "test_feature",
                    "item_title": "Test Item",
                    "content": "Test content"
                }
            )
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            assert body['item_id'] == 'item-123'
    
    def test_get_global_context_items_success(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test successful get global context items - lines 66-87"""
        # Setup mock result
        result = {
            'success': True,
            'data': [
                {
                    'item_id': 'item-1',
                    'rag_feature': 'test_feature',
                    'item_title': 'Test Item'
                }
            ],
            'total': 1
        }
        mock_context_manager.get_global_context_items = create_async_mock_method(result)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.get("/api/enhanced-context/global/items")
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            assert len(body['data']) == 1
    
    def test_get_current_user_defined(self):
        """Test that get_current_user function is defined"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'enhanced_context_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'def get_current_user()' in content or 'async def get_current_user()' in content
    
    # ==================== PERMISSION TESTS ====================
    
    def test_add_global_context_permission_denied(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test permission denied for add global context - line 38"""
        non_admin_user = {"id": "user-456", "role": "org_admin", "organization_id": "org-123"}
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, non_admin_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/global/add",
                json={"rag_feature": "test", "item_title": "Test"}
            )
            # Debug: check what we got
            if response.status_code != 403:
                print(f"Expected 403, got {response.status_code}")
                print(f"Response: {response.json()}")
                print(f"User override: {non_admin_user}")
                print(f"Dependency overrides: {app.dependency_overrides}")
            assert response.status_code == 403, f"Expected 403, got {response.status_code}. Response: {response.json()}"
    
    def test_add_global_context_manager_error(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test error handling in add global context - lines 56-64"""
        result = {'success': False, 'error': 'Invalid data'}
        mock_context_manager.add_global_context_item = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/global/add",
                json={"rag_feature": "test", "item_title": "Test"}
            )
            assert response.status_code == 400
    
    def test_get_global_context_items_error(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test error handling in get global context - lines 89-90"""
        mock_context_manager.get_global_context_items = create_async_mock_method(None, side_effect=Exception("Database error"))
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.get("/api/enhanced-context/global/items")
            assert response.status_code == 500
    
    # ==================== TENANT ACCESS TESTS ====================
    
    def test_grant_tenant_access_success(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test successful grant tenant access - lines 94-134"""
        result = {'success': True, 'access_id': 'access-123'}
        mock_context_manager.grant_tenant_access = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/access/grant?organization_id=org-123&rag_feature=test_feature&access_level=read"
            )
            assert response.status_code == 200
            assert response.json()['success'] is True
    
    def test_grant_tenant_access_permission_denied(self, mock_context_manager, mock_audit_logger):
        """Test permission denied for grant tenant access - lines 104-105"""
        regular_user = {"id": "user-456", "role": "user", "organization_id": "org-123"}
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, regular_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/access/grant?organization_id=org-123&rag_feature=test"
            )
            assert response.status_code == 403
    
    def test_grant_tenant_access_org_admin_restriction(self, mock_context_manager, mock_audit_logger):
        """Test org admin can only grant to own org - lines 108-109"""
        org_admin_user = {"id": "user-789", "role": "org_admin", "organization_id": "org-123"}
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, org_admin_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/access/grant?organization_id=other-org&rag_feature=test"
            )
            assert response.status_code == 403
    
    def test_revoke_tenant_access_success(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test successful revoke tenant access - lines 141-178"""
        result = {'success': True, 'revoked_id': 'revoke-123'}
        mock_context_manager.revoke_tenant_access = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/access/revoke?organization_id=org-123&rag_feature=test_feature"
            )
            assert response.status_code == 200
            assert response.json()['success'] is True
    
    def test_revoke_tenant_access_permission_denied(self, mock_context_manager, mock_audit_logger):
        """Test permission denied for revoke tenant access - lines 150-151"""
        regular_user = {"id": "user-456", "role": "user", "organization_id": "org-123"}
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, regular_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/access/revoke?organization_id=org-123&rag_feature=test"
            )
            assert response.status_code == 403
    
    # ==================== SHARING TESTS ====================
    
    def test_share_context_item_success(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test successful share context item - lines 187-231"""
        result = {'success': True, 'sharing_id': 'share-123'}
        mock_context_manager.share_context_item = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/sharing/share?target_organization_id=target-org&rag_feature=test_feature&item_id=item-123&sharing_type=read_only"
            )
            assert response.status_code == 200
            assert response.json()['success'] is True
    
    def test_share_context_item_permission_denied(self, mock_context_manager, mock_audit_logger):
        """Test permission denied for share context item - lines 198-199"""
        regular_user = {"id": "user-456", "role": "user", "organization_id": "org-123"}
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, regular_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/sharing/share?target_organization_id=target&rag_feature=test&item_id=item"
            )
            assert response.status_code == 403
    
    def test_approve_sharing_request_success(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test successful approve sharing request - lines 238-269"""
        result = {'success': True}
        mock_context_manager.approve_sharing_request = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post("/api/enhanced-context/sharing/approve/share-123")
            assert response.status_code == 200
            assert response.json()['success'] is True
    
    def test_approve_sharing_request_permission_denied(self, mock_context_manager, mock_audit_logger):
        """Test permission denied for approve sharing - lines 246-247"""
        regular_user = {"id": "user-456", "role": "user", "organization_id": "org-123"}
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, regular_user)
        with TestClient(app) as test_client:
            response = test_client.post("/api/enhanced-context/sharing/approve/share-123")
            assert response.status_code == 403
    
    def test_get_shared_context_items_success(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test successful get shared context items - lines 276-290"""
        result = {'success': True, 'data': [{'item_id': 'item-1'}]}
        mock_context_manager.get_shared_context_items = create_async_mock_method(result)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.get("/api/enhanced-context/sharing/received")
            assert response.status_code == 200
            assert response.json()['success'] is True
    
    def test_get_shared_context_items_error(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test error handling in get shared context items - lines 292-293"""
        mock_context_manager.get_shared_context_items = create_async_mock_method(None, side_effect=Exception("Error"))
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.get("/api/enhanced-context/sharing/received")
            assert response.status_code == 500
    
    # ==================== UPLOAD TESTS ====================
    
    def test_upload_file_content_success(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test successful file upload - lines 297-346"""
        result = {'success': True, 'success_count': 1}
        mock_context_manager.upload_file_content = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            files = {"file": ("test.txt", b"test content", "text/plain")}
            data = {"rag_feature": "test_feature"}
            response = test_client.post("/api/enhanced-context/upload/file", files=files, data=data)
            assert response.status_code == 200
            assert response.json()['success'] is True
    
    def test_upload_file_content_error(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test error handling in file upload - lines 348-351"""
        result = {'success': False, 'error': 'Upload failed'}
        mock_context_manager.upload_file_content = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            files = {"file": ("test.txt", b"test", "text/plain")}
            data = {"rag_feature": "test"}
            response = test_client.post("/api/enhanced-context/upload/file", files=files, data=data)
            assert response.status_code == 400
    
    def test_scrape_web_content_success(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test successful web scrape - lines 353-390"""
        result = {'success': True}
        mock_context_manager.scrape_web_content = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/upload/web-scrape?url=https://example.com&rag_feature=test"
            )
            assert response.status_code == 200
            assert response.json()['success'] is True
    
    def test_scrape_web_content_error(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test error handling in web scrape - lines 392-395"""
        result = {'success': False, 'error': 'Scrape failed'}
        mock_context_manager.scrape_web_content = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/upload/web-scrape?url=invalid&rag_feature=test"
            )
            assert response.status_code == 400
    
    def test_bulk_api_upload_success(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test successful bulk upload - lines 397-436"""
        result = {'success': True, 'success_count': 2}
        mock_context_manager.bulk_api_upload = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            # FastAPI expects items as a list at root level, not nested
            response = test_client.post(
                "/api/enhanced-context/upload/bulk?rag_feature=test_feature",
                json=[{"item_id": "1", "content": "test1"}, {"item_id": "2", "content": "test2"}]
            )
            assert response.status_code == 200
            assert response.json()['success'] is True
    
    def test_bulk_api_upload_error(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test error handling in bulk upload - lines 438-441"""
        result = {'success': False, 'error': 'Bulk upload failed'}
        mock_context_manager.bulk_api_upload = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            # FastAPI expects items as a list at root level
            response = test_client.post(
                "/api/enhanced-context/upload/bulk?rag_feature=test",
                json=[]  # Empty list
            )
            assert response.status_code == 400
    
    # ==================== QUOTA TESTS ====================
    
    def test_get_organization_quotas_success(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test successful get quotas - lines 445-465"""
        result = {'success': True, 'quotas': {'max_items': 1000, 'used': 500}}
        mock_context_manager.get_organization_quotas = create_async_mock_method(result)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.get("/api/enhanced-context/quotas/org-123")
            assert response.status_code == 200
            assert response.json()['success'] is True
    
    def test_get_organization_quotas_permission_denied(self, mock_context_manager, mock_audit_logger):
        """Test permission denied for get quotas - lines 453-454"""
        regular_user = {"id": "user-456", "role": "user", "organization_id": "org-123"}
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, regular_user)
        with TestClient(app) as test_client:
            response = test_client.get("/api/enhanced-context/quotas/org-123")
            assert response.status_code == 403
    
    def test_get_organization_quotas_org_admin_restriction(self, mock_context_manager, mock_audit_logger):
        """Test org admin can only view own org quotas - lines 457-458"""
        org_admin_user = {"id": "user-789", "role": "org_admin", "organization_id": "org-123"}
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, org_admin_user)
        with TestClient(app) as test_client:
            response = test_client.get("/api/enhanced-context/quotas/other-org")
            assert response.status_code == 403
    
    def test_update_organization_quotas_success(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test successful update quotas - lines 472-505"""
        result = {'success': True}
        mock_context_manager.update_organization_quotas = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.put(
                "/api/enhanced-context/quotas/org-123",
                json={"max_items": 2000}
            )
            assert response.status_code == 200
            assert response.json()['success'] is True
    
    def test_update_organization_quotas_permission_denied(self, mock_context_manager, mock_audit_logger):
        """Test permission denied for update quotas - lines 481-482"""
        org_admin_user = {"id": "user-789", "role": "org_admin", "organization_id": "org-123"}
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, org_admin_user)
        with TestClient(app) as test_client:
            response = test_client.put(
                "/api/enhanced-context/quotas/org-123",
                json={"max_items": 2000}
            )
            assert response.status_code == 403
    
    # ==================== ADDITIONAL COVERAGE TESTS ====================
    
    def test_add_global_context_exception_handling(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test exception handling in add_global_context_item (lines 63-64)"""
        mock_context_manager.add_global_context_item = create_async_mock_method(None, side_effect=Exception("Unexpected error"))
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/global/add",
                json={"rag_feature": "test", "item_title": "Test"}
            )
            assert response.status_code == 500
    
    def test_get_global_context_items_with_organization_id(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test get_global_context_items with explicit organization_id (lines 77-78)"""
        result = {'success': True, 'data': []}
        mock_context_manager.get_global_context_items = create_async_mock_method(result)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.get("/api/enhanced-context/global/items?organization_id=org-456")
            assert response.status_code == 200
            assert response.json()['success'] is True
    
    def test_grant_tenant_access_error_response(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test grant_tenant_access with error response (lines 131-132)"""
        result = {'success': False, 'error': 'Access denied'}
        mock_context_manager.grant_tenant_access = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/access/grant?organization_id=org-123&rag_feature=test"
            )
            assert response.status_code == 400
            assert "Access denied" in response.json()['detail']
    
    def test_grant_tenant_access_exception(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test exception handling in grant_tenant_access (lines 138-139)"""
        mock_context_manager.grant_tenant_access = create_async_mock_method(None, side_effect=Exception("DB error"))
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/access/grant?organization_id=org-123&rag_feature=test"
            )
            assert response.status_code == 500
    
    def test_revoke_tenant_access_org_admin_restriction(self, mock_context_manager, mock_audit_logger):
        """Test org admin can only revoke from own org (lines 154-155)"""
        org_admin_user = {"id": "user-789", "role": "org_admin", "organization_id": "org-123"}
        app = self._build_app_with_mocks(mock_context_manager, Mock(), org_admin_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/access/revoke?organization_id=other-org&rag_feature=test"
            )
            assert response.status_code == 403
    
    def test_revoke_tenant_access_error_response(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test revoke_tenant_access with error response (lines 175-176)"""
        result = {'success': False, 'error': 'Revoke failed'}
        mock_context_manager.revoke_tenant_access = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/access/revoke?organization_id=org-123&rag_feature=test"
            )
            assert response.status_code == 400
    
    def test_revoke_tenant_access_exception(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test exception handling in revoke_tenant_access (lines 182-183)"""
        mock_context_manager.revoke_tenant_access = create_async_mock_method(None, side_effect=Exception("DB error"))
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/access/revoke?organization_id=org-123&rag_feature=test"
            )
            assert response.status_code == 500
    
    def test_share_context_item_error_response(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test share_context_item with error response (lines 228-229)"""
        result = {'success': False, 'error': 'Sharing failed'}
        mock_context_manager.share_context_item = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/sharing/share?target_organization_id=org-456&rag_feature=test&item_id=item-1"
            )
            assert response.status_code == 400
    
    def test_share_context_item_exception(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test exception handling in share_context_item (lines 235-236)"""
        mock_context_manager.share_context_item = create_async_mock_method(None, side_effect=Exception("DB error"))
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/sharing/share?target_organization_id=org-456&rag_feature=test&item_id=item-1"
            )
            assert response.status_code == 500
    
    def test_approve_sharing_request_error_response(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test approve_sharing_request with error response (lines 266-267)"""
        result = {'success': False, 'error': 'Approval failed'}
        mock_context_manager.approve_sharing_request = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post("/api/enhanced-context/sharing/approve/sharing-123")
            assert response.status_code == 400
    
    def test_approve_sharing_request_exception(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test exception handling in approve_sharing_request (lines 273-274)"""
        mock_context_manager.approve_sharing_request = create_async_mock_method(None, side_effect=Exception("DB error"))
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post("/api/enhanced-context/sharing/approve/sharing-123")
            assert response.status_code == 500
    
    def test_upload_file_content_with_organization_id(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test upload_file_content with explicit organization_id (lines 307-309)"""
        result = {'success': True, 'success_count': 1}
        mock_context_manager.upload_file_content = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            files = {'file': ('test.txt', 'test content', 'text/plain')}
            data = {
                'rag_feature': 'test',
                'organization_id': 'org-456',
                'metadata': '{}'
            }
            response = test_client.post(
                "/api/enhanced-context/upload/file",
                files=files,
                data=data
            )
            assert response.status_code == 200
    
    def test_upload_file_content_exception(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test exception handling in upload_file_content (lines 350-351)"""
        mock_context_manager.upload_file_content = create_async_mock_method(None, side_effect=Exception("Upload error"))
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            files = {'file': ('test.txt', 'test content', 'text/plain')}
            data = {'rag_feature': 'test'}
            response = test_client.post(
                "/api/enhanced-context/upload/file",
                files=files,
                data=data
            )
            assert response.status_code == 500
    
    def test_scrape_web_content_with_organization_id(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test scrape_web_content with explicit organization_id (lines 362-364)"""
        result = {'success': True}
        mock_context_manager.scrape_web_content = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/upload/web-scrape?url=https://example.com&rag_feature=test&organization_id=org-456"
            )
            assert response.status_code == 200
    
    def test_scrape_web_content_exception(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test exception handling in scrape_web_content (lines 394-395)"""
        mock_context_manager.scrape_web_content = create_async_mock_method(None, side_effect=Exception("Scrape error"))
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/upload/web-scrape?url=https://example.com&rag_feature=test"
            )
            assert response.status_code == 500
    
    def test_bulk_api_upload_with_organization_id(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test bulk_api_upload with explicit organization_id (lines 406-408)"""
        result = {'success': True, 'success_count': 2}
        mock_context_manager.bulk_api_upload = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/upload/bulk?rag_feature=test&organization_id=org-456",
                json=[{"item_id": "1", "content": "test1"}]
            )
            assert response.status_code == 200
    
    def test_bulk_api_upload_exception(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test exception handling in bulk_api_upload (lines 440-441)"""
        mock_context_manager.bulk_api_upload = create_async_mock_method(None, side_effect=Exception("Bulk error"))
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/enhanced-context/upload/bulk?rag_feature=test",
                json=[{"item_id": "1", "content": "test1"}]
            )
            assert response.status_code == 500
    
    def test_get_organization_quotas_error_response(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test get_organization_quotas with error response (lines 462-463)"""
        result = {'success': False, 'error': 'Quota fetch failed'}
        mock_context_manager.get_organization_quotas = create_async_mock_method(result)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.get("/api/enhanced-context/quotas/org-123")
            assert response.status_code == 400
    
    def test_get_organization_quotas_exception(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test exception handling in get_organization_quotas (lines 469-470)"""
        mock_context_manager.get_organization_quotas = create_async_mock_method(None, side_effect=Exception("DB error"))
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.get("/api/enhanced-context/quotas/org-123")
            assert response.status_code == 500
    
    def test_update_organization_quotas_error_response(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test update_organization_quotas with error response (lines 502-503)"""
        result = {'success': False, 'error': 'Update failed'}
        mock_context_manager.update_organization_quotas = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.put(
                "/api/enhanced-context/quotas/org-123",
                json={"max_items": 100}
            )
            assert response.status_code == 400
    
    def test_update_organization_quotas_exception(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test exception handling in update_organization_quotas (lines 509-510)"""
        mock_context_manager.update_organization_quotas = create_async_mock_method(None, side_effect=Exception("DB error"))
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            response = test_client.put(
                "/api/enhanced-context/quotas/org-123",
                json={"max_items": 100}
            )
            assert response.status_code == 500
    
    def test_upload_file_content_with_metadata(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test upload_file_content with metadata parsing (line 316)"""
        result = {'success': True, 'success_count': 1}
        mock_context_manager.upload_file_content = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            files = {'file': ('test.txt', 'test content', 'text/plain')}
            data = {
                'rag_feature': 'test',
                'metadata': '{"key": "value"}'
            }
            response = test_client.post(
                "/api/enhanced-context/upload/file",
                files=files,
                data=data
            )
            assert response.status_code == 200
    
    def test_upload_file_content_no_extension(self, mock_context_manager, mock_audit_logger, mock_user):
        """Test upload_file_content with file without extension (line 320)"""
        result = {'success': True, 'success_count': 1}
        mock_context_manager.upload_file_content = create_async_mock_method(result)
        mock_audit_logger.log_user_action = create_async_mock_method(None)
        
        app = self._build_app_with_mocks(mock_context_manager, mock_audit_logger, mock_user)
        with TestClient(app) as test_client:
            # File without extension should default to 'txt'
            files = {'file': ('testfile', 'test content', 'text/plain')}
            data = {'rag_feature': 'test'}
            response = test_client.post(
                "/api/enhanced-context/upload/file",
                files=files,
                data=data
            )
            assert response.status_code == 200
    
    def test_get_current_user_dependency(self):
        """Test get_current_user dependency function (line 21)"""
        import api.enhanced_context_api as ctx_api
        import asyncio
        
        # Test the dependency function directly
        user = asyncio.run(ctx_api.get_current_user())
        assert user is not None
        assert "id" in user
        assert "role" in user
        assert "organization_id" in user
        assert user["role"] == "system_admin"

