# apps/app-api/__tests__/test_permissions_final_lines.py
"""
Final tests for last 4 missing lines: 79, 91, 117, 121
"""

import pytest
from unittest.mock import Mock
from middleware.permissions import can_access_organization, can_access_rag_feature, UserRole


class TestLastMissingLines:
    """Test the last 4 missing lines"""
    
    def test_line_79_system_admin_org_access(self):
        """Test line 79: system admin returns True for org access"""
        user_data = {'role': 'system_admin', 'organization_id': 'org-123'}
        mock_supabase = Mock()
        
        # System admin should return True (line 79)
        result = can_access_organization(user_data, 'org-any', mock_supabase, check_parent=False)
        assert result is True
    
    def test_line_91_parent_check_success(self):
        """Test line 91: parent check returns True when org is child"""
        user_data = {'role': 'org_admin', 'organization_id': 'org-parent'}
        mock_supabase = Mock()
        
        # Setup mock for parent check
        mock_result = Mock()
        mock_result.data = [{'id': 'org-child'}]  # Parent relationship exists
        
        mock_eq_chain = Mock()
        mock_eq_chain.execute = Mock(return_value=mock_result)
        mock_eq_chain.eq = Mock(return_value=mock_eq_chain)
        
        mock_select = Mock()
        mock_select.eq = Mock(return_value=mock_eq_chain)
        
        mock_table = Mock()
        mock_table.select = Mock(return_value=mock_select)
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        # Test parent check (line 90-91)
        result = can_access_organization(user_data, 'org-child', mock_supabase, check_parent=True)
        assert result is True
    
    def test_line_117_feature_enabled_in_toggles(self):
        """Test line 117: feature enabled returns True from toggles"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        mock_supabase = Mock()
        
        # Setup mock for toggles query
        mock_result = Mock()
        mock_result.data = [{'enabled': True}]
        
        mock_eq_chain = Mock()
        mock_eq_chain.execute = Mock(return_value=mock_result)
        mock_eq_chain.eq = Mock(return_value=mock_eq_chain)
        
        mock_select = Mock()
        mock_select.eq = Mock(return_value=mock_eq_chain)
        
        mock_table = Mock()
        mock_table.select = Mock(return_value=mock_select)
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        # Test feature access with toggle enabled (line 115-117)
        result = can_access_rag_feature(user_data, 'sales_intelligence', 'org-123', mock_supabase)
        assert result is True
    
    def test_line_121_default_enabled_in_metadata(self):
        """Test line 121: default enabled returns True from metadata"""
        user_data = {'role': 'user', 'organization_id': 'org-123'}
        mock_supabase = Mock()
        
        # Setup mocks for two queries: toggles (empty) and metadata
        mock_toggle_result = Mock()
        mock_toggle_result.data = []  # No toggle
        
        mock_metadata_result = Mock()
        mock_metadata_result.data = [{'default_enabled': True}]
        
        # Mock both queries
        execute_calls = [mock_toggle_result, mock_metadata_result]
        
        mock_eq_chain = Mock()
        mock_eq_chain.execute = Mock(side_effect=lambda: execute_calls.pop(0))
        mock_eq_chain.eq = Mock(return_value=mock_eq_chain)
        
        mock_select = Mock()
        mock_select.eq = Mock(return_value=mock_eq_chain)
        
        mock_table = Mock()
        mock_table.select = Mock(return_value=mock_select)
        
        mock_supabase.from_ = Mock(return_value=mock_table)
        
        # Test feature access with default enabled (line 119-121)
        result = can_access_rag_feature(user_data, 'sales_intelligence', 'org-123', mock_supabase)
        assert result is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=middleware.permissions', '--cov-report=html'])

