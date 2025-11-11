# apps/app-api/__tests__/test_permissions_middleware_database_paths_95.py
"""
Additional tests for Permissions Middleware to reach 95% coverage
Focusing on database query paths and PermissionChecker methods
"""

import pytest
from unittest.mock import Mock, patch
from middleware.permissions import (
    can_access_organization,
    can_access_rag_feature,
    PermissionChecker,
    UserRole,
    OrganizationAccessError,
    FeatureAccessError,
    validate_permissions
)


class TestPermissionsDatabasePaths:
    """Tests for database query paths in permission functions"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create a mock supabase client"""
        return Mock()
    
    def test_can_access_organization_check_parent_child_exists(self, mock_supabase):
        """Test can_access_organization with check_parent when child exists - lines 88-91"""
        user_data = {'role': 'org_admin', 'organization_id': 'parent-123'}
        target_org_id = 'child-123'
        
        # Mock result - child organization exists with parent
        result = Mock()
        result.data = [{'id': 'child-123'}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        can_access = can_access_organization(user_data, target_org_id, mock_supabase, check_parent=True)
        assert can_access is True
    
    def test_can_access_organization_check_parent_child_not_exists(self, mock_supabase):
        """Test can_access_organization with check_parent when child doesn't exist - lines 88-91"""
        user_data = {'role': 'org_admin', 'organization_id': 'parent-123'}
        target_org_id = 'child-123'
        
        # Mock result - no child organization
        result = Mock()
        result.data = []
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        can_access = can_access_organization(user_data, target_org_id, mock_supabase, check_parent=True)
        assert can_access is False
    
    def test_can_access_organization_check_parent_exception(self, mock_supabase):
        """Test can_access_organization with check_parent when exception occurs - lines 88-94"""
        user_data = {'role': 'org_admin', 'organization_id': 'parent-123'}
        target_org_id = 'child-123'
        
        # Mock to raise exception
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        mock_supabase.from_.return_value = mock_table
        
        can_access = can_access_organization(user_data, target_org_id, mock_supabase, check_parent=True)
        assert can_access is False
    
    def test_can_access_rag_feature_toggle_enabled(self, mock_supabase):
        """Test can_access_rag_feature when toggle exists and is enabled - lines 113-117"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        feature_name = 'sales_intelligence'
        organization_id = 'org-123'
        
        # Mock toggle result - enabled
        toggle_result = Mock()
        toggle_result.data = [{'enabled': True}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = toggle_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        can_access = can_access_rag_feature(user_data, feature_name, organization_id, mock_supabase)
        assert can_access is True
    
    def test_can_access_rag_feature_toggle_disabled(self, mock_supabase):
        """Test can_access_rag_feature when toggle exists but is disabled - lines 113-117"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        feature_name = 'sales_intelligence'
        organization_id = 'org-123'
        
        # Mock toggle result - disabled
        toggle_result = Mock()
        toggle_result.data = [{'enabled': False}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = toggle_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        can_access = can_access_rag_feature(user_data, feature_name, organization_id, mock_supabase)
        assert can_access is False
    
    def test_can_access_rag_feature_no_toggle_check_metadata_enabled(self, mock_supabase):
        """Test can_access_rag_feature when no toggle, check metadata default_enabled=True - lines 113-121"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        feature_name = 'sales_intelligence'
        organization_id = 'org-123'
        
        # Mock toggle result - no data
        toggle_result = Mock()
        toggle_result.data = []
        
        # Mock metadata result - default_enabled=True
        metadata_result = Mock()
        metadata_result.data = [{'default_enabled': True}]
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            mock_select = Mock()
            
            if call_count[0] == 1:  # organization_rag_toggles
                mock_eq1 = Mock()
                mock_eq2 = Mock()
                mock_execute = Mock()
                mock_execute.return_value = toggle_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq1)
                mock_eq1.eq = Mock(return_value=mock_eq2)
                mock_eq2.execute = mock_execute
            else:  # rag_feature_metadata
                mock_eq = Mock()
                mock_execute = Mock()
                mock_execute.return_value = metadata_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_eq.execute = mock_execute
            
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        can_access = can_access_rag_feature(user_data, feature_name, organization_id, mock_supabase)
        assert can_access is True
    
    def test_can_access_rag_feature_no_toggle_check_metadata_disabled(self, mock_supabase):
        """Test can_access_rag_feature when no toggle, check metadata default_enabled=False - lines 113-122"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        feature_name = 'sales_intelligence'
        organization_id = 'org-123'
        
        # Mock toggle result - no data
        toggle_result = Mock()
        toggle_result.data = []
        
        # Mock metadata result - default_enabled=False
        metadata_result = Mock()
        metadata_result.data = [{'default_enabled': False}]
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            mock_select = Mock()
            
            if call_count[0] == 1:  # organization_rag_toggles
                mock_eq1 = Mock()
                mock_eq2 = Mock()
                mock_execute = Mock()
                mock_execute.return_value = toggle_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq1)
                mock_eq1.eq = Mock(return_value=mock_eq2)
                mock_eq2.execute = mock_execute
            else:  # rag_feature_metadata
                mock_eq = Mock()
                mock_execute = Mock()
                mock_execute.return_value = metadata_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_eq.execute = mock_execute
            
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        can_access = can_access_rag_feature(user_data, feature_name, organization_id, mock_supabase)
        assert can_access is False
    
    def test_can_access_rag_feature_no_toggle_no_metadata(self, mock_supabase):
        """Test can_access_rag_feature when no toggle and no metadata - lines 113-122"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        feature_name = 'sales_intelligence'
        organization_id = 'org-123'
        
        # Mock toggle result - no data
        toggle_result = Mock()
        toggle_result.data = []
        
        # Mock metadata result - no data
        metadata_result = Mock()
        metadata_result.data = []
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            mock_select = Mock()
            
            if call_count[0] == 1:  # organization_rag_toggles
                mock_eq1 = Mock()
                mock_eq2 = Mock()
                mock_execute = Mock()
                mock_execute.return_value = toggle_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq1)
                mock_eq1.eq = Mock(return_value=mock_eq2)
                mock_eq2.execute = mock_execute
            else:  # rag_feature_metadata
                mock_eq = Mock()
                mock_execute = Mock()
                mock_execute.return_value = metadata_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_eq.execute = mock_execute
            
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        can_access = can_access_rag_feature(user_data, feature_name, organization_id, mock_supabase)
        assert can_access is False
    
    def test_can_access_rag_feature_exception(self, mock_supabase):
        """Test can_access_rag_feature when exception occurs - lines 113-125"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        feature_name = 'sales_intelligence'
        organization_id = 'org-123'
        
        # Mock to raise exception
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        mock_supabase.from_.return_value = mock_table
        
        can_access = can_access_rag_feature(user_data, feature_name, organization_id, mock_supabase)
        assert can_access is False


class TestPermissionCheckerDatabasePaths:
    """Tests for PermissionChecker database query paths"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create a mock supabase client"""
        return Mock()
    
    def test_permission_checker_can_use_rag_feature_toggle_enabled(self, mock_supabase):
        """Test PermissionChecker.can_use_rag_feature when toggle is enabled - lines 287-293"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        # Mock toggle result - enabled
        toggle_result = Mock()
        toggle_result.data = [{'enabled': True}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = toggle_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        can_use = checker.can_use_rag_feature('sales_intelligence', 'org-123')
        assert can_use is True
    
    def test_permission_checker_can_use_rag_feature_toggle_disabled(self, mock_supabase):
        """Test PermissionChecker.can_use_rag_feature when toggle is disabled - lines 287-293"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        # Mock toggle result - disabled
        toggle_result = Mock()
        toggle_result.data = [{'enabled': False}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = toggle_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        can_use = checker.can_use_rag_feature('sales_intelligence', 'org-123')
        assert can_use is False
    
    def test_permission_checker_can_use_rag_feature_no_toggle_metadata_enabled(self, mock_supabase):
        """Test PermissionChecker.can_use_rag_feature when no toggle, metadata default_enabled=True - lines 287-293"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        # Mock toggle result - no data
        toggle_result = Mock()
        toggle_result.data = []
        
        # Mock metadata result - default_enabled=True
        metadata_result = Mock()
        metadata_result.data = [{'default_enabled': True}]
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            mock_select = Mock()
            
            if call_count[0] == 1:  # organization_rag_toggles
                mock_eq1 = Mock()
                mock_eq2 = Mock()
                mock_execute = Mock()
                mock_execute.return_value = toggle_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq1)
                mock_eq1.eq = Mock(return_value=mock_eq2)
                mock_eq2.execute = mock_execute
            else:  # rag_feature_metadata
                mock_eq = Mock()
                mock_execute = Mock()
                mock_execute.return_value = metadata_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_eq.execute = mock_execute
            
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        can_use = checker.can_use_rag_feature('sales_intelligence', 'org-123')
        assert can_use is True
    
    def test_permission_checker_can_use_rag_feature_no_toggle_metadata_disabled(self, mock_supabase):
        """Test PermissionChecker.can_use_rag_feature when no toggle, metadata default_enabled=False - lines 287-293"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        # Mock toggle result - no data
        toggle_result = Mock()
        toggle_result.data = []
        
        # Mock metadata result - default_enabled=False
        metadata_result = Mock()
        metadata_result.data = [{'default_enabled': False}]
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            mock_select = Mock()
            
            if call_count[0] == 1:  # organization_rag_toggles
                mock_eq1 = Mock()
                mock_eq2 = Mock()
                mock_execute = Mock()
                mock_execute.return_value = toggle_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq1)
                mock_eq1.eq = Mock(return_value=mock_eq2)
                mock_eq2.execute = mock_execute
            else:  # rag_feature_metadata
                mock_eq = Mock()
                mock_execute = Mock()
                mock_execute.return_value = metadata_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_eq.execute = mock_execute
            
            return mock_table
        
        mock_supabase.from_.side_effect = from_side_effect
        
        can_use = checker.can_use_rag_feature('sales_intelligence', 'org-123')
        assert can_use is False
    
    def test_permission_checker_can_use_rag_feature_exception(self, mock_supabase):
        """Test PermissionChecker.can_use_rag_feature when exception occurs - lines 287-293"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        # Mock to raise exception
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        mock_supabase.from_.return_value = mock_table
        
        can_use = checker.can_use_rag_feature('sales_intelligence', 'org-123')
        assert can_use is False
    
    def test_permission_checker_get_accessible_organizations_system_admin_with_orgs(self, mock_supabase):
        """Test PermissionChecker.get_accessible_organizations for system admin with orgs - lines 307-314"""
        user_data = {'role': 'system_admin'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        # Mock result - organizations exist
        result = Mock()
        result.data = [{'id': 'org-1'}, {'id': 'org-2'}, {'id': 'org-3'}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_execute = Mock()
        mock_execute.return_value = result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        orgs = checker.get_accessible_organizations()
        assert orgs == ['org-1', 'org-2', 'org-3']
    
    def test_permission_checker_get_accessible_organizations_system_admin_no_orgs(self, mock_supabase):
        """Test PermissionChecker.get_accessible_organizations for system admin with no orgs - lines 307-314"""
        user_data = {'role': 'system_admin'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        # Mock result - no organizations
        result = Mock()
        result.data = []
        
        mock_table = Mock()
        mock_select = Mock()
        mock_execute = Mock()
        mock_execute.return_value = result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        orgs = checker.get_accessible_organizations()
        assert orgs == []
    
    def test_permission_checker_get_accessible_organizations_system_admin_exception(self, mock_supabase):
        """Test PermissionChecker.get_accessible_organizations for system admin when exception occurs - lines 307-314"""
        user_data = {'role': 'system_admin'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        # Mock to raise exception
        mock_table = Mock()
        mock_table.select.return_value.execute.side_effect = Exception("DB error")
        mock_supabase.from_.return_value = mock_table
        
        orgs = checker.get_accessible_organizations()
        assert orgs == []
    
    def test_permission_checker_get_accessible_organizations_org_admin(self, mock_supabase):
        """Test PermissionChecker.get_accessible_organizations for org admin - lines 316-317"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        orgs = checker.get_accessible_organizations()
        assert orgs == ['org-123']
    
    def test_permission_checker_get_accessible_organizations_no_org_id(self, mock_supabase):
        """Test PermissionChecker.get_accessible_organizations when no org_id - lines 319"""
        user_data = {'role': 'user'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        orgs = checker.get_accessible_organizations()
        assert orgs == []


class TestPermissionCheckerMethods:
    """Tests for PermissionChecker methods"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create a mock supabase client"""
        return Mock()
    
    def test_permission_checker_can_manage_rag_features_system_admin(self, mock_supabase):
        """Test PermissionChecker.can_manage_rag_features for system admin - line 255"""
        user_data = {'role': 'system_admin'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        can_manage = checker.can_manage_rag_features('any-org-id')
        assert can_manage is True
    
    def test_permission_checker_can_manage_rag_features_org_admin_same_org(self, mock_supabase):
        """Test PermissionChecker.can_manage_rag_features for org admin same org - line 257-258"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        can_manage = checker.can_manage_rag_features('org-123')
        assert can_manage is True
    
    def test_permission_checker_can_manage_rag_features_org_admin_different_org(self, mock_supabase):
        """Test PermissionChecker.can_manage_rag_features for org admin different org - line 260"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        can_manage = checker.can_manage_rag_features('org-456')
        assert can_manage is False
    
    def test_permission_checker_can_view_rag_features_system_admin(self, mock_supabase):
        """Test PermissionChecker.can_view_rag_features for system admin - line 264-265"""
        user_data = {'role': 'system_admin'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        can_view = checker.can_view_rag_features('any-org-id')
        assert can_view is True
    
    def test_permission_checker_can_view_rag_features_org_admin(self, mock_supabase):
        """Test PermissionChecker.can_view_rag_features for org admin - line 264-265"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        can_view = checker.can_view_rag_features('any-org-id')
        assert can_view is True
    
    def test_permission_checker_can_view_rag_features_same_org(self, mock_supabase):
        """Test PermissionChecker.can_view_rag_features for user same org - line 267-268"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        can_view = checker.can_view_rag_features('org-123')
        assert can_view is True
    
    def test_permission_checker_can_view_rag_features_different_org(self, mock_supabase):
        """Test PermissionChecker.can_view_rag_features for user different org - line 270"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        can_view = checker.can_view_rag_features('org-456')
        assert can_view is False
    
    def test_permission_checker_can_use_rag_feature_system_admin(self, mock_supabase):
        """Test PermissionChecker.can_use_rag_feature for system admin - line 274-275"""
        user_data = {'role': 'system_admin'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        can_use = checker.can_use_rag_feature('any-feature', 'any-org-id')
        assert can_use is True
    
    def test_permission_checker_can_use_rag_feature_different_org(self, mock_supabase):
        """Test PermissionChecker.can_use_rag_feature for user different org - line 277-278"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        can_use = checker.can_use_rag_feature('any-feature', 'org-456')
        assert can_use is False
    
    def test_permission_checker_can_access_organization_hierarchy_system_admin(self, mock_supabase):
        """Test PermissionChecker.can_access_organization_hierarchy for system admin - line 297-298"""
        user_data = {'role': 'system_admin'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        can_access = checker.can_access_organization_hierarchy('any-org-id')
        assert can_access is True
    
    def test_permission_checker_can_access_organization_hierarchy_org_admin_same_org(self, mock_supabase):
        """Test PermissionChecker.can_access_organization_hierarchy for org admin same org - line 300-301"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        can_access = checker.can_access_organization_hierarchy('org-123')
        assert can_access is True
    
    def test_permission_checker_can_access_organization_hierarchy_org_admin_different_org(self, mock_supabase):
        """Test PermissionChecker.can_access_organization_hierarchy for org admin different org - line 303"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        can_access = checker.can_access_organization_hierarchy('org-456')
        assert can_access is False


class TestValidatePermissions:
    """Tests for validate_permissions function"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create a mock supabase client"""
        return Mock()
    
    def test_validate_permissions_manage_rag_features(self, mock_supabase):
        """Test validate_permissions for manage_rag_features action"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        
        with patch('middleware.permissions.get_supabase_client', return_value=mock_supabase):
            result = validate_permissions(user_data, 'manage_rag_features', 'org-123', supabase=mock_supabase)
            assert result is True
    
    def test_validate_permissions_view_rag_features(self, mock_supabase):
        """Test validate_permissions for view_rag_features action"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        
        with patch('middleware.permissions.get_supabase_client', return_value=mock_supabase):
            result = validate_permissions(user_data, 'view_rag_features', 'org-123', supabase=mock_supabase)
            assert result is True
    
    def test_validate_permissions_use_rag_feature_with_feature(self, mock_supabase):
        """Test validate_permissions for use_rag_feature action with feature name"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        # Mock toggle result - enabled
        toggle_result = Mock()
        toggle_result.data = [{'enabled': True}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = toggle_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        with patch('middleware.permissions.get_supabase_client', return_value=mock_supabase):
            result = validate_permissions(user_data, 'use_rag_feature', 'org-123', feature_name='sales_intelligence', supabase=mock_supabase)
            assert result is True
    
    def test_validate_permissions_use_rag_feature_without_feature(self, mock_supabase):
        """Test validate_permissions for use_rag_feature action without feature name - line 334-335"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        with patch('middleware.permissions.get_supabase_client', return_value=mock_supabase):
            result = validate_permissions(user_data, 'use_rag_feature', 'org-123', feature_name=None, supabase=mock_supabase)
            assert result is False
    
    def test_validate_permissions_access_hierarchy(self, mock_supabase):
        """Test validate_permissions for access_hierarchy action"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        
        with patch('middleware.permissions.get_supabase_client', return_value=mock_supabase):
            result = validate_permissions(user_data, 'access_hierarchy', 'org-123', supabase=mock_supabase)
            assert result is True
    
    def test_validate_permissions_unknown_action(self, mock_supabase):
        """Test validate_permissions for unknown action - line 340"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        
        with patch('middleware.permissions.get_supabase_client', return_value=mock_supabase):
            result = validate_permissions(user_data, 'unknown_action', 'org-123', supabase=mock_supabase)
            assert result is False
    
    def test_validate_permissions_no_supabase_uses_get_client(self, mock_supabase):
        """Test validate_permissions when supabase is None, uses get_supabase_client - line 325-326"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        
        with patch('middleware.permissions.get_supabase_client', return_value=mock_supabase):
            result = validate_permissions(user_data, 'manage_rag_features', 'org-123', supabase=None)
            assert result is True


class TestPermissionsDecoratorErrorPaths:
    """Tests for decorator error paths"""
    
    @pytest.fixture
    def mock_supabase_for_metadata(self):
        """Create a mock supabase client for metadata tests"""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_require_org_access_error_path_no_user_no_org(self):
        """Test require_org_access decorator error path - line 163"""
        from middleware.permissions import require_org_access, OrganizationAccessError
        
        @require_org_access()
        async def test_func():
            return "success"
        
        # Call without user or organization_id - should raise OrganizationAccessError
        with pytest.raises(OrganizationAccessError, match="organization ID not found"):
            await test_func()
    
    @pytest.mark.asyncio
    async def test_require_feature_enabled_error_path_no_user_no_org(self):
        """Test require_feature_enabled decorator error path - line 187"""
        from middleware.permissions import require_feature_enabled, FeatureAccessError
        
        @require_feature_enabled('sales_intelligence')
        async def test_func():
            return "success"
        
        # Call without user or organization_id - should raise FeatureAccessError
        with pytest.raises(FeatureAccessError, match="organization ID not found"):
            await test_func()
    
    @pytest.mark.asyncio
    async def test_require_any_role_error_path_no_user(self):
        """Test require_any_role decorator error path - lines 206-209"""
        from middleware.permissions import require_any_role, UserRole, PermissionError
        
        @require_any_role([UserRole.MANAGER, UserRole.ORG_ADMIN])
        async def test_func():
            return "success"
        
        # Call without user - should raise PermissionError
        with pytest.raises(PermissionError, match="User data not found"):
            await test_func()
    
    @pytest.mark.asyncio
    async def test_require_any_role_user_in_kwargs(self):
        """Test require_any_role decorator with user in kwargs - line 207"""
        from middleware.permissions import require_any_role, UserRole
        
        @require_any_role([UserRole.MANAGER, UserRole.ORG_ADMIN])
        async def test_func(**kwargs):
            return "success"
        
        user_data = {'role': 'manager', 'organization_id': 'org-123'}
        result = await test_func(user=user_data)
        assert result == "success"
    
    def test_permission_checker_can_use_rag_feature_no_toggle_no_metadata(self, mock_supabase_for_metadata):
        """Test PermissionChecker.can_use_rag_feature when no toggle and no metadata - line 290"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase_for_metadata)
        
        # Mock toggle result - no data
        toggle_result = Mock()
        toggle_result.data = []
        
        # Mock metadata result - no data
        metadata_result = Mock()
        metadata_result.data = []
        
        call_count = [0]
        def from_side_effect(table_name):
            call_count[0] += 1
            mock_table = Mock()
            mock_select = Mock()
            
            if call_count[0] == 1:  # organization_rag_toggles
                mock_eq1 = Mock()
                mock_eq2 = Mock()
                mock_execute = Mock()
                mock_execute.return_value = toggle_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq1)
                mock_eq1.eq = Mock(return_value=mock_eq2)
                mock_eq2.execute = mock_execute
            else:  # rag_feature_metadata
                mock_eq = Mock()
                mock_execute = Mock()
                mock_execute.return_value = metadata_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_eq.execute = mock_execute
            
            return mock_table
        
        mock_supabase_for_metadata.from_.side_effect = from_side_effect
        
        can_use = checker.can_use_rag_feature('sales_intelligence', 'org-123')
        assert can_use is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=middleware.permissions', '--cov-report=term-missing'])

