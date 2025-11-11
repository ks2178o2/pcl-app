"""
Tests to cover remaining gaps in permissions.py to reach 95% coverage
Targeting missing lines: 79, 86-96, 106, 110, 117, 121, 123-125, 166, 255, 290, 298, 317
"""
import pytest
from unittest.mock import Mock, patch
from middleware.permissions import (
    UserRole, PermissionError, OrganizationAccessError, FeatureAccessError,
    can_access_organization, can_access_rag_feature,
    require_org_access, PermissionChecker, validate_permissions,
    get_supabase_client
)


class TestCanAccessOrganizationGaps:
    """Test missing coverage in can_access_organization"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client"""
        mock_client = Mock()
        return mock_client
    
    def test_can_access_organization_system_admin(self, mock_supabase):
        """Test line 79: SYSTEM_ADMIN can access any organization"""
        user_data = {'role': 'system_admin', 'organization_id': 'org-1'}
        result = can_access_organization(user_data, 'org-999', mock_supabase, check_parent=False)
        assert result is True
    
    def test_can_access_organization_check_parent_true(self, mock_supabase):
        """Test lines 86-96: check_parent=True with child organization"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-parent'}
        
        # Mock child organization query
        mock_result = Mock()
        mock_result.data = [{'id': 'org-child'}]
        
        mock_query = Mock()
        mock_query.eq = Mock(return_value=mock_query)
        mock_query.execute = Mock(return_value=mock_result)
        
        mock_table = Mock()
        mock_table.select = Mock(return_value=mock_query)
        mock_supabase.from_.return_value = mock_table
        
        result = can_access_organization(user_data, 'org-child', mock_supabase, check_parent=True)
        assert result is True
    
    def test_can_access_organization_check_parent_no_child(self, mock_supabase):
        """Test line 96: check_parent=True but target is not a child"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-parent'}
        
        # Mock no child found
        mock_result = Mock()
        mock_result.data = []
        
        mock_query = Mock()
        mock_query.eq = Mock(return_value=mock_query)
        mock_query.execute = Mock(return_value=mock_result)
        
        mock_table = Mock()
        mock_table.select = Mock(return_value=mock_query)
        mock_supabase.from_.return_value = mock_table
        
        result = can_access_organization(user_data, 'org-other', mock_supabase, check_parent=True)
        assert result is False
    
    def test_can_access_organization_different_org_no_parent_check(self, mock_supabase):
        """Test line 96: Different org, check_parent=False, should return False"""
        user_data = {'role': 'user', 'organization_id': 'org-1'}
        result = can_access_organization(user_data, 'org-2', mock_supabase, check_parent=False)
        assert result is False
    
    def test_can_access_organization_check_parent_exception(self, mock_supabase):
        """Test lines 93-94: Exception handling in check_parent"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-parent'}
        
        # Mock exception
        mock_query = Mock()
        mock_query.eq = Mock(return_value=mock_query)
        mock_query.execute = Mock(side_effect=Exception("Database error"))
        
        mock_table = Mock()
        mock_table.select = Mock(return_value=mock_query)
        mock_supabase.from_.return_value = mock_table
        
        result = can_access_organization(user_data, 'org-child', mock_supabase, check_parent=True)
        assert result is False


class TestCanAccessRAGFeatureGaps:
    """Test missing coverage in can_access_rag_feature"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client"""
        mock_client = Mock()
        return mock_client
    
    def test_can_access_rag_feature_system_admin(self, mock_supabase):
        """Test line 106: SYSTEM_ADMIN can access any feature"""
        user_data = {'role': 'system_admin', 'organization_id': 'org-1'}
        result = can_access_rag_feature(user_data, 'any_feature', 'org-999', mock_supabase)
        assert result is True
    
    def test_can_access_rag_feature_different_org(self, mock_supabase):
        """Test line 110: User cannot access feature in different org"""
        user_data = {'role': 'user', 'organization_id': 'org-1'}
        result = can_access_rag_feature(user_data, 'feature', 'org-2', mock_supabase)
        assert result is False
    
    def test_can_access_rag_feature_enabled(self, mock_supabase):
        """Test line 117: Feature is enabled in organization_rag_toggles"""
        user_data = {'role': 'user', 'organization_id': 'org-1'}
        
        # Mock enabled toggle
        toggle_result = Mock()
        toggle_result.data = [{'enabled': True}]
        
        toggle_query = Mock()
        toggle_query.eq = Mock(return_value=toggle_query)
        toggle_query.execute = Mock(return_value=toggle_result)
        
        mock_table = Mock()
        mock_table.select = Mock(return_value=toggle_query)
        mock_supabase.from_.return_value = mock_table
        
        result = can_access_rag_feature(user_data, 'feature', 'org-1', mock_supabase)
        assert result is True
    
    def test_can_access_rag_feature_default_enabled(self, mock_supabase):
        """Test line 121: Feature enabled by default in metadata"""
        user_data = {'role': 'user', 'organization_id': 'org-1'}
        
        # Mock no toggle, but default enabled in metadata
        toggle_result = Mock()
        toggle_result.data = []
        
        metadata_result = Mock()
        metadata_result.data = [{'default_enabled': True}]
        
        toggle_query = Mock()
        toggle_query.eq = Mock(return_value=toggle_query)
        toggle_query.execute = Mock(side_effect=[toggle_result, metadata_result])
        
        mock_table = Mock()
        mock_table.select = Mock(return_value=toggle_query)
        mock_supabase.from_.return_value = mock_table
        
        result = can_access_rag_feature(user_data, 'feature', 'org-1', mock_supabase)
        assert result is True
    
    def test_can_access_rag_feature_exception(self, mock_supabase):
        """Test lines 123-125: Exception handling"""
        user_data = {'role': 'user', 'organization_id': 'org-1'}
        
        # Mock exception
        mock_query = Mock()
        mock_query.eq = Mock(return_value=mock_query)
        mock_query.execute = Mock(side_effect=Exception("Database error"))
        
        mock_table = Mock()
        mock_table.select = Mock(return_value=mock_query)
        mock_supabase.from_.return_value = mock_table
        
        result = can_access_rag_feature(user_data, 'feature', 'org-1', mock_supabase)
        assert result is False


