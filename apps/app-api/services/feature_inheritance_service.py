"""
Feature Inheritance Service
Provides business logic for resolving inherited RAG features across organization hierarchy
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .supabase_client import get_supabase_client
from .tenant_isolation_service import TenantIsolationService

logger = logging.getLogger(__name__)

class FeatureInheritanceService:
    """Service for managing RAG feature inheritance across organization hierarchy"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.tenant_service = TenantIsolationService()
    
    async def resolve_features(self, org_id: str) -> Dict[str, Any]:
        """
        Resolve all effective features for an organization (own + inherited)
        Returns comprehensive feature resolution with inheritance details
        """
        try:
            # Get inheritance chain
            chain_result = await self.get_inheritance_chain(org_id)
            if not chain_result["success"]:
                return chain_result
            
            inheritance_chain = chain_result["inheritance_chain"]
            
            # Get effective features from tenant service
            effective_result = await self.tenant_service.get_effective_features(org_id)
            if not effective_result["success"]:
                return effective_result
            
            effective_features = effective_result["effective_features"]
            
            # Enhance with inheritance details
            enhanced_features = []
            for feature in effective_features:
                enhanced_feature = {
                    **feature,
                    'inheritance_source': self._get_inheritance_source(feature, inheritance_chain),
                    'can_override': self._can_override_feature(feature, inheritance_chain),
                    'override_reason': self._get_override_reason(feature, inheritance_chain)
                }
                enhanced_features.append(enhanced_feature)
            
            return {
                "success": True,
                "effective_features": enhanced_features,
                "inheritance_chain": inheritance_chain,
                "own_count": effective_result["own_count"],
                "inherited_count": effective_result["inherited_count"],
                "total_count": effective_result["total_count"]
            }
            
        except Exception as e:
            logger.error(f"Error resolving features for org {org_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "effective_features": []
            }
    
    async def get_inheritance_chain(self, org_id: str) -> Dict[str, Any]:
        """
        Get the inheritance chain for an organization (parent -> grandparent -> etc.)
        """
        try:
            chain = []
            current_org_id = org_id
            
            # Walk up the hierarchy
            while current_org_id:
                org_result = self.supabase.from_('organizations').select('id, name, parent_organization_id').eq('id', current_org_id).execute()
                
                if not org_result.data:
                    break
                
                org_data = org_result.data[0]
                chain.append({
                    'id': org_data['id'],
                    'name': org_data['name'],
                    'parent_organization_id': org_data.get('parent_organization_id'),
                    'level': len(chain)  # 0-based level
                })
                
                current_org_id = org_data.get('parent_organization_id')
            
            return {
                "success": True,
                "inheritance_chain": chain,
                "depth": len(chain) - 1  # Exclude the organization itself
            }
            
        except Exception as e:
            logger.error(f"Error getting inheritance chain for org {org_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "inheritance_chain": []
            }
    
    async def can_override_feature(self, org_id: str, feature_name: str) -> Dict[str, Any]:
        """
        Check if an organization can override a specific feature
        """
        try:
            # Get inheritance chain
            chain_result = await self.get_inheritance_chain(org_id)
            if not chain_result["success"]:
                return chain_result
            
            inheritance_chain = chain_result["inheritance_chain"]
            
            # Check if organization has explicit setting
            org_result = self.supabase.from_('organization_rag_toggles').select('*').eq('organization_id', org_id).eq('rag_feature', feature_name).execute()
            
            if org_result.data:
                # Organization has explicit setting
                return {
                    "success": True,
                    "can_override": True,
                    "current_status": "explicit",
                    "reason": "Organization has explicit setting for this feature"
                }
            
            # Check if inherited from any parent
            for parent_org in inheritance_chain[1:]:  # Skip the organization itself
                parent_result = self.supabase.from_('organization_rag_toggles').select('*').eq('organization_id', parent_org['id']).eq('rag_feature', feature_name).execute()
                
                if parent_result.data:
                    parent_toggle = parent_result.data[0]
                    return {
                        "success": True,
                        "can_override": True,
                        "current_status": "inherited",
                        "inherited_from": parent_org['id'],
                        "inherited_from_name": parent_org['name'],
                        "parent_enabled": parent_toggle['enabled'],
                        "reason": f"Inherited from {parent_org['name']} (level {parent_org['level']})"
                    }
            
            return {
                "success": True,
                "can_override": True,
                "current_status": "not_configured",
                "reason": "Feature not configured in organization hierarchy"
            }
            
        except Exception as e:
            logger.error(f"Error checking override capability for feature {feature_name} in org {org_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "can_override": False
            }
    
    async def get_override_status(self, org_id: str, feature_name: str) -> Dict[str, Any]:
        """
        Get detailed override status for a feature
        """
        try:
            # Get inheritance chain
            chain_result = await self.get_inheritance_chain(org_id)
            if not chain_result["success"]:
                return chain_result
            
            inheritance_chain = chain_result["inheritance_chain"]
            
            # Check organization's explicit setting
            org_result = self.supabase.from_('organization_rag_toggles').select('*').eq('organization_id', org_id).eq('rag_feature', feature_name).execute()
            
            if org_result.data:
                toggle = org_result.data[0]
                return {
                    "success": True,
                    "status": "enabled" if toggle['enabled'] else "disabled",
                    "is_inherited": False,
                    "inherited_from": None,
                    "inherited_from_name": None,
                    "can_override": True,
                    "inheritance_level": 0,
                    "override_type": "explicit"
                }
            
            # Check inheritance from parents
            for parent_org in inheritance_chain[1:]:  # Skip the organization itself
                parent_result = self.supabase.from_('organization_rag_toggles').select('*').eq('organization_id', parent_org['id']).eq('rag_feature', feature_name).execute()
                
                if parent_result.data:
                    parent_toggle = parent_result.data[0]
                    return {
                        "success": True,
                        "status": "enabled" if parent_toggle['enabled'] else "disabled",
                        "is_inherited": True,
                        "inherited_from": parent_org['id'],
                        "inherited_from_name": parent_org['name'],
                        "can_override": True,
                        "inheritance_level": parent_org['level'],
                        "override_type": "inherited"
                    }
            
            return {
                "success": True,
                "status": "not_configured",
                "is_inherited": False,
                "inherited_from": None,
                "inherited_from_name": None,
                "can_override": True,
                "inheritance_level": 0,
                "override_type": "not_configured"
            }
            
        except Exception as e:
            logger.error(f"Error getting override status for feature {feature_name} in org {org_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "unknown"
            }
    
    async def get_inheritance_summary(self, org_id: str) -> Dict[str, Any]:
        """
        Get summary of inheritance status for all features
        """
        try:
            # Get effective features
            effective_result = await self.resolve_features(org_id)
            if not effective_result["success"]:
                return effective_result
            
            effective_features = effective_result["effective_features"]
            inheritance_chain = effective_result["inheritance_chain"]
            
            # Categorize features
            explicit_features = []
            inherited_features = []
            not_configured_features = []
            
            for feature in effective_features:
                if feature.get('inheritance_source') == 'explicit':
                    explicit_features.append(feature)
                elif feature.get('inheritance_source') == 'inherited':
                    inherited_features.append(feature)
                else:
                    not_configured_features.append(feature)
            
            # Calculate statistics
            total_features = len(effective_features)
            enabled_features = len([f for f in effective_features if f.get('enabled', False)])
            
            # Group inherited features by source
            inherited_by_source = {}
            for feature in inherited_features:
                source = feature.get('inherited_from')
                if source not in inherited_by_source:
                    inherited_by_source[source] = []
                inherited_by_source[source].append(feature)
            
            return {
                "success": True,
                "summary": {
                    "total_features": total_features,
                    "enabled_features": enabled_features,
                    "disabled_features": total_features - enabled_features,
                    "explicit_features": len(explicit_features),
                    "inherited_features": len(inherited_features),
                    "not_configured_features": len(not_configured_features),
                    "inheritance_depth": len(inheritance_chain) - 1,
                    "inherited_by_source": inherited_by_source
                },
                "inheritance_chain": inheritance_chain,
                "feature_breakdown": {
                    "explicit": explicit_features,
                    "inherited": inherited_features,
                    "not_configured": not_configured_features
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting inheritance summary for org {org_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "summary": {}
            }
    
    def _get_inheritance_source(self, feature: Dict[str, Any], inheritance_chain: List[Dict[str, Any]]) -> str:
        """Determine the source of a feature (explicit, inherited, not_configured)"""
        if feature.get('is_inherited', False):
            return 'inherited'
        elif feature.get('rag_feature'):
            return 'explicit'
        else:
            return 'not_configured'
    
    def _can_override_feature(self, feature: Dict[str, Any], inheritance_chain: List[Dict[str, Any]]) -> bool:
        """Determine if a feature can be overridden"""
        # If it's explicit, it can always be overridden
        if not feature.get('is_inherited', False):
            return True
        
        # If it's inherited, it can be overridden (child can disable parent's feature)
        return True
    
    def _get_override_reason(self, feature: Dict[str, Any], inheritance_chain: List[Dict[str, Any]]) -> str:
        """Get human-readable reason for override capability"""
        if not feature.get('is_inherited', False):
            return "Organization has explicit control over this feature"
        
        inherited_from = feature.get('inherited_from')
        if inherited_from:
            # Find the parent organization name
            for parent in inheritance_chain:
                if parent['id'] == inherited_from:
                    return f"Inherited from {parent['name']} - can be overridden"
        
        return "Feature inheritance status unknown"
    
    async def validate_inheritance_rules(self, org_id: str, feature_name: str, enabled: bool) -> Dict[str, Any]:
        """
        Validate inheritance rules before allowing a feature toggle
        """
        try:
            # Get inheritance chain
            chain_result = await self.get_inheritance_chain(org_id)
            if not chain_result["success"]:
                return chain_result
            
            inheritance_chain = chain_result["inheritance_chain"]
            
            # If enabling, check if parent allows it
            if enabled:
                for parent_org in inheritance_chain[1:]:  # Skip the organization itself
                    parent_result = self.supabase.from_('organization_rag_toggles').select('enabled').eq('organization_id', parent_org['id']).eq('rag_feature', feature_name).execute()
                    
                    if parent_result.data:
                        parent_enabled = parent_result.data[0].get('enabled', False)
                        if not parent_enabled:
                            return {
                                "success": False,
                                "can_proceed": False,
                                "reason": f"Cannot enable feature '{feature_name}': parent organization {parent_org['name']} has it disabled"
                            }
            
            # If disabling, always allowed (child can disable parent's feature)
            return {
                "success": True,
                "can_proceed": True,
                "reason": "Inheritance rules satisfied"
            }
            
        except Exception as e:
            logger.error(f"Error validating inheritance rules for feature {feature_name} in org {org_id}: {e}")
            return {
                "success": False,
                "can_proceed": False,
                "reason": f"Error validating inheritance: {str(e)}"
            }
