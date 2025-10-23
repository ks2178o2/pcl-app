# apps/app-api/services/tenant_isolation_service.py

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class TenantIsolationService:
    """Service for managing tenant isolation policies and quotas"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    # ==================== TENANT ISOLATION POLICIES ====================
    
    async def enforce_tenant_isolation(self, user_id: str, organization_id: str, 
                                     resource_type: str, resource_id: str) -> Dict[str, Any]:
        """Enforce tenant isolation for resource access"""
        try:
            # Get user's organization
            user_org = await self._get_user_organization(user_id)
            if not user_org:
                return {
                    "success": False,
                    "error": "User organization not found"
                }
            
            # Check if user is trying to access resources from different organization
            if user_org['organization_id'] != organization_id:
                # Check if user has cross-tenant access permissions
                has_cross_access = await self._check_cross_tenant_access(
                    user_id, organization_id, resource_type
                )
                
                if not has_cross_access:
                    return {
                        "success": False,
                        "error": "Cross-tenant access denied",
                        "isolation_violation": True
                    }
            
            return {
                "success": True,
                "access_granted": True,
                "user_organization": user_org['organization_id']
            }
            
        except Exception as e:
            logger.error(f"Error enforcing tenant isolation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_isolation_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tenant isolation policy"""
        try:
            required_fields = ['organization_id', 'policy_type', 'policy_name', 'policy_rules']
            for field in required_fields:
                if not policy_data.get(field):
                    raise ValueError(f"{field} is required")
            
            policy_data['created_at'] = datetime.utcnow().isoformat()
            policy_data['status'] = policy_data.get('status', 'active')
            
            result = self.supabase.from_('tenant_isolation_policies').insert(policy_data).execute()
            
            if result.data:
                return {
                    "success": True,
                    "policy_id": result.data[0]['id']
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create isolation policy"
                }
                
        except Exception as e:
            logger.error(f"Error creating isolation policy: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_isolation_policies(self, organization_id: str) -> Dict[str, Any]:
        """Get isolation policies for an organization"""
        try:
            result = self.supabase.from_('tenant_isolation_policies').select('*').eq('organization_id', organization_id).eq('status', 'active').execute()
            
            return {
                "success": True,
                "policies": result.data or []
            }
            
        except Exception as e:
            logger.error(f"Error getting isolation policies: {e}")
            return {
                "success": False,
                "error": str(e),
                "policies": []
            }
    
    # ==================== QUOTA MANAGEMENT ====================
    
    async def check_quota_limits(self, organization_id: str, operation_type: str, 
                               quantity: int = 1) -> Dict[str, Any]:
        """Check if an operation would exceed quota limits"""
        try:
            # Get organization quotas
            quotas_result = await self._get_organization_quotas(organization_id)
            if not quotas_result['success']:
                return quotas_result
            
            quotas = quotas_result['quotas']
            
            # Check specific quota based on operation type
            if operation_type == 'context_items':
                if quotas['current_context_items'] + quantity > quotas['max_context_items']:
                    return {
                        "success": False,
                        "quota_exceeded": True,
                        "quota_type": "context_items",
                        "current": quotas['current_context_items'],
                        "limit": quotas['max_context_items'],
                        "requested": quantity
                    }
            
            elif operation_type == 'global_access':
                if quotas['current_global_access'] + quantity > quotas['max_global_access_features']:
                    return {
                        "success": False,
                        "quota_exceeded": True,
                        "quota_type": "global_access",
                        "current": quotas['current_global_access'],
                        "limit": quotas['max_global_access_features'],
                        "requested": quantity
                    }
            
            elif operation_type == 'sharing_requests':
                if quotas['current_sharing_requests'] + quantity > quotas['max_sharing_requests']:
                    return {
                        "success": False,
                        "quota_exceeded": True,
                        "quota_type": "sharing_requests",
                        "current": quotas['current_sharing_requests'],
                        "limit": quotas['max_sharing_requests'],
                        "requested": quantity
                    }
            
            return {
                "success": True,
                "quota_check_passed": True,
                "quotas": quotas
            }
            
        except Exception as e:
            logger.error(f"Error checking quota limits: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_quota_usage(self, organization_id: str, operation_type: str, 
                                quantity: int, operation: str = 'increment') -> Dict[str, Any]:
        """Update quota usage after an operation"""
        try:
            # Get current quotas
            quotas_result = await self._get_organization_quotas(organization_id)
            if not quotas_result['success']:
                return quotas_result
            
            quotas = quotas_result['quotas']
            
            # Update the appropriate quota counter
            if operation_type == 'context_items':
                if operation == 'increment':
                    quotas['current_context_items'] += quantity
                else:  # decrement
                    quotas['current_context_items'] = max(0, quotas['current_context_items'] - quantity)
            
            elif operation_type == 'global_access':
                if operation == 'increment':
                    quotas['current_global_access'] += quantity
                else:  # decrement
                    quotas['current_global_access'] = max(0, quotas['current_global_access'] - quantity)
            
            elif operation_type == 'sharing_requests':
                if operation == 'increment':
                    quotas['current_sharing_requests'] += quantity
                else:  # decrement
                    quotas['current_sharing_requests'] = max(0, quotas['current_sharing_requests'] - quantity)
            
            # Update quotas in database
            quotas['updated_at'] = datetime.utcnow().isoformat()
            
            result = self.supabase.from_('organization_context_quotas').update(quotas).eq('organization_id', organization_id).execute()
            
            if result.data:
                return {
                    "success": True,
                    "updated_quotas": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update quota usage"
                }
                
        except Exception as e:
            logger.error(f"Error updating quota usage: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def reset_quota_usage(self, organization_id: str, quota_type: Optional[str] = None) -> Dict[str, Any]:
        """Reset quota usage for an organization"""
        try:
            # Get current quotas
            quotas_result = await self._get_organization_quotas(organization_id)
            if not quotas_result['success']:
                return quotas_result
            
            quotas = quotas_result['quotas']
            
            # Reset specific quota or all quotas
            if quota_type:
                quotas[f'current_{quota_type}'] = 0
            else:
                quotas['current_context_items'] = 0
                quotas['current_global_access'] = 0
                quotas['current_sharing_requests'] = 0
            
            quotas['updated_at'] = datetime.utcnow().isoformat()
            
            result = self.supabase.from_('organization_context_quotas').update(quotas).eq('organization_id', organization_id).execute()
            
            if result.data:
                return {
                    "success": True,
                    "reset_quotas": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to reset quota usage"
                }
                
        except Exception as e:
            logger.error(f"Error resetting quota usage: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== RAG FEATURE TOGGLES ====================
    
    async def get_rag_feature_toggles(self, organization_id: str) -> Dict[str, Any]:
        """Get RAG feature toggles for an organization"""
        try:
            result = self.supabase.from_('organization_rag_toggles').select('*').eq('organization_id', organization_id).execute()
            
            # If no toggles exist, create default ones
            if not result.data:
                default_toggles = await self._create_default_rag_toggles(organization_id)
                return {
                    "success": True,
                    "toggles": default_toggles
                }
            
            return {
                "success": True,
                "toggles": result.data
            }
            
        except Exception as e:
            logger.error(f"Error getting RAG feature toggles: {e}")
            return {
                "success": False,
                "error": str(e),
                "toggles": []
            }
    
    async def update_rag_feature_toggle(self, organization_id: str, rag_feature: str, 
                                       enabled: bool) -> Dict[str, Any]:
        """Update a RAG feature toggle for an organization"""
        try:
            # Check if toggle exists
            existing = self.supabase.from_('organization_rag_toggles').select('*').eq('organization_id', organization_id).eq('rag_feature', rag_feature).execute()
            
            if existing.data:
                # Update existing toggle
                result = self.supabase.from_('organization_rag_toggles').update({
                    'enabled': enabled,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('organization_id', organization_id).eq('rag_feature', rag_feature).execute()
            else:
                # Create new toggle
                result = self.supabase.from_('organization_rag_toggles').insert({
                    'organization_id': organization_id,
                    'rag_feature': rag_feature,
                    'enabled': enabled,
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
            
            if result.data:
                return {
                    "success": True,
                    "toggle": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update RAG feature toggle"
                }
                
        except Exception as e:
            logger.error(f"Error updating RAG feature toggle: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def bulk_update_rag_toggles(self, organization_id: str, 
                                    toggle_updates: Dict[str, bool]) -> Dict[str, Any]:
        """Bulk update multiple RAG feature toggles"""
        try:
            updated_toggles = []
            
            for rag_feature, enabled in toggle_updates.items():
                result = await self.update_rag_feature_toggle(organization_id, rag_feature, enabled)
                if result['success']:
                    updated_toggles.append(result['toggle'])
                else:
                    logger.error(f"Failed to update toggle for {rag_feature}: {result['error']}")
            
            return {
                "success": True,
                "updated_toggles": updated_toggles,
                "total_updated": len(updated_toggles)
            }
            
        except Exception as e:
            logger.error(f"Error bulk updating RAG toggles: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== HELPER METHODS ====================
    
    async def _get_user_organization(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's organization information"""
        try:
            result = self.supabase.from_('profiles').select('organization_id').eq('user_id', user_id).single().execute()
            return result.data if result.data else None
        except:
            return None
    
    async def _check_cross_tenant_access(self, user_id: str, target_org_id: str, 
                                       resource_type: str) -> bool:
        """Check if user has cross-tenant access permissions"""
        try:
            # Get user's role
            user_result = self.supabase.from_('profiles').select('role').eq('user_id', user_id).single().execute()
            if not user_result.data:
                return False
            
            user_role = user_result.data['role']
            
            # System admins have cross-tenant access
            if user_role == 'system_admin':
                return True
            
            # Check for specific cross-tenant permissions
            cross_access_result = self.supabase.from_('cross_tenant_permissions').select('*').eq('user_id', user_id).eq('target_organization_id', target_org_id).eq('resource_type', resource_type).eq('enabled', True).execute()
            
            return len(cross_access_result.data or []) > 0
            
        except:
            return False
    
    async def _get_organization_quotas(self, organization_id: str) -> Dict[str, Any]:
        """Get organization quotas"""
        try:
            result = self.supabase.from_('organization_context_quotas').select('*').eq('organization_id', organization_id).single().execute()
            
            if result.data:
                return {
                    "success": True,
                    "quotas": result.data
                }
            else:
                # Create default quotas if they don't exist
                default_quotas = {
                    'organization_id': organization_id,
                    'max_context_items': 1000,
                    'max_global_access_features': 10,
                    'max_sharing_requests': 50,
                    'current_context_items': 0,
                    'current_global_access': 0,
                    'current_sharing_requests': 0
                }
                
                create_result = self.supabase.from_('organization_context_quotas').insert(default_quotas).execute()
                
                return {
                    "success": True,
                    "quotas": create_result.data[0] if create_result.data else default_quotas
                }
                
        except Exception as e:
            logger.error(f"Error getting organization quotas: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== FEATURE INHERITANCE ====================
    
    async def get_inherited_features(self, organization_id: str) -> Dict[str, Any]:
        """Get RAG features inherited from parent organization"""
        try:
            # Get organization's parent
            org_result = self.supabase.from_('organizations').select('parent_organization_id').eq('id', organization_id).execute()
            
            if not org_result.data or not org_result.data[0].get('parent_organization_id'):
                return {
                    "success": True,
                    "inherited_features": [],
                    "parent_organization_id": None
                }
            
            parent_id = org_result.data[0]['parent_organization_id']
            
            # Get parent's enabled features
            parent_result = self.supabase.from_('organization_rag_toggles').select('*').eq('organization_id', parent_id).eq('enabled', True).execute()
            
            inherited_features = []
            if parent_result.data:
                for toggle in parent_result.data:
                    inherited_features.append({
                        'rag_feature': toggle['rag_feature'],
                        'enabled': True,
                        'is_inherited': True,
                        'inherited_from': parent_id,
                        'category': toggle.get('category'),
                        'created_at': toggle.get('created_at'),
                        'updated_at': toggle.get('updated_at')
                    })
            
            return {
                "success": True,
                "inherited_features": inherited_features,
                "parent_organization_id": parent_id
            }
            
        except Exception as e:
            logger.error(f"Error getting inherited features: {e}")
            return {
                "success": False,
                "error": str(e),
                "inherited_features": []
            }
    
    async def get_effective_features(self, organization_id: str) -> Dict[str, Any]:
        """Get effective RAG features (own + inherited) for an organization"""
        try:
            # Get own features
            own_result = await self.get_rag_feature_toggles(organization_id)
            if not own_result["success"]:
                return own_result
            
            # Get inherited features
            inherited_result = await self.get_inherited_features(organization_id)
            if not inherited_result["success"]:
                return inherited_result
            
            own_features = own_result["toggles"]
            inherited_features = inherited_result["inherited_features"]
            
            # Merge features, with own features taking precedence
            effective_features = []
            feature_map = {}
            
            # Add inherited features first
            for feature in inherited_features:
                feature_map[feature['rag_feature']] = feature
                effective_features.append(feature)
            
            # Override with own features
            for feature in own_features:
                if feature['rag_feature'] in feature_map:
                    # Update existing inherited feature
                    for i, eff_feature in enumerate(effective_features):
                        if eff_feature['rag_feature'] == feature['rag_feature']:
                            effective_features[i] = {
                                **feature,
                                'is_inherited': False,
                                'inherited_from': None
                            }
                            break
                else:
                    # Add new own feature
                    effective_features.append({
                        **feature,
                        'is_inherited': False,
                        'inherited_from': None
                    })
            
            return {
                "success": True,
                "effective_features": effective_features,
                "own_count": len(own_features),
                "inherited_count": len(inherited_features),
                "total_count": len(effective_features)
            }
            
        except Exception as e:
            logger.error(f"Error getting effective features: {e}")
            return {
                "success": False,
                "error": str(e),
                "effective_features": []
            }
    
    async def can_enable_feature(self, organization_id: str, feature_name: str) -> Dict[str, Any]:
        """Check if an organization can enable a specific feature"""
        try:
            # Check if feature exists in catalog
            catalog_result = self.supabase.from_('rag_feature_metadata').select('*').eq('rag_feature', feature_name).eq('is_active', True).execute()
            
            if not catalog_result.data:
                return {
                    "success": False,
                    "can_enable": False,
                    "reason": f"Feature '{feature_name}' does not exist or is inactive"
                }
            
            # Get organization's parent
            org_result = self.supabase.from_('organizations').select('parent_organization_id').eq('id', organization_id).execute()
            
            if not org_result.data:
                return {
                    "success": False,
                    "can_enable": False,
                    "reason": f"Organization '{organization_id}' not found"
                }
            
            parent_id = org_result.data[0].get('parent_organization_id')
            
            # If no parent, can enable any feature
            if not parent_id:
                return {
                    "success": True,
                    "can_enable": True,
                    "reason": "No parent organization - can enable any feature"
                }
            
            # Check if parent has this feature enabled
            parent_result = self.supabase.from_('organization_rag_toggles').select('enabled').eq('organization_id', parent_id).eq('rag_feature', feature_name).execute()
            
            if not parent_result.data:
                return {
                    "success": True,
                    "can_enable": False,
                    "reason": f"Parent organization does not have feature '{feature_name}' configured"
                }
            
            parent_enabled = parent_result.data[0].get('enabled', False)
            
            if not parent_enabled:
                return {
                    "success": True,
                    "can_enable": False,
                    "reason": f"Cannot enable feature '{feature_name}': parent organization has it disabled"
                }
            
            return {
                "success": True,
                "can_enable": True,
                "reason": "Parent organization has this feature enabled"
            }
            
        except Exception as e:
            logger.error(f"Error checking if feature can be enabled: {e}")
            return {
                "success": False,
                "can_enable": False,
                "reason": f"Error checking feature: {str(e)}"
            }
    
    async def get_inheritance_chain(self, organization_id: str) -> Dict[str, Any]:
        """Get the inheritance chain for an organization (parent -> grandparent -> etc.)"""
        try:
            chain = []
            current_org_id = organization_id
            
            # Walk up the hierarchy
            while current_org_id:
                org_result = self.supabase.from_('organizations').select('id, name, parent_organization_id').eq('id', current_org_id).execute()
                
                if not org_result.data:
                    break
                
                org_data = org_result.data[0]
                chain.append({
                    'id': org_data['id'],
                    'name': org_data['name'],
                    'parent_organization_id': org_data.get('parent_organization_id')
                })
                
                current_org_id = org_data.get('parent_organization_id')
            
            return {
                "success": True,
                "inheritance_chain": chain,
                "depth": len(chain) - 1  # Exclude the organization itself
            }
            
        except Exception as e:
            logger.error(f"Error getting inheritance chain: {e}")
            return {
                "success": False,
                "error": str(e),
                "inheritance_chain": []
            }
    
    async def get_override_status(self, organization_id: str, feature_name: str) -> Dict[str, Any]:
        """Get the override status for a feature (inherited, enabled, disabled)"""
        try:
            # Check if organization has this feature configured
            org_result = self.supabase.from_('organization_rag_toggles').select('*').eq('organization_id', organization_id).eq('rag_feature', feature_name).execute()
            
            if org_result.data:
                # Organization has explicit setting
                toggle = org_result.data[0]
                return {
                    "success": True,
                    "status": "enabled" if toggle['enabled'] else "disabled",
                    "is_inherited": False,
                    "inherited_from": None,
                    "can_override": True
                }
            
            # Check if inherited from parent
            inherited_result = await self.get_inherited_features(organization_id)
            if inherited_result["success"]:
                for feature in inherited_result["inherited_features"]:
                    if feature['rag_feature'] == feature_name:
                        return {
                            "success": True,
                            "status": "inherited",
                            "is_inherited": True,
                            "inherited_from": feature['inherited_from'],
                            "can_override": True
                        }
            
            return {
                "success": True,
                "status": "not_configured",
                "is_inherited": False,
                "inherited_from": None,
                "can_override": True
            }
            
        except Exception as e:
            logger.error(f"Error getting override status: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "unknown"
            }
    
    async def _create_default_rag_toggles(self, organization_id: str) -> List[Dict[str, Any]]:
        try:
            default_features = [
                'best_practice_kb',
                'customer_insight_rag',
                'success_pattern_rag',
                'content_personalization_rag',
                'live_call_coaching_rag',
                'performance_improvement_rag',
                'predictive_analytics_rag',
                'regulatory_guidance_rag',
                'legal_knowledge_rag',
                'scheduling_intelligence_rag',
                'resource_optimization_rag',
                'dynamic_content_rag',
                'multi_channel_optimization_rag',
                'performance_benchmarking_rag',
                'trend_analysis_rag',
                'document_intelligence_integration',
                'knowledge_sharing_rag',
                'unified_customer_view_rag',
                'best_practice_transfer_rag',
                'historical_context_rag'
            ]
            
            toggle_data = []
            for feature in default_features:
                toggle_data.append({
                    'organization_id': organization_id,
                    'rag_feature': feature,
                    'enabled': True,  # Default to enabled
                    'created_at': datetime.utcnow().isoformat()
                })
            
            result = self.supabase.from_('organization_rag_toggles').insert(toggle_data).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error creating default RAG toggles: {e}")
            return []
