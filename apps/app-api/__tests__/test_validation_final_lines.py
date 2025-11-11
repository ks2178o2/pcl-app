"""
Tests to cover final missing lines in validation.py (lines 124, 129)
Target: 98.33% → 100%
"""
import pytest
from unittest.mock import Mock, patch
from middleware.validation import RAGFeatureValidator, ValidationError


class TestValidationFinalLines:
    """Test final missing coverage lines"""
    
    @pytest.fixture
    def validator(self):
        """Create validator with mocked dependencies"""
        with patch('services.supabase_client.get_supabase_client', return_value=Mock()):
            with patch('middleware.validation.get_supabase_client', return_value=Mock()):
                return RAGFeatureValidator()
    
    @pytest.mark.asyncio
    async def test_validate_feature_inheritance_parent_not_enabled(self, validator):
        """Test line 124: Parent organization has feature but it's disabled"""
        # Mock organization exists with parent
        org_result = Mock()
        org_result.data = [{'parent_organization_id': 'org-parent'}]
        
        # Mock parent toggle exists but disabled
        parent_toggle_result = Mock()
        parent_toggle_result.data = [{'enabled': False}]
        
        org_query = Mock()
        org_query.eq = Mock(return_value=org_query)
        org_query.execute = Mock(return_value=org_result)
        
        toggle_query = Mock()
        toggle_query.eq = Mock(return_value=toggle_query)
        toggle_query.execute = Mock(return_value=parent_toggle_result)
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call for organization
                org_table = Mock()
                org_table.select = Mock(return_value=org_query)
                return org_table
            else:
                # Second call for parent toggle
                toggle_table = Mock()
                toggle_table.select = Mock(return_value=toggle_query)
                return toggle_table
        
        validator.supabase.from_ = Mock(side_effect=from_side_effect)
        
        can_enable, error_msg = await validator.validate_feature_inheritance('org-child', 'feature_name')
        
        assert can_enable is False
        assert 'parent organization' in error_msg.lower()
        assert 'disabled' in error_msg.lower()
    
    @pytest.mark.asyncio
    async def test_validate_feature_inheritance_parent_not_configured(self, validator):
        """Test line 129: Parent organization doesn't have feature configured"""
        # Mock organization exists with parent
        org_result = Mock()
        org_result.data = [{'parent_organization_id': 'org-parent'}]
        
        # Mock parent toggle doesn't exist
        parent_toggle_result = Mock()
        parent_toggle_result.data = []
        
        org_query = Mock()
        org_query.eq = Mock(return_value=org_query)
        org_query.execute = Mock(return_value=org_result)
        
        toggle_query = Mock()
        toggle_query.eq = Mock(return_value=toggle_query)
        toggle_query.execute = Mock(return_value=parent_toggle_result)
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call for organization
                org_table = Mock()
                org_table.select = Mock(return_value=org_query)
                return org_table
            else:
                # Second call for parent toggle
                toggle_table = Mock()
                toggle_table.select = Mock(return_value=toggle_query)
                return toggle_table
        
        validator.supabase.from_ = Mock(side_effect=from_side_effect)
        
        can_enable, error_msg = await validator.validate_feature_inheritance('org-child', 'feature_name')
        
        assert can_enable is False
        assert 'not have feature' in error_msg.lower()
        assert 'configured' in error_msg.lower()

