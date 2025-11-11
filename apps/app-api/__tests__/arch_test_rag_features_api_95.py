# apps/app-api/__tests__/test_rag_features_api_95_fixed.py
"""
Comprehensive tests for RAG Features API endpoints - Fixed version
Target: 0% → 85% coverage
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from middleware.permissions import UserRole
from api.rag_features_api import (
    get_rag_feature_catalog,
    get_rag_feature,
    create_rag_feature,
    update_rag_feature,
    delete_rag_feature,
    get_rag_feature_categories,
    RAGFeatureCreateRequest,
    RAGFeatureUpdateRequest
)


class TestRAGFeaturesAPI:
    """Tests for RAG Features API endpoints"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create a mock supabase client"""
        return Mock()
    
    @pytest.fixture
    def mock_user_system_admin(self):
        """Mock user with system admin role"""
        return {
            "id": "user-1",
            "role": "system_admin",
            "organization_id": "org-123"
        }
    
    @pytest.fixture
    def mock_user_org_admin(self):
        """Mock user with org admin role"""
        return {
            "id": "user-2",
            "role": "org_admin",
            "organization_id": "org-123"
        }
    
    @pytest.fixture
    def mock_user_regular(self):
        """Mock user with regular role"""
        return {
            "id": "user-3",
            "role": "user",
            "organization_id": "org-123"
        }
    
    def setup_mock_permission_checker(self, can_view=True, can_manage=True):
        """Helper to setup PermissionChecker mock"""
        class MockPermissionChecker:
            def __init__(self, user_data, supabase=None):
                if supabase is None:
                    from services.supabase_client import get_supabase_client
                    supabase = get_supabase_client()
                self.user_data = user_data
                self.supabase = supabase
                self.can_view_rag_features = Mock(return_value=can_view)
                self.can_manage_rag_features = Mock(return_value=can_manage)
        return MockPermissionChecker
    
    def get_unwrapped_function(self, func):
        """Get the original function bypassing decorators"""
        return getattr(func, '__wrapped__', func)
    
    def setup_require_role_decorator_patch(self):
        """Helper to patch require_role decorator to work with current_user"""
        from functools import wraps
        from middleware.permissions import has_role, get_user_role
        
        def mock_require_role(required_role):
            def decorator(func):
                @wraps(func)
                async def wrapper(*args, **kwargs):
                    # Extract user data from current_user if available, otherwise from user
                    user_data = None
                    if 'current_user' in kwargs:
                        user_data = kwargs['current_user']
                    elif args and hasattr(args[0], 'user'):
                        user_data = args[0].user
                    elif 'user' in kwargs:
                        user_data = kwargs['user']
                    
                    if not user_data:
                        from middleware.permissions import PermissionError
                        raise PermissionError("User data not found in request")
                    
                    if not has_role(user_data, required_role):
                        from middleware.permissions import PermissionError
                        raise PermissionError(
                            f"User role {get_user_role(user_data).value} does not meet "
                            f"required role {required_role.value}"
                        )
                    
                    # Don't pass 'user' to the underlying function if it was added
                    # The function expects current_user, not user
                    kwargs_clean = {k: v for k, v in kwargs.items() if k != 'user' or 'user' not in func.__code__.co_varnames}
                    return await func(*args, **kwargs_clean)
                return wrapper
            return decorator
        return mock_require_role
    
    def setup_query_mocks(self, mock_supabase, query_data, count_result=None):
        """Helper to setup Supabase query mocks"""
        call_count = [0]
        
        # Create count query mock if needed
        if count_result is not None:
            mock_count_query = Mock()
            mock_count_query.eq = Mock(return_value=mock_count_query)
            mock_count_query.execute = Mock(return_value=count_result)
        
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            
            def select_side_effect(*args, **kwargs):
                # Check if this is a count query
                if len(args) > 0 and args[0] == 'count' and kwargs.get('count') == 'exact':
                    return mock_count_query if count_result else Mock()
                # Regular select query
                mock_select = Mock()
                if call_count[0] == 1:
                    # First call - main query with data and range
                    mock_range = Mock()
                    mock_range.execute = Mock(return_value=query_data)
                    mock_select.range = Mock(return_value=mock_range)
                    mock_select.eq = Mock(return_value=mock_select)
                else:
                    # Subsequent calls - just eq support
                    mock_select.eq = Mock(return_value=mock_select)
                    mock_select.execute = Mock(return_value=query_data)
                return mock_select
            
            mock_table.select = Mock(side_effect=select_side_effect)
            mock_table.insert = Mock()
            mock_table.update = Mock()
            mock_table.delete = Mock()
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        return mock_supabase
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_catalog_success(self, mock_supabase, mock_user_system_admin):
        """Test get_rag_feature_catalog success"""
        # Mock features data
        features_data = [
            {
                "id": "feature-1",
                "rag_feature": "sales_intelligence",
                "name": "Sales Intelligence",
                "description": "AI-powered sales insights",
                "category": "sales",
                "is_active": True
            },
            {
                "id": "feature-2",
                "rag_feature": "manager_dashboard",
                "name": "Manager Dashboard",
                "description": "Management tools",
                "category": "manager",
                "is_active": True
            }
        ]
        
        query_result = Mock()
        query_result.data = features_data
        
        # Mock count result
        class CountResult:
            def __init__(self):
                self.count = 2
        count_result = CountResult()
        
        self.setup_query_mocks(mock_supabase, query_result, count_result)
        
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=True)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
                result = await get_rag_feature_catalog(
                    category=None,
                    is_active=None,
                    limit=100,
                    offset=0,
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
                
                assert result.success is True
                assert len(result.data) == 2
                assert result.data[0].rag_feature == "sales_intelligence"
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_catalog_with_filters(self, mock_supabase, mock_user_system_admin):
        """Test get_rag_feature_catalog with category and is_active filters"""
        features_data = [
            {
                "id": "feature-1",
                "rag_feature": "sales_intelligence",
                "name": "Sales Intelligence",
                "category": "sales",
                "is_active": True
            }
        ]
        
        query_result = Mock()
        query_result.data = features_data
        
        class CountResult:
            def __init__(self):
                self.count = 1
        count_result = CountResult()
        
        self.setup_query_mocks(mock_supabase, query_result, count_result)
        
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=True)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
                result = await get_rag_feature_catalog(
                    category="sales",
                    is_active=True,
                    limit=100,
                    offset=0,
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
                
                assert result.success is True
                assert len(result.data) == 1
                assert result.data[0].category == "sales"
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_catalog_no_permission(self, mock_supabase, mock_user_regular):
        """Test get_rag_feature_catalog without permission"""
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=False)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with pytest.raises(HTTPException) as exc_info:
                await get_rag_feature_catalog(
                    category=None,
                    is_active=None,
                    limit=100,
                    offset=0,
                    supabase=mock_supabase,
                    current_user=mock_user_regular
                )
            
            assert exc_info.value.status_code == 403
            assert "Insufficient permissions" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_catalog_no_data(self, mock_supabase, mock_user_system_admin):
        """Test get_rag_feature_catalog when no data returned"""
        query_result = Mock()
        query_result.data = None
        
        self.setup_query_mocks(mock_supabase, query_result)
        
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=True)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
                result = await get_rag_feature_catalog(
                    category=None,
                    is_active=None,
                    limit=100,
                    offset=0,
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
                
                assert result.success is True
                assert len(result.data) == 0
                assert result.total == 0
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_success(self, mock_supabase, mock_user_system_admin):
        """Test get_rag_feature success"""
        feature_data = {
            "id": "feature-1",
            "rag_feature": "sales_intelligence",
            "name": "Sales Intelligence",
            "description": "AI-powered sales insights",
            "category": "sales",
            "is_active": True
        }
        
        query_result = Mock()
        query_result.data = [feature_data]
        
        # Setup mock for single feature query
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_eq.execute = Mock(return_value=query_result)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_table.select = Mock(return_value=mock_select)
        mock_supabase.from_.return_value = mock_table
        
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=True)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
                result = await get_rag_feature(
                    feature_name="sales_intelligence",
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
                
                assert result.success is True
                assert result.data.rag_feature == "sales_intelligence"
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_not_found(self, mock_supabase, mock_user_system_admin):
        """Test get_rag_feature when feature not found"""
        query_result = Mock()
        query_result.data = []
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_eq.execute = Mock(return_value=query_result)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_table.select = Mock(return_value=mock_select)
        mock_supabase.from_.return_value = mock_table
        
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=True)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with pytest.raises(HTTPException) as exc_info:
                await get_rag_feature(
                    feature_name="unknown_feature",
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
            
            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_create_rag_feature_success(self, mock_supabase, mock_user_system_admin):
        """Test create_rag_feature success"""
        feature_request = RAGFeatureCreateRequest(
            rag_feature="new_feature",
            name="New Feature",
            description="A new feature",
            category="sales",
            is_active=True
        )
        
        # Mock existing check - no existing feature
        existing_result = Mock()
        existing_result.data = []
        
        # Mock insert result
        insert_result = Mock()
        insert_result.data = [{
            "id": "feature-new",
            "rag_feature": "new_feature",
            "name": "New Feature",
            "description": "A new feature",
            "category": "sales",
            "is_active": True,
            "created_by": mock_user_system_admin["id"],
            "updated_by": mock_user_system_admin["id"]
        }]
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            
            if call_count[0] == 1:
                # First call - check existing
                mock_select = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=existing_result)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_table.select = Mock(return_value=mock_select)
            else:
                # Second call - insert
                mock_insert = Mock()
                mock_insert.execute = Mock(return_value=insert_result)
                mock_table.insert = Mock(return_value=mock_insert)
            
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        # Use __wrapped__ to bypass decorator and call original function
        original_func = self.get_unwrapped_function(create_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            result = await original_func(
                request=feature_request,
                supabase=mock_supabase,
                current_user=mock_user_system_admin
            )
        
        assert result.success is True
        assert result.data.rag_feature == "new_feature"
    
    @pytest.mark.asyncio
    async def test_create_rag_feature_duplicate(self, mock_supabase, mock_user_system_admin):
        """Test create_rag_feature when feature already exists"""
        feature_request = RAGFeatureCreateRequest(
            rag_feature="existing_feature",
            name="Existing Feature",
            category="sales",
            is_active=True
        )
        
        # Mock existing check - feature exists
        existing_result = Mock()
        existing_result.data = [{"rag_feature": "existing_feature"}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_eq.execute = Mock(return_value=existing_result)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_table.select = Mock(return_value=mock_select)
        mock_supabase.from_.return_value = mock_table
        
        original_func = self.get_unwrapped_function(create_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc_info:
                await original_func(
                    request=feature_request,
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
            
            assert exc_info.value.status_code == 409
            assert "already exists" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_success(self, mock_supabase, mock_user_system_admin):
        """Test update_rag_feature success"""
        feature_request = RAGFeatureUpdateRequest(
            name="Updated Feature",
            description="Updated description",
            is_active=False
        )
        
        # Mock existing check
        existing_result = Mock()
        existing_result.data = [{
            "id": "feature-1",
            "rag_feature": "sales_intelligence",
            "name": "Sales Intelligence",
            "category": "sales"
        }]
        
        # Mock update result
        update_result = Mock()
        update_result.data = [{
            "id": "feature-1",
            "rag_feature": "sales_intelligence",
            "name": "Updated Feature",
            "description": "Updated description",
            "category": "sales",
            "is_active": False,
            "updated_by": mock_user_system_admin["id"]
        }]
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            
            if call_count[0] == 1:
                # First call - check existing
                mock_select = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=existing_result)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_table.select = Mock(return_value=mock_select)
            else:
                # Second call - update
                mock_update = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=update_result)
                mock_update.eq = Mock(return_value=mock_eq)
                mock_table.update = Mock(return_value=mock_update)
            
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        original_func = self.get_unwrapped_function(update_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            result = await original_func(
                feature_name="sales_intelligence",
                request=feature_request,
                supabase=mock_supabase,
                current_user=mock_user_system_admin
            )
            
            assert result.success is True
            assert result.data.name == "Updated Feature"
            assert result.data.is_active is False
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_not_found(self, mock_supabase, mock_user_system_admin):
        """Test update_rag_feature when feature not found"""
        feature_request = RAGFeatureUpdateRequest(
            name="Updated Feature"
        )
        
        # Mock existing check - no feature
        existing_result = Mock()
        existing_result.data = []
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_eq.execute = Mock(return_value=existing_result)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_table.select = Mock(return_value=mock_select)
        mock_supabase.from_.return_value = mock_table
        
        original_func = self.get_unwrapped_function(update_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc_info:
                await original_func(
                    feature_name="unknown_feature",
                    request=feature_request,
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
            
            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_delete_rag_feature_success(self, mock_supabase, mock_user_system_admin):
        """Test delete_rag_feature success"""
        # Mock existing check
        existing_result = Mock()
        existing_result.data = [{"rag_feature": "sales_intelligence"}]
        
        # Mock update result (soft delete)
        update_result = Mock()
        update_result.data = [{"id": "feature-1", "is_active": False}]
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            
            if call_count[0] == 1:
                # First call - check existing
                mock_select = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=existing_result)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_table.select = Mock(return_value=mock_select)
            else:
                # Second call - update (soft delete)
                mock_update = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=update_result)
                mock_update.eq = Mock(return_value=mock_eq)
                mock_table.update = Mock(return_value=mock_update)
            
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        original_func = self.get_unwrapped_function(delete_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            result = await original_func(
                feature_name="sales_intelligence",
                supabase=mock_supabase,
                current_user=mock_user_system_admin
            )
            
            assert result["success"] is True
            assert "deleted" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_rag_feature_not_found(self, mock_supabase, mock_user_system_admin):
        """Test delete_rag_feature when feature not found"""
        # Mock existing check - no feature
        existing_result = Mock()
        existing_result.data = []
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_eq.execute = Mock(return_value=existing_result)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_table.select = Mock(return_value=mock_select)
        mock_supabase.from_.return_value = mock_table
        
        original_func = self.get_unwrapped_function(delete_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc_info:
                await original_func(
                    feature_name="unknown_feature",
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
            
            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_categories_success(self, mock_supabase, mock_user_system_admin):
        """Test get_rag_feature_categories success"""
        # Mock category counts
        category_result = Mock()
        category_result.data = [
            {"category": "sales", "count": 5},
            {"category": "manager", "count": 3},
            {"category": "admin", "count": 2}
        ]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_eq.execute = Mock(return_value=category_result)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_table.select = Mock(return_value=mock_select)
        mock_supabase.from_.return_value = mock_table
        
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=True)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
                result = await get_rag_feature_categories(
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
                
                assert result["success"] is True
                assert "data" in result
                assert result["data"]["sales"]["count"] == 5
                assert result["data"]["manager"]["count"] == 3
                assert result["data"]["admin"]["count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_categories_no_permission(self, mock_supabase, mock_user_regular):
        """Test get_rag_feature_categories without permission"""
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=False)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with pytest.raises(HTTPException) as exc_info:
                await get_rag_feature_categories(
                    supabase=mock_supabase,
                    current_user=mock_user_regular
                )
            
            assert exc_info.value.status_code == 403
            assert "Insufficient permissions" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_create_rag_feature_no_data_returned(self, mock_supabase, mock_user_system_admin):
        """Test create_rag_feature when insert returns no data"""
        feature_request = RAGFeatureCreateRequest(
            rag_feature="new_feature",
            name="New Feature",
            category="sales"
        )
        
        # Mock existing check - no existing feature
        existing_result = Mock()
        existing_result.data = []
        
        # Mock insert result - no data
        insert_result = Mock()
        insert_result.data = None
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            
            if call_count[0] == 1:
                mock_select = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=existing_result)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_table.select = Mock(return_value=mock_select)
            else:
                mock_insert = Mock()
                mock_insert.execute = Mock(return_value=insert_result)
                mock_table.insert = Mock(return_value=mock_insert)
            
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        original_func = self.get_unwrapped_function(create_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc_info:
                await original_func(
                    request=feature_request,
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
            
            assert exc_info.value.status_code == 500
            assert "Failed to create" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_no_data_returned(self, mock_supabase, mock_user_system_admin):
        """Test update_rag_feature when update returns no data"""
        feature_request = RAGFeatureUpdateRequest(
            name="Updated Feature"
        )
        
        # Mock existing check
        existing_result = Mock()
        existing_result.data = [{"rag_feature": "sales_intelligence"}]
        
        # Mock update result - no data (empty list)
        update_result = Mock()
        update_result.data = []  # Empty list
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            
            if call_count[0] == 1:
                mock_select = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=existing_result)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_table.select = Mock(return_value=mock_select)
            else:
                mock_update = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=update_result)
                mock_update.eq = Mock(return_value=mock_eq)
                mock_table.update = Mock(return_value=mock_update)
            
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        original_func = self.get_unwrapped_function(update_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc_info:
                await original_func(
                    feature_name="sales_intelligence",
                    request=feature_request,
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
            
            assert exc_info.value.status_code == 500
            assert "Failed to update" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_delete_rag_feature_no_data_returned(self, mock_supabase, mock_user_system_admin):
        """Test delete_rag_feature when update returns no data"""
        # Mock existing check
        existing_result = Mock()
        existing_result.data = [{"rag_feature": "sales_intelligence"}]
        
        # Mock update result - no data (empty list)
        update_result = Mock()
        update_result.data = []  # Empty list
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            
            if call_count[0] == 1:
                mock_select = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=existing_result)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_table.select = Mock(return_value=mock_select)
            else:
                mock_update = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=update_result)
                mock_update.eq = Mock(return_value=mock_eq)
                mock_table.update = Mock(return_value=mock_update)
            
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        original_func = self.get_unwrapped_function(delete_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc_info:
                await original_func(
                    feature_name="sales_intelligence",
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
            
            assert exc_info.value.status_code == 500
            assert "Failed to delete" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_catalog_exception(self, mock_supabase, mock_user_system_admin):
        """Test get_rag_feature_catalog exception handling"""
        # Mock to raise exception
        mock_table = Mock()
        mock_table.select.side_effect = Exception("DB error")
        mock_supabase.from_.return_value = mock_table
        
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=True)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
                with pytest.raises(HTTPException) as exc_info:
                    await get_rag_feature_catalog(
                        category=None,
                        is_active=None,
                        limit=100,
                        offset=0,
                        supabase=mock_supabase,
                        current_user=mock_user_system_admin
                    )
                
                assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_exception(self, mock_supabase, mock_user_system_admin):
        """Test get_rag_feature exception handling"""
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        mock_supabase.from_.return_value = mock_table
        
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=True)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
                with pytest.raises(HTTPException) as exc_info:
                    await get_rag_feature(
                        feature_name="sales_intelligence",
                        supabase=mock_supabase,
                        current_user=mock_user_system_admin
                    )
                
                assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_create_rag_feature_exception(self, mock_supabase, mock_user_system_admin):
        """Test create_rag_feature exception handling"""
        feature_request = RAGFeatureCreateRequest(
            rag_feature="new_feature",
            name="New Feature",
            category="sales"
        )
        
        # Mock to raise exception during existing check
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            if call_count[0] == 1:
                # First call - check existing, raise exception
                mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("DB error")
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        original_func = self.get_unwrapped_function(create_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc_info:
                await original_func(
                    request=feature_request,
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
            
            assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_exception(self, mock_supabase, mock_user_system_admin):
        """Test update_rag_feature exception handling"""
        feature_request = RAGFeatureUpdateRequest(
            name="Updated Feature"
        )
        
        # Mock to raise exception during existing check
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        mock_supabase.from_.return_value = mock_table
        
        original_func = self.get_unwrapped_function(update_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc_info:
                await original_func(
                    feature_name="sales_intelligence",
                    request=feature_request,
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
            
            assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_delete_rag_feature_exception(self, mock_supabase, mock_user_system_admin):
        """Test delete_rag_feature exception handling"""
        # Mock to raise exception during existing check
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        mock_supabase.from_.return_value = mock_table
        
        original_func = self.get_unwrapped_function(delete_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc_info:
                await original_func(
                    feature_name="sales_intelligence",
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
            
            assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_categories_exception(self, mock_supabase, mock_user_system_admin):
        """Test get_rag_feature_categories exception handling"""
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        mock_supabase.from_.return_value = mock_table
        
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=True)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
                with pytest.raises(HTTPException) as exc_info:
                    await get_rag_feature_categories(
                        supabase=mock_supabase,
                        current_user=mock_user_system_admin
                    )
                
                assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_catalog_count_none(self, mock_supabase, mock_user_system_admin):
        """Test get_rag_feature_catalog when count is None"""
        features_data = [
            {
                "id": "feature-1",
                "rag_feature": "sales_intelligence",
                "name": "Sales Intelligence",
                "category": "sales",
                "is_active": True
            }
        ]
        
        query_result = Mock()
        query_result.data = features_data
        
        # Mock count result with count=None
        class CountResult:
            def __init__(self):
                self.count = None
        count_result = CountResult()
        
        self.setup_query_mocks(mock_supabase, query_result, count_result)
        
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=True)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
                result = await get_rag_feature_catalog(
                    category=None,
                    is_active=None,
                    limit=100,
                    offset=0,
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
                
                assert result.success is True
                # When count is None, it should use len(features)
                assert result.total == 1
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_no_permission(self, mock_supabase, mock_user_regular):
        """Test get_rag_feature without permission (line 175)"""
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=False)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with pytest.raises(HTTPException) as exc_info:
                await get_rag_feature(
                    feature_name="sales_intelligence",
                    supabase=mock_supabase,
                    current_user=mock_user_regular
                )
            
            assert exc_info.value.status_code == 403
            assert "Insufficient permissions" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_with_all_optional_fields(self, mock_supabase, mock_user_system_admin):
        """Test update_rag_feature with all optional fields (lines 287-296)"""
        feature_request = RAGFeatureUpdateRequest(
            name="Updated Feature",
            description="Updated description",
            category="manager",
            icon="new-icon",
            color="new-color",
            is_active=True
        )
        
        # Mock existing check
        existing_result = Mock()
        existing_result.data = [{
            "id": "feature-1",
            "rag_feature": "sales_intelligence",
            "name": "Sales Intelligence",
            "category": "sales"
        }]
        
        # Mock update result
        update_result = Mock()
        update_result.data = [{
            "id": "feature-1",
            "rag_feature": "sales_intelligence",
            "name": "Updated Feature",
            "description": "Updated description",
            "category": "manager",
            "icon": "new-icon",
            "color": "new-color",
            "is_active": True,
            "updated_by": mock_user_system_admin["id"]
        }]
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            
            if call_count[0] == 1:
                # First call - check existing
                mock_select = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=existing_result)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_table.select = Mock(return_value=mock_select)
            else:
                # Second call - update
                mock_update = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=update_result)
                mock_update.eq = Mock(return_value=mock_eq)
                mock_table.update = Mock(return_value=mock_update)
            
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        original_func = self.get_unwrapped_function(update_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            result = await original_func(
                feature_name="sales_intelligence",
                request=feature_request,
                supabase=mock_supabase,
                current_user=mock_user_system_admin
            )
            
            assert result.success is True
            assert result.data.name == "Updated Feature"
            assert result.data.description == "Updated description"
            assert result.data.category == "manager"
            assert result.data.icon == "new-icon"
            assert result.data.color == "new-color"
            assert result.data.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_categories_with_data(self, mock_supabase, mock_user_system_admin):
        """Test get_rag_feature_categories with category data (lines 402-408)"""
        # Mock category counts from database
        category_result = Mock()
        category_result.data = [
            {"category": "sales", "count": 5},
            {"category": "manager", "count": 3},
            {"category": "admin", "count": 2}
        ]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_eq.execute = Mock(return_value=category_result)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_table.select = Mock(return_value=mock_select)
        mock_supabase.from_.return_value = mock_table
        
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=True)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
                result = await get_rag_feature_categories(
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
                
                assert result["success"] is True
                assert "data" in result
                # Verify counts are updated from database
                assert result["data"]["sales"]["count"] == 5
                assert result["data"]["manager"]["count"] == 3
                assert result["data"]["admin"]["count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_categories_with_unknown_category(self, mock_supabase, mock_user_system_admin):
        """Test get_rag_feature_categories with unknown category in data (line 405)"""
        # Mock category counts with an unknown category
        category_result = Mock()
        category_result.data = [
            {"category": "sales", "count": 5},
            {"category": "unknown_category", "count": 10}  # Unknown category
        ]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_eq.execute = Mock(return_value=category_result)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_table.select = Mock(return_value=mock_select)
        mock_supabase.from_.return_value = mock_table
        
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=True)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
                result = await get_rag_feature_categories(
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
                
                assert result["success"] is True
                # Unknown category should be ignored (not in categories dict)
                assert result["data"]["sales"]["count"] == 5
                assert result["data"]["manager"]["count"] == 0
                assert result["data"]["admin"]["count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_rag_feature_categories_with_missing_count(self, mock_supabase, mock_user_system_admin):
        """Test get_rag_feature_categories with missing count field (line 406)"""
        # Mock category counts with missing count field
        category_result = Mock()
        category_result.data = [
            {"category": "sales"},  # No count field
            {"category": "manager", "count": 3}
        ]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_eq.execute = Mock(return_value=category_result)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_table.select = Mock(return_value=mock_select)
        mock_supabase.from_.return_value = mock_table
        
        MockPermissionChecker = self.setup_mock_permission_checker(can_view=True)
        with patch('api.rag_features_api.PermissionChecker', MockPermissionChecker):
            with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
                result = await get_rag_feature_categories(
                    supabase=mock_supabase,
                    current_user=mock_user_system_admin
                )
                
                assert result["success"] is True
                # Missing count should default to 0
                assert result["data"]["sales"]["count"] == 0
                assert result["data"]["manager"]["count"] == 3
    
    @pytest.mark.asyncio
    async def test_update_rag_feature_with_partial_fields(self, mock_supabase, mock_user_system_admin):
        """Test update_rag_feature with only some optional fields"""
        # Test with only name and icon
        feature_request = RAGFeatureUpdateRequest(
            name="Updated Name Only",
            icon="new-icon"
        )
        
        existing_result = Mock()
        existing_result.data = [{
            "id": "feature-1",
            "rag_feature": "sales_intelligence",
            "name": "Sales Intelligence",
            "description": "Original description",
            "category": "sales",
            "icon": "old-icon",
            "color": "old-color",
            "is_active": True
        }]
        
        update_result = Mock()
        update_result.data = [{
            "id": "feature-1",
            "rag_feature": "sales_intelligence",
            "name": "Updated Name Only",
            "description": "Original description",  # Keep original
            "category": "sales",  # Keep original
            "icon": "new-icon",  # Updated
            "color": "old-color",  # Keep original
            "is_active": True,  # Keep original
            "updated_by": mock_user_system_admin["id"]
        }]
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            if call_count[0] == 1:
                mock_select = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=existing_result)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_table.select = Mock(return_value=mock_select)
            else:
                mock_update = Mock()
                mock_eq = Mock()
                mock_eq.execute = Mock(return_value=update_result)
                mock_update.eq = Mock(return_value=mock_eq)
                mock_table.update = Mock(return_value=mock_update)
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        original_func = self.get_unwrapped_function(update_rag_feature)
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            result = await original_func(
                feature_name="sales_intelligence",
                request=feature_request,
                supabase=mock_supabase,
                current_user=mock_user_system_admin
            )
            
            assert result.success is True
            assert result.data.name == "Updated Name Only"
            assert result.data.icon == "new-icon"
            assert result.data.category == "sales"  # Should remain unchanged
    
    def test_get_supabase_dependency(self):
        """Test get_supabase dependency function (line 74)"""
        from api.rag_features_api import get_supabase
        from services.supabase_client import get_supabase_client
        
        with patch('api.rag_features_api.get_supabase_client', return_value=Mock()) as mock_get:
            result = get_supabase()
            mock_get.assert_called_once()
            assert result is not None
    
    def test_get_current_user_dependency(self):
        """Test get_current_user dependency function (line 80)"""
        from api.rag_features_api import get_current_user
        
        user = get_current_user()
        assert user is not None
        assert "id" in user
        assert "role" in user
        assert "organization_id" in user
        assert user["role"] == "system_admin"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=api.rag_features_api', '--cov-report=term-missing'])

