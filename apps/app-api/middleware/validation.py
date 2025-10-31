"""
Backend validation middleware for RAG features
Provides validation functions for RAG feature operations and organization hierarchy
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from functools import wraps
import asyncio

from services.supabase_client import get_supabase_client
from .permissions import PermissionChecker, UserRole

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Raised when validation fails"""
    pass

class RAGFeatureValidator:
    """Validator for RAG feature operations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def validate_rag_feature_exists(self, feature_name: str) -> bool:
        """Validate that a RAG feature exists in the catalog"""
        try:
            result = self.supabase.from_('rag_feature_metadata').select('rag_feature').eq('rag_feature', feature_name).eq('is_active', True).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error validating RAG feature {feature_name}: {e}")
            return False
    
    async def validate_rag_feature_enabled(self, org_id: str, feature_name: str) -> Tuple[bool, str]:
        """
        Validate that a RAG feature is enabled for the organization
        Returns (is_enabled, error_message)
        """
        try:
            # Check if feature exists in catalog
            if not await self.validate_rag_feature_exists(feature_name):
                return False, f"RAG feature '{feature_name}' does not exist or is inactive"
            
            # Check if feature is enabled for organization
            result = self.supabase.from_('organization_rag_toggles').select('enabled').eq('organization_id', org_id).eq('rag_feature', feature_name).execute()
            
            if not result.data:
                return False, f"RAG feature '{feature_name}' is not configured for organization {org_id}"
            
            toggle = result.data[0]
            if not toggle.get('enabled', False):
                return False, f"RAG feature '{feature_name}' is disabled for organization {org_id}"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating RAG feature enabled status: {e}")
            return False, f"Error validating RAG feature: {str(e)}"
    
    async def validate_organization_exists(self, org_id: str) -> bool:
        """Validate that an organization exists"""
        try:
            result = self.supabase.from_('organizations').select('id').eq('id', org_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error validating organization {org_id}: {e}")
            return False
    
    async def validate_org_hierarchy(self, parent_id: str, child_id: str) -> Tuple[bool, str]:
        """
        Validate organization hierarchy relationships
        Prevents circular dependencies and invalid relationships
        Returns (is_valid, error_message)
        """
        try:
            # Check if both organizations exist
            if not await self.validate_organization_exists(parent_id):
                return False, f"Parent organization {parent_id} does not exist"
            
            if not await self.validate_organization_exists(child_id):
                return False, f"Child organization {child_id} does not exist"
            
            # Check for circular dependency
            if parent_id == child_id:
                return False, "Organization cannot be its own parent"
            
            # Check if child is already a parent of the parent (circular dependency)
            # This would require a recursive check up the hierarchy
            # For now, we'll implement a simple check
            result = self.supabase.from_('organizations').select('parent_organization_id').eq('id', parent_id).execute()
            
            if result.data and result.data[0].get('parent_organization_id') == child_id:
                return False, "Circular dependency detected: child organization is already a parent"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating organization hierarchy: {e}")
            return False, f"Error validating hierarchy: {str(e)}"
    
    async def validate_feature_inheritance(self, org_id: str, feature_name: str) -> Tuple[bool, str]:
        """
        Validate that a child organization can only enable features enabled by parent
        Returns (can_enable, error_message)
        """
        try:
            # Get organization's parent
            result = self.supabase.from_('organizations').select('parent_organization_id').eq('id', org_id).execute()
            
            if not result.data:
                return False, f"Organization {org_id} not found"
            
            parent_id = result.data[0].get('parent_organization_id')
            
            # If no parent, organization can enable any feature
            if not parent_id:
                return True, ""
            
            # Check if parent has this feature enabled
            parent_result = self.supabase.from_('organization_rag_toggles').select('enabled').eq('organization_id', parent_id).eq('rag_feature', feature_name).execute()
            
            if not parent_result.data:
                return False, f"Parent organization {parent_id} does not have feature '{feature_name}' configured"
            
            parent_enabled = parent_result.data[0].get('enabled', False)
            
            if not parent_enabled:
                return False, f"Cannot enable feature '{feature_name}': parent organization {parent_id} has it disabled"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating feature inheritance: {e}")
            return False, f"Error validating inheritance: {str(e)}"
    
    async def validate_user_can_manage_features(self, user_data: Dict[str, Any], org_id: str) -> Tuple[bool, str]:
        """Validate that user can manage RAG features for the organization"""
        try:
            checker = PermissionChecker(user_data)
            
            if not checker.can_manage_rag_features(org_id):
                user_role = checker.user_role.value
                return False, f"User role '{user_role}' cannot manage RAG features for organization {org_id}"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating user permissions: {e}")
            return False, f"Error validating permissions: {str(e)}"

# Global validator instance
rag_validator = RAGFeatureValidator()

# Validation decorators
def validate_rag_feature_enabled(feature_name_param: str = "feature_name", org_id_param: str = "organization_id"):
    """Decorator to validate that a RAG feature is enabled before allowing operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract parameters
            feature_name = kwargs.get(feature_name_param)
            org_id = kwargs.get(org_id_param)
            
            if not feature_name or not org_id:
                raise ValidationError(f"Missing required parameters: {feature_name_param}, {org_id_param}")
            
            # Validate feature is enabled
            is_enabled, error_msg = await rag_validator.validate_rag_feature_enabled(org_id, feature_name)
            
            if not is_enabled:
                raise ValidationError(error_msg)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def validate_org_hierarchy(parent_param: str = "parent_id", child_param: str = "child_id"):
    """Decorator to validate organization hierarchy relationships"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract parameters
            parent_id = kwargs.get(parent_param)
            child_id = kwargs.get(child_param)
            
            if not parent_id or not child_id:
                raise ValidationError(f"Missing required parameters: {parent_param}, {child_param}")
            
            # Validate hierarchy
            is_valid, error_msg = await rag_validator.validate_org_hierarchy(parent_id, child_id)
            
            if not is_valid:
                raise ValidationError(error_msg)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def validate_feature_inheritance(feature_param: str = "feature_name", org_param: str = "organization_id"):
    """Decorator to validate feature inheritance rules"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract parameters
            feature_name = kwargs.get(feature_param)
            org_id = kwargs.get(org_param)
            
            if not feature_name or not org_id:
                raise ValidationError(f"Missing required parameters: {feature_param}, {org_param}")
            
            # Validate inheritance
            can_enable, error_msg = await rag_validator.validate_feature_inheritance(org_id, feature_name)
            
            if not can_enable:
                raise ValidationError(error_msg)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def validate_user_permissions(user_param: str = "user", org_param: str = "organization_id"):
    """Decorator to validate user permissions for RAG feature management"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract parameters
            user_data = kwargs.get(user_param)
            org_id = kwargs.get(org_param)
            
            if not user_data or not org_id:
                raise ValidationError(f"Missing required parameters: {user_param}, {org_param}")
            
            # Validate permissions
            can_manage, error_msg = await rag_validator.validate_user_can_manage_features(user_data, org_id)
            
            if not can_manage:
                raise ValidationError(error_msg)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Validation functions for use in service methods
async def validate_rag_feature_operation(org_id: str, feature_name: str, operation: str) -> Dict[str, Any]:
    """
    Comprehensive validation for RAG feature operations
    Returns validation result with success status and error message
    """
    try:
        # Validate organization exists
        if not await rag_validator.validate_organization_exists(org_id):
            return {
                "success": False,
                "error": f"Organization {org_id} does not exist"
            }
        
        # Validate feature exists
        if not await rag_validator.validate_rag_feature_exists(feature_name):
            return {
                "success": False,
                "error": f"RAG feature '{feature_name}' does not exist or is inactive"
            }
        
        # Validate feature is enabled (for usage operations)
        if operation in ["use", "upload", "create_context"]:
            is_enabled, error_msg = await rag_validator.validate_rag_feature_enabled(org_id, feature_name)
            if not is_enabled:
                return {
                    "success": False,
                    "error": error_msg
                }
        
        return {
            "success": True,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Error validating RAG feature operation: {e}")
        return {
            "success": False,
            "error": f"Validation error: {str(e)}"
        }

async def validate_bulk_toggle_operation(org_id: str, toggle_updates: Dict[str, bool], user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate bulk toggle operation
    Returns validation result with success status and error message
    """
    try:
        # Validate organization exists
        if not await rag_validator.validate_organization_exists(org_id):
            return {
                "success": False,
                "error": f"Organization {org_id} does not exist"
            }
        
        # Validate user permissions
        can_manage, error_msg = await rag_validator.validate_user_can_manage_features(user_data, org_id)
        if not can_manage:
            return {
                "success": False,
                "error": error_msg
            }
        
        # Validate each feature
        invalid_features = []
        for feature_name, enabled in toggle_updates.items():
            # Check if feature exists
            if not await rag_validator.validate_rag_feature_exists(feature_name):
                invalid_features.append(f"{feature_name} (does not exist)")
                continue
            
            # If enabling, check inheritance rules
            if enabled:
                can_enable, error_msg = await rag_validator.validate_feature_inheritance(org_id, feature_name)
                if not can_enable:
                    invalid_features.append(f"{feature_name} ({error_msg})")
        
        if invalid_features:
            return {
                "success": False,
                "error": f"Invalid features: {', '.join(invalid_features)}"
            }
        
        return {
            "success": True,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Error validating bulk toggle operation: {e}")
        return {
            "success": False,
            "error": f"Validation error: {str(e)}"
        }

# Export commonly used functions and classes
__all__ = [
    'ValidationError',
    'RAGFeatureValidator',
    'rag_validator',
    'validate_rag_feature_enabled',
    'validate_org_hierarchy',
    'validate_feature_inheritance',
    'validate_user_permissions',
    'validate_rag_feature_operation',
    'validate_bulk_toggle_operation'
]
