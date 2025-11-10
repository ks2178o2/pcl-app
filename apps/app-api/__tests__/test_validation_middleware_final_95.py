# apps/app-api/__tests__/test_validation_middleware_final_95.py
"""
Final tests to reach 95% coverage for Validation Middleware
Covering the remaining missing lines: 30, 43, 51-55, 65, 131, 142-146, 218, 240
"""

import pytest
from unittest.mock import Mock, patch
from middleware.validation import (
    RAGFeatureValidator,
    ValidationError,
    validate_rag_feature_enabled,
    validate_feature_inheritance,
    validate_user_permissions,
    rag_validator
)


class TestValidationMiddlewareFinal95:
    """Final tests to reach 95% coverage"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create a mock supabase client"""
        return Mock()
    
    @pytest.fixture
    def validator(self, mock_supabase):
        """Create validator with mocked dependencies"""
        with patch('services.supabase_client.get_supabase_client', return_value=mock_supabase):
            with patch('middleware.validation.get_supabase_client', return_value=mock_supabase):
                validator = RAGFeatureValidator()
                validator.supabase = mock_supabase
                return validator
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_exists_result_data_access(self, validator, mock_supabase):
        """Test validate_rag_feature_exists accessing result.data - line 30"""
        # Mock result with data attribute
        result = Mock()
        result.data = [{'rag_feature': 'test_feature', 'is_active': True}]
        
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
        
        exists = await validator.validate_rag_feature_exists('test_feature')
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_enabled_feature_not_exists(self, validator, mock_supabase):
        """Test validate_rag_feature_enabled when feature doesn't exist - line 43"""
        # Mock validate_rag_feature_exists to return False
        with patch.object(validator, 'validate_rag_feature_exists', return_value=False):
            is_enabled, error = await validator.validate_rag_feature_enabled('org-123', 'unknown_feature')
            assert is_enabled is False
            assert 'does not exist' in error
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_enabled_toggle_disabled(self, validator, mock_supabase):
        """Test validate_rag_feature_enabled when toggle exists but is disabled - lines 51-55"""
        # Mock feature exists
        with patch.object(validator, 'validate_rag_feature_exists', return_value=True):
            # Mock toggle query - disabled
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
            
            is_enabled, error = await validator.validate_rag_feature_enabled('org-123', 'test_feature')
            assert is_enabled is False
            assert 'disabled' in error
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_enabled_toggle_enabled(self, validator, mock_supabase):
        """Test validate_rag_feature_enabled when toggle is enabled - line 55"""
        # Mock feature exists
        with patch.object(validator, 'validate_rag_feature_exists', return_value=True):
            # Mock toggle query - enabled
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
            
            is_enabled, error = await validator.validate_rag_feature_enabled('org-123', 'test_feature')
            assert is_enabled is True
            assert error == ""
    
    @pytest.mark.asyncio
    async def test_validate_organization_exists_success(self, validator, mock_supabase):
        """Test validate_organization_exists success - line 65"""
        # Mock result with data
        result = Mock()
        result.data = [{'id': 'org-123'}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        exists = await validator.validate_organization_exists('org-123')
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_validate_feature_inheritance_parent_enabled_success(self, validator, mock_supabase):
        """Test validate_feature_inheritance when parent has feature enabled - line 131"""
        # Mock organization query - has parent
        org_result = Mock()
        org_result.data = [{'parent_organization_id': 'parent-123'}]
        
        # Mock parent toggle query - enabled
        parent_result = Mock()
        parent_result.data = [{'enabled': True}]
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            
            if call_count == 1:  # Organizations table
                mock_select = Mock()
                mock_eq = Mock()
                mock_execute = Mock()
                mock_execute.return_value = org_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq)
                mock_eq.execute = mock_execute
            else:  # organization_rag_toggles table
                mock_select = Mock()
                mock_eq1 = Mock()
                mock_eq2 = Mock()
                mock_execute = Mock()
                mock_execute.return_value = parent_result
                mock_table.select = Mock(return_value=mock_select)
                mock_select.eq = Mock(return_value=mock_eq1)
                mock_eq1.eq = Mock(return_value=mock_eq2)
                mock_eq2.execute = mock_execute
            
            return mock_table
        
        validator.supabase = mock_supabase
        mock_supabase.from_.side_effect = from_side_effect
        
        can_enable, error = await validator.validate_feature_inheritance('org-123', 'test_feature')
        assert can_enable is True
        assert error == ""
    
    @pytest.mark.asyncio
    async def test_validate_user_can_manage_features_success(self, validator):
        """Test validate_user_can_manage_features success - lines 142-146"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-123'}
        org_id = 'org-123'
        
        # PermissionChecker needs supabase client, so we need to provide it
        mock_supabase = Mock()
        with patch('middleware.validation.PermissionChecker') as mock_checker_class:
            mock_checker = Mock()
            mock_checker.can_manage_rag_features.return_value = True
            mock_checker.user_role.value = 'org_admin'
            # PermissionChecker is initialized with user_data and supabase
            mock_checker_class.return_value = mock_checker
            
            can_manage, error = await validator.validate_user_can_manage_features(user_data, org_id)
            assert can_manage is True
            assert error == ""
    
    @pytest.mark.asyncio
    async def test_validate_user_can_manage_features_not_allowed(self, validator):
        """Test validate_user_can_manage_features when not allowed - lines 142-144"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        org_id = 'org-123'
        
        with patch('middleware.validation.PermissionChecker') as mock_checker_class:
            mock_checker = Mock()
            mock_checker.can_manage_rag_features.return_value = False
            mock_checker.user_role.value = 'user'
            mock_checker_class.return_value = mock_checker
            
            can_manage, error = await validator.validate_user_can_manage_features(user_data, org_id)
            assert can_manage is False
            assert 'cannot manage' in error
            assert 'user' in error  # User role should be in error message (line 143)
    
    @pytest.mark.asyncio
    async def test_validate_feature_inheritance_decorator_success(self):
        """Test validate_feature_inheritance decorator success - line 218"""
        from middleware.validation import validate_feature_inheritance
        
        @validate_feature_inheritance()
        async def test_func(**kwargs):
            return "success"
        
        with patch.object(rag_validator, 'validate_feature_inheritance', return_value=(True, "")):
            result = await test_func(feature_name='test_feature', organization_id='org-123')
            assert result == "success"
    
    @pytest.mark.asyncio
    async def test_validate_user_permissions_decorator_success(self):
        """Test validate_user_permissions decorator success - line 240"""
        from middleware.validation import validate_user_permissions
        
        @validate_user_permissions()
        async def test_func(**kwargs):
            return "success"
        
        with patch.object(rag_validator, 'validate_user_can_manage_features', return_value=(True, "")):
            result = await test_func(user={'role': 'admin'}, organization_id='org-123')
            assert result == "success"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=middleware.validation', '--cov-report=term-missing'])

