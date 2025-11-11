"""
Tests for feature_inheritance_service.py to achieve 95% coverage
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.feature_inheritance_service import FeatureInheritanceService


class TestFeatureInheritanceService:
    """Test FeatureInheritanceService"""
    
    @pytest.fixture
    def feature_service(self):
        """Create FeatureInheritanceService instance"""
        with patch('services.feature_inheritance_service.get_supabase_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            return FeatureInheritanceService()
    
    @pytest.mark.asyncio
    async def test_resolve_features_success(self, feature_service):
        """Test successful feature resolution"""
        # Mock inheritance chain
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-1', 'name': 'Org 1', 'parent_organization_id': None},
                {'id': 'org-2', 'name': 'Org 2', 'parent_organization_id': 'org-1'}
            ]
        }
        
        # Mock effective features
        effective_result = {
            'success': True,
            'effective_features': [
                {'rag_feature': 'feature1', 'enabled': True, 'is_inherited': False},
                {'rag_feature': 'feature2', 'enabled': True, 'is_inherited': True, 'inherited_from': 'org-1'}
            ],
            'own_count': 1,
            'inherited_count': 1,
            'total_count': 2
        }
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            with patch.object(feature_service.tenant_service, 'get_effective_features', return_value=effective_result):
                result = await feature_service.resolve_features('org-2')
                
                assert result['success'] is True
                assert len(result['effective_features']) == 2
                assert result['own_count'] == 1
                assert result['inherited_count'] == 1
                # Check that features are enhanced
                assert 'inheritance_source' in result['effective_features'][0]
                assert 'can_override' in result['effective_features'][0]
    
    @pytest.mark.asyncio
    async def test_resolve_features_chain_failure(self, feature_service):
        """Test resolve_features when chain fails"""
        chain_result = {'success': False, 'error': 'Chain error'}
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.resolve_features('org-1')
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_resolve_features_effective_failure(self, feature_service):
        """Test resolve_features when effective features fail"""
        chain_result = {'success': True, 'inheritance_chain': []}
        effective_result = {'success': False, 'error': 'Effective error'}
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            with patch.object(feature_service.tenant_service, 'get_effective_features', return_value=effective_result):
                result = await feature_service.resolve_features('org-1')
                
                assert result['success'] is False
                assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_resolve_features_exception(self, feature_service):
        """Test resolve_features exception handling"""
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=Exception("DB error")):
            result = await feature_service.resolve_features('org-1')
            
            assert result['success'] is False
            assert 'error' in result
            assert result['effective_features'] == []
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_success(self, feature_service):
        """Test successful inheritance chain retrieval"""
        # Mock org hierarchy: org-3 -> org-2 -> org-1 -> None
        org1_result = Mock()
        org1_result.data = [{'id': 'org-1', 'name': 'Org 1', 'parent_organization_id': None}]
        
        org2_result = Mock()
        org2_result.data = [{'id': 'org-2', 'name': 'Org 2', 'parent_organization_id': 'org-1'}]
        
        org3_result = Mock()
        org3_result.data = [{'id': 'org-3', 'name': 'Org 3', 'parent_organization_id': 'org-2'}]
        
        call_count = [0]
        def execute_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return org3_result
            elif call_count[0] == 2:
                return org2_result
            else:
                return org1_result
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(side_effect=execute_side_effect)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        result = await feature_service.get_inheritance_chain('org-3')
        
        assert result['success'] is True
        assert len(result['inheritance_chain']) == 3
        assert result['depth'] == 2  # Exclude org-3 itself
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_no_parent(self, feature_service):
        """Test inheritance chain with no parent"""
        org_result = Mock()
        org_result.data = [{'id': 'org-1', 'name': 'Org 1', 'parent_organization_id': None}]
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=org_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        result = await feature_service.get_inheritance_chain('org-1')
        
        assert result['success'] is True
        assert len(result['inheritance_chain']) == 1
        assert result['depth'] == 0
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_not_found(self, feature_service):
        """Test inheritance chain when org not found"""
        org_result = Mock()
        org_result.data = []
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=org_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        result = await feature_service.get_inheritance_chain('org-1')
        
        assert result['success'] is True
        assert len(result['inheritance_chain']) == 0
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_exception(self, feature_service):
        """Test inheritance chain exception"""
        feature_service.supabase.from_.side_effect = Exception("DB error")
        
        result = await feature_service.get_inheritance_chain('org-1')
        
        assert result['success'] is False
        assert 'error' in result
        assert result['inheritance_chain'] == []
    
    @pytest.mark.asyncio
    async def test_can_override_feature_explicit(self, feature_service):
        """Test can_override_feature when org has explicit setting"""
        chain_result = {
            'success': True,
            'inheritance_chain': [{'id': 'org-1', 'name': 'Org 1'}]
        }
        
        org_result = Mock()
        org_result.data = [{'rag_feature': 'feature1', 'enabled': True}]
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=org_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.can_override_feature('org-1', 'feature1')
            
            assert result['success'] is True
            assert result['can_override'] is True
            assert result['current_status'] == 'explicit'
    
    @pytest.mark.asyncio
    async def test_can_override_feature_inherited(self, feature_service):
        """Test can_override_feature when feature is inherited"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-2', 'name': 'Org 2', 'level': 0},
                {'id': 'org-1', 'name': 'Org 1', 'level': 1}
            ]
        }
        
        # Org has no explicit setting
        org_result = Mock()
        org_result.data = []
        
        # Parent has the feature
        parent_result = Mock()
        parent_result.data = [{'rag_feature': 'feature1', 'enabled': True}]
        
        call_count = [0]
        def execute_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return org_result
            else:
                return parent_result
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(side_effect=execute_side_effect)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.can_override_feature('org-2', 'feature1')
            
            assert result['success'] is True
            assert result['can_override'] is True
            assert result['current_status'] == 'inherited'
            assert result['inherited_from'] == 'org-1'
    
    @pytest.mark.asyncio
    async def test_can_override_feature_inherited_multiple_parents(self, feature_service):
        """Test can_override_feature when checking multiple parents (line 137->134)"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-3', 'name': 'Org 3', 'level': 0},
                {'id': 'org-2', 'name': 'Org 2', 'level': 1},
                {'id': 'org-1', 'name': 'Org 1', 'level': 2}
            ]
        }
        
        # Org has no explicit setting
        org_result = Mock()
        org_result.data = []
        
        # First parent (org-2) doesn't have feature
        parent1_result = Mock()
        parent1_result.data = []
        
        # Second parent (org-1) has the feature
        parent2_result = Mock()
        parent2_result.data = [{'rag_feature': 'feature1', 'enabled': True}]
        
        call_count = [0]
        def execute_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return org_result
            elif call_count[0] == 2:
                return parent1_result
            else:
                return parent2_result
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(side_effect=execute_side_effect)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.can_override_feature('org-3', 'feature1')
            
            assert result['success'] is True
            assert result['current_status'] == 'inherited'
            assert result['inherited_from'] == 'org-1'
    
    @pytest.mark.asyncio
    async def test_can_override_feature_not_configured(self, feature_service):
        """Test can_override_feature when feature not configured"""
        chain_result = {
            'success': True,
            'inheritance_chain': [{'id': 'org-1', 'name': 'Org 1'}]
        }
        
        org_result = Mock()
        org_result.data = []
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=org_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.can_override_feature('org-1', 'feature1')
            
            assert result['success'] is True
            assert result['can_override'] is True
            assert result['current_status'] == 'not_configured'
    
    @pytest.mark.asyncio
    async def test_can_override_feature_exception(self, feature_service):
        """Test can_override_feature exception"""
        chain_result = {'success': False, 'error': 'Chain error'}
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.can_override_feature('org-1', 'feature1')
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_override_status_explicit(self, feature_service):
        """Test get_override_status with explicit setting"""
        chain_result = {
            'success': True,
            'inheritance_chain': [{'id': 'org-1', 'name': 'Org 1'}]
        }
        
        org_result = Mock()
        org_result.data = [{'rag_feature': 'feature1', 'enabled': True}]
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=org_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.get_override_status('org-1', 'feature1')
            
            assert result['success'] is True
            assert result['status'] == 'enabled'
            assert result['is_inherited'] is False
            assert result['override_type'] == 'explicit'
    
    @pytest.mark.asyncio
    async def test_get_override_status_inherited(self, feature_service):
        """Test get_override_status with inherited feature"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-2', 'name': 'Org 2', 'level': 0},
                {'id': 'org-1', 'name': 'Org 1', 'level': 1}
            ]
        }
        
        org_result = Mock()
        org_result.data = []
        
        parent_result = Mock()
        parent_result.data = [{'rag_feature': 'feature1', 'enabled': False}]
        
        call_count = [0]
        def execute_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return org_result
            else:
                return parent_result
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(side_effect=execute_side_effect)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.get_override_status('org-2', 'feature1')
            
            assert result['success'] is True
            assert result['status'] == 'disabled'
            assert result['is_inherited'] is True
            assert result['inherited_from'] == 'org-1'
            assert result['override_type'] == 'inherited'
    
    @pytest.mark.asyncio
    async def test_get_override_status_inherited_multiple_parents(self, feature_service):
        """Test get_override_status when checking multiple parents (line 196->193)"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-3', 'name': 'Org 3', 'level': 0},
                {'id': 'org-2', 'name': 'Org 2', 'level': 1},
                {'id': 'org-1', 'name': 'Org 1', 'level': 2}
            ]
        }
        
        org_result = Mock()
        org_result.data = []
        
        parent1_result = Mock()
        parent1_result.data = []  # org-2 doesn't have feature
        
        parent2_result = Mock()
        parent2_result.data = [{'rag_feature': 'feature1', 'enabled': True}]
        
        call_count = [0]
        def execute_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return org_result
            elif call_count[0] == 2:
                return parent1_result
            else:
                return parent2_result
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(side_effect=execute_side_effect)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.get_override_status('org-3', 'feature1')
            
            assert result['success'] is True
            assert result['is_inherited'] is True
            assert result['inherited_from'] == 'org-1'
    
    @pytest.mark.asyncio
    async def test_get_override_status_not_configured(self, feature_service):
        """Test get_override_status when not configured"""
        chain_result = {
            'success': True,
            'inheritance_chain': [{'id': 'org-1', 'name': 'Org 1'}]
        }
        
        org_result = Mock()
        org_result.data = []
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=org_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.get_override_status('org-1', 'feature1')
            
            assert result['success'] is True
            assert result['status'] == 'not_configured'
            assert result['override_type'] == 'not_configured'
    
    @pytest.mark.asyncio
    async def test_get_inheritance_summary_success(self, feature_service):
        """Test get_inheritance_summary"""
        resolve_result = {
            'success': True,
            'effective_features': [
                {'rag_feature': 'feature1', 'enabled': True, 'inheritance_source': 'explicit'},
                {'rag_feature': 'feature2', 'enabled': True, 'inheritance_source': 'inherited', 'inherited_from': 'org-1'},
                {'rag_feature': 'feature3', 'enabled': False, 'inheritance_source': 'not_configured'}
            ],
            'inheritance_chain': [
                {'id': 'org-2', 'name': 'Org 2'},
                {'id': 'org-1', 'name': 'Org 1'}
            ]
        }
        
        with patch.object(feature_service, 'resolve_features', return_value=resolve_result):
            result = await feature_service.get_inheritance_summary('org-2')
            
            assert result['success'] is True
            assert result['summary']['total_features'] == 3
            assert result['summary']['explicit_features'] == 1
            assert result['summary']['inherited_features'] == 1
            assert result['summary']['not_configured_features'] == 1
            assert result['summary']['enabled_features'] == 2
    
    @pytest.mark.asyncio
    async def test_get_inheritance_summary_failure(self, feature_service):
        """Test get_inheritance_summary when resolve fails"""
        resolve_result = {'success': False, 'error': 'Resolve error'}
        
        with patch.object(feature_service, 'resolve_features', return_value=resolve_result):
            result = await feature_service.get_inheritance_summary('org-1')
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_inheritance_summary_exception(self, feature_service):
        """Test get_inheritance_summary exception"""
        with patch.object(feature_service, 'resolve_features', side_effect=Exception("DB error")):
            result = await feature_service.get_inheritance_summary('org-1')
            
            assert result['success'] is False
            assert 'error' in result
    
    def test_get_inheritance_source_explicit(self, feature_service):
        """Test _get_inheritance_source for explicit feature"""
        feature = {'rag_feature': 'feature1', 'is_inherited': False}
        chain = []
        
        result = feature_service._get_inheritance_source(feature, chain)
        assert result == 'explicit'
    
    def test_get_inheritance_source_inherited(self, feature_service):
        """Test _get_inheritance_source for inherited feature"""
        feature = {'rag_feature': 'feature1', 'is_inherited': True}
        chain = []
        
        result = feature_service._get_inheritance_source(feature, chain)
        assert result == 'inherited'
    
    def test_get_inheritance_source_not_configured(self, feature_service):
        """Test _get_inheritance_source for not configured"""
        feature = {}  # No rag_feature
        chain = []
        
        result = feature_service._get_inheritance_source(feature, chain)
        assert result == 'not_configured'
    
    def test_can_override_feature_helper(self, feature_service):
        """Test _can_override_feature helper"""
        # Explicit feature
        feature1 = {'is_inherited': False}
        result1 = feature_service._can_override_feature(feature1, [])
        assert result1 is True
        
        # Inherited feature
        feature2 = {'is_inherited': True}
        result2 = feature_service._can_override_feature(feature2, [])
        assert result2 is True
    
    def test_get_override_reason_explicit(self, feature_service):
        """Test _get_override_reason for explicit feature"""
        feature = {'is_inherited': False}
        chain = []
        
        result = feature_service._get_override_reason(feature, chain)
        assert 'explicit control' in result
    
    def test_get_override_reason_inherited(self, feature_service):
        """Test _get_override_reason for inherited feature"""
        feature = {'is_inherited': True, 'inherited_from': 'org-1'}
        chain = [{'id': 'org-1', 'name': 'Parent Org'}]
        
        result = feature_service._get_override_reason(feature, chain)
        assert 'Parent Org' in result
        assert 'can be overridden' in result
    
    def test_get_override_reason_unknown(self, feature_service):
        """Test _get_override_reason for unknown (line 318->324)"""
        feature = {'is_inherited': True, 'inherited_from': 'org-999'}
        chain = [{'id': 'org-1', 'name': 'Org 1'}]
        
        result = feature_service._get_override_reason(feature, chain)
        assert 'unknown' in result
    
    def test_get_override_reason_inherited_no_source(self, feature_service):
        """Test _get_override_reason when inherited_from is None"""
        feature = {'is_inherited': True, 'inherited_from': None}
        chain = [{'id': 'org-1', 'name': 'Org 1'}]
        
        result = feature_service._get_override_reason(feature, chain)
        assert 'unknown' in result
    
    @pytest.mark.asyncio
    async def test_validate_inheritance_rules_enable_allowed(self, feature_service):
        """Test validate_inheritance_rules when enabling is allowed"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-2', 'name': 'Org 2'},
                {'id': 'org-1', 'name': 'Org 1'}
            ]
        }
        
        parent_result = Mock()
        parent_result.data = [{'enabled': True}]
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=parent_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.validate_inheritance_rules('org-2', 'feature1', True)
            
            assert result['success'] is True
            assert result['can_proceed'] is True
    
    @pytest.mark.asyncio
    async def test_validate_inheritance_rules_enable_blocked(self, feature_service):
        """Test validate_inheritance_rules when enabling is blocked by parent"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-2', 'name': 'Org 2'},
                {'id': 'org-1', 'name': 'Org 1'}
            ]
        }
        
        parent_result = Mock()
        parent_result.data = [{'enabled': False}]
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=parent_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.validate_inheritance_rules('org-2', 'feature1', True)
            
            assert result['success'] is False
            assert result['can_proceed'] is False
            assert 'disabled' in result['reason']
    
    @pytest.mark.asyncio
    async def test_validate_inheritance_rules_disable_allowed(self, feature_service):
        """Test validate_inheritance_rules when disabling is always allowed"""
        chain_result = {
            'success': True,
            'inheritance_chain': [{'id': 'org-1', 'name': 'Org 1'}]
        }
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.validate_inheritance_rules('org-1', 'feature1', False)
            
            assert result['success'] is True
            assert result['can_proceed'] is True
    
    @pytest.mark.asyncio
    async def test_validate_inheritance_rules_exception(self, feature_service):
        """Test validate_inheritance_rules exception"""
        chain_result = {'success': False, 'error': 'Chain error'}
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.validate_inheritance_rules('org-1', 'feature1', True)
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_inheritance_summary_inherited_by_source(self, feature_service):
        """Test get_inheritance_summary with inherited_by_source grouping"""
        resolve_result = {
            'success': True,
            'effective_features': [
                {'rag_feature': 'feature1', 'enabled': True, 'inheritance_source': 'inherited', 'inherited_from': 'org-1'},
                {'rag_feature': 'feature2', 'enabled': True, 'inheritance_source': 'inherited', 'inherited_from': 'org-1'},
                {'rag_feature': 'feature3', 'enabled': False, 'inheritance_source': 'inherited', 'inherited_from': 'org-2'}
            ],
            'inheritance_chain': [
                {'id': 'org-3', 'name': 'Org 3'},
                {'id': 'org-1', 'name': 'Org 1'},
                {'id': 'org-2', 'name': 'Org 2'}
            ]
        }
        
        with patch.object(feature_service, 'resolve_features', return_value=resolve_result):
            result = await feature_service.get_inheritance_summary('org-3')
            
            assert result['success'] is True
            assert 'inherited_by_source' in result['summary']
            assert 'org-1' in result['summary']['inherited_by_source']
            assert len(result['summary']['inherited_by_source']['org-1']) == 2
    
    @pytest.mark.asyncio
    async def test_can_override_feature_chain_failure(self, feature_service):
        """Test can_override_feature when chain fails"""
        chain_result = {'success': False, 'error': 'Chain error'}
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.can_override_feature('org-1', 'feature1')
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_can_override_feature_general_exception(self, feature_service):
        """Test can_override_feature general exception"""
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=Exception("DB error")):
            result = await feature_service.can_override_feature('org-1', 'feature1')
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_override_status_chain_failure(self, feature_service):
        """Test get_override_status when chain fails"""
        chain_result = {'success': False, 'error': 'Chain error'}
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.get_override_status('org-1', 'feature1')
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_get_override_status_exception(self, feature_service):
        """Test get_override_status exception"""
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=Exception("DB error")):
            result = await feature_service.get_override_status('org-1', 'feature1')
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_validate_inheritance_rules_parent_not_found(self, feature_service):
        """Test validate_inheritance_rules when parent doesn't have feature"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-2', 'name': 'Org 2'},
                {'id': 'org-1', 'name': 'Org 1'}
            ]
        }
        
        parent_result = Mock()
        parent_result.data = []  # Parent doesn't have feature
        
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(return_value=parent_result)
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.validate_inheritance_rules('org-2', 'feature1', True)
            
            assert result['success'] is True
            assert result['can_proceed'] is True
    
    @pytest.mark.asyncio
    async def test_validate_inheritance_rules_exception_handling(self, feature_service):
        """Test validate_inheritance_rules exception handling"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-2', 'name': 'Org 2'},
                {'id': 'org-1', 'name': 'Org 1'}
            ]
        }
        
        # Make the query raise an exception
        select_chain = Mock()
        select_chain.eq = Mock(return_value=select_chain)
        select_chain.execute = Mock(side_effect=Exception("DB error"))
        
        table_mock = Mock()
        table_mock.select = Mock(return_value=select_chain)
        feature_service.supabase.from_.return_value = table_mock
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.validate_inheritance_rules('org-2', 'feature1', True)
            
            assert result['success'] is False
            assert 'error' in result['reason']

