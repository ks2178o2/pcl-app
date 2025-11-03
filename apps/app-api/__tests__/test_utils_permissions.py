# apps/app-api/__tests__/test_utils_permissions.py
"""
Test utilities for Permissions Middleware mocking
Specifically handles Supabase query chains for permission checks
"""

from unittest.mock import Mock
from typing import Dict, Any, List


class SupabasePermissionMockBuilder:
    """Builder for creating Supabase mocks for permission-related queries"""
    
    def __init__(self):
        self.organizations_data = []
        self.toggles_data = []
        self.metadata_data = []
    
    def setup_organizations(self, orgs: List[Dict[str, Any]]):
        """Setup organization data"""
        self.organizations_data = orgs
    
    def setup_toggles(self, toggles: List[Dict[str, Any]]):
        """Setup RAG feature toggles"""
        self.toggles_data = toggles
    
    def setup_metadata(self, metadata: List[Dict[str, Any]]):
        """Setup feature metadata"""
        self.metadata_data = metadata
    
    def get_mock_client(self) -> Mock:
        """Get a mock Supabase client with proper query chain mocking"""
        mock_client = Mock()
        
        def from_side_effect(table_name: str):
            """Create a mock table with chained query support"""
            table_mock = Mock()
            
            # Setup select chain
            select_chain = Mock()
            
            # Setup eq chains (can be called multiple times)
            eq_result_mocks = []
            
            def eq_side_effect(col: str, val: Any):
                """Handle .eq() calls"""
                eq_mock = Mock()
                eq_result_mocks.append((col, val))
                eq_mock.eq = eq_side_effect  # Allow chaining
                eq_mock.execute = Mock(side_effect=lambda: self._execute_mock(table_name, eq_result_mocks))
                eq_mock.select = Mock(return_value=eq_mock)  # For nested calls
                return eq_mock
            
            select_chain.eq = eq_side_effect
            
            # Setup execute to return mock data
            def execute_mock():
                return self._get_mock_result(table_name)
            
            select_chain.execute = Mock(side_effect=execute_mock)
            
            table_mock.select = Mock(return_value=select_chain)
            return table_mock
        
        mock_client.from_ = Mock(side_effect=from_side_effect)
        return mock_client
    
    def _get_mock_result(self, table_name: str) -> Mock:
        """Get mock result for a table query"""
        result = Mock()
        
        if table_name == 'organizations':
            result.data = self.organizations_data if isinstance(self.organizations_data, list) else []
        elif table_name == 'organization_rag_toggles':
            result.data = self.toggles_data if isinstance(self.toggles_data, list) else []
        elif table_name == 'rag_feature_metadata':
            result.data = self.metadata_data if isinstance(self.metadata_data, list) else []
        else:
            result.data = []
        
        return result
    
    def _execute_mock(self, table_name: str, eq_filters: List[tuple]) -> Mock:
        """Execute a query with filters"""
        result = Mock()
        all_data = []
        
        if table_name == 'organizations':
            all_data = self.organizations_data
        elif table_name == 'organization_rag_toggles':
            all_data = self.toggles_data
        elif table_name == 'rag_feature_metadata':
            all_data = self.metadata_data
        
        # Filter data based on eq filters
        filtered_data = all_data
        for col, val in eq_filters:
            filtered_data = [item for item in filtered_data if item.get(col) == val]
        
        result.data = filtered_data if isinstance(filtered_data, list) else []
        return result


class PermissionsTestHelper:
    """Helper class for permission testing scenarios"""
    
    @staticmethod
    def create_org_hierarchy_mock(builder: SupabasePermissionMockBuilder, 
                                 parent_id: str, child_id: str) -> None:
        """Setup mock for parent-child organization hierarchy"""
        builder.setup_organizations([
            {'id': child_id, 'parent_organization_id': parent_id}
        ])
    
    @staticmethod
    def create_enabled_feature_mock(builder: SupabasePermissionMockBuilder,
                                   organization_id: str, 
                                   rag_feature: str) -> None:
        """Setup mock for enabled RAG feature"""
        builder.setup_toggles([
            {'organization_id': organization_id, 
             'rag_feature': rag_feature, 
             'enabled': True}
        ])
    
    @staticmethod
    def create_disabled_feature_mock(builder: SupabasePermissionMockBuilder,
                                    organization_id: str,
                                    rag_feature: str) -> None:
        """Setup mock for disabled RAG feature"""
        builder.setup_toggles([
            {'organization_id': organization_id,
             'rag_feature': rag_feature,
             'enabled': False}
        ])
    
    @staticmethod
    def create_default_enabled_metadata_mock(builder: SupabasePermissionMockBuilder,
                                           rag_feature: str) -> None:
        """Setup mock for default enabled metadata"""
        builder.setup_metadata([
            {'rag_feature': rag_feature, 'default_enabled': True}
        ])
    
    @staticmethod
    def create_all_orgs_mock(builder: SupabasePermissionMockBuilder,
                           org_ids: List[str]) -> None:
        """Setup mock to return all organization IDs"""
        builder.setup_organizations([
            {'id': org_id} for org_id in org_ids
        ])


# Export commonly used scenarios
def setup_system_admin_access_mock():
    """Setup mock for system admin who can access everything"""
    builder = SupabasePermissionMockBuilder()
    builder.setup_organizations([])
    builder.setup_toggles([])
    builder.setup_metadata([])
    return builder.get_mock_client()


def setup_org_admin_access_mock(org_id: str):
    """Setup mock for org admin in their organization"""
    builder = SupabasePermissionMockBuilder()
    builder.setup_organizations([{'id': org_id}])
    builder.setup_toggles([])
    builder.setup_metadata([])
    return builder.get_mock_client()


def setup_user_with_enabled_feature(org_id: str, rag_feature: str):
    """Setup mock for user with enabled feature"""
    builder = SupabasePermissionMockBuilder()
    builder.setup_organizations([{'id': org_id}])
    builder.setup_toggles([
        {'organization_id': org_id,
         'rag_feature': rag_feature,
         'enabled': True}
    ])
    builder.setup_metadata([])
    return builder.get_mock_client()

