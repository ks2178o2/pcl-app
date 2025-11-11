# apps/app-api/__tests__/test_permissions_95_final.py
"""
Final tests to push Permissions Middleware to 95%
Focusing on remaining missing lines without complex decorator testing
"""

import pytest
from unittest.mock import Mock
from middleware.permissions import (
    can_access_organization, can_access_rag_feature,
    PermissionChecker, UserRole
)
from test_utils_permissions import SupabasePermissionMockBuilder


class TestOrganizationAccessEdgeCases:
    """Test organization access edge cases - line 122"""
    
    def test_can_access_organization_error_handling(self):
        """Test access with exception in query"""
        mock_supabase = Mock()
        mock_supabase.from_.side_effect = Exception("Database error")
        
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        result = can_access_organization(user_data, 'org-other', mock_supabase, check_parent=True)
        
        assert result is False


class TestRAGFeatureAccessEdgeCases:
    """Test RAG feature access edge cases - line 122"""
    
    def test_can_access_rag_feature_error_handling(self):
        """Test RAG feature access with exception"""
        mock_supabase = Mock()
        mock_supabase.from_.side_effect = Exception("Database error")
        
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        result = can_access_rag_feature(user_data, 'sales_intelligence', 'org-123', mock_supabase)
        
        assert result is False
    
    def test_can_access_rag_feature_no_data(self):
        """Test RAG feature access when no data returned"""
        builder = SupabasePermissionMockBuilder()
        # No toggles, no metadata
        builder.setup_toggles([])
        builder.setup_metadata([])
        
        mock_supabase = builder.get_mock_client()
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        result = can_access_rag_feature(user_data, 'unknown_feature', 'org-123', mock_supabase)
        assert result is False


