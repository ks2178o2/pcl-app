"""
Twilio API endpoints for SMS and voice messaging
Enhanced with delivery status checking from SAR project
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import os
import time
import logging

from middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/twilio", tags=["twilio"])


class SendSMSPayload(BaseModel):
    callRecordId: Optional[str] = Field(None, alias="callRecordId")
    recipientPhone: str
    recipientName: Optional[str] = None
    message: str
    messageType: Optional[str] = "follow_up"


def _get_twilio_client():
    """
    Get Twilio client instance with credentials from environment
    
    Returns:
        Tuple of (Client, from_number)
    """
    try:
        from twilio.rest import Client  # type: ignore
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Twilio SDK not installed: {e}")

    # Support both TWILIO_ACCOUNT_SID and TWILIO_PHONE_NUMBER (from SAR project)
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER") or os.getenv("TWILIO_PHONE_NUMBER")
    
    if not sid or not token or not from_number:
        raise HTTPException(
            status_code=500,
            detail="Twilio credentials are not configured. Required: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER"
        )
    return Client(sid, token), from_number


@router.post("/send-sms", response_model=dict)
async def send_sms(payload: SendSMSPayload, current_user: dict = Depends(get_current_user)):
    """
    Send SMS message via Twilio
    
    Enhanced from SAR project to include delivery status checking
    """
    client, from_number = _get_twilio_client()

    if not payload.recipientPhone or not payload.message:
        raise HTTPException(status_code=400, detail="Missing recipientPhone or message")

    try:
        logger.info(
            f"📨 Sending SMS via Twilio to {payload.recipientPhone} for call {payload.callRecordId}"
        )
        
        # Send message
        msg = client.messages.create(
            to=payload.recipientPhone,
            from_=from_number,
            body=payload.message,
        )
        
        logger.info(f"✅ Message SID: {msg.sid}")
        
        # Wait briefly and check delivery status (from SAR project)
        time.sleep(2)
        
        try:
            # Fetch full message object with error info
            msg_details = client.messages(msg.sid).fetch()
            logger.info(f"📦 Message Delivery Status: {msg_details.status}")
            if msg_details.error_code:
                logger.warning(f"❗ Error Code: {msg_details.error_code}")
                logger.warning(f"❗ Error Message: {msg_details.error_message}")
        except Exception as fetch_error:
            logger.warning(f"⚠️ Could not fetch message details: {fetch_error}")
            # Continue even if we can't fetch details
        
        return {
            "success": True,
            "sid": msg.sid,
            "status": getattr(msg, "status", None),
            "error_code": getattr(msg, "error_code", None),
            "error_message": getattr(msg, "error_message", None),
        }
    except Exception as e:
        logger.error(f"❌ Twilio send error: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to send SMS: {str(e)}")


@router.get("/test-connection", response_model=dict)
async def test_connection(current_user: dict = Depends(get_current_user)):
    """
    Test Twilio connection and credentials
    
    Validates env and Twilio client initialization only
    """
    try:
        _, from_number = _get_twilio_client()
        return {
            "success": True,
            "message": "Twilio client initialized successfully",
            "from": from_number
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twilio init failed: {str(e)}")


@router.get("/debug", response_model=dict)
async def debug(current_user: dict = Depends(get_current_user)):
    """
    Debug endpoint to check Twilio configuration
    
    Returns masked config to help debugging (from SAR project pattern)
    """
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER") or os.getenv("TWILIO_PHONE_NUMBER")
    
    configured = bool(sid and token and from_number)
    
    return {
        "success": configured,
        "sid_prefix": sid[:6] + "…" if sid else None,
        "from": from_number,
        "has_token": bool(token),
    }



