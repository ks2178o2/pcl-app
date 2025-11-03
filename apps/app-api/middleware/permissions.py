"""
Role-based permission middleware and decorators for RAG feature management
"""

import functools
import logging
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from services.supabase_client import get_supabase_client
from supabase import Client

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles in the system"""
    SYSTEM_ADMIN = "system_admin"
    ORG_ADMIN = "org_admin"
    MANAGER = "manager"
    SALESPERSON = "salesperson"
    USER = "user"

class PermissionError(Exception):
    """Raised when user lacks required permissions"""
    pass

class OrganizationAccessError(Exception):
    """Raised when user cannot access organization resources"""
    pass

class FeatureAccessError(Exception):
    """Raised when user cannot access RAG feature"""
    pass

def get_user_role(user_data: Dict[str, Any]) -> UserRole:
    """Extract user role from user data"""
    role = user_data.get('role', 'user')
    
    # Map role strings to enum values
    role_mapping = {
        'system_admin': UserRole.SYSTEM_ADMIN,
        'org_admin': UserRole.ORG_ADMIN,
        'manager': UserRole.MANAGER,
        'salesperson': UserRole.SALESPERSON,
        'user': UserRole.USER
    }
    
    return role_mapping.get(role, UserRole.USER)

def get_user_organization_id(user_data: Dict[str, Any]) -> Optional[str]:
    """Extract organization ID from user data"""
    return user_data.get('organization_id')

def has_role(user_data: Dict[str, Any], required_role: UserRole) -> bool:
    """Check if user has the required role or higher"""
    user_role = get_user_role(user_data)
    
    # Define role hierarchy (higher roles inherit permissions of lower roles)
    role_hierarchy = {
        UserRole.SYSTEM_ADMIN: 5,
        UserRole.ORG_ADMIN: 4,
        UserRole.MANAGER: 3,
        UserRole.SALESPERSON: 2,
        UserRole.USER: 1
    }
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

def can_access_organization(user_data: Dict[str, Any], target_org_id: str, 
                          supabase: Client, check_parent: bool = False) -> bool:
    """Check if user can access the target organization"""
    user_org_id = get_user_organization_id(user_data)
    user_role = get_user_role(user_data)
    
    # System admins can access any organization
    if user_role == UserRole.SYSTEM_ADMIN:
        return True
    
    # Users can only access their own organization
    if user_org_id == target_org_id:
        return True
    
    # If checking parent relationships, allow access to child organizations
    if check_parent:
        # Check if target_org_id is a child of user_org_id
        try:
            # Query to check if target_org_id has user_org_id as parent
            result = supabase.from_('organizations').select('id').eq('id', target_org_id).eq('parent_organization_id', user_org_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking organization hierarchy: {e}")
            return False
    
    return False

def can_access_rag_feature(user_data: Dict[str, Any], feature_name: str, 
                         organization_id: str, supabase: Client) -> bool:
    """Check if user can access the RAG feature for the organization"""
    user_role = get_user_role(user_data)
    user_org_id = get_user_organization_id(user_data)
    
    # System admins can access any feature
    if user_role == UserRole.SYSTEM_ADMIN:
        return True
    
    # Users can only access features in their own organization
    if user_org_id != organization_id:
        return False
    
    # Check if the feature is enabled for the organization
    try:
        # Query organization_rag_toggles to check if feature is enabled
        result = supabase.from_('organization_rag_toggles').select('enabled').eq('organization_id', organization_id).eq('rag_feature', feature_name).execute()
        if result.data:
            return result.data[0]['enabled']
        # If no toggle found, check if feature is enabled by default in metadata
        metadata_result = supabase.from_('rag_feature_metadata').select('default_enabled').eq('rag_feature', feature_name).execute()
        if metadata_result.data:
            return metadata_result.data[0]['default_enabled']
        return False
    except Exception as e:
        logger.error(f"Error checking RAG feature access: {e}")
        return False

def require_role(required_role: UserRole):
    """Decorator to require a specific role or higher"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user data from the first argument (assuming it's a request or user object)
            if args and hasattr(args[0], 'user'):
                user_data = args[0].user
            elif 'user' in kwargs:
                user_data = kwargs['user']
            else:
                raise PermissionError("User data not found in request")
            
            if not has_role(user_data, required_role):
                raise PermissionError(
                    f"User role {get_user_role(user_data).value} does not meet "
                    f"required role {required_role.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_org_access(check_parent: bool = False):
    """Decorator to require access to a specific organization"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user data and organization ID
            if args and hasattr(args[0], 'user'):
                user_data = args[0].user
                org_id = getattr(args[0], 'organization_id', None) or kwargs.get('organization_id')
            elif 'user' in kwargs and 'organization_id' in kwargs:
                user_data = kwargs['user']
                org_id = kwargs['organization_id']
            else:
                raise OrganizationAccessError("User data or organization ID not found in request")
            
            if not can_access_organization(user_data, org_id, check_parent):
                raise OrganizationAccessError(
                    f"User cannot access organization {org_id}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_feature_enabled(feature_name: str):
    """Decorator to require that a RAG feature is enabled for the organization"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user data and organization ID
            if args and hasattr(args[0], 'user'):
                user_data = args[0].user
                org_id = getattr(args[0], 'organization_id', None) or kwargs.get('organization_id')
            elif 'user' in kwargs and 'organization_id' in kwargs:
                user_data = kwargs['user']
                org_id = kwargs['organization_id']
            else:
                raise FeatureAccessError("User data or organization ID not found in request")
            
            if not can_access_rag_feature(user_data, feature_name, org_id):
                raise FeatureAccessError(
                    f"User cannot access RAG feature {feature_name} for organization {org_id}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_any_role(required_roles: List[UserRole]):
    """Decorator to require any one of the specified roles"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user data
            if args and hasattr(args[0], 'user'):
                user_data = args[0].user
            elif 'user' in kwargs:
                user_data = kwargs['user']
            else:
                raise PermissionError("User data not found in request")
            
            user_role = get_user_role(user_data)
            
            if user_role not in required_roles:
                role_names = [role.value for role in required_roles]
                raise PermissionError(
                    f"User role {user_role.value} not in required roles: {role_names}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_system_admin(func: Callable) -> Callable:
    """Convenience decorator for system admin only"""
    return require_role(UserRole.SYSTEM_ADMIN)(func)

def require_org_admin(func: Callable) -> Callable:
    """Convenience decorator for org admin or higher"""
    return require_role(UserRole.ORG_ADMIN)(func)

def require_manager_or_higher(func: Callable) -> Callable:
    """Convenience decorator for manager or higher"""
    return require_role(UserRole.MANAGER)(func)

def require_salesperson_or_higher(func: Callable) -> Callable:
    """Convenience decorator for salesperson or higher"""
    return require_role(UserRole.SALESPERSON)(func)

def require_admin_access(func: Callable) -> Callable:
    """Convenience decorator for admin access (system or org admin)"""
    return require_any_role([UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN])(func)

class PermissionChecker:
    """Utility class for checking permissions in service methods"""
    
    def __init__(self, user_data: Dict[str, Any], supabase: Client):
        self.user_data = user_data
        self.user_role = get_user_role(user_data)
        self.user_org_id = get_user_organization_id(user_data)
        self.supabase = supabase
    
    def can_manage_rag_features(self, target_org_id: str) -> bool:
        """Check if user can manage RAG features for target organization"""
        if self.user_role == UserRole.SYSTEM_ADMIN:
            return True
        
        if self.user_role == UserRole.ORG_ADMIN and self.user_org_id == target_org_id:
            return True
        
        return False
    
    def can_view_rag_features(self, target_org_id: str) -> bool:
        """Check if user can view RAG features for target organization"""
        if self.user_role in [UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN]:
            return True
        
        if self.user_org_id == target_org_id:
            return True
        
        return False
    
    def can_use_rag_feature(self, feature_name: str, target_org_id: str) -> bool:
        """Check if user can use RAG feature for target organization"""
        if self.user_role == UserRole.SYSTEM_ADMIN:
            return True
        
        if self.user_org_id != target_org_id:
            return False
        
        # TODO: Add check for feature being enabled
        try:
            # Query organization_rag_toggles to check if feature is enabled
            result = self.supabase.from_('organization_rag_toggles').select('enabled').eq('organization_id', target_org_id).eq('rag_feature', feature_name).execute()
            if result.data:
                return result.data[0]['enabled']
            # If no toggle found, check if feature is enabled by default in metadata
            metadata_result = self.supabase.from_('rag_feature_metadata').select('default_enabled').eq('rag_feature', feature_name).execute()
            if metadata_result.data:
                return metadata_result.data[0]['default_enabled']
            return False
        except Exception as e:
            logger.error(f"Error checking RAG feature enabled status: {e}")
            return False
    
    def can_access_organization_hierarchy(self, target_org_id: str) -> bool:
        """Check if user can access organization hierarchy"""
        if self.user_role == UserRole.SYSTEM_ADMIN:
            return True
        
        if self.user_role == UserRole.ORG_ADMIN and self.user_org_id == target_org_id:
            return True
        
        return False
    
    def get_accessible_organizations(self) -> List[str]:
        """Get list of organization IDs the user can access"""
        if self.user_role == UserRole.SYSTEM_ADMIN:
            # System admins can access all organizations
            try:
                result = self.supabase.from_('organizations').select('id').execute()
                return [org['id'] for org in result.data] if result.data else []
            except Exception as e:
                logger.error(f"Error getting all organization IDs: {e}")
                return []
        
        if self.user_org_id:
            return [self.user_org_id]
        
        return []

def validate_permissions(user_data: Dict[str, Any], action: str, 
                        target_org_id: str, feature_name: Optional[str] = None,
                        supabase: Client = None) -> bool:
    """Validate permissions for a specific action"""
    if supabase is None:
        supabase = get_supabase_client()
    checker = PermissionChecker(user_data, supabase)
    
    if action == "manage_rag_features":
        return checker.can_manage_rag_features(target_org_id)
    elif action == "view_rag_features":
        return checker.can_view_rag_features(target_org_id)
    elif action == "use_rag_feature":
        if not feature_name:
            return False
        return checker.can_use_rag_feature(feature_name, target_org_id)
    elif action == "access_hierarchy":
        return checker.can_access_organization_hierarchy(target_org_id)
    else:
        return False

# Export commonly used decorators and classes
__all__ = [
    'UserRole',
    'PermissionError',
    'OrganizationAccessError', 
    'FeatureAccessError',
    'require_role',
    'require_org_access',
    'require_feature_enabled',
    'require_any_role',
    'require_system_admin',
    'require_org_admin',
    'require_manager_or_higher',
    'require_salesperson_or_higher',
    'require_admin_access',
    'PermissionChecker',
    'validate_permissions',
    'get_user_role',
    'get_user_organization_id',
    'has_role',
    'can_access_organization',
    'can_access_rag_feature'
]
