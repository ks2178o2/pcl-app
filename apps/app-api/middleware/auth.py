"""
Authentication middleware for FastAPI
Provides user authentication and authorization helpers
"""
import os
import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# HTTP Bearer token security
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Authenticate user and return enriched user info with profile, roles, and assignments
    
    Returns a dict with:
    - user_id: str (UUID from auth.users)
    - email: str
    - role: str (from user_roles)
    - organization_id: str
    - center_ids: List[str]
    - region_id: Optional[str]
    - salesperson_name: Optional[str]
    """
    supabase_client = get_supabase_client()
    if not supabase_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )
    
    try:
        # Verify JWT token with Supabase
        auth_response = supabase_client.auth.get_user(credentials.credentials)
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = auth_response.user.id
        email = auth_response.user.email
        
        # Get profile with organization info
        # Fetch profile; tolerate duplicate rows by picking the most recent
        profile_result = (
            supabase_client
            .table("profiles")
            .select("organization_id, salesperson_name, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        profile = (profile_result.data[0] if isinstance(profile_result.data, list) and profile_result.data else profile_result.data) or {}
        organization_id = profile.get('organization_id')
        full_name = profile.get('salesperson_name')
        
        # Get user's primary role
        role_result = supabase_client.table("user_roles").select(
            "role"
        ).eq("user_id", user_id).limit(1).execute()
        
        role = role_result.data[0].get('role') if role_result.data else 'salesperson'
        
        # Get center assignments
        assignments_result = supabase_client.table("user_assignments").select(
            "center_id"
        ).eq("user_id", user_id).execute()
        
        center_ids = [assignment['center_id'] for assignment in assignments_result.data if assignment.get('center_id')]
        
        # Build enriched user object
        user = {
            "user_id": user_id,
            "id": user_id,  # Alias for compatibility
            "email": email,
            "role": role,
            "organization_id": organization_id,
            "center_ids": center_ids,
            "full_name": full_name  # Keep for backward compatibility
        }
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_org_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require org_admin or system_admin role"""
    if user.get('role') not in ['org_admin', 'system_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Org admin access required"
        )
    return user


async def require_system_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require system_admin role"""
    if user.get('role') != 'system_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System admin access required"
        )
    return user


async def verify_org_access(
    org_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Verify user has access to the specified organization"""
    if user.get('organization_id') != org_id and user.get('role') != 'system_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    return user

