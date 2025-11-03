"""
Authentication API - Login, logout, JWT, 2FA
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
from services.supabase_client import get_supabase_client
from middleware.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ===========================================
# Pydantic Models
# ===========================================

class LoginAuditCreate(BaseModel):
    user_id: str
    organization_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    device_name: Optional[str] = None
    login_method: str = Field(pattern="^(password|oauth_google|oauth_apple|magic_link|2fa_code)$")
    status: str = Field(pattern="^(success|failed|blocked)$")
    failure_reason: Optional[str] = None
    location_data: Optional[dict] = None


class LoginHistoryResponse(BaseModel):
    logins: List[dict]
    total: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class RevokeTokenRequest(BaseModel):
    token: str


# ===========================================
# API Endpoints
# ===========================================

@router.post("/login-audit", status_code=status.HTTP_201_CREATED)
async def log_login_attempt(audit: LoginAuditCreate):
    """
    Log a login attempt (called by auth middleware)
    """
    supabase = get_supabase_client()
    
    try:
        audit_data = audit.dict()
        audit_data['login_at'] = datetime.utcnow().isoformat()
        
        result = supabase.from_('login_audit').insert(audit_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to log login attempt"
            )
        
        # Update last login in profile
        supabase.from_('profiles').update({
            'last_login_ip': audit_data.get('ip_address'),
            'last_login_at': audit_data['login_at']
        }).eq('user_id', audit.user_id).execute()
        
        return {"success": True, "audit_id": result.data[0]['id']}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error logging login attempt: {str(e)}"
        )


@router.get("/login-history", response_model=LoginHistoryResponse)
async def get_login_history(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's login history
    """
    supabase = get_supabase_client()
    
    try:
        result = supabase.from_('login_audit').select('*').eq('user_id', current_user['user_id']).order('login_at', desc=True).range(offset, offset + limit - 1).execute()
        
        total_result = supabase.from_('login_audit').select('id', count='exact').eq('user_id', current_user['user_id']).execute()
        total = total_result.count if total_result.count else 0
        
        return LoginHistoryResponse(
            logins=result.data if result.data else [],
            total=total
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching login history: {str(e)}"
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh an access token using a refresh token
    """
    supabase = get_supabase_client()
    
    try:
        # Use Supabase's built-in refresh method
        result = supabase.auth.refresh_session(request.refresh_token)
        
        if not result.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        session = result.session
        
        return RefreshTokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_in=session.expires_in or 3600
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refreshing token: {str(e)}"
        )


@router.post("/revoke", status_code=status.HTTP_200_OK)
async def revoke_token(request: RevokeTokenRequest):
    """
    Revoke an access token
    """
    supabase = get_supabase_client()
    
    try:
        # Sign out the user (revokes all tokens)
        supabase.auth.sign_out()
        
        return {"success": True, "message": "Token revoked successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking token: {str(e)}"
        )


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return current_user

