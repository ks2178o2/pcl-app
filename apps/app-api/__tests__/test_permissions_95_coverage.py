"""
Additional tests for Permissions Middleware to reach 95% coverage
Target: 47.65% → 95%
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from middleware.permissions import (
    UserRole, PermissionError, OrganizationAccessError, FeatureAccessError,
    require_role, require_org_access, require_feature_enabled,
    require_any_role, require_system_admin, require_org_admin,
    require_manager_or_higher, require_salesperson_or_higher, require_admin_access,
    PermissionChecker, validate_permissions, get_supabase_client
)


class TestPermissionDecorators:
    """Test permission decorators"""
    
    @pytest.fixture
    def mock_user_request(self):
        """Create a mock request with user data"""
        class MockRequest:
            def __init__(self, user_data):
                self.user = user_data
        
        return MockRequest({'role': 'user', 'organization_id': 'org-123'})
    
    @pytest.mark.asyncio
    async def test_require_role_success(self, mock_user_request):
        """Test require_role decorator allows access for sufficient role"""
        @require_role(UserRole.USER)
        async def test_func(request, *args, **kwargs):
            return {'status': 'ok'}
        
        result = await test_func(mock_user_request)
        assert result['status'] == 'ok'
    
    @pytest.mark.asyncio
    async def test_require_role_failure(self, mock_user_request):
        """Test require_role decorator raises PermissionError for insufficient role"""
        @require_role(UserRole.SYSTEM_ADMIN)
        async def test_func(request, *args, **kwargs):
            return {'status': 'ok'}
        
        with pytest.raises(PermissionError) as exc_info:
            await test_func(mock_user_request)
        
        assert 'system_admin' in str(exc_info.value) or 'required role' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_require_role_with_kwargs(self):
        """Test require_role decorator extracts user from kwargs"""
        @require_role(UserRole.USER)
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        result = await test_func(user={'role': 'user', 'organization_id': 'org-123'})
        assert result['status'] == 'ok'
    
    @pytest.mark.asyncio
    async def test_require_role_user_data_not_found(self):
        """Test require_role raises error when user data not found"""
        @require_role(UserRole.USER)
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        with pytest.raises(PermissionError) as exc_info:
            await test_func('no-user-here')
        
        assert 'not found' in str(exc_info.value) or 'User data' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_require_org_access_success(self):
        """Test require_org_access decorator allows access"""
        @require_org_access(check_parent=False)
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        result = await test_func(
            user={'role': 'user', 'organization_id': 'org-123'},
            organization_id='org-123'
        )
        assert result['status'] == 'ok'
    
    @pytest.mark.asyncio
    async def test_require_org_access_with_request(self, mock_user_request):
        """Test require_org_access with request object"""
        @require_org_access(check_parent=False)
        async def test_func(request, *args, **kwargs):
            return {'status': 'ok'}
        
        result = await test_func(mock_user_request, organization_id='org-123')
        assert result['status'] == 'ok'
    
    @pytest.mark.asyncio
    async def test_require_org_access_data_not_found(self):
        """Test require_org_access raises error when data not found"""
        @require_org_access(check_parent=False)
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        with pytest.raises(OrganizationAccessError) as exc_info:
            await test_func('invalid')
        
        assert 'not found' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_require_feature_enabled_success(self):
        """Test require_feature_enabled decorator"""
        @require_feature_enabled('sales_intelligence')
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        # Mock supabase client
        mock_supabase = Mock()
        toggle_result = Mock()
        toggle_result.data = [{'enabled': True}]
        toggle_eq2 = Mock()
        toggle_eq2.execute = Mock(return_value=toggle_result)
        toggle_eq1 = Mock()
        toggle_eq1.eq = Mock(return_value=toggle_eq2)
        toggle_select = Mock()
        toggle_select.eq = Mock(return_value=toggle_eq1)
        toggle_table = Mock()
        toggle_table.select = Mock(return_value=toggle_select)
        mock_supabase.from_ = Mock(return_value=toggle_table)
        
        # Mock can_access_rag_feature to avoid calling real function
        with patch('middleware.permissions.can_access_rag_feature', return_value=True):
            result = await test_func(
                user={'role': 'user', 'organization_id': 'org-123'},
                organization_id='org-123'
            )
        
        assert result['status'] == 'ok'
    
    @pytest.mark.asyncio
    async def test_require_feature_enabled_data_not_found(self):
        """Test require_feature_enabled raises error when data not found"""
        @require_feature_enabled('sales_intelligence')
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        with pytest.raises(FeatureAccessError) as exc_info:
            await test_func('invalid')
        
        assert 'not found' in str(exc_info.value)
    
    def test_require_system_admin_convenience(self):
        """Test require_system_admin convenience decorator"""
        @require_system_admin
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        assert hasattr(test_func, '__wrapped__')
    
    def test_require_org_admin_convenience(self):
        """Test require_org_admin convenience decorator"""
        @require_org_admin
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        assert hasattr(test_func, '__wrapped__')
    
    def test_require_manager_or_higher_convenience(self):
        """Test require_manager_or_higher convenience decorator"""
        @require_manager_or_higher
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        assert hasattr(test_func, '__wrapped__')
    
    def test_require_salesperson_or_higher_convenience(self):
        """Test require_salesperson_or_higher convenience decorator"""
        @require_salesperson_or_higher
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        assert hasattr(test_func, '__wrapped__')
    
    def test_require_admin_access_convenience(self):
        """Test require_admin_access convenience decorator"""
        @require_admin_access
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        assert hasattr(test_func, '__wrapped__')
    
    @pytest.mark.asyncio
    async def test_require_any_role_success(self):
        """Test require_any_role with matching role"""
        @require_any_role([UserRole.MANAGER, UserRole.ORG_ADMIN])
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        result = await test_func(user={'role': 'manager', 'organization_id': 'org-123'})
        assert result['status'] == 'ok'
    
    @pytest.mark.asyncio
    async def test_require_any_role_failure(self):
        """Test require_any_role raises error for non-matching role"""
        @require_any_role([UserRole.MANAGER, UserRole.ORG_ADMIN])
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        with pytest.raises(PermissionError) as exc_info:
            await test_func(user={'role': 'user', 'organization_id': 'org-123'})
        
        assert 'not in required roles' in str(exc_info.value)


class TestPermissionCheckerExtended:
    """Extended tests for PermissionChecker class"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create mock supabase client"""
        return Mock()
    
    def test_permission_checker_initialization(self, mock_supabase):
        """Test PermissionChecker initialization"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        assert checker.user_data == user_data
        assert checker.user_role == UserRole.USER
        assert checker.user_org_id == 'org-123'
        assert checker.supabase == mock_supabase
    
    def test_can_manage_rag_features_org_admin(self, mock_supabase):
        """Test org admin can manage features for their own org"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        assert checker.can_manage_rag_features('org-123') is True
        assert checker.can_manage_rag_features('org-456') is False
    
    def test_can_view_rag_features_regular_user(self, mock_supabase):
        """Test regular user can view features in own org"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        assert checker.can_view_rag_features('org-123') is True
        assert checker.can_view_rag_features('org-456') is False
    
    def test_can_view_rag_features_system_admin(self, mock_supabase):
        """Test system admin can view any org's features"""
        user_data = {'role': 'system_admin'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        assert checker.can_view_rag_features('org-999') is True
    
    def test_can_use_rag_feature_system_admin(self, mock_supabase):
        """Test system admin can use any feature"""
        user_data = {'role': 'system_admin'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        assert checker.can_use_rag_feature('sales_intelligence', 'org-999') is True
    
    def test_can_use_rag_feature_different_org(self, mock_supabase):
        """Test cannot use feature in different org"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        assert checker.can_use_rag_feature('sales_intelligence', 'org-456') is False
    
    def test_can_use_rag_feature_enabled_in_toggle(self, mock_supabase):
        """Test can use feature when enabled in toggle"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        toggle_result = Mock()
        toggle_result.data = [{'enabled': True}]
        
        toggle_eq2 = Mock()
        toggle_eq2.execute = Mock(return_value=toggle_result)
        toggle_eq1 = Mock()
        toggle_eq1.eq = Mock(return_value=toggle_eq2)
        toggle_select = Mock()
        toggle_select.eq = Mock(return_value=toggle_eq1)
        toggle_table = Mock()
        toggle_table.select = Mock(return_value=toggle_select)
        mock_supabase.from_ = Mock(return_value=toggle_table)
        
        assert checker.can_use_rag_feature('sales_intelligence', 'org-123') is True
    
    def test_can_use_rag_feature_default_enabled(self, mock_supabase):
        """Test can use feature when default enabled in metadata"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        # No toggle but default enabled
        no_toggle_result = Mock()
        no_toggle_result.data = []
        
        metadata_result = Mock()
        metadata_result.data = [{'default_enabled': True}]
        
        toggle_eq2 = Mock()
        toggle_eq2.execute = Mock(return_value=no_toggle_result)
        toggle_eq1 = Mock()
        toggle_eq1.eq = Mock(return_value=toggle_eq2)
        toggle_select = Mock()
        toggle_select.eq = Mock(return_value=toggle_eq1)
        toggle_table = Mock()
        toggle_table.select = Mock(return_value=toggle_select)
        
        metadata_eq1 = Mock()
        metadata_eq1.execute = Mock(return_value=metadata_result)
        metadata_select = Mock()
        metadata_select.eq = Mock(return_value=metadata_eq1)
        metadata_table = Mock()
        metadata_table.select = Mock(return_value=metadata_select)
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if table_name == 'organization_rag_toggles':
                return toggle_table
            else:
                return metadata_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        assert checker.can_use_rag_feature('sales_intelligence', 'org-123') is True
    
    def test_can_use_rag_feature_error_handling(self, mock_supabase):
        """Test error handling in can_use_rag_feature"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        mock_supabase.from_.return_value.select.return_value.eq.side_effect = Exception("DB error")
        
        assert checker.can_use_rag_feature('sales_intelligence', 'org-123') is False
    
    def test_can_access_organization_hierarchy_org_admin_own_org(self, mock_supabase):
        """Test org admin can access hierarchy of own org"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        assert checker.can_access_organization_hierarchy('org-123') is True
        assert checker.can_access_organization_hierarchy('org-456') is False
    
    def test_get_accessible_organizations_system_admin_success(self, mock_supabase):
        """Test system admin gets all orgs successfully"""
        user_data = {'role': 'system_admin'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        org_result = Mock()
        org_result.data = [{'id': 'org-1'}, {'id': 'org-2'}]
        mock_supabase.from_.return_value.select.return_value.execute.return_value = org_result
        
        orgs = checker.get_accessible_organizations()
        assert 'org-1' in orgs
        assert 'org-2' in orgs
    
    def test_get_accessible_organizations_error_handling(self, mock_supabase):
        """Test error handling when getting all orgs"""
        user_data = {'role': 'system_admin'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        mock_supabase.from_.return_value.select.return_value.execute.side_effect = Exception("DB error")
        
        orgs = checker.get_accessible_organizations()
        assert orgs == []
    
    def test_get_accessible_organizations_no_org_id(self, mock_supabase):
        """Test get accessible orgs when user has no org ID"""
        user_data = {'role': 'user'}  # No organization_id
        checker = PermissionChecker(user_data, mock_supabase)
        
        orgs = checker.get_accessible_organizations()
        assert orgs == []


class TestValidatePermissionsFunction:
    """Test validate_permissions function with various actions"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create mock supabase client"""
        return Mock()
    
    def test_validate_manage_rag_features_action(self, mock_supabase):
        """Test validate manage_rag_features action"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        
        with patch('middleware.permissions.PermissionChecker') as MockChecker:
            mock_checker = MockChecker.return_value
            mock_checker.can_manage_rag_features.return_value = True
            
            result = validate_permissions(user_data, 'manage_rag_features', 'org-123', supabase=mock_supabase)
            assert result is True
    
    def test_validate_view_rag_features_action(self, mock_supabase):
        """Test validate view_rag_features action"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        with patch('middleware.permissions.PermissionChecker') as MockChecker:
            mock_checker = MockChecker.return_value
            mock_checker.can_view_rag_features.return_value = True
            
            result = validate_permissions(user_data, 'view_rag_features', 'org-123', supabase=mock_supabase)
            assert result is True
    
    def test_validate_use_rag_feature_action_success(self, mock_supabase):
        """Test validate use_rag_feature action with feature name"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        with patch('middleware.permissions.PermissionChecker') as MockChecker:
            mock_checker = MockChecker.return_value
            mock_checker.can_use_rag_feature.return_value = True
            
            result = validate_permissions(user_data, 'use_rag_feature', 'org-123', 
                                         feature_name='sales_intelligence', supabase=mock_supabase)
            assert result is True
    
    def test_validate_use_rag_feature_action_no_feature_name(self, mock_supabase):
        """Test validate use_rag_feature action without feature name"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        result = validate_permissions(user_data, 'use_rag_feature', 'org-123', 
                                     feature_name=None, supabase=mock_supabase)
        assert result is False
    
    def test_validate_access_hierarchy_action(self, mock_supabase):
        """Test validate access_hierarchy action"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        
        with patch('middleware.permissions.PermissionChecker') as MockChecker:
            mock_checker = MockChecker.return_value
            mock_checker.can_access_organization_hierarchy.return_value = True
            
            result = validate_permissions(user_data, 'access_hierarchy', 'org-123', supabase=mock_supabase)
            assert result is True
    
    def test_validate_invalid_action(self, mock_supabase):
        """Test validate invalid action returns False"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        result = validate_permissions(user_data, 'invalid_action', 'org-123', supabase=mock_supabase)
        assert result is False
    
    def test_validate_permissions_without_supabase(self):
        """Test validate_permissions gets supabase client when not provided"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        
        mock_supabase = Mock()
        with patch('middleware.permissions.get_supabase_client', return_value=mock_supabase):
            with patch('middleware.permissions.PermissionChecker') as MockChecker:
                mock_checker = MockChecker.return_value
                mock_checker.can_manage_rag_features.return_value = True
                
                result = validate_permissions(user_data, 'manage_rag_features', 'org-123')
                assert result is True


class TestMissingLinesTargeted:
    """Tests for specific missing coverage lines to reach 95%"""
    
    @pytest.mark.asyncio
    async def test_require_feature_enabled_with_request_object(self):
        """Test require_feature_enabled with request object - line 181-182"""
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'user', 'organization_id': 'org-123'}
                self.organization_id = 'org-123'
        
        @require_feature_enabled('sales_intelligence')
        async def test_func(request, *args, **kwargs):
            return {'status': 'ok'}
        
        with patch('middleware.permissions.can_access_rag_feature', return_value=True):
            result = await test_func(MockRequest())
        
        assert result['status'] == 'ok'
    
    @pytest.mark.asyncio
    async def test_require_feature_enabled_access_denied(self):
        """Test require_feature_enabled raises FeatureAccessError when access denied - line 190"""
        @require_feature_enabled('sales_intelligence')
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        with patch('middleware.permissions.can_access_rag_feature', return_value=False):
            with pytest.raises(FeatureAccessError) as exc_info:
                await test_func(
                    user={'role': 'user', 'organization_id': 'org-123'},
                    organization_id='org-123'
                )
        
        assert 'cannot access RAG feature' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_require_any_role_with_args_hasattr(self):
        """Test require_any_role extracts user from args with hasattr - line 205"""
        class MockRequest:
            def __init__(self):
                self.user = {'role': 'manager', 'organization_id': 'org-123'}
        
        @require_any_role([UserRole.MANAGER, UserRole.ORG_ADMIN])
        async def test_func(request, *args, **kwargs):
            return {'status': 'ok'}
        
        result = await test_func(MockRequest())
        assert result['status'] == 'ok'
    
    @pytest.mark.asyncio
    async def test_require_any_role_user_data_not_found(self):
        """Test require_any_role raises PermissionError - line 209"""
        @require_any_role([UserRole.MANAGER])
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        with pytest.raises(PermissionError) as exc_info:
            await test_func('no-user-here')
        
        assert 'not found' in str(exc_info.value) or 'User data' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_require_org_access_calls_can_access_with_supabase(self):
        """Test require_org_access calls can_access_organization properly - line 166"""
        @require_org_access(check_parent=True)
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        with patch('middleware.permissions.can_access_organization', return_value=True):
            result = await test_func(
                user={'role': 'user', 'organization_id': 'org-123'},
                organization_id='org-456'
            )
        
        assert result['status'] == 'ok'
    
    def test_can_access_rag_feature_no_toggle_no_metadata(self):
        """Test can_access_rag_feature when no toggle and no metadata - line 122"""
        from middleware.permissions import can_access_rag_feature
        
        mock_supabase = Mock()
        
        # No toggle found
        no_toggle_result = Mock()
        no_toggle_result.data = []
        
        # No metadata found
        no_metadata_result = Mock()
        no_metadata_result.data = []
        
        toggle_eq2 = Mock()
        toggle_eq2.execute = Mock(return_value=no_toggle_result)
        toggle_eq1 = Mock()
        toggle_eq1.eq = Mock(return_value=toggle_eq2)
        toggle_select = Mock()
        toggle_select.eq = Mock(return_value=toggle_eq1)
        toggle_table = Mock()
        toggle_table.select = Mock(return_value=toggle_select)
        
        metadata_eq1 = Mock()
        metadata_eq1.execute = Mock(return_value=no_metadata_result)
        metadata_select = Mock()
        metadata_select.eq = Mock(return_value=metadata_eq1)
        metadata_table = Mock()
        metadata_table.select = Mock(return_value=metadata_select)
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if table_name == 'organization_rag_toggles':
                return toggle_table
            else:
                return metadata_table
        
        mock_supabase.from_ = Mock(side_effect=from_side_effect)
        
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        result = can_access_rag_feature(user_data, 'sales_intelligence', 'org-123', mock_supabase)
        assert result is False