class TestPermissionCheckerComplexMethods:
    """Test PermissionChecker complex methods - lines 275, 278, 287-293"""
    
    def test_can_use_rag_feature_system_admin(self):
        """Test system admin can use any feature - line 275"""
        mock_supabase = Mock()
        user_data = {'role': 'system_admin', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_use_rag_feature('sales_intelligence', 'org-any')
        
        assert result is True
    
    def test_can_use_rag_feature_different_org(self):
        """Test user cannot use feature in different org - line 278"""
        mock_supabase = Mock()
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_use_rag_feature('sales_intelligence', 'org-other')
        
        assert result is False
    
    def test_can_use_rag_feature_enabled_via_toggle(self):
        """Test can use when toggle is enabled - lines 287-293"""
        builder = SupabasePermissionMockBuilder()
        builder.setup_toggles([
            {'organization_id': 'org-123', 'rag_feature': 'sales_intelligence', 'enabled': True}
        ])
        builder.setup_metadata([])
        
        mock_supabase = builder.get_mock_client()
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_use_rag_feature('sales_intelligence', 'org-123')
        
        assert result is True
    
    def test_can_use_rag_feature_enabled_via_metadata(self):
        """Test can use when enabled via metadata - lines 287-293"""
        builder = SupabasePermissionMockBuilder()
        builder.setup_toggles([])  # No toggle
        builder.setup_metadata([
            {'rag_feature': 'sales_intelligence', 'default_enabled': True}
        ])
        
        mock_supabase = builder.get_mock_client()
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_use_rag_feature('sales_intelligence', 'org-123')
        
        assert result is True
    
    def test_can_use_rag_feature_disabled(self):
        """Test cannot use disabled feature"""
        builder = SupabasePermissionMockBuilder()
        builder.setup_toggles([
            {'organization_id': 'org-123', 'rag_feature': 'sales_intelligence', 'enabled': False}
        ])
        builder.setup_metadata([])
        
        mock_supabase = builder.get_mock_client()
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_use_rag_feature('sales_intelligence', 'org-123')
        
        assert result is False
    
    def test_can_use_rag_feature_error_handling(self):
        """Test error handling in can_use_rag_feature"""
        mock_supabase = Mock()
        mock_supabase.from_.side_effect = Exception("Database error")
        
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_use_rag_feature('sales_intelligence', 'org-123')
        
        assert result is False


class TestPermissionCheckerAccessMethods:
    """Test PermissionChecker access checking methods"""
    
    def test_can_manage_rag_features_system_admin(self):
        """Test system admin can manage any org - line 254"""
        mock_supabase = Mock()
        user_data = {'role': 'system_admin', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_manage_rag_features('org-any')
        
        assert result is True
    
    def test_can_manage_rag_features_org_admin_own_org(self):
        """Test org admin can manage own org - line 257"""
        mock_supabase = Mock()
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_manage_rag_features('org-123')
        
        assert result is True
    
    def test_can_manage_rag_features_org_admin_other_org(self):
        """Test org admin cannot manage other org"""
        mock_supabase = Mock()
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_manage_rag_features('org-other')
        
        assert result is False
    
    def test_can_view_rag_features_system_admin(self):
        """Test system admin can view any org - line 264"""
        mock_supabase = Mock()
        user_data = {'role': 'system_admin', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_view_rag_features('org-any')
        
        assert result is True
    
    def test_can_view_rag_features_org_admin(self):
        """Test org admin can view any org - line 264"""
        mock_supabase = Mock()
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_view_rag_features('org-any')
        
        assert result is True
    
    def test_can_view_rag_features_user_same_org(self):
        """Test user can view own org"""
        mock_supabase = Mock()
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_view_rag_features('org-123')
        
        assert result is True
    
    def test_can_view_rag_features_user_different_org(self):
        """Test user cannot view other org"""
        mock_supabase = Mock()
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_view_rag_features('org-other')
        
        assert result is False
    
    def test_can_access_organization_hierarchy_system_admin(self):
        """Test system admin can access hierarchy - line 297"""
        mock_supabase = Mock()
        user_data = {'role': 'system_admin', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_access_organization_hierarchy('org-any')
        
        assert result is True
    
    def test_can_access_organization_hierarchy_org_admin_same_org(self):
        """Test org admin can access own hierarchy"""
        mock_supabase = Mock()
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_access_organization_hierarchy('org-123')
        
        assert result is True
    
    def test_can_access_organization_hierarchy_org_admin_different_org(self):
        """Test org admin cannot access other org's hierarchy"""
        mock_supabase = Mock()
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.can_access_organization_hierarchy('org-other')
        
        assert result is False


class TestGetAccessibleOrganizations:
    """Test get_accessible_organizations method"""
    
    def test_get_accessible_orgs_system_admin(self):
        """Test system admin gets all orgs"""
        builder = SupabasePermissionMockBuilder()
        builder.setup_organizations([
            {'id': 'org-1'}, {'id': 'org-2'}, {'id': 'org-3'}
        ])
        
        mock_supabase = builder.get_mock_client()
        user_data = {'role': 'system_admin'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.get_accessible_organizations()
        
        assert len(result) == 3
        assert 'org-1' in result
        assert 'org-2' in result
        assert 'org-3' in result
    
    def test_get_accessible_orgs_system_admin_error(self):
        """Test system admin handles error getting orgs"""
        mock_supabase = Mock()
        mock_supabase.from_.side_effect = Exception("Database error")
        
        user_data = {'role': 'system_admin'}
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.get_accessible_organizations()
        
        assert result == []
    
    def test_get_accessible_orgs_user_with_org(self):
        """Test user with org gets their org"""
        mock_supabase = Mock()
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.get_accessible_organizations()
        
        assert result == ['org-123']
    
    def test_get_accessible_orgs_user_no_org(self):
        """Test user without org gets empty list"""
        mock_supabase = Mock()
        user_data = {'role': 'user'}
        
        checker = PermissionChecker(user_data, mock_supabase)
        result = checker.get_accessible_organizations()
        
        assert result == []


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=middleware.permissions', '--cov-report=html'])

