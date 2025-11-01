"""
Invitations API - Handle user invitation management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, timedelta
import secrets
import hashlib
import logging
from services.supabase_client import get_supabase_client
from services.email_service import get_email_service
from middleware.auth import get_current_user, require_org_admin

router = APIRouter(prefix="/api/invitations", tags=["invitations"])


# ===========================================
# Pydantic Models
# ===========================================

class InvitationCreateRequest(BaseModel):
    email: EmailStr
    organization_id: str
    role: str = Field(default="salesperson", pattern="^(salesperson|coach|leader|doctor|org_admin)$")
    center_ids: Optional[List[str]] = None
    region_id: Optional[str] = None
    expires_in_days: int = Field(default=7, ge=1, le=30)


class InvitationResponse(BaseModel):
    invitation_id: str
    email: str
    token: str
    expires_at: datetime
    status: str
    created_at: datetime


class InvitationListResponse(BaseModel):
    invitations: List[dict]
    total: int


class InvitationValidateRequest(BaseModel):
    token: str


class InvitationAcceptRequest(BaseModel):
    token: str
    password: str
    name: Optional[str] = None


class InvitationAcceptResponse(BaseModel):
    success: bool
    user_id: str
    message: str


# ===========================================
# Helper Functions
# ===========================================

def generate_invitation_token() -> str:
    """Generate a secure random token for invitations"""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token for storage (only use hash, never plain token)"""
    return hashlib.sha256(token.encode()).hexdigest()


def get_user_organization(user_id: str, supabase) -> Optional[str]:
    """Get the user's organization ID"""
    result = supabase.from_('profiles').select('organization_id').eq('user_id', user_id).single().execute()
    if result.data:
        return result.data.get('organization_id')
    return None


# ===========================================
# API Endpoints
# ===========================================

@router.post("/", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    request: InvitationCreateRequest,
    current_user: dict = Depends(require_org_admin)
):
    """
    Create a new user invitation
    
    Requires org_admin or system_admin role
    """
    supabase = get_supabase_client()
    
    try:
        # Verify user belongs to the organization they're inviting to
        user_org = get_user_organization(current_user['user_id'], supabase)
        if user_org != request.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only invite users to your own organization"
            )
        
        # Check if user already exists
        existing_user = supabase.auth.admin.list_users().execute()
        for user in existing_user.users:
            if user.email == request.email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists"
                )
        
        # Check for existing pending invitation
        existing_inv = supabase.from_('user_invitations').select('id').eq('email', request.email).eq('status', 'pending').execute()
        if existing_inv.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active invitation already exists for this email"
            )
        
        # Generate token
        token = generate_invitation_token()
        token_hash = hash_token(token)
        
        # Calculate expiry
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
        
        # Create invitation record
        invitation_data = {
            'email': request.email,
            'organization_id': request.organization_id,
            'role': request.role,
            'center_ids': request.center_ids or [],
            'region_id': request.region_id,
            'invited_by': current_user['user_id'],
            'token': token_hash,  # Store hash, but return plain token
            'expires_at': expires_at.isoformat(),
            'status': 'pending'
        }
        
        result = supabase.from_('user_invitations').insert(invitation_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create invitation"
            )
        
        invitation_id = result.data[0]['id']
        
        # Get organization and inviter details for email
        org_result = supabase.from_('organizations').select('name').eq('id', request.organization_id).single().execute()
        organization_name = org_result.data.get('name', 'the organization') if org_result.data else 'the organization'
        
        inviter_result = supabase.from_('profiles').select('salesperson_name').eq('user_id', current_user['user_id']).single().execute()
        inviter_name = inviter_result.data.get('salesperson_name', 'A team member') if inviter_result.data else 'A team member'
        
        # Send invitation email
        email_service = get_email_service()
        email_sent = await email_service.send_invitation_email(
            recipient_email=request.email,
            invitation_token=token,
            inviter_name=inviter_name,
            organization_name=organization_name,
            expires_in_days=request.expires_in_days
        )
        
        if not email_sent:
            # Log warning but don't fail - invitation is still created
            logging.warning(f"Failed to send invitation email to {request.email}, but invitation was created")
        
        return InvitationResponse(
            invitation_id=invitation_id,
            email=request.email,
            token=token,  # Return plain token for email
            expires_at=expires_at,
            status='pending',
            created_at=result.data[0]['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating invitation: {str(e)}"
        )


@router.get("/", response_model=InvitationListResponse)
async def list_invitations(
    organization_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(require_org_admin)
):
    """
    List invitations for the user's organization
    """
    supabase = get_supabase_client()
    
    try:
        # Get user's organization
        user_org = get_user_organization(current_user['user_id'], supabase)
        if not user_org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not associated with any organization"
            )
        
        # Build query
        query = supabase.from_('user_invitations').select('*').eq('organization_id', user_org)
        
        if status_filter:
            query = query.eq('status', status_filter)
        
        query = query.order('created_at', desc=True)
        
        result = query.execute()
        
        # Remove token hashes from response
        invitations = result.data if result.data else []
        for inv in invitations:
            inv.pop('token', None)  # Never expose token hash
        
        return InvitationListResponse(
            invitations=invitations,
            total=len(invitations)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing invitations: {str(e)}"
        )