class TestRequireOrgAccessGaps:
    """Test missing coverage in require_org_access decorator"""
    
    @pytest.mark.asyncio
    async def test_require_org_access_raises_error(self):
        """Test line 166: OrganizationAccessError when user cannot access org"""
        @require_org_access(check_parent=False)
        async def test_func(*args, **kwargs):
            return {'status': 'ok'}
        
        with patch('middleware.permissions.can_access_organization', return_value=False):
            with pytest.raises(OrganizationAccessError):
                await test_func(
                    user={'role': 'user', 'organization_id': 'org-1'},
                    organization_id='org-2'
                )


class TestPermissionCheckerGaps:
    """Test missing coverage in PermissionChecker class"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client"""
        mock_client = Mock()
        return mock_client
    
    def test_can_manage_rag_features_system_admin(self, mock_supabase):
        """Test line 255: SYSTEM_ADMIN can manage RAG features"""
        user_data = {'role': 'system_admin', 'organization_id': 'org-1'}
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_manage_rag_features('org-999')
        assert result is True
    
    def test_can_use_rag_feature_no_toggle_no_metadata(self, mock_supabase):
        """Test line 290: No toggle and no metadata returns False"""
        user_data = {'role': 'user', 'organization_id': 'org-1'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        # Mock no toggle and no metadata
        toggle_result = Mock()
        toggle_result.data = []
        
        metadata_result = Mock()
        metadata_result.data = []
        
        mock_query = Mock()
        mock_query.eq = Mock(return_value=mock_query)
        mock_query.execute = Mock(side_effect=[toggle_result, metadata_result])
        
        mock_table = Mock()
        mock_table.select = Mock(return_value=mock_query)
        mock_supabase.from_.return_value = mock_table
        
        result = checker.can_use_rag_feature('feature', 'org-1')
        assert result is False
    
    def test_can_access_organization_hierarchy_system_admin(self, mock_supabase):
        """Test line 298: SYSTEM_ADMIN can access organization hierarchy"""
        user_data = {'role': 'system_admin', 'organization_id': 'org-1'}
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_access_organization_hierarchy('org-999')
        assert result is True
    
    def test_get_accessible_organizations_with_org_id(self, mock_supabase):
        """Test line 317: User with org_id returns list with that org"""
        user_data = {'role': 'user', 'organization_id': 'org-1'}
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.get_accessible_organizations()
        assert result == ['org-1']


class TestValidatePermissionsGaps:
    """Test validate_permissions function"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client"""
        mock_client = Mock()
        return mock_client
    
    def test_validate_permissions_with_none_supabase(self):
        """Test validate_permissions calls get_supabase_client when supabase is None"""
        user_data = {'role': 'system_admin', 'organization_id': 'org-1'}
        
        with patch('middleware.permissions.get_supabase_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            
            with patch('middleware.permissions.PermissionChecker') as mock_checker_class:
                mock_checker = Mock()
                mock_checker.can_manage_rag_features.return_value = True
                mock_checker_class.return_value = mock_checker
                
                result = validate_permissions(
                    user_data, 'manage_rag_features', 'org-1',
                    supabase=None
                )
                
                assert result is True
                mock_get_client.assert_called_once()

