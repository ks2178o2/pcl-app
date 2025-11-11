# apps/app-api/__tests__/test_validation_middleware_coverage_gaps_95.py
"""
Additional tests to fill coverage gaps and reach 95% for Validation Middleware
Focusing on exception handling, edge cases, and error paths
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from middleware.validation import (
    RAGFeatureValidator,
    ValidationError,
    validate_rag_feature_enabled,
    validate_org_hierarchy,
    validate_feature_inheritance,
    validate_user_permissions,
    validate_rag_feature_operation,
    validate_bulk_toggle_operation,
    rag_validator
)


class TestValidationMiddlewareCoverageGaps:
    """Tests to fill remaining coverage gaps"""
    
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
    async def test_validate_rag_feature_exists_exception(self, validator, mock_supabase):
        """Test validate_rag_feature_exists exception handling - lines 28-33"""
        # Mock supabase to raise exception
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.side_effect = Exception("Database error")
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        result = await validator.validate_rag_feature_exists('test_feature')
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_enabled_exception_in_exists_check(self, validator, mock_supabase):
        """Test validate_rag_feature_enabled exception when checking if feature exists - lines 43, 57-59"""
        # Mock validate_rag_feature_exists to raise exception
        with patch.object(validator, 'validate_rag_feature_exists', side_effect=Exception("DB error")):
            is_enabled, error = await validator.validate_rag_feature_enabled('org-123', 'test_feature')
            assert is_enabled is False
            assert 'Error' in error
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_enabled_exception_in_toggle_check(self, validator, mock_supabase):
        """Test validate_rag_feature_enabled exception when checking toggle - lines 51-59"""
        # Mock feature exists, but toggle check raises exception
        with patch.object(validator, 'validate_rag_feature_exists', return_value=True):
            mock_table = Mock()
            mock_select = Mock()
            mock_eq1 = Mock()
            mock_eq2 = Mock()
            mock_execute = Mock()
            mock_execute.side_effect = Exception("Database error")
            
            mock_table.select = Mock(return_value=mock_select)
            mock_select.eq = Mock(return_value=mock_eq1)
            mock_eq1.eq = Mock(return_value=mock_eq2)
            mock_eq2.execute = mock_execute
            mock_supabase.from_.return_value = mock_table
            
            is_enabled, error = await validator.validate_rag_feature_enabled('org-123', 'test_feature')
            assert is_enabled is False
            assert 'Error' in error
    
    @pytest.mark.asyncio
    async def test_validate_organization_exists_exception(self, validator, mock_supabase):
        """Test validate_organization_exists exception handling - lines 63-68"""
        # Mock supabase to raise exception
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.side_effect = Exception("Database error")
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        result = await validator.validate_organization_exists('org-123')
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_org_hierarchy_parent_not_exists(self, validator, mock_supabase):
        """Test validate_org_hierarchy when parent doesn't exist - line 79"""
        with patch.object(validator, 'validate_organization_exists', side_effect=lambda x: x != 'parent-123'):
            is_valid, error = await validator.validate_org_hierarchy('parent-123', 'child-123')
            assert is_valid is False
            assert 'Parent organization' in error
    
    @pytest.mark.asyncio
    async def test_validate_org_hierarchy_child_not_exists(self, validator, mock_supabase):
        """Test validate_org_hierarchy when child doesn't exist - line 82"""
        with patch.object(validator, 'validate_organization_exists', side_effect=lambda x: x == 'parent-123'):
            is_valid, error = await validator.validate_org_hierarchy('parent-123', 'child-123')
            assert is_valid is False
            assert 'Child organization' in error
    
    @pytest.mark.asyncio
    async def test_validate_org_hierarchy_circular_self(self, validator, mock_supabase):
        """Test validate_org_hierarchy when parent equals child - line 86"""
        with patch.object(validator, 'validate_organization_exists', return_value=True):
            is_valid, error = await validator.validate_org_hierarchy('org-123', 'org-123')
            assert is_valid is False
            assert 'cannot be its own parent' in error
    
    @pytest.mark.asyncio
    async def test_validate_org_hierarchy_circular_dependency(self, validator, mock_supabase):
        """Test validate_org_hierarchy circular dependency - line 94"""
        with patch.object(validator, 'validate_organization_exists', return_value=True):
            # Mock parent query to return child as parent (circular)
            org_result = Mock()
            org_result.data = [{'parent_organization_id': 'child-123'}]
            
            mock_table = Mock()
            mock_select = Mock()
            mock_eq = Mock()
            mock_execute = Mock()
            mock_execute.return_value = org_result
            
            mock_table.select = Mock(return_value=mock_select)
            mock_select.eq = Mock(return_value=mock_eq)
            mock_eq.execute = mock_execute
            mock_supabase.from_.return_value = mock_table
            
            is_valid, error = await validator.validate_org_hierarchy('parent-123', 'child-123')
            assert is_valid is False
            assert 'Circular dependency' in error
    
    @pytest.mark.asyncio
    async def test_validate_org_hierarchy_exception(self, validator, mock_supabase):
        """Test validate_org_hierarchy exception handling - lines 98-100"""
        with patch.object(validator, 'validate_organization_exists', side_effect=Exception("DB error")):
            is_valid, error = await validator.validate_org_hierarchy('parent-123', 'child-123')
            assert is_valid is False
            assert 'Error' in error
    
    @pytest.mark.asyncio
    async def test_validate_feature_inheritance_org_not_found(self, validator, mock_supabase):
        """Test validate_feature_inheritance when org not found - line 112"""
        # Mock organization query - no data
        org_result = Mock()
        org_result.data = []
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = org_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        can_enable, error = await validator.validate_feature_inheritance('org-unknown', 'sales_intelligence')
        assert can_enable is False
        assert 'not found' in error
    
    @pytest.mark.asyncio
    async def test_validate_feature_inheritance_no_parent(self, validator, mock_supabase):
        """Test validate_feature_inheritance when no parent - line 118"""
        # Mock organization query - no parent
        org_result = Mock()
        org_result.data = [{'parent_organization_id': None}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = org_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        mock_supabase.from_.return_value = mock_table
        
        can_enable, error = await validator.validate_feature_inheritance('org-123', 'sales_intelligence')
        assert can_enable is True
        assert error == ""
    
    @pytest.mark.asyncio
    async def test_validate_feature_inheritance_exception(self, validator, mock_supabase):
        """Test validate_feature_inheritance exception handling - lines 131, 133-135"""
        # Mock to raise exception
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        mock_supabase.from_.return_value = mock_table
        
        can_enable, error = await validator.validate_feature_inheritance('org-123', 'sales_intelligence')
        assert can_enable is False
        assert 'Error' in error
    
    @pytest.mark.asyncio
    async def test_validate_user_can_manage_features_exception(self, validator):
        """Test validate_user_can_manage_features exception handling - lines 142-146, 148-150"""
        user_data = {'role': 'admin'}
        org_id = 'org-123'
        
        # Mock PermissionChecker to raise exception
        with patch('middleware.validation.PermissionChecker', side_effect=Exception("Permission error")):
            can_manage, error = await validator.validate_user_can_manage_features(user_data, org_id)
            assert can_manage is False
            assert 'Error' in error
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_enabled_decorator_missing_feature_name(self):
        """Test validate_rag_feature_enabled decorator with missing feature_name - line 166"""
        from middleware.validation import validate_rag_feature_enabled, ValidationError
        
        @validate_rag_feature_enabled()
        async def test_func(**kwargs):
            return "success"
        
        with pytest.raises(ValidationError, match="Missing required parameters"):
            await test_func(organization_id='org-123')
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_enabled_decorator_missing_org_id(self):
        """Test validate_rag_feature_enabled decorator with missing org_id - line 166"""
        from middleware.validation import validate_rag_feature_enabled, ValidationError
        
        @validate_rag_feature_enabled()
        async def test_func(**kwargs):
            return "success"
        
        with pytest.raises(ValidationError, match="Missing required parameters"):
            await test_func(feature_name='test_feature')
    
    @pytest.mark.asyncio
    async def test_validate_org_hierarchy_decorator_missing_parent_id(self):
        """Test validate_org_hierarchy decorator with missing parent_id - line 188"""
        from middleware.validation import validate_org_hierarchy, ValidationError
        
        @validate_org_hierarchy()
        async def test_func(**kwargs):
            return "success"
        
        with pytest.raises(ValidationError, match="Missing required parameters"):
            await test_func(child_id='child-123')
    
    @pytest.mark.asyncio
    async def test_validate_org_hierarchy_decorator_missing_child_id(self):
        """Test validate_org_hierarchy decorator with missing child_id - line 188"""
        from middleware.validation import validate_org_hierarchy, ValidationError
        
        @validate_org_hierarchy()
        async def test_func(**kwargs):
            return "success"
        
        with pytest.raises(ValidationError, match="Missing required parameters"):
            await test_func(parent_id='parent-123')
    
    @pytest.mark.asyncio
    async def test_validate_feature_inheritance_decorator_missing_feature_name(self):
        """Test validate_feature_inheritance decorator with missing feature_name - line 210"""
        from middleware.validation import validate_feature_inheritance, ValidationError
        
        @validate_feature_inheritance()
        async def test_func(**kwargs):
            return "success"
        
        with pytest.raises(ValidationError, match="Missing required parameters"):
            await test_func(organization_id='org-123')
    
    @pytest.mark.asyncio
    async def test_validate_feature_inheritance_decorator_missing_org_id(self):
        """Test validate_feature_inheritance decorator with missing org_id - line 210"""
        from middleware.validation import validate_feature_inheritance, ValidationError
        
        @validate_feature_inheritance()
        async def test_func(**kwargs):
            return "success"
        
        with pytest.raises(ValidationError, match="Missing required parameters"):
            await test_func(feature_name='test_feature')
    
    @pytest.mark.asyncio
    async def test_validate_user_permissions_decorator_missing_user(self):
        """Test validate_user_permissions decorator with missing user - line 232"""
        from middleware.validation import validate_user_permissions, ValidationError
        
        @validate_user_permissions()
        async def test_func(**kwargs):
            return "success"
        
        with pytest.raises(ValidationError, match="Missing required parameters"):
            await test_func(organization_id='org-123')
    
    @pytest.mark.asyncio
    async def test_validate_user_permissions_decorator_missing_org_id(self):
        """Test validate_user_permissions decorator with missing org_id - line 232"""
        from middleware.validation import validate_user_permissions, ValidationError
        
        @validate_user_permissions()
        async def test_func(**kwargs):
            return "success"
        
        with pytest.raises(ValidationError, match="Missing required parameters"):
            await test_func(user={'role': 'admin'})
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_operation_org_not_exists(self):
        """Test validate_rag_feature_operation when org doesn't exist - line 253"""
        with patch.object(rag_validator, 'validate_organization_exists', return_value=False):
            result = await validate_rag_feature_operation('org-unknown', 'test_feature', 'list')
            assert result['success'] is False
            assert 'does not exist' in result['error']
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_operation_feature_not_exists(self):
        """Test validate_rag_feature_operation when feature doesn't exist - line 260"""
        with patch.object(rag_validator, 'validate_organization_exists', return_value=True):
            with patch.object(rag_validator, 'validate_rag_feature_exists', return_value=False):
                result = await validate_rag_feature_operation('org-123', 'unknown_feature', 'list')
                assert result['success'] is False
                assert 'does not exist' in result['error']
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_operation_feature_disabled_for_use(self):
        """Test validate_rag_feature_operation when feature disabled for use operation - line 269"""
        with patch.object(rag_validator, 'validate_organization_exists', return_value=True):
            with patch.object(rag_validator, 'validate_rag_feature_exists', return_value=True):
                with patch.object(rag_validator, 'validate_rag_feature_enabled', return_value=(False, "Feature disabled")):
                    result = await validate_rag_feature_operation('org-123', 'test_feature', 'use')
                    assert result['success'] is False
                    assert 'disabled' in result['error']
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_operation_exception(self):
        """Test validate_rag_feature_operation exception handling - lines 279-284"""
        with patch.object(rag_validator, 'validate_organization_exists', side_effect=Exception("DB error")):
            result = await validate_rag_feature_operation('org-123', 'test_feature', 'list')
            assert result['success'] is False
            assert 'Validation error' in result['error']
    
    @pytest.mark.asyncio
    async def test_validate_bulk_toggle_operation_org_not_exists(self):
        """Test validate_bulk_toggle_operation when org doesn't exist - line 294"""
        toggle_updates = {'feature1': True}
        user_data = {'role': 'admin'}
        
        with patch.object(rag_validator, 'validate_organization_exists', return_value=False):
            result = await validate_bulk_toggle_operation('org-unknown', toggle_updates, user_data)
            assert result['success'] is False
            assert 'does not exist' in result['error']
    
    @pytest.mark.asyncio
    async def test_validate_bulk_toggle_operation_user_not_allowed(self):
        """Test validate_bulk_toggle_operation when user not allowed - line 302"""
        toggle_updates = {'feature1': True}
        user_data = {'role': 'viewer'}
        
        with patch.object(rag_validator, 'validate_organization_exists', return_value=True):
            with patch.object(rag_validator, 'validate_user_can_manage_features', return_value=(False, "Cannot manage")):
                result = await validate_bulk_toggle_operation('org-123', toggle_updates, user_data)
                assert result['success'] is False
                assert 'Cannot manage' in result['error']
    
    @pytest.mark.asyncio
    async def test_validate_bulk_toggle_operation_exception(self):
        """Test validate_bulk_toggle_operation exception handling - lines 332-337"""
        toggle_updates = {'feature1': True}
        user_data = {'role': 'admin'}
        
        with patch.object(rag_validator, 'validate_organization_exists', side_effect=Exception("DB error")):
            result = await validate_bulk_toggle_operation('org-123', toggle_updates, user_data)
            assert result['success'] is False
            assert 'Validation error' in result['error']
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_enabled_decorator_feature_disabled(self):
        """Test validate_rag_feature_enabled decorator when feature is disabled - line 172"""
        from middleware.validation import validate_rag_feature_enabled, ValidationError
        
        @validate_rag_feature_enabled()
        async def test_func(**kwargs):
            return "success"
        
        with patch.object(rag_validator, 'validate_rag_feature_enabled', return_value=(False, "Feature disabled")):
            with pytest.raises(ValidationError, match="disabled"):
                await test_func(feature_name='disabled_feature', organization_id='org-123')
    
    @pytest.mark.asyncio
    async def test_validate_org_hierarchy_decorator_invalid_hierarchy(self):
        """Test validate_org_hierarchy decorator when hierarchy is invalid - line 194"""
        from middleware.validation import validate_org_hierarchy, ValidationError
        
        @validate_org_hierarchy()
        async def test_func(**kwargs):
            return "success"
        
        with patch.object(rag_validator, 'validate_org_hierarchy', return_value=(False, "Invalid hierarchy")):
            with pytest.raises(ValidationError, match="Invalid"):
                await test_func(parent_id='parent-123', child_id='child-123')
    
    @pytest.mark.asyncio
    async def test_validate_feature_inheritance_decorator_blocked(self):
        """Test validate_feature_inheritance decorator when inheritance is blocked - line 216"""
        from middleware.validation import validate_feature_inheritance, ValidationError
        
        @validate_feature_inheritance()
        async def test_func(**kwargs):
            return "success"
        
        with patch.object(rag_validator, 'validate_feature_inheritance', return_value=(False, "Parent disabled")):
            with pytest.raises(ValidationError, match="disabled"):
                await test_func(feature_name='blocked_feature', organization_id='org-123')
    
    @pytest.mark.asyncio
    async def test_validate_user_permissions_decorator_blocked(self):
        """Test validate_user_permissions decorator when permission is blocked - line 240"""
        from middleware.validation import validate_user_permissions, ValidationError
        
        @validate_user_permissions()
        async def test_func(**kwargs):
            return "success"
        
        with patch.object(rag_validator, 'validate_user_can_manage_features', return_value=(False, "Cannot manage")):
            with pytest.raises(ValidationError, match="Cannot manage"):
                await test_func(user={'role': 'viewer'}, organization_id='org-123')
    
    @pytest.mark.asyncio
    async def test_validate_rag_feature_operation_non_usage_operation(self):
        """Test validate_rag_feature_operation for non-usage operations (doesn't check enabled) - line 266"""
        with patch.object(rag_validator, 'validate_organization_exists', return_value=True):
            with patch.object(rag_validator, 'validate_rag_feature_exists', return_value=True):
                # For non-usage operations, enabled check should be skipped
                result = await validate_rag_feature_operation('org-123', 'test_feature', 'list')
                assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_validate_bulk_toggle_operation_disabling_feature(self):
        """Test validate_bulk_toggle_operation when disabling (no inheritance check) - line 316"""
        toggle_updates = {'feature1': False}  # Disabling
        user_data = {'role': 'admin'}
        
        with patch.object(rag_validator, 'validate_organization_exists', return_value=True):
            with patch.object(rag_validator, 'validate_user_can_manage_features', return_value=(True, "")):
                with patch.object(rag_validator, 'validate_rag_feature_exists', return_value=True):
                    # When disabling, inheritance check is skipped
                    result = await validate_bulk_toggle_operation('org-123', toggle_updates, user_data)
                    assert result['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=middleware.validation', '--cov-report=term-missing'])

