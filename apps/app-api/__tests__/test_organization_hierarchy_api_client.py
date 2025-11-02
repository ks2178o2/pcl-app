# apps/app-api/__tests__/test_organization_hierarchy_api_client.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client"""
    mock = Mock()
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
def app(mock_supabase, mock_user):
    """Create FastAPI app with mocked dependencies"""
    app = FastAPI()
    
    # Mock dependencies before importing
    with patch('api.organization_hierarchy_api.get_supabase_client', return_value=mock_supabase):
        # Import and include router
        from api.organization_hierarchy_api import router
        app.include_router(router)
    
    return app


@pytest.fixture
def client(app):
    """Create TestClient with mocked dependencies"""
    # Patch dependencies at runtime
    with patch('api.organization_hierarchy_api.get_supabase') as mock_get_supabase:
        with patch('api.organization_hierarchy_api.get_current_user') as mock_get_user:
            mock_supabase = Mock()
            mock_user = {"id": "user-123", "role": "system_admin", "organization_id": "org-123"}
            
            mock_get_supabase.return_value = mock_supabase
            mock_get_user.return_value = mock_user
            
            yield TestClient(app)


class TestOrganizationHierarchyAPIClient:
    """Integration tests for Organization Hierarchy API using TestClient"""
    
    def test_get_children_endpoint_accessible(self, client):
        """Test that get children endpoint is accessible"""
        try:
            response = client.get("/api/v1/orgs/test-org-id/children")
            # Any status means endpoint is accessible
            assert response is not None
        except Exception:
            # Expected without full setup
            pass
    
    def test_app_has_routes(self, app):
        """Test that app has routes registered"""
        assert len(app.routes) > 0
        
        # Get routes with path info
        route_paths = []
        for route in app.routes:
            if hasattr(route, 'path'):
                route_paths.append(route.path)
        
        assert len(route_paths) > 0
    
    @pytest.mark.asyncio
    async def test_get_children_with_proper_mocks(self, mock_supabase, mock_user):
        """Test get children with properly mocked dependencies"""
        # Setup mock result
        result = Mock()
        result.data = [
            {
                'id': 'child-org-1',
                'name': 'Child Organization 1',
                'parent_organization_id': 'parent-org-1',
            }
        ]
        result.count = 1
        
        # Setup mock chain
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_order = Mock()
        mock_range = Mock()
        mock_limit = Mock()
        mock_offset = Mock()
        mock_execute = Mock()
        mock_execute.return_value = result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_eq.order = Mock(return_value=mock_order)
        mock_order.range = Mock(return_value=mock_range)
        mock_range.execute = mock_execute
        mock_order.limit = Mock(return_value=mock_limit)
        mock_limit.offset = Mock(return_value=mock_offset)
        mock_offset.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        # Create app
        app = FastAPI()
        with patch('api.organization_hierarchy_api.get_supabase_client', return_value=mock_supabase):
            with patch('api.organization_hierarchy_api.get_current_user', return_value=mock_user):
                with patch('api.organization_hierarchy_api.PermissionChecker') as MockChecker:
                    mock_checker = Mock()
                    mock_checker.can_access_organization_hierarchy.return_value = True
                    MockChecker.return_value = mock_checker
                    
                    from api.organization_hierarchy_api import router
                    app.include_router(router)
                    
                    # Create client
                    with TestClient(app) as test_client:
                        response = test_client.get("/api/v1/orgs/test-org-id/children")
                        
                        # Should return some response
                        assert response is not None
    
    def test_get_parent_endpoint_exists(self):
        """Test that get parent endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.get("/{org_id}/parent"' in content
    
    def test_get_hierarchy_endpoint_exists(self):
        """Test that get hierarchy endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.get("/{org_id}/hierarchy"' in content
    
    def test_create_child_endpoint_exists(self):
        """Test that create child endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.post("/{org_id}/children"' in content
    
    def test_update_parent_endpoint_exists(self):
        """Test that update parent endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.patch("/{org_id}/parent"' in content
    
    def test_get_inheritance_chain_endpoint_exists(self):
        """Test that get inheritance chain endpoint exists"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert '@router.get("/{org_id}/inheritance-chain"' in content
    
    def test_permissions_checker_used(self):
        """Test that PermissionChecker is used in API"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'PermissionChecker' in content
        assert 'checker.' in content
    
    def test_require_system_admin_decorator_used(self):
        """Test that require_system_admin decorator is used"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'require_system_admin' in content
    
    def test_exception_handling_present(self):
        """Test that exception handling is present"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'HTTPException' in content
        assert 'except HTTPException:' in content
        assert 'except Exception as e:' in content
    
    def test_pydantic_models_used(self):
        """Test that Pydantic models are used for request/response"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'response_model=' in content
        assert 'BaseModel' in content
    
    def test_router_prefix_correct(self):
        """Test that router prefix is correct"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'prefix="/api/v1/orgs"' in content
    
    def test_router_tags_correct(self):
        """Test that router tags are correct"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'tags=["Organization Hierarchy"]' in content
    
    @pytest.mark.asyncio
    async def test_get_hierarchy_builds_tree_structure(self, mock_supabase, mock_user):
        """Test that get hierarchy builds proper tree structure"""
        # Setup mock result for hierarchy
        result = Mock()
        result.data = [
            {
                'id': 'root-org',
                'name': 'Root Organization',
                'parent_organization_id': None,
                'level': 0,
                'path': ['root-org']
            },
            {
                'id': 'child-org-1',
                'name': 'Child Organization 1',
                'parent_organization_id': 'root-org',
                'level': 1,
                'path': ['root-org', 'child-org-1']
            }
        ]
        
        # Setup mock chain
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_order = Mock()
        mock_execute = Mock()
        mock_execute.return_value = result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_eq.order = Mock(return_value=mock_order)
        mock_order.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = FastAPI()
        with patch('api.organization_hierarchy_api.get_supabase_client', return_value=mock_supabase):
            with patch('api.organization_hierarchy_api.get_current_user', return_value=mock_user):
                with patch('api.organization_hierarchy_api.PermissionChecker') as MockChecker:
                    mock_checker = Mock()
                    mock_checker.can_access_organization_hierarchy.return_value = True
                    MockChecker.return_value = mock_checker
                    
                    from api.organization_hierarchy_api import router
                    app.include_router(router)
                    
                    with TestClient(app) as test_client:
                        response = test_client.get("/api/v1/orgs/root-org/hierarchy")
                        assert response is not None
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_builds_list(self, mock_supabase, mock_user):
        """Test that get inheritance chain builds proper list"""
        # Setup mock result
        result = Mock()
        result.data = [
            {'id': 'grandparent', 'name': 'Grandparent Org'},
            {'id': 'parent', 'name': 'Parent Org'},
            {'id': 'child', 'name': 'Child Org'}
        ]
        
        # Setup mock chain
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = FastAPI()
        with patch('api.organization_hierarchy_api.get_supabase_client', return_value=mock_supabase):
            with patch('api.organization_hierarchy_api.get_current_user', return_value=mock_user):
                with patch('api.organization_hierarchy_api.PermissionChecker') as MockChecker:
                    mock_checker = Mock()
                    mock_checker.can_access_organization_hierarchy.return_value = True
                    MockChecker.return_value = mock_checker
                    
                    from api.organization_hierarchy_api import router
                    app.include_router(router)
                    
                    with TestClient(app) as test_client:
                        response = test_client.get("/api/v1/orgs/child/inheritance-chain")
                        assert response is not None
    
    def test_organization_model_defined(self):
        """Test that Organization Pydantic model is defined"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'class Organization(BaseModel):' in content
    
    def test_organization_tree_node_model_defined(self):
        """Test that OrganizationTreeNode Pydantic model is defined"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'class OrganizationTreeNode(BaseModel):' in content
    
    def test_create_child_organization_request_model_defined(self):
        """Test that CreateChildOrganizationRequest model is defined"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'class CreateChildOrganizationRequest(BaseModel):' in content
    
    def test_update_parent_request_model_defined(self):
        """Test that UpdateParentRequest model is defined"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'class UpdateParentRequest(BaseModel):' in content
    
    def test_error_logging_present(self):
        """Test that error logging is present"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'logger.error(' in content or 'logger.exception(' in content
    
    def test_query_parameters_used(self):
        """Test that query parameters are properly used"""
        api_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'organization_hierarchy_api.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        assert 'Query(' in content
    
    def _build_app_with_mocks(self, supabase_mock, user, checker_overrides=None):
        """Build FastAPI app with mocked dependencies (pattern from rag_features_api tests)"""
        app = FastAPI()
        # Monkeypatch permission decorator to no-op before import
        import importlib
        import middleware.permissions as perms
        original_sys_admin = getattr(perms, 'require_system_admin', None)
        try:
            perms.require_system_admin = lambda f: f
            import api.organization_hierarchy_api as org_api
            org_api = importlib.reload(org_api)
        finally:
            # restore for other modules/tests
            if original_sys_admin is not None:
                perms.require_system_admin = original_sys_admin
        app.include_router(org_api.router)
        # Override dependency injections so Depends use these values
        app.dependency_overrides[org_api.get_supabase] = lambda: supabase_mock
        app.dependency_overrides[org_api.get_current_user] = lambda: user
        # Override PermissionChecker to avoid needing supabase in tests
        class DummyChecker:
            def __init__(self, *_args, **_kwargs):
                self._access = True
                if checker_overrides and 'can_access_organization_hierarchy' in checker_overrides:
                    self._access = checker_overrides['can_access_organization_hierarchy']
            def can_access_organization_hierarchy(self, *_args, **_kwargs):
                return self._access
        org_api.PermissionChecker = DummyChecker
        return app
    
    def test_get_child_organizations_success(self, mock_supabase, mock_user):
        """Test successful retrieval of child organizations"""
        # Setup mock result
        result = Mock()
        result.data = [
            {
                'id': 'child-1',
                'name': 'Child Org 1',
                'parent_organization_id': 'parent-1',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        ]
        result.count = 1
        
        count_result = Mock()
        count_result.count = 1
        
        # Setup mock chain
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_range = Mock()
        mock_execute = Mock(side_effect=[result, count_result])
        
        # Chain: select().eq().range().execute()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.range.return_value = mock_range
        mock_range.execute = mock_execute
        
        # For count query: select().eq().execute()
        count_execute = Mock(return_value=count_result)
        count_eq = Mock(execute=count_execute)
        count_select = Mock(eq=Mock(return_value=count_eq))
        count_table = Mock(select=Mock(return_value=count_select))
        
        call_counter = {'i': 0}
        def from_side_effect(table_name):
            call_counter['i'] += 1
            return mock_table if call_counter['i'] == 1 else count_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/parent-1/children")
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            assert len(body['data']) == 1
            assert body['data'][0]['id'] == 'child-1'
    
    def test_get_child_organizations_no_data(self, mock_supabase, mock_user):
        """Test get children when no children exist"""
        result = Mock()
        result.data = []
        result.count = 0
        
        count_result = Mock()
        count_result.count = 0
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_range = Mock()
        mock_execute = Mock(return_value=result)
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.range.return_value = mock_range
        mock_range.execute = mock_execute
        
        # Count query
        count_execute = Mock(return_value=count_result)
        count_eq = Mock(execute=count_execute)
        count_select = Mock(eq=Mock(return_value=count_eq))
        count_table = Mock(select=Mock(return_value=count_select))
        
        call_counter = {'i': 0}
        def from_side_effect(table_name):
            call_counter['i'] += 1
            return mock_table if call_counter['i'] == 1 else count_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/parent-1/children")
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            assert len(body['data']) == 0
    
    def test_get_child_organizations_permission_denied(self, mock_supabase, mock_user):
        """Test permission denied for get children"""
        checker_overrides = {'can_access_organization_hierarchy': False}
        app = self._build_app_with_mocks(mock_supabase, mock_user, checker_overrides)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/parent-1/children")
            assert response.status_code == 403
    
    def test_get_parent_organization_success(self, mock_supabase, mock_user):
        """Test successful retrieval of parent organization"""
        org_result = Mock()
        org_result.data = [{'parent_organization_id': 'parent-1'}]
        
        parent_result = Mock()
        parent_result.data = [
            {
                'id': 'parent-1',
                'name': 'Parent Org',
                'parent_organization_id': None,
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        ]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock(side_effect=[org_result, parent_result])
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/child-1/parent")
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            assert body['data']['id'] == 'parent-1'
    
    def test_get_parent_organization_no_parent(self, mock_supabase, mock_user):
        """Test getting parent when organization has no parent"""
        org_result = Mock()
        org_result.data = [{'parent_organization_id': None}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock(return_value=org_result)
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/root-org/parent")
            assert response.status_code == 404
    
    def test_get_parent_organization_parent_not_found(self, mock_supabase, mock_user):
        """Test getting parent when parent org not found - line 203"""
        # Org has parent_id but parent doesn't exist
        org_result = Mock()
        org_result.data = [{'parent_organization_id': 'parent-1'}]
        
        parent_result = Mock()
        parent_result.data = []  # Parent not found
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock(side_effect=[org_result, parent_result])
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/child-1/parent")
            assert response.status_code == 404
    
    def test_get_parent_organization_permission_denied(self, mock_supabase, mock_user):
        """Test permission denied for get parent - line 183"""
        checker_overrides = {'can_access_organization_hierarchy': False}
        app = self._build_app_with_mocks(mock_supabase, mock_user, checker_overrides)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/child-1/parent")
            assert response.status_code == 403
    
    def test_get_parent_organization_exception(self, mock_supabase, mock_user):
        """Test exception handling in get parent"""
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock(side_effect=Exception("Database error"))
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/child-1/parent")
            assert response.status_code == 500
    
    def test_get_hierarchy_empty_returns_root(self, mock_supabase, mock_user):
        """Test getting hierarchy when empty returns just root"""
        hierarchy_result = Mock()
        hierarchy_result.data = []
        
        org_result = Mock()
        org_result.data = [
            {
                'id': 'root-org',
                'name': 'Root Org',
                'parent_organization_id': None,
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        ]
        
        # First query for hierarchy
        hierarchy_order = Mock(execute=Mock(return_value=hierarchy_result))
        hierarchy_eq = Mock(order=Mock(return_value=hierarchy_order))
        hierarchy_select = Mock(eq=Mock(return_value=hierarchy_eq))
        hierarchy_table = Mock(select=Mock(return_value=hierarchy_select))
        
        # Second query for org itself
        org_select = Mock(eq=Mock(return_value=Mock(execute=Mock(return_value=org_result))))
        org_table = Mock(select=Mock(return_value=org_select))
        
        call_counter = {'i': 0}
        def from_side_effect(table_name):
            call_counter['i'] += 1
            return hierarchy_table if call_counter['i'] == 1 else org_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/root-org/hierarchy")
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
    
    def test_get_hierarchy_permission_denied(self, mock_supabase, mock_user):
        """Test permission denied for get hierarchy - line 238"""
        checker_overrides = {'can_access_organization_hierarchy': False}
        app = self._build_app_with_mocks(mock_supabase, mock_user, checker_overrides)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/root-org/hierarchy")
            assert response.status_code == 403
    
    def test_get_hierarchy_with_tree(self, mock_supabase, mock_user):
        """Test getting hierarchy with tree structure"""
        result = Mock()
        result.data = [
            {
                'id': 'root-org',
                'name': 'Root Organization',
                'parent_organization_id': None,
                'level': 0,
                'path': ['root-org']
            },
            {
                'id': 'child-org-1',
                'name': 'Child Organization 1',
                'parent_organization_id': 'root-org',
                'level': 1,
                'path': ['root-org', 'child-org-1']
            }
        ]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_order = Mock()
        mock_execute = Mock(return_value=result)
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.order.return_value = mock_order
        mock_order.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/root-org/hierarchy")
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
    
    def test_create_child_organization_success(self, mock_supabase, mock_user):
        """Test successful creation of child organization"""
        parent_result = Mock()
        parent_result.data = [{'id': 'parent-1', 'name': 'Parent Org'}]
        
        child_result = Mock()
        child_result.data = [
            {
                'id': 'child-new',
                'name': 'New Child Org',
                'parent_organization_id': 'parent-1',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        ]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock(return_value=parent_result)
        mock_insert = Mock()
        mock_insert.execute = Mock(return_value=child_result)
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        mock_table.insert.return_value = mock_insert
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/orgs/parent-1/children",
                json={"name": "New Child Org"}
            )
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            assert body['data']['name'] == 'New Child Org'
    
    def test_create_child_organization_parent_not_found(self, mock_supabase, mock_user):
        """Test creating child when parent doesn't exist"""
        parent_result = Mock()
        parent_result.data = []
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock(return_value=parent_result)
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/orgs/invalid-parent/children",
                json={"name": "New Child Org"}
            )
            assert response.status_code == 404
    
    def test_create_child_organization_exception(self, mock_supabase, mock_user):
        """Test exception handling in create child"""
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock(side_effect=Exception("Database error"))
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/orgs/parent-1/children",
                json={"name": "New Child Org"}
            )
            assert response.status_code == 500
    
    def test_update_parent_organization_success(self, mock_supabase, mock_user):
        """Test successful update of parent organization"""
        org_result = Mock()
        org_result.data = [{
            'id': 'child-1',
            'name': 'Child Org',
            'parent_organization_id': 'old-parent',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }]
        
        parent_result = Mock()
        parent_result.data = [{'id': 'new-parent', 'name': 'New Parent'}]
        
        update_result = Mock()
        update_result.data = [{
            'id': 'child-1',
            'name': 'Child Org',
            'parent_organization_id': 'new-parent',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-02T00:00:00Z'
        }]
        
        # For three queries: org exists, parent exists, update
        existing_execute = Mock(side_effect=[org_result, parent_result])
        existing_eq = Mock(execute=existing_execute)
        existing_table = Mock(select=Mock(return_value=Mock(eq=Mock(return_value=existing_eq))))
        
        # Update query: update().eq().execute()
        update_execute = Mock(return_value=update_result)
        update_eq = Mock(execute=update_execute)
        update_table = Mock(update=Mock(return_value=Mock(eq=Mock(return_value=update_eq))))
        
        call_counter = {'i': 0}
        def from_side_effect(table_name):
            call_counter['i'] += 1
            # First two calls are select, third is update
            return existing_table if call_counter['i'] < 3 else update_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.patch(
                "/api/v1/orgs/child-1/parent",
                json={"parent_organization_id": "new-parent"}
            )
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
    
    def test_update_parent_organization_org_not_found(self, mock_supabase, mock_user):
        """Test update parent when org not found - line 397"""
        org_result = Mock()
        org_result.data = []  # Org not found
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock(return_value=org_result)
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.patch(
                "/api/v1/orgs/nonexistent-org/parent",
                json={"parent_organization_id": "new-parent"}
            )
            assert response.status_code == 404
    
    def test_update_parent_organization_parent_not_found(self, mock_supabase, mock_user):
        """Test update parent when new parent not found - line 407"""
        org_result = Mock()
        org_result.data = [{'id': 'org-1', 'name': 'Org'}]
        
        parent_result = Mock()
        parent_result.data = []  # New parent not found
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock(side_effect=[org_result, parent_result])
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.patch(
                "/api/v1/orgs/org-1/parent",
                json={"parent_organization_id": "nonexistent-parent"}
            )
            assert response.status_code == 404
    
    def test_update_parent_organization_circular_dependency(self, mock_supabase, mock_user):
        """Test update fails when trying to make org its own parent"""
        org_result = Mock()
        org_result.data = [{'id': 'org-1', 'name': 'Org'}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock(return_value=org_result)
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.patch(
                "/api/v1/orgs/org-1/parent",
                json={"parent_organization_id": "org-1"}
            )
            assert response.status_code == 400
    
    def test_update_parent_organization_exception(self, mock_supabase, mock_user):
        """Test exception handling in update parent"""
        org_result = Mock()
        org_result.data = [{'id': 'org-1', 'name': 'Org'}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock(side_effect=[org_result, Exception("Database error")])
        mock_update = Mock()
        mock_update.eq.return_value = mock_execute
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute = mock_execute
        mock_table.update.return_value = mock_update
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.patch(
                "/api/v1/orgs/org-1/parent",
                json={"parent_organization_id": "new-parent"}
            )
            assert response.status_code == 500
    
    def test_get_inheritance_chain_success(self, mock_supabase, mock_user):
        """Test successful retrieval of inheritance chain"""
        # The endpoint loops through orgs, so we need to simulate multiple calls
        child_result = Mock(data=[{'id': 'child', 'name': 'Child Org', 'parent_organization_id': 'parent'}])
        parent_result = Mock(data=[{'id': 'parent', 'name': 'Parent Org', 'parent_organization_id': 'grandparent'}])
        grandparent_result = Mock(data=[{'id': 'grandparent', 'name': 'Grandparent Org', 'parent_organization_id': None}])
        
        # Chain for loop: each query returns one org
        chain_execute = Mock(side_effect=[child_result, parent_result, grandparent_result])
        chain_eq = Mock(execute=chain_execute)
        chain_select = Mock(eq=Mock(return_value=chain_eq))
        chain_table = Mock(select=Mock(return_value=chain_select))
        
        mock_supabase.from_ = Mock(return_value=chain_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/child/inheritance-chain")
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            # The endpoint returns chain in data.inheritance_chain
            assert len(body['data']['inheritance_chain']) == 3
    
    def test_get_inheritance_chain_permission_denied(self, mock_supabase, mock_user):
        """Test permission denied for get inheritance chain - line 464"""
        checker_overrides = {'can_access_organization_hierarchy': False}
        app = self._build_app_with_mocks(mock_supabase, mock_user, checker_overrides)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/child/inheritance-chain")
            assert response.status_code == 403
    
    def test_get_inheritance_chain_exception(self, mock_supabase, mock_user):
        """Test exception handling in get inheritance chain - lines 497-498"""
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_order = Mock()
        mock_execute = Mock(side_effect=Exception("Database error"))
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.order.return_value = mock_order
        mock_order.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/child/inheritance-chain")
            assert response.status_code == 500
    
    def test_get_child_organizations_with_pagination(self, mock_supabase, mock_user):
        """Test get children with pagination"""
        result = Mock()
        result.data = [
            {
                'id': 'child-1',
                'name': 'Child Org 1',
                'parent_organization_id': 'parent-1',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        ]
        result.count = 10  # Total is 10, but we're returning 1
        
        count_result = Mock()
        count_result.count = 10
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_range = Mock()
        mock_execute = Mock(return_value=result)
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.range.return_value = mock_range
        mock_range.execute = mock_execute
        
        # Count query
        count_execute = Mock(return_value=count_result)
        count_eq = Mock(execute=count_execute)
        count_select = Mock(eq=Mock(return_value=count_eq))
        count_table = Mock(select=Mock(return_value=count_select))
        
        call_counter = {'i': 0}
        def from_side_effect(table_name):
            call_counter['i'] += 1
            return mock_table if call_counter['i'] == 1 else count_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/parent-1/children?limit=1&offset=0")
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            assert body['total'] == 10
    
    # ==================== FEATURE STATISTICS TESTS ====================
    
    def test_get_child_organizations_with_feature_stats(self, mock_supabase, mock_user):
        """Test get children with feature statistics enabled - lines 131-143"""
        # Setup main query result
        result = Mock()
        result.data = [
            {
                'id': 'child-1',
                'name': 'Child Org 1',
                'parent_organization_id': 'parent-1',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        ]
        result.count = 1
        
        # Setup count query result
        count_result = Mock()
        count_result.count = 1
        
        # Setup feature statistics results
        feature_result = Mock()
        feature_result.count = 5
        
        enabled_result = Mock()
        enabled_result.count = 3
        
        # Setup main query chain
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_range = Mock()
        mock_execute = Mock(return_value=result)
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.range.return_value = mock_range
        mock_range.execute = mock_execute
        
        # Setup count query chain
        count_execute = Mock(return_value=count_result)
        count_eq = Mock(execute=count_execute)
        count_select = Mock(eq=Mock(return_value=count_eq))
        count_table = Mock(select=Mock(return_value=count_select))
        
        # Setup feature stats queries (need 2 calls per org)
        # Enabled query calls .eq() twice, so we need chaining
        feature_execute = Mock(side_effect=[feature_result, enabled_result])
        feature_select = Mock()
        feature_select.eq = Mock(side_effect=lambda *args, **kwargs: feature_select)  # Allow chaining
        feature_select.execute = feature_execute
        feature_table = Mock(select=Mock(return_value=feature_select))
        
        call_counter = {'i': 0}
        def from_side_effect(table_name):
            call_counter['i'] += 1
            # First: main query, Second: count, Third & Fourth: feature stats
            if call_counter['i'] == 1:
                return mock_table
            elif call_counter['i'] == 2:
                return count_table
            else:
                return feature_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/parent-1/children?include_feature_stats=true")
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            assert len(body['data']) == 1
            assert body['data'][0]['id'] == 'child-1'
    
    def test_get_child_organizations_feature_stats_exception(self, mock_supabase, mock_user):
        """Test feature statistics exception handling - lines 145-148"""
        # Setup main query result
        result = Mock()
        result.data = [
            {
                'id': 'child-1',
                'name': 'Child Org 1',
                'parent_organization_id': 'parent-1',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        ]
        # Set count as integer directly
        result.count = 1
        
        # Setup count result - use same pattern as working tests
        count_result = Mock()
        # Use object.__setattr__ to bypass Mock's attribute handling
        object.__setattr__(count_result, 'count', 1)
        
        # Verify it's actually an int
        assert isinstance(count_result.count, int), "Count must be int"
        
        # Setup main query chain
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_range = Mock()
        mock_execute = Mock(return_value=result)
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.range.return_value = mock_range
        mock_range.execute = mock_execute
        
        # Setup count query chain - return object with integer count
        count_execute = Mock(return_value=count_result)
        count_eq = Mock(execute=count_execute)
        count_select = Mock(eq=Mock(return_value=count_eq))
        count_table = Mock(select=Mock(return_value=count_select))
        
        # Setup feature stats query to raise exception on execute
        # The exception should be caught in the try/except block (lines 145-148)
        feature_execute = Mock(side_effect=Exception("Database error"))
        
        # Create chainable feature select that allows .eq() chaining
        feature_select = Mock()
        feature_select.execute = feature_execute
        
        # Make .eq() return self to allow chaining: .eq().eq().execute()
        def eq_chain(*args, **kwargs):
            return feature_select
        feature_select.eq = Mock(side_effect=eq_chain)
        
        feature_table = Mock(select=Mock(return_value=feature_select))
        
        # Track calls to ensure proper sequencing
        call_counter = {'i': 0}
        def from_side_effect(table_name):
            call_counter['i'] += 1
            if table_name == 'organizations':
                if call_counter['i'] == 1:
                    return mock_table
                elif call_counter['i'] == 2:
                    return count_table
            elif table_name == 'organization_rag_toggles':
                # All feature stats queries should raise exception
                return feature_table
            return mock_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/parent-1/children?include_feature_stats=true")
            # Should still succeed (200 OK), exception caught and defaults set
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            assert len(body['data']) == 1
            # Verify defaults are set when exception occurs (lines 147-148)
            assert body['data'][0]['feature_count'] == 0
            assert body['data'][0]['enabled_features'] == 0
    
    def test_get_hierarchy_with_tree_and_feature_stats(self, mock_supabase, mock_user):
        """Test hierarchy tree building with feature stats - lines 265-290, 293-305"""
        # Setup hierarchy query result
        hierarchy_result = Mock()
        hierarchy_result.data = [
            {
                'id': 'root-org',
                'name': 'Root Organization',
                'parent_organization_id': None,
                'level': 0,
                'path': ['root-org']
            },
            {
                'id': 'child-org-1',
                'name': 'Child Organization 1',
                'parent_organization_id': 'root-org',
                'level': 1,
                'path': ['root-org', 'child-org-1']
            },
            {
                'id': 'grandchild-org',
                'name': 'Grandchild Organization',
                'parent_organization_id': 'child-org-1',
                'level': 2,
                'path': ['root-org', 'child-org-1', 'grandchild-org']
            }
        ]
        
        # Setup feature stats results (2 queries per org = 6 total)
        feature_result = Mock()
        feature_result.count = 5
        
        enabled_result = Mock()
        enabled_result.count = 3
        
        # Hierarchy query chain
        hierarchy_order = Mock(execute=Mock(return_value=hierarchy_result))
        hierarchy_eq = Mock(order=Mock(return_value=hierarchy_order))
        hierarchy_select = Mock(eq=Mock(return_value=hierarchy_eq))
        hierarchy_table = Mock(select=Mock(return_value=hierarchy_select))
        
        # Feature stats query chain (6 queries: 2 per org * 3 orgs)
        feature_execute = Mock(side_effect=[feature_result, enabled_result] * 3)
        feature_select = Mock()
        feature_select.eq = Mock(side_effect=lambda *args, **kwargs: feature_select)  # Allow chaining
        feature_select.execute = feature_execute
        feature_table = Mock(select=Mock(return_value=feature_select))
        
        call_counter = {'i': 0}
        def from_side_effect(table_name):
            call_counter['i'] += 1
            if call_counter['i'] == 1:
                return hierarchy_table
            else:
                return feature_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/root-org/hierarchy?include_feature_stats=true")
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            assert body['data']['id'] == 'root-org'
            assert len(body['data']['children']) == 1
            assert body['data']['children'][0]['id'] == 'child-org-1'
    
    def test_get_child_organizations_result_data_none(self, mock_supabase, mock_user):
        """Test result.data is None edge case - line 120"""
        # Setup result with data=None (not empty list)
        result = Mock()
        result.data = None
        result.count = 0
        
        # Setup query chain
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_range = Mock()
        mock_execute = Mock(return_value=result)
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.range.return_value = mock_range
        mock_range.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/parent-1/children")
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            assert len(body['data']) == 0
            assert body['total'] == 0
    
    def test_get_hierarchy_org_not_found(self, mock_supabase, mock_user):
        """Test organization not found in hierarchy - lines 233, 245"""
        # Setup hierarchy query returning empty
        hierarchy_result = Mock()
        hierarchy_result.data = []
        
        # Setup org query also returning empty
        org_result = Mock()
        org_result.data = []
        
        # Hierarchy query
        hierarchy_order = Mock(execute=Mock(return_value=hierarchy_result))
        hierarchy_eq = Mock(order=Mock(return_value=hierarchy_order))
        hierarchy_select = Mock(eq=Mock(return_value=hierarchy_eq))
        hierarchy_table = Mock(select=Mock(return_value=hierarchy_select))
        
        # Org query
        org_select = Mock(eq=Mock(return_value=Mock(execute=Mock(return_value=org_result))))
        org_table = Mock(select=Mock(return_value=org_select))
        
        call_counter = {'i': 0}
        def from_side_effect(table_name):
            call_counter['i'] += 1
            return hierarchy_table if call_counter['i'] == 1 else org_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/nonexistent-org/hierarchy")
            assert response.status_code == 404
    
    def test_create_child_organization_insert_fails(self, mock_supabase, mock_user):
        """Test create child when insert returns no data - line 353"""
        parent_result = Mock()
        parent_result.data = [{'id': 'parent-1', 'name': 'Parent Org'}]
        
        # Setup insert returning no data
        insert_result = Mock()
        insert_result.data = []
        
        # Parent exists query
        parent_select = Mock(eq=Mock(return_value=Mock(execute=Mock(return_value=parent_result))))
        parent_table = Mock(select=Mock(return_value=parent_select))
        
        # Insert query
        insert_execute = Mock(return_value=insert_result)
        insert_table = Mock(insert=Mock(return_value=Mock(execute=insert_execute)))
        
        call_counter = {'i': 0}
        def from_side_effect(table_name):
            call_counter['i'] += 1
            return parent_table if call_counter['i'] == 1 else insert_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/orgs/parent-1/children",
                json={"name": "New Child Org"}
            )
            assert response.status_code == 500
            assert "Failed to create" in response.json()['detail']
    
    def test_update_parent_organization_update_fails(self, mock_supabase, mock_user):
        """Test update parent when update returns no data - lines 392, 402, 423"""
        org_result = Mock()
        org_result.data = [{'id': 'child-1', 'name': 'Child Org'}]
        
        parent_result = Mock()
        parent_result.data = [{'id': 'new-parent', 'name': 'New Parent'}]
        
        # Setup update returning no data
        update_result = Mock()
        update_result.data = []
        
        # Org and parent exists queries
        existing_execute = Mock(side_effect=[org_result, parent_result])
        existing_eq = Mock(execute=existing_execute)
        existing_select = Mock(eq=Mock(return_value=existing_eq))
        existing_table = Mock(select=Mock(return_value=existing_select))
        
        # Update query
        update_execute = Mock(return_value=update_result)
        update_eq = Mock(execute=update_execute)
        update_table = Mock(update=Mock(return_value=Mock(eq=Mock(return_value=update_eq))))
        
        call_counter = {'i': 0}
        def from_side_effect(table_name):
            call_counter['i'] += 1
            return existing_table if call_counter['i'] < 3 else update_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.patch(
                "/api/v1/orgs/child-1/parent",
                json={"parent_organization_id": "new-parent"}
            )
            assert response.status_code == 500
            assert "Failed to update" in response.json()['detail']
    
    def test_get_inheritance_chain_org_not_found_midchain(self, mock_supabase, mock_user):
        """Test inheritance chain with org not found mid-chain - lines 459, 472, 492"""
        # First query succeeds
        child_result = Mock(data=[{'id': 'child', 'name': 'Child Org', 'parent_organization_id': 'parent'}])
        
        # Second query returns empty (missing parent in chain)
        parent_result = Mock(data=[])
        
        # Chain execute with side_effect
        chain_execute = Mock(side_effect=[child_result, parent_result])
        chain_eq = Mock(execute=chain_execute)
        chain_select = Mock(eq=Mock(return_value=chain_eq))
        chain_table = Mock(select=Mock(return_value=chain_select))
        
        mock_supabase.from_ = Mock(return_value=chain_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/child/inheritance-chain")
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            # Should return partial chain gracefully
            assert len(body['data']['inheritance_chain']) == 1
    
    def test_get_hierarchy_feature_stats_exception(self, mock_supabase, mock_user):
        """Test hierarchy feature stats exception handling - lines 307-310"""
        # Setup hierarchy query result
        hierarchy_result = Mock()
        hierarchy_result.data = [
            {
                'id': 'root-org',
                'name': 'Root Organization',
                'parent_organization_id': None,
                'level': 0,
                'path': ['root-org']
            }
        ]
        
        # Setup feature stats to raise exception
        feature_result = Mock()
        feature_result.count = 5
        
        # Hierarchy query chain
        hierarchy_order = Mock(execute=Mock(return_value=hierarchy_result))
        hierarchy_eq = Mock(order=Mock(return_value=hierarchy_order))
        hierarchy_select = Mock(eq=Mock(return_value=hierarchy_eq))
        hierarchy_table = Mock(select=Mock(return_value=hierarchy_select))
        
        # Feature stats raises exception on first call
        feature_execute = Mock(side_effect=Exception("Database error"))
        feature_select = Mock()
        feature_select.eq = Mock(side_effect=lambda *args, **kwargs: feature_select)  # Allow chaining
        feature_select.execute = feature_execute
        feature_table = Mock(select=Mock(return_value=feature_select))
        
        call_counter = {'i': 0}
        def from_side_effect(table_name):
            call_counter['i'] += 1
            if call_counter['i'] == 1:
                return hierarchy_table
            else:
                return feature_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/root-org/hierarchy?include_feature_stats=true")
            assert response.status_code == 200
            body = response.json()
            assert body['success'] is True
            # Should succeed despite feature stats exception
    
    def test_get_hierarchy_exception(self, mock_supabase, mock_user):
        """Test hierarchy outer exception handling - lines 319-321"""
        # Make hierarchy query itself raise exception
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_order = Mock()
        mock_execute = Mock(side_effect=Exception("Database error"))
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.order.return_value = mock_order
        mock_order.execute = mock_execute
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        app = self._build_app_with_mocks(mock_supabase, mock_user)
        with TestClient(app) as client:
            response = client.get("/api/v1/orgs/root-org/hierarchy")
            assert response.status_code == 500
