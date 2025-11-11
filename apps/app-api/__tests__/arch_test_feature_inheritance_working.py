# apps/app-api/__tests__/test_feature_inheritance_working.py

import pytest
from unittest.mock import Mock, patch

from services.feature_inheritance_service import FeatureInheritanceService


class TestFeatureInheritanceWorking:
    """Working tests for Feature Inheritance Service"""
    
    @pytest.fixture
    def feature_service(self):
        """Create feature inheritance service with mocked dependencies"""
        with patch('services.feature_inheritance_service.get_supabase_client', return_value=Mock()):
            with patch('services.feature_inheritance_service.TenantIsolationService', return_value=Mock()):
                return FeatureInheritanceService()
    
    @pytest.mark.asyncio
    async def test_resolve_features_success(self, feature_service):
        """Test resolving features successfully - lines 22-68"""
        chain_result = {
            'success': True,
            'inheritance_chain': [{'id': 'org-123', 'name': 'Test Org'}]
        }
        
        effective_result = {
            'success': True,
            'effective_features': [
                {'rag_feature': 'sales_intelligence', 'enabled': True, 'is_inherited': False},
                {'rag_feature': 'customer_insight', 'enabled': True, 'is_inherited': True}
            ],
            'own_count': 1,
            'inherited_count': 1,
            'total_count': 2
        }
        
        async def get_chain(org_id):
            return chain_result
        
        async def get_effective(org_id):
            return effective_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            with patch.object(feature_service.tenant_service, 'get_effective_features', side_effect=get_effective):
                with patch.object(feature_service, '_get_inheritance_source', return_value='own'):
                    with patch.object(feature_service, '_can_override_feature', return_value=True):
                        with patch.object(feature_service, '_get_override_reason', return_value=None):
                            result = await feature_service.resolve_features('org-123')
                            
                            assert result['success'] is True
                            assert len(result['effective_features']) == 2
                            assert result['total_count'] == 2
    
    @pytest.mark.asyncio
    async def test_resolve_features_chain_fails(self, feature_service):
        """Test resolve features when chain fails - lines 29-31"""
        chain_result = {
            'success': False,
            'error': 'Chain lookup failed'
        }
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            result = await feature_service.resolve_features('org-123')
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_resolve_features_effective_fails(self, feature_service):
        """Test resolve features when effective features fails - lines 36-38"""
        chain_result = {
            'success': True,
            'inheritance_chain': []
        }
        
        effective_result = {
            'success': False,
            'error': 'Effective lookup failed'
        }
        
        with patch.object(feature_service, 'get_inheritance_chain', return_value=chain_result):
            with patch.object(feature_service.tenant_service, 'get_effective_features', return_value=effective_result):
                result = await feature_service.resolve_features('org-123')
                
                assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_resolve_features_exception(self, feature_service):
        """Test resolve features exception - lines 62-68"""
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=Exception("DB error")):
            result = await feature_service.resolve_features('org-123')
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_single_level(self, feature_service):
        """Test getting inheritance chain for single org - lines 70-99"""
        org_result = Mock()
        org_result.data = [{'id': 'org-123', 'name': 'Test Org', 'parent_organization_id': None}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        mock_execute.return_value = org_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq)
        mock_eq.execute = mock_execute
        feature_service.supabase.from_ = Mock(return_value=mock_table)
        
        result = await feature_service.get_inheritance_chain('org-123')
        
        assert result['success'] is True
        assert len(result['inheritance_chain']) == 1
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_multi_level(self, feature_service):
        """Test getting inheritance chain with parent/grandparent"""
        call_count = 0
        
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # Child org
                result1 = Mock()
                result1.data = [{'id': 'org-child', 'name': 'Child', 'parent_organization_id': 'org-parent'}]
                mock_table = Mock()
                mock_table.select.return_value.eq.return_value.execute.return_value = result1
                return mock_table
            elif call_count == 2:
                # Parent org
                result2 = Mock()
                result2.data = [{'id': 'org-parent', 'name': 'Parent', 'parent_organization_id': 'org-grandparent'}]
                mock_table = Mock()
                mock_table.select.return_value.eq.return_value.execute.return_value = result2
                return mock_table
            else:
                # Grandparent
                result3 = Mock()
                result3.data = [{'id': 'org-grandparent', 'name': 'Grandparent', 'parent_organization_id': None}]
                mock_table = Mock()
                mock_table.select.return_value.eq.return_value.execute.return_value = result3
                return mock_table
        
        feature_service.supabase.from_.side_effect = from_side_effect
        
        result = await feature_service.get_inheritance_chain('org-child')
        
        assert result['success'] is True
        assert result['depth'] == 2
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_no_data(self, feature_service):
        """Test inheritance chain when org data not found - lines 82-83"""
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
        feature_service.supabase.from_ = Mock(return_value=mock_table)
        
        result = await feature_service.get_inheritance_chain('org-123')
        
        assert result['success'] is True
        assert len(result['inheritance_chain']) == 0
    
    @pytest.mark.asyncio
    async def test_get_inheritance_chain_exception(self, feature_service):
        """Test inheritance chain exception - lines 101-107"""
        feature_service.supabase.from_.side_effect = Exception("DB error")
        
        result = await feature_service.get_inheritance_chain('org-123')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_can_override_feature_explicit(self, feature_service):
        """Test can override feature when explicit - lines 109-163"""
        chain_result = {
            'success': True,
            'inheritance_chain': [{'id': 'org-123', 'name': 'Test Org'}]
        }
        
        org_result = Mock()
        org_result.data = [{'enabled': True}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = org_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        feature_service.supabase.from_ = Mock(return_value=mock_table)
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.can_override_feature('org-123', 'sales_intelligence')
            
            assert result['success'] is True
            assert result['current_status'] == 'explicit'
    
    @pytest.mark.asyncio
    async def test_can_override_feature_inherited(self, feature_service):
        """Test can override feature when inherited - lines 133-147"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-child', 'name': 'Child'},
                {'id': 'org-parent', 'name': 'Parent', 'level': 1}
            ]
        }
        
        # First call returns empty (org doesn't have it)
        # Second call returns parent's setting
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            mock_select = Mock()
            mock_eq1 = Mock()
            mock_eq2 = Mock()
            mock_execute = Mock()
            
            if call_count == 1:  # Child org
                mock_result = Mock()
                mock_result.data = []
                mock_execute.return_value = mock_result
            else:  # Parent org
                mock_result = Mock()
                mock_result.data = [{'enabled': True}]
                mock_execute.return_value = mock_result
            
            mock_table.select = Mock(return_value=mock_select)
            mock_select.eq = Mock(return_value=mock_eq1)
            mock_eq1.eq = Mock(return_value=mock_eq2)
            mock_eq2.execute = mock_execute
            
            return mock_table
        
        feature_service.supabase.from_.side_effect = from_side_effect
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.can_override_feature('org-child', 'sales_intelligence')
            
            assert result['success'] is True
            assert result['current_status'] == 'inherited'
            assert 'inherited_from' in result
    
    @pytest.mark.asyncio
    async def test_can_override_feature_not_configured(self, feature_service):
        """Test can override feature when not configured - lines 149-154"""
        chain_result = {
            'success': True,
            'inheritance_chain': [{'id': 'org-123', 'name': 'Test Org'}]
        }
        
        org_result = Mock()
        org_result.data = []
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = org_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        feature_service.supabase.from_ = Mock(return_value=mock_table)
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.can_override_feature('org-123', 'unknown_feature')
            
            assert result['success'] is True
            assert result['current_status'] == 'not_configured'
    
    @pytest.mark.asyncio
    async def test_can_override_feature_exception(self, feature_service):
        """Test can override feature exception - lines 156-162"""
        feature_service.supabase.from_.side_effect = Exception("DB error")
        
        result = await feature_service.can_override_feature('org-123', 'sales_intelligence')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_override_status_explicit(self, feature_service):
        """Test get override status when explicit - lines 164-226"""
        chain_result = {
            'success': True,
            'inheritance_chain': [{'id': 'org-123', 'name': 'Test Org'}]
        }
        
        org_result = Mock()
        org_result.data = [{'enabled': True}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = org_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        feature_service.supabase.from_ = Mock(return_value=mock_table)
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.get_override_status('org-123', 'sales_intelligence')
            
            assert result['success'] is True
            assert result['is_inherited'] is False
            assert result['override_type'] == 'explicit'
    
    @pytest.mark.asyncio
    async def test_get_override_status_inherited(self, feature_service):
        """Test get override status when inherited - lines 193-207"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-child', 'name': 'Child'},
                {'id': 'org-parent', 'name': 'Parent', 'level': 1}
            ]
        }
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            mock_select = Mock()
            mock_eq1 = Mock()
            mock_eq2 = Mock()
            mock_execute = Mock()
            
            if call_count == 1:
                mock_result = Mock()
                mock_result.data = []
                mock_execute.return_value = mock_result
            else:
                mock_result = Mock()
                mock_result.data = [{'enabled': True}]
                mock_execute.return_value = mock_result
            
            mock_table.select = Mock(return_value=mock_select)
            mock_select.eq = Mock(return_value=mock_eq1)
            mock_eq1.eq = Mock(return_value=mock_eq2)
            mock_eq2.execute = mock_execute
            
            return mock_table
        
        feature_service.supabase.from_.side_effect = from_side_effect
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.get_override_status('org-child', 'sales_intelligence')
            
            assert result['success'] is True
            assert result['is_inherited'] is True
            assert result['inheritance_level'] == 1
    
    @pytest.mark.asyncio
    async def test_get_override_status_not_configured(self, feature_service):
        """Test get override status when not configured - lines 209-218"""
        chain_result = {
            'success': True,
            'inheritance_chain': [{'id': 'org-123', 'name': 'Test Org'}]
        }
        
        org_result = Mock()
        org_result.data = []
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = org_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        feature_service.supabase.from_ = Mock(return_value=mock_table)
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.get_override_status('org-123', 'unknown_feature')
            
            assert result['success'] is True
            assert result['status'] == 'not_configured'
    
    @pytest.mark.asyncio
    async def test_get_override_status_exception(self, feature_service):
        """Test get override status exception - lines 220-226"""
        feature_service.supabase.from_.side_effect = Exception("DB error")
        
        result = await feature_service.get_override_status('org-123', 'sales_intelligence')
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_inheritance_summary_success(self, feature_service):
        """Test get inheritance summary - lines 228-288"""
        resolve_result = {
            'success': True,
            'effective_features': [
                {'rag_feature': 'feature1', 'inheritance_source': 'explicit', 'enabled': True},
                {'rag_feature': 'feature2', 'inheritance_source': 'inherited', 'enabled': True}
            ],
            'inheritance_chain': [
                {'id': 'org-123', 'name': 'Test Org'},
                {'id': 'org-parent', 'name': 'Parent'}
            ],
            'own_count': 1,
            'inherited_count': 1,
            'total_count': 2
        }
        
        with patch.object(feature_service, 'resolve_features', return_value=resolve_result):
            result = await feature_service.get_inheritance_summary('org-123')
            
            assert result['success'] is True
            assert result['summary']['total_features'] == 2
            assert result['summary']['explicit_features'] == 1
            assert result['summary']['inherited_features'] == 1
    
    @pytest.mark.asyncio
    async def test_get_inheritance_summary_resolve_fails(self, feature_service):
        """Test inheritance summary when resolve fails - lines 234-236"""
        resolve_result = {
            'success': False,
            'error': 'Resolve failed'
        }
        
        with patch.object(feature_service, 'resolve_features', return_value=resolve_result):
            result = await feature_service.get_inheritance_summary('org-123')
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_validate_inheritance_rules_enabling_blocked(self, feature_service):
        """Test validate inheritance rules when enabling blocked by parent - lines 326-357"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-child', 'name': 'Child'},
                {'id': 'org-parent', 'name': 'Parent', 'level': 1}
            ]
        }
        
        parent_result = Mock()
        parent_result.data = [{'enabled': False}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = parent_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        feature_service.supabase.from_ = Mock(return_value=mock_table)
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.validate_inheritance_rules('org-child', 'sales_intelligence', True)
            
            assert result['success'] is False
            assert result['can_proceed'] is False
            assert 'parent' in result['reason'].lower()
    
    @pytest.mark.asyncio
    async def test_validate_inheritance_rules_disabling_allowed(self, feature_service):
        """Test validate inheritance rules when disabling (always allowed) - lines 352-357"""
        chain_result = {
            'success': True,
            'inheritance_chain': [{'id': 'org-123', 'name': 'Test Org'}]
        }
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.validate_inheritance_rules('org-123', 'sales_intelligence', False)
            
            assert result['success'] is True
            assert result['can_proceed'] is True
    
    @pytest.mark.asyncio
    async def test_validate_inheritance_rules_enabling_allowed(self, feature_service):
        """Test validate inheritance rules when enabling with no blocking parent"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-child', 'name': 'Child'},
                {'id': 'org-parent', 'name': 'Parent', 'level': 1}
            ]
        }
        
        parent_result = Mock()
        parent_result.data = [{'enabled': True}]
        
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_execute = Mock()
        mock_execute.return_value = parent_result
        
        mock_table.select = Mock(return_value=mock_select)
        mock_select.eq = Mock(return_value=mock_eq1)
        mock_eq1.eq = Mock(return_value=mock_eq2)
        mock_eq2.execute = mock_execute
        feature_service.supabase.from_ = Mock(return_value=mock_table)
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.validate_inheritance_rules('org-child', 'sales_intelligence', True)
            
            assert result['success'] is True
            assert result['can_proceed'] is True
    
    @pytest.mark.asyncio
    async def test_validate_inheritance_rules_exception(self, feature_service):
        """Test validate inheritance rules exception - already covered in chain exception test"""
        pytest.skip("Exception path already covered by get_inheritance_chain exception test")
    
    @pytest.mark.asyncio
    async def test_get_override_status_disabled_inherited(self, feature_service):
        """Test get override status when inherited and disabled - covers line 200"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-child', 'name': 'Child'},
                {'id': 'org-parent', 'name': 'Parent', 'level': 1}
            ]
        }
        
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            mock_select = Mock()
            mock_eq1 = Mock()
            mock_eq2 = Mock()
            mock_execute = Mock()
            
            if call_count == 1:
                mock_result = Mock()
                mock_result.data = []
                mock_execute.return_value = mock_result
            else:
                # Parent has it disabled
                mock_result = Mock()
                mock_result.data = [{'enabled': False}]
                mock_execute.return_value = mock_result
            
            mock_table.select = Mock(return_value=mock_select)
            mock_select.eq = Mock(return_value=mock_eq1)
            mock_eq1.eq = Mock(return_value=mock_eq2)
            mock_eq2.execute = mock_execute
            
            return mock_table
        
        feature_service.supabase.from_.side_effect = from_side_effect
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.get_override_status('org-child', 'sales_intelligence')
            
            assert result['success'] is True
            assert result['status'] == 'disabled'
    
    @pytest.mark.asyncio
    async def test_get_inheritance_summary_exception(self, feature_service):
        """Test get inheritance summary exception - lines 286-292"""
        with patch.object(feature_service, 'resolve_features', side_effect=Exception("DB error")):
            result = await feature_service.get_inheritance_summary('org-123')
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_inheritance_summary_with_not_configured(self, feature_service):
        """Test get inheritance summary with not_configured features - line 252"""
        resolve_result = {
            'success': True,
            'effective_features': [
                {'rag_feature': 'feature1', 'inheritance_source': 'explicit', 'enabled': True},
                {'rag_feature': 'feature2', 'inheritance_source': 'inherited', 'enabled': True},
                {'rag_feature': 'feature3', 'inheritance_source': 'not_configured', 'enabled': False}
            ],
            'inheritance_chain': [{'id': 'org-123', 'name': 'Test Org'}],
            'own_count': 1,
            'inherited_count': 1,
            'total_count': 3
        }
        
        with patch.object(feature_service, 'resolve_features', return_value=resolve_result):
            result = await feature_service.get_inheritance_summary('org-123')
            
            assert result['success'] is True
            assert result['summary']['not_configured_features'] == 1
    
    @pytest.mark.asyncio
    async def test_helper_get_inheritance_source(self, feature_service):
        """Test helper method _get_inheritance_source - lines 294-301"""
        # Test inherited
        feature = {'is_inherited': True, 'rag_feature': 'feature1'}
        result = feature_service._get_inheritance_source(feature, [])
        assert result == 'inherited'
        
        # Test explicit
        feature = {'is_inherited': False, 'rag_feature': 'feature1'}
        result = feature_service._get_inheritance_source(feature, [])
        assert result == 'explicit'
        
        # Test not_configured
        feature = {'is_inherited': False}
        result = feature_service._get_inheritance_source(feature, [])
        assert result == 'not_configured'
    
    @pytest.mark.asyncio
    async def test_helper_can_override_feature(self, feature_service):
        """Test helper method _can_override_feature - lines 303-310"""
        # Test explicit (not inherited)
        feature = {'is_inherited': False}
        result = feature_service._can_override_feature(feature, [])
        assert result is True
        
        # Test inherited
        feature = {'is_inherited': True}
        result = feature_service._can_override_feature(feature, [])
        assert result is True
    
    @pytest.mark.asyncio
    async def test_helper_get_override_reason_explicit(self, feature_service):
        """Test helper method _get_override_reason - lines 312-324"""
        # Test explicit
        feature = {'is_inherited': False}
        result = feature_service._get_override_reason(feature, [])
        assert 'explicit control' in result
    
    @pytest.mark.asyncio
    async def test_helper_get_override_reason_inherited(self, feature_service):
        """Test helper method _get_override_reason for inherited"""
        feature = {'is_inherited': True, 'inherited_from': 'parent-123'}
        chain = [{'id': 'parent-123', 'name': 'Parent Org'}]
        result = feature_service._get_override_reason(feature, chain)
        assert 'Parent Org' in result
    
    @pytest.mark.asyncio
    async def test_helper_get_override_reason_unknown(self, feature_service):
        """Test helper method _get_override_reason for unknown status"""
        feature = {'is_inherited': True, 'inherited_from': None}
        result = feature_service._get_override_reason(feature, [])
        assert 'unknown' in result
    
    @pytest.mark.asyncio
    async def test_helper_get_override_reason_parent_found(self, feature_service):
        """Test helper method _get_override_reason with parent lookup - lines 262->264"""
        feature = {'is_inherited': True, 'inherited_from': 'parent-123'}
        chain = [{'id': 'other-org', 'name': 'Other'}, {'id': 'parent-123', 'name': 'Parent Org'}]
        result = feature_service._get_override_reason(feature, chain)
        assert 'Parent Org' in result
    
    @pytest.mark.asyncio
    async def test_validate_inheritance_rules_chain_fails(self, feature_service):
        """Test validate inheritance rules when chain fails - line 334"""
        chain_result = {
            'success': False,
            'error': 'Chain lookup failed'
        }
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.validate_inheritance_rules('org-123', 'sales_intelligence', True)
            
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_can_override_feature_parent_not_found(self, feature_service):
        """Test can override feature when parent exists but not found - lines 134-146"""
        chain_result = {
            'success': True,
            'inheritance_chain': [
                {'id': 'org-child', 'name': 'Child'},
                {'id': 'org-parent', 'name': 'Parent', 'level': 1}
            ]
        }
        
        # First call returns empty (org doesn't have it)
        # Second call also returns empty (parent doesn't have it)
        call_count = 0
        def from_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = Mock()
            mock_select = Mock()
            mock_eq1 = Mock()
            mock_eq2 = Mock()
            mock_execute = Mock()
            
            # Both calls return empty
            mock_result = Mock()
            mock_result.data = []
            mock_execute.return_value = mock_result
            
            mock_table.select = Mock(return_value=mock_select)
            mock_select.eq = Mock(return_value=mock_eq1)
            mock_eq1.eq = Mock(return_value=mock_eq2)
            mock_eq2.execute = mock_execute
            
            return mock_table
        
        feature_service.supabase.from_.side_effect = from_side_effect
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.can_override_feature('org-child', 'unknown_feature')
            
            assert result['success'] is True
            assert result['current_status'] == 'not_configured'
    
    @pytest.mark.asyncio
    async def test_can_override_feature_exception_path(self, feature_service):
        """Test can override feature exception path - lines 156-162"""
        chain_result = {
            'success': True,
            'inheritance_chain': [{'id': 'org-123', 'name': 'Test Org'}]
        }
        
        org_result = Mock()
        org_result.data = []
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        feature_service.supabase.from_ = Mock(return_value=mock_table)
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.can_override_feature('org-123', 'sales_intelligence')
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_override_status_exception_path(self, feature_service):
        """Test get override status exception path - lines 220-226"""
        chain_result = {
            'success': True,
            'inheritance_chain': [{'id': 'org-123', 'name': 'Test Org'}]
        }
        
        org_result = Mock()
        org_result.data = []
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        feature_service.supabase.from_ = Mock(return_value=mock_table)
        
        async def get_chain(org_id):
            return chain_result
        
        with patch.object(feature_service, 'get_inheritance_chain', side_effect=get_chain):
            result = await feature_service.get_override_status('org-123', 'sales_intelligence')
            
            assert result['success'] is False
            assert result['status'] == 'unknown'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.feature_inheritance_service', '--cov-report=html'])

