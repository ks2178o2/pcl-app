"""
Email Service for sending notifications
Uses FastAPI-Mail with Gmail SMTP configuration
"""
import os
import logging
from typing import Optional, Dict, Any
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

logger = logging.getLogger(__name__)

# Email configuration from environment variables
EMAIL_CONFIG = ConnectionConfig(
    MAIL_USERNAME=os.getenv("SMTP_USER", ""),
    MAIL_PASSWORD=os.getenv("SMTP_PASSWORD", ""),
    MAIL_FROM=os.getenv("EMAILS_FROM_EMAIL", "noreply@pitcrew-labs.com"),
    MAIL_FROM_NAME=os.getenv("EMAILS_FROM_NAME", "PitCrew Labs"),
    MAIL_PORT=int(os.getenv("SMTP_PORT", "587")),
    MAIL_SERVER=os.getenv("SMTP_HOST", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.fast_mail = FastMail(EMAIL_CONFIG)
    
    async def send_invitation_email(
        self,
        recipient_email: str,
        invitation_token: str,
        inviter_name: str,
        organization_name: str,
        expires_in_days: int = 7
    ) -> bool:
        """
        Send user invitation email
        
        Args:
            recipient_email: Email address of invitee
            invitation_token: Secure invitation token
            inviter_name: Name of person sending invitation
            organization_name: Name of organization
            expires_in_days: Number of days until invitation expires
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create acceptance URL
            site_url = os.getenv("SITE_URL", "http://localhost:3000")
            acceptance_url = f"{site_url}/accept-invitation?token={invitation_token}"
            
            # Create HTML email body
            html_body = self._create_invitation_html(
                inviter_name=inviter_name,
                organization_name=organization_name,
                acceptance_url=acceptance_url,
                expires_in_days=expires_in_days
            )
            
            # Plain text version
            text_body = f"""
You've been invited to join {organization_name} on Sales Angel Buddy!

{inviter_name} has invited you to join their sales team.

Click here to accept your invitation:
{acceptance_url}

This invitation expires in {expires_in_days} days.

If you have any questions, please contact {inviter_name}.
"""
            
            # Create message
            message = MessageSchema(
                recipients=[recipient_email],
                subject=f"You're Invited to Join {organization_name}",
                body=text_body,
                subtype=MessageType.plain
            )
            
            # Send email
            await self.fast_mail.send_message(message)
            
            logger.info(f"Invitation email sent to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send invitation email to {recipient_email}: {e}")
            return False
    
    def _create_invitation_html(
        self,
        inviter_name: str,
        organization_name: str,
        acceptance_url: str,
        expires_in_days: int
    ) -> str:
        """Create HTML email body for invitation"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>You're Invited!</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0;">You're Invited!</h1>
    </div>
    
    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
        <p style="font-size: 18px;">Hello!</p>
        
        <p>{inviter_name} has invited you to join <strong>{organization_name}</strong> on Sales Angel Buddy, an AI-powered sales co-pilot platform.</p>
        
        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
            <p style="margin: 0 0 15px 0; font-weight: bold;">What is Sales Angel Buddy?</p>
            <ul style="margin: 0; padding-left: 20px;">
                <li>AI-powered sales assistant</li>
                <li>Call analysis and insights</li>
                <li>Follow-up plan generation</li>
                <li>Team collaboration tools</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{acceptance_url}" 
               style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
                Accept Invitation
            </a>
        </div>
        
        <p style="color: #666; font-size: 14px; text-align: center;">
            Or copy and paste this link into your browser:<br>
            <a href="{acceptance_url}" style="color: #667eea; word-break: break-all;">{acceptance_url}</a>
        </p>
        
        <div style="border-top: 1px solid #ddd; margin-top: 30px; padding-top: 20px; color: #666; font-size: 14px;">
            <p>⏰ This invitation expires in {expires_in_days} days</p>
            <p>📧 Questions? Contact {inviter_name}</p>
        </div>
    </div>
    
    <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
        <p>© {organization_name} - Powered by Sales Angel Buddy</p>
    </div>
</body>
</html>
        """
    
    async def send_password_reset_email(
        self,
        recipient_email: str,
        reset_token: str
    ) -> bool:
        """
        Send password reset email
        
        Args:
            recipient_email: Email address
            reset_token: Password reset token
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            site_url = os.getenv("SITE_URL", "http://localhost:3000")
            reset_url = f"{site_url}/reset-password?token={reset_token}"
            
            text_body = f"""
You requested a password reset for your Sales Angel Buddy account.

Click here to reset your password:
{reset_url}

If you didn't request this, please ignore this email.
"""
            
            message = MessageSchema(
                recipients=[recipient_email],
                subject="Reset Your Password",
                body=text_body,
                subtype=MessageType.plain
            )
            
            await self.fast_mail.send_message(message)
            logger.info(f"Password reset email sent to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {recipient_email}: {e}")
            return False


# Singleton instance
_email_service_instance: Optional[EmailService] = None

def get_email_service() -> EmailService:
    """Get or create email service instance"""
    global _email_service_instance
    if _email_service_instance is None:
        _email_service_instance = EmailService()
    return _email_service_instance

