from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import os
import logging

from api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/twilio", tags=["twilio"])


class SendSMSPayload(BaseModel):
    callRecordId: Optional[str] = Field(None, alias="callRecordId")
    recipientPhone: str
    recipientName: Optional[str] = None
    message: str
    messageType: Optional[str] = "follow_up"


def _get_twilio_client():
    try:
        from twilio.rest import Client  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twilio SDK not installed: {e}")

    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    if not sid or not token or not from_number:
        raise HTTPException(status_code=500, detail="Twilio credentials are not configured")
    return Client(sid, token), from_number


@router.post("/send-sms", response_model=dict)
async def send_sms(payload: SendSMSPayload, current_user: dict = Depends(get_current_user)):
    client, from_number = _get_twilio_client()

    try:
        logger.info(
            f"Sending SMS via Twilio to {payload.recipientPhone} for call {payload.callRecordId}"
        )
        msg = client.messages.create(
            to=payload.recipientPhone,
            from_=from_number,
            body=payload.message,
        )
        return {
            "success": True,
            "sid": msg.sid,
            "status": getattr(msg, "status", None),
        }
    except Exception as e:
        logger.error(f"Twilio send error: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to send SMS: {e}")


@router.get("/test-connection", response_model=dict)
async def test_connection(current_user: dict = Depends(get_current_user)):
    # Validate env and Twilio client init only
    try:
        _, from_number = _get_twilio_client()
        return {"success": True, "message": "Twilio client initialized", "from": from_number}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twilio init failed: {e}")


@router.get("/debug", response_model=dict)
async def debug(current_user: dict = Depends(get_current_user)):
    # Return masked config to help debugging
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    configured = bool(sid and from_number and os.getenv("TWILIO_AUTH_TOKEN"))
    return {
        "success": configured,
        "sid_prefix": sid[:6] + "…" if sid else None,
        "from": from_number,
    }



