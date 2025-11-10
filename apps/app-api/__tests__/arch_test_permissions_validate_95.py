# apps/app-api/__tests__/test_permissions_validate_95.py
"""
Tests for validate_permissions function to push to 95%
Lines: 326-337
"""

import pytest
from unittest.mock import Mock
from middleware.permissions import validate_permissions


class TestValidatePermissionsFunction:
    """Test validate_permissions function - lines 326-337"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create mock supabase client"""
        return Mock()
    
    def test_validate_permissions_manage_rag_features(self, mock_supabase):
        """Test validate for manage_rag_features action - line 327"""
        # Mock PermissionChecker to avoid need for supabase
        with pytest.mock.patch('middleware.permissions.PermissionChecker') as mock_checker:
            instance = Mock()
            instance.can_manage_rag_features.return_value = True
            mock_checker.return_value = instance
            
            user_data = {'role': 'system_admin', 'organization_id': 'org-123'}
            result = validate_permissions(user_data, "manage_rag_features", 'org-123')
            
            assert result is True
    
    def test_validate_permissions_view_rag_features(self, mock_supabase):
        """Test validate for view_rag_features action - line 329"""
        with pytest.mock.patch('middleware.permissions.PermissionChecker') as mock_checker:
            instance = Mock()
            instance.can_view_rag_features.return_value = True
            mock_checker.return_value = instance
            
            user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
            result = validate_permissions(user_data, "view_rag_features", 'org-123')
            
            assert result is True
    
    def test_validate_permissions_use_rag_feature_with_name(self, mock_supabase):
        """Test validate for use_rag_feature with feature name - line 333"""
        with pytest.mock.patch('middleware.permissions.PermissionChecker') as mock_checker:
            instance = Mock()
            instance.can_use_rag_feature.return_value = True
            mock_checker.return_value = instance
            
            user_data = {'role': 'user', 'organization_id': 'org-123'}
            result = validate_permissions(user_data, "use_rag_feature", 'org-123', feature_name='sales_intelligence')
            
            assert result is True
    
    def test_validate_permissions_use_rag_feature_without_name(self, mock_supabase):
        """Test validate for use_rag_feature without feature name - line 331-332"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        result = validate_permissions(user_data, "use_rag_feature", 'org-123', feature_name=None)
        
        # Should return False when no feature name
        assert result is False
    
    def test_validate_permissions_access_hierarchy(self, mock_supabase):
        """Test validate for access_hierarchy action - line 335"""
        with pytest.mock.patch('middleware.permissions.PermissionChecker') as mock_checker:
            instance = Mock()
            instance.can_access_organization_hierarchy.return_value = True
            mock_checker.return_value = instance
            
            user_data = {'role': 'system_admin', 'organization_id': 'org-123'}
            result = validate_permissions(user_data, "access_hierarchy", 'org-123')
            
            assert result is True
    
    def test_validate_permissions_unknown_action(self, mock_supabase):
        """Test validate for unknown action - lines 336-337"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        result = validate_permissions(user_data, "unknown_action", 'org-123')
        
        # Should return False for unknown action
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=middleware.permissions', '--cov-report=html'])