@router.get("/{invitation_id}", response_model=dict)
async def get_invitation(
    invitation_id: str,
    current_user: dict = Depends(require_org_admin)
):
    """
    Get a specific invitation by ID
    """
    supabase = get_supabase_client()
    
    try:
        result = supabase.from_('user_invitations').select('*').eq('id', invitation_id).single().execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        
        invitation = result.data
        invitation.pop('token', None)  # Never expose token hash
        
        return invitation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching invitation: {str(e)}"
        )


@router.post("/validate-token", response_model=dict)
async def validate_invitation_token(request: InvitationValidateRequest):
    """
    Validate an invitation token (public endpoint)
    """
    supabase = get_supabase_client()
    token_hash = hash_token(request.token)
    
    try:
        result = supabase.from_('user_invitations').select('*').eq('token', token_hash).eq('status', 'pending').single().execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired invitation token"
            )
        
        invitation = result.data
        
        # Check if expired
        expires_at = datetime.fromisoformat(invitation['expires_at'].replace('Z', '+00:00'))
        if expires_at < datetime.now(expires_at.tzinfo):
            # Auto-update to expired
            supabase.from_('user_invitations').update({'status': 'expired'}).eq('id', invitation['id']).execute()
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Invitation has expired"
            )
        
        # Return safe invitation data
        return {
            'valid': True,
            'email': invitation['email'],
            'organization_id': invitation['organization_id'],
            'role': invitation['role'],
            'expires_at': invitation['expires_at']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating token: {str(e)}"
        )


@router.post("/accept", response_model=InvitationAcceptResponse)
async def accept_invitation(request: InvitationAcceptRequest):
    """
    Accept an invitation and create user account (public endpoint)
    """
    supabase = get_supabase_client()
    token_hash = hash_token(request.token)
    
    try:
        # Validate token
        inv_result = supabase.from_('user_invitations').select('*').eq('token', token_hash).eq('status', 'pending').single().execute()
        
        if not inv_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired invitation token"
            )
        
        invitation = inv_result.data
        
        # Check if expired
        expires_at = datetime.fromisoformat(invitation['expires_at'].replace('Z', '+00:00'))
        if expires_at < datetime.now(expires_at.tzinfo):
            supabase.from_('user_invitations').update({'status': 'expired'}).eq('id', invitation['id']).execute()
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Invitation has expired"
            )
        
        # Check if user already exists
        existing_user = supabase.auth.admin.list_users().execute()
        for user in existing_user.users:
            if user.email == invitation['email']:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists"
                )
        
        # Create user account
        user_name = request.name or invitation['email'].split('@')[0]
        create_result = supabase.auth.admin.create_user({
            "email": invitation['email'],
            "password": request.password,
            "email_confirm": False,  # Require email confirmation
            "user_metadata": {
                "name": user_name,
                "organization_id": invitation['organization_id']
            }
        })
        
        if not create_result.user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )
        
        new_user_id = create_result.user.id
        
        # Wait for profile to be created by trigger
        import asyncio
        await asyncio.sleep(1)
        
        # Update profile with role and assignments
        profile_update = {
            'salesperson_name': user_name
        }
        supabase.from_('profiles').update(profile_update).eq('user_id', new_user_id).execute()
        
        # Create user_roles
        role_insert = {
            'user_id': new_user_id,
            'role': invitation['role']
        }
        supabase.from_('user_roles').insert(role_insert).execute()
        
        # Create user_assignments
        assignments = []
        if invitation.get('center_ids'):
            for center_id in invitation['center_ids']:
                assignments.append({
                    'user_id': new_user_id,
                    'center_id': center_id,
                    'role': invitation['role']
                })
        
        if invitation.get('region_id'):
            assignments.append({
                'user_id': new_user_id,
                'region_id': invitation['region_id'],
                'role': invitation['role']
            })
        
        if not invitations and invitation.get('organization_id'):
            # Organization-level assignment if no center/region
            assignments.append({
                'user_id': new_user_id,
                'organization_id': invitation['organization_id'],
                'role': invitation['role']
            })
        
        if assignments:
            supabase.from_('user_assignments').insert(assignments).execute()
        
        # Update invitation status
        supabase.from_('user_invitations').update({
            'status': 'accepted',
            'accepted_at': datetime.utcnow().isoformat(),
            'accepted_by': new_user_id
        }).eq('id', invitation['id']).execute()
        
        return InvitationAcceptResponse(
            success=True,
            user_id=new_user_id,
            message="Account created successfully. Please check your email to verify your account."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accepting invitation: {str(e)}"
        )


@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    invitation_id: str,
    current_user: dict = Depends(require_org_admin)
):
    """
    Cancel a pending invitation
    """
    supabase = get_supabase_client()
    
    try:
        result = supabase.from_('user_invitations').update({'status': 'cancelled'}).eq('id', invitation_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling invitation: {str(e)}"
        )

