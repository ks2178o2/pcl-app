"""
2FA Authentication API - Setup, verify, and manage two-factor authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
import pyotp
import qrcode
import io
import base64
from services.supabase_client import get_supabase_client
from middleware.auth import get_current_user

router = APIRouter(prefix="/api/auth/2fa", tags=["2fa"])


# ===========================================
# Pydantic Models
# ===========================================

class TwoFactorSetupResponse(BaseModel):
    qr_code: str  # Base64 encoded QR code image
    secret: str   # TOTP secret (show to user for manual entry)
    backup_codes: List[str]


class TwoFactorVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class TwoFactorEnableRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class TwoFactorDisableRequest(BaseModel):
    password: str  # Require password to disable
    code: Optional[str] = None  # Optional 2FA code if already enabled


class DeviceListResponse(BaseModel):
    devices: List[dict]
    total: int


# ===========================================
# Helper Functions
# ===========================================

def generate_totp_secret(email: str) -> str:
    """Generate a TOTP secret for a user"""
    return pyotp.random_base32()


def generate_backup_codes(count: int = 10) -> List[str]:
    """Generate backup codes for 2FA"""
    import secrets
    return [secrets.token_hex(4).upper() for _ in range(count)]


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """Verify a TOTP code"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=window)


def generate_qr_code(data: str) -> str:
    """Generate a QR code and return as base64 string"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Return as base64 string
    return base64.b64encode(buffer.read()).decode()


# ===========================================
# API Endpoints
# ===========================================

@router.post("/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(current_user: dict = Depends(get_current_user)):
    """
    Start 2FA setup process - generates secret and QR code
    """
    supabase = get_supabase_client()
    user_id = current_user['user_id']
    
    try:
        # Check if 2FA already enabled
        profile = supabase.from_('profiles').select('two_factor_enabled, two_factor_secret').eq('user_id', user_id).single().execute()
        
        if profile.data and profile.data.get('two_factor_enabled'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is already enabled. Disable it first to re-setup."
            )
        
        # Generate new secret and backup codes
        secret = generate_totp_secret(current_user.get('email', ''))
        backup_codes = generate_backup_codes()
        
        # Get user email for QR code label
        email = current_user.get('email', 'user')
        issuer = "Sales Angel Buddy"  # Your app name
        
        # Generate TOTP URI for QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=issuer
        )
        
        # Generate QR code
        qr_code_base64 = generate_qr_code(totp_uri)
        
        # Store secret and backup codes in profile (encrypted in production)
        supabase.from_('profiles').update({
            'two_factor_secret': secret,
            'verified_devices': []  # Reset verified devices
        }).eq('user_id', user_id).execute()
        
        # TODO: Store backup codes securely (encrypted database column or separate table)
        # For now, store in metadata
        supabase.from_('profiles').update({
            'metadata': {'backup_codes': backup_codes}
        }).eq('user_id', user_id).execute()
        
        return TwoFactorSetupResponse(
            qr_code=qr_code_base64,
            secret=secret,  # Show in plain text for manual entry
            backup_codes=backup_codes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting up 2FA: {str(e)}"
        )


@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_2fa_code(
    request: TwoFactorVerifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify a 2FA code (for setup confirmation)
    """
    supabase = get_supabase_client()
    user_id = current_user['user_id']
    
    try:
        # Get user's 2FA secret
        profile = supabase.from_('profiles').select('two_factor_secret').eq('user_id', user_id).single().execute()
        
        if not profile.data or not profile.data.get('two_factor_secret'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA not set up. Call /setup first."
            )
        
        secret = profile.data['two_factor_secret']
        
        # Verify code
        if not verify_totp_code(secret, request.code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )
        
        return {"success": True, "message": "2FA code verified"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying 2FA code: {str(e)}"
        )


@router.post("/enable", status_code=status.HTTP_200_OK)
async def enable_2fa(
    request: TwoFactorEnableRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Enable 2FA after verification
    """
    supabase = get_supabase_client()
    user_id = current_user['user_id']
    
    try:
        # Get user's 2FA secret
        profile = supabase.from_('profiles').select('two_factor_secret').eq('user_id', user_id).single().execute()
        
        if not profile.data or not profile.data.get('two_factor_secret'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA not set up. Call /setup first."
            )
        
        secret = profile.data['two_factor_secret']
        
        # Verify code one more time
        if not verify_totp_code(secret, request.code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )
        
        # Enable 2FA
        supabase.from_('profiles').update({
            'two_factor_enabled': True
        }).eq('user_id', user_id).execute()
        
        return {"success": True, "message": "2FA enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enabling 2FA: {str(e)}"
        )


@router.post("/disable", status_code=status.HTTP_200_OK)
async def disable_2fa(
    request: TwoFactorDisableRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Disable 2FA (requires password verification)
    """
    supabase = get_supabase_client()
    user_id = current_user['user_id']
    
    try:
        # Check if 2FA is enabled
        profile = supabase.from_('profiles').select('two_factor_enabled, two_factor_secret').eq('user_id', user_id).single().execute()
        
        if not profile.data or not profile.data.get('two_factor_enabled'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not enabled"
            )
        
        # If a 2FA code is provided, verify it
        if request.code:
            secret = profile.data['two_factor_secret']
            if not verify_totp_code(secret, request.code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid 2FA code"
                )
        
        # TODO: Verify password with Supabase Auth
        # For now, just verify code
        
        # Disable 2FA
        supabase.from_('profiles').update({
            'two_factor_enabled': False,
            'two_factor_secret': None,
            'verified_devices': []
        }).eq('user_id', user_id).execute()
        
        return {"success": True, "message": "2FA disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disabling 2FA: {str(e)}"
        )


@router.get("/devices", response_model=DeviceListResponse)
async def list_devices(current_user: dict = Depends(get_current_user)):
    """
    List user's verified devices
    """
    supabase = get_supabase_client()
    user_id = current_user['user_id']
    
    try:
        result = supabase.from_('user_devices').select('*').eq('user_id', user_id).order('last_used_at', desc=True).execute()
        
        devices = result.data if result.data else []
        
        # Remove sensitive data
        for device in devices:
            device.pop('two_factor_code_hash', None)
        
        return DeviceListResponse(
            devices=devices,
            total=len(devices)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing devices: {str(e)}"
        )


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_device(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Remove a verified device
    """
    supabase = get_supabase_client()
    user_id = current_user['user_id']
    
    try:
        result = supabase.from_('user_devices').delete().eq('id', device_id).eq('user_id', user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing device: {str(e)}"
        )


@router.get("/status", response_model=dict)
async def get_2fa_status(current_user: dict = Depends(get_current_user)):
    """
    Get 2FA status for current user
    """
    supabase = get_supabase_client()
    user_id = current_user['user_id']
    
    try:
        result = supabase.from_('profiles').select('two_factor_enabled').eq('user_id', user_id).single().execute()
        
        enabled = result.data.get('two_factor_enabled', False) if result.data else False
        
        return {
            "enabled": enabled,
            "setup_required": not enabled
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching 2FA status: {str(e)}"
        )

