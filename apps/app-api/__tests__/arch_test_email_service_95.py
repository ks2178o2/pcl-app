"""
Tests for email_service.py to achieve 95% coverage
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import os
import sys

# Create proper mocks for fastapi_mail
class MockFastMail:
    def __init__(self, config):
        self.config = config
        self.send_message = AsyncMock()

class MockMessageSchema:
    def __init__(self, **kwargs):
        self.recipients = kwargs.get('recipients', [])
        self.subject = kwargs.get('subject', '')
        self.body = kwargs.get('body', '')
        self.subtype = kwargs.get('subtype', 'plain')

class MockMessageType:
    plain = 'plain'

# Patch sys.modules before importing
sys.modules['fastapi_mail'] = MagicMock()
sys.modules['fastapi_mail'].FastMail = MockFastMail
sys.modules['fastapi_mail'].MessageSchema = MockMessageSchema
sys.modules['fastapi_mail'].ConnectionConfig = Mock
sys.modules['fastapi_mail'].MessageType = MockMessageType

# Now import
from services.email_service import EmailService, EMAIL_CONFIG


class TestEmailService:
    """Test EmailService"""
    
    @pytest.fixture
    def email_service(self):
        """Create EmailService instance"""
        service = EmailService()
        service.fast_mail.send_message = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SITE_URL': 'http://localhost:3000'}, clear=False)
    async def test_send_invitation_email_success(self, email_service):
        """Test successful invitation email send"""
        result = await email_service.send_invitation_email(
            recipient_email="test@example.com",
            invitation_token="token123",
            inviter_name="John Doe",
            organization_name="Test Org",
            expires_in_days=7
        )
        
        assert result is True
        email_service.fast_mail.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SITE_URL': 'http://localhost:3000'}, clear=False)
    async def test_send_invitation_email_custom_days(self, email_service):
        """Test invitation email with custom expiration days"""
        result = await email_service.send_invitation_email(
            recipient_email="test@example.com",
            invitation_token="token123",
            inviter_name="Jane Doe",
            organization_name="Test Org",
            expires_in_days=14
        )
        
        assert result is True
        email_service.fast_mail.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SITE_URL': 'http://localhost:3000'}, clear=False)
    async def test_send_invitation_email_failure(self, email_service):
        """Test invitation email send failure"""
        email_service.fast_mail.send_message = AsyncMock(side_effect=Exception("SMTP error"))
        
        result = await email_service.send_invitation_email(
            recipient_email="test@example.com",
            invitation_token="token123",
            inviter_name="John Doe",
            organization_name="Test Org"
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_send_invitation_email_default_site_url(self, email_service):
        """Test invitation email with default SITE_URL"""
        result = await email_service.send_invitation_email(
            recipient_email="test@example.com",
            invitation_token="token123",
            inviter_name="John Doe",
            organization_name="Test Org"
        )
        
        assert result is True
        email_service.fast_mail.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SITE_URL': 'http://localhost:3000'}, clear=False)
    async def test_send_password_reset_email_success(self, email_service):
        """Test successful password reset email send"""
        result = await email_service.send_password_reset_email(
            recipient_email="user@example.com",
            reset_token="reset_token_123"
        )
        
        assert result is True
        email_service.fast_mail.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SITE_URL': 'http://localhost:3000'}, clear=False)
    async def test_send_password_reset_email_failure(self, email_service):
        """Test password reset email send failure"""
        email_service.fast_mail.send_message = AsyncMock(side_effect=Exception("SMTP error"))
        
        result = await email_service.send_password_reset_email(
            recipient_email="user@example.com",
            reset_token="reset_token_123"
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_send_password_reset_email_default_site_url(self, email_service):
        """Test password reset email with default SITE_URL"""
        result = await email_service.send_password_reset_email(
            recipient_email="user@example.com",
            reset_token="reset_token_123"
        )
        
        assert result is True
        email_service.fast_mail.send_message.assert_called_once()
    
    def test_create_invitation_html(self, email_service):
        """Test _create_invitation_html method"""
        html = email_service._create_invitation_html(
            inviter_name="John Doe",
            organization_name="Test Org",
            acceptance_url="https://example.com/accept?token=123",
            expires_in_days=7
        )
        
        assert "John Doe" in html
        assert "Test Org" in html
        assert "https://example.com/accept?token=123" in html
        assert "7" in html
        assert "<html>" in html.lower()
    
    def test_get_email_service_singleton(self):
        """Test get_email_service returns singleton"""
        import services.email_service
        # Clear singleton
        services.email_service._email_service_instance = None
        
        service1 = services.email_service.get_email_service()
        service2 = services.email_service.get_email_service()
        
        assert service1 is service2
        assert service1 is not None
