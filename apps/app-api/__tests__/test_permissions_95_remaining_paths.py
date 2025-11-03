# apps/app-api/__tests__/test_permissions_95_remaining_paths.py
"""
Final tests to reach 95% for Permissions Middleware
Target: Lines 290, 135-138, 152-172, 176-196, 206-209
"""

import pytest
from unittest.mock import Mock
from middleware.permissions import (
    can_access_organization, can_access_rag_feature,
    PermissionChecker, UserRole
)
from test_utils_permissions import SupabasePermissionMockBuilder


class TestRemainingPaths:
    """Test remaining missing paths to push to 95%"""
    
    def test_can_access_organization_error_path(self):
        """Test can_access_organization error handling - line 93"""
        mock_supabase = Mock()
        mock_supabase.from_.side_effect = Exception("Database error")
        
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        result = can_access_organization(user_data, 'org-other', mock_supabase, check_parent=True)
        
        assert result is False
    
    def test_can_access_rag_feature_error_path(self):
        """Test can_access_rag_feature error handling - line 124"""
        mock_supabase = Mock()
        mock_supabase.from_.side_effect = Exception("Database error")
        
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        result = can_access_rag_feature(user_data, 'sales_intelligence', 'org-123', mock_supabase)
        
        assert result is False
    
    def test_can_access_rag_feature_no_toggle_no_metadata(self):
        """Test can_access_rag_feature when no toggle and no metadata"""
        builder = SupabasePermissionMockBuilder()
        builder.setup_toggles([])
        builder.setup_metadata([])  # No metadata
        
        mock_supabase = builder.get_mock_client()
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        result = can_access_rag_feature(user_data, 'unknown_feature', 'org-123', mock_supabase)
        
        assert result is False
    
    def test_permission_checker_can_use_rag_feature_error(self):
        """Test PermissionChecker.can_use_rag_feature error handling - line 290-293"""
        mock_supabase = Mock()
        mock_supabase.from_.side_effect = Exception("Database error")
        
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        
        result = checker.can_use_rag_feature('sales_intelligence', 'org-123')
        
        assert result is False
    
    def test_permission_checker_can_use_no_toggle_no_metadata(self):
        """Test PermissionChecker when no toggle and no metadata - line 290"""
        builder = SupabasePermissionMockBuilder()
        builder.setup_toggles([])
        builder.setup_metadata([])
        
        mock_supabase = builder.get_mock_client()
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_use_rag_feature('unknown_feature', 'org-123')
        
        assert result is False


class TestRoleHierarchyEdgeCases:
    """Test role hierarchy edge cases"""
    
    def test_has_role_with_level_zero(self):
        """Test has_role when user has invalid role (level 0)"""
        from middleware.permissions import has_role, get_user_role
        
        user_data = {'role': 'invalid_role'}
        user_role = get_user_role(user_data)
        
        # User role will be USER (default), but if it were truly invalid, level would be 0
        result = has_role(user_data, UserRole.SYSTEM_ADMIN)
        
        assert result is False  # USER < SYSTEM_ADMIN
    
    def test_can_access_organization_no_check_parent_same_org(self):
        """Test can_access_organization without parent check, same org - line 82"""
        mock_supabase = Mock()
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        result = can_access_organization(user_data, 'org-123', mock_supabase, check_parent=False)
        
        assert result is True
    
    def test_can_access_organization_no_check_parent_different_org(self):
        """Test can_access_organization without parent check, different org - line 96"""
        mock_supabase = Mock()
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        result = can_access_organization(user_data, 'org-other', mock_supabase, check_parent=False)
        
        assert result is False
    
    def test_can_access_rag_feature_system_admin(self):
        """Test RAG feature access for system admin - line 105"""
        mock_supabase = Mock()
        user_data = {'role': 'system_admin'}
        
        result = can_access_rag_feature(user_data, 'sales_intelligence', 'org-any', mock_supabase)
        
        assert result is True
    
    def test_can_access_rag_feature_different_org(self):
        """Test RAG feature access for different org - line 109"""
        mock_supabase = Mock()
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        result = can_access_rag_feature(user_data, 'sales_intelligence', 'org-456', mock_supabase)
        
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=middleware.permissions', '--cov-report=html'])

