# apps/app-api/__tests__/test_permissions_validate_95_final.py
"""
Final tests for validate_permissions to reach 95%
Lines: 324-337
"""

import pytest
from unittest.mock import Mock
from middleware.permissions import validate_permissions, UserRole
from test_utils_permissions import SupabasePermissionMockBuilder


class TestValidatePermissionsFixed:
    """Test fixed validate_permissions function - lines 324-337"""
    
    def test_validate_manage_rag_features(self):
        """Test validate for manage_rag_features action - line 329"""
        builder = SupabasePermissionMockBuilder()
        mock_supabase = builder.get_mock_client()
        
        user_data = {'role': 'system_admin', 'organization_id': 'org-123'}
        result = validate_permissions(user_data, "manage_rag_features", 'org-123', supabase=mock_supabase)
        
        assert result is True
    
    def test_validate_view_rag_features(self):
        """Test validate for view_rag_features action - line 331"""
        builder = SupabasePermissionMockBuilder()
        mock_supabase = builder.get_mock_client()
        
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        result = validate_permissions(user_data, "view_rag_features", 'org-123', supabase=mock_supabase)
        
        assert result is True
    
    def test_validate_use_rag_feature_with_name(self):
        """Test validate for use_rag_feature with name - line 333"""
        builder = SupabasePermissionMockBuilder()
        mock_supabase = builder.get_mock_client()
        
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        result = validate_permissions(user_data, "use_rag_feature", 'org-123', 
                                      feature_name='sales_intelligence', supabase=mock_supabase)
        
        assert result is not None
    
    def test_validate_use_rag_feature_without_name(self):
        """Test validate for use_rag_feature without name - line 331-332"""
        builder = SupabasePermissionMockBuilder()
        mock_supabase = builder.get_mock_client()
        
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        result = validate_permissions(user_data, "use_rag_feature", 'org-123', feature_name=None, supabase=mock_supabase)
        
        # Should return False when no feature name
        assert result is False
    
    def test_validate_access_hierarchy(self):
        """Test validate for access_hierarchy action - line 335"""
        builder = SupabasePermissionMockBuilder()
        mock_supabase = builder.get_mock_client()
        
        user_data = {'role': 'system_admin', 'organization_id': 'org-123'}
        result = validate_permissions(user_data, "access_hierarchy", 'org-123', supabase=mock_supabase)
        
        assert result is True
    
    def test_validate_unknown_action(self):
        """Test validate for unknown action - lines 336-337"""
        builder = SupabasePermissionMockBuilder()
        mock_supabase = builder.get_mock_client()
        
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        result = validate_permissions(user_data, "unknown_action", 'org-123', supabase=mock_supabase)
        
        # Should return False for unknown action
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=middleware.permissions', '--cov-report=html'])

