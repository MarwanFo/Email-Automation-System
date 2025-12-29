"""
Tests for the EmailSender module.

We mock SMTP to avoid actually sending emails during tests.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.email_sender import EmailSender, Email, EmailResult
from src.config import Config, SMTPConfig, SenderConfig, RateLimitConfig


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_config():
    """Create a test configuration."""
    return Config(
        smtp=SMTPConfig(
            host="smtp.test.com",
            port=587,
            username="test@test.com",
            password="test-password",
            use_tls=True
        ),
        sender=SenderConfig(
            name="Test Sender",
            email="test@test.com"
        ),
        rate_limit=RateLimitConfig(
            emails_per_minute=60,  # Fast for tests
            max_retries=2,
            retry_delay_seconds=1
        )
    )


@pytest.fixture
def sample_email():
    """Create a sample email for testing."""
    return Email(
        to="recipient@example.com",
        subject="Test Subject",
        body_text="This is a test email.",
        body_html="<p>This is a test email.</p>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Email Creation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEmail:
    """Tests for the Email dataclass."""
    
    def test_email_with_text_body(self):
        """Should create email with text body only."""
        email = Email(
            to="test@example.com",
            subject="Hello",
            body_text="Plain text content"
        )
        assert email.to == "test@example.com"
        assert email.subject == "Hello"
        assert email.body_text == "Plain text content"
        assert email.body_html is None
    
    def test_email_with_html_body(self):
        """Should create email with HTML body only."""
        email = Email(
            to="test@example.com",
            subject="Hello",
            body_html="<p>HTML content</p>"
        )
        assert email.body_html == "<p>HTML content</p>"
    
    def test_email_with_both_bodies(self):
        """Should create email with both text and HTML bodies."""
        email = Email(
            to="test@example.com",
            subject="Hello",
            body_text="Plain text",
            body_html="<p>HTML</p>"
        )
        assert email.body_text == "Plain text"
        assert email.body_html == "<p>HTML</p>"
    
    def test_email_requires_body(self):
        """Should raise error if no body provided."""
        with pytest.raises(ValueError, match="must have either HTML or plain text body"):
            Email(to="test@example.com", subject="Hello")
    
    def test_email_with_cc_bcc(self):
        """Should create email with CC and BCC."""
        email = Email(
            to="test@example.com",
            subject="Hello",
            body_text="Content",
            cc=["cc1@example.com", "cc2@example.com"],
            bcc=["bcc@example.com"]
        )
        assert len(email.cc) == 2
        assert len(email.bcc) == 1
    
    def test_email_defaults(self):
        """Should have empty lists as defaults for cc, bcc, attachments."""
        email = Email(
            to="test@example.com",
            subject="Hello",
            body_text="Content"
        )
        assert email.cc == []
        assert email.bcc == []
        assert email.attachments == []


# ═══════════════════════════════════════════════════════════════════════════════
# Email Sending Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEmailSender:
    """Tests for the EmailSender class."""
    
    @patch('src.email_sender.smtplib.SMTP')
    def test_send_success(self, mock_smtp_class, mock_config, sample_email):
        """Should successfully send an email."""
        # Mock the SMTP connection
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        
        sender = EmailSender(mock_config)
        result = sender.send(sample_email)
        
        assert result.success is True
        assert result.recipient == "recipient@example.com"
        assert result.message_id is not None
        assert result.error_message is None
    
    @patch('src.email_sender.smtplib.SMTP')
    def test_invalid_email_returns_failure(self, mock_smtp_class, mock_config):
        """Should fail validation for invalid email addresses."""
        invalid_email = Email(
            to="not-a-valid-email",
            subject="Test",
            body_text="Content"
        )
        
        sender = EmailSender(mock_config)
        result = sender.send(invalid_email)
        
        assert result.success is False
        assert result.error_code == "INVALID_EMAIL"
    
    @patch('src.email_sender.smtplib.SMTP')
    def test_test_connection_success(self, mock_smtp_class, mock_config):
        """Should return success for valid connection."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        
        sender = EmailSender(mock_config)
        success, message = sender.test_connection()
        
        assert success is True
        assert "successful" in message.lower()
    
    @patch('src.email_sender.smtplib.SMTP')
    def test_context_manager(self, mock_smtp_class, mock_config):
        """Should work as a context manager."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp
        
        with EmailSender(mock_config) as sender:
            assert sender is not None
        
        # Connection should be closed after exiting context
        mock_smtp.quit.assert_called()


# ═══════════════════════════════════════════════════════════════════════════════
# Email Result Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEmailResult:
    """Tests for the EmailResult dataclass."""
    
    def test_success_result(self):
        """Should create a success result."""
        result = EmailResult(
            success=True,
            recipient="test@example.com",
            message_id="<123@example.com>",
            sent_at=datetime.now()
        )
        assert result.success is True
        assert result.error_message is None
    
    def test_failure_result(self):
        """Should create a failure result with error details."""
        result = EmailResult(
            success=False,
            recipient="test@example.com",
            error_message="Connection refused",
            error_code="CONNECTION_ERROR",
            retry_count=3
        )
        assert result.success is False
        assert result.error_message == "Connection refused"
        assert result.retry_count == 3


# ═══════════════════════════════════════════════════════════════════════════════
# Provider Detection Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestProviderDetection:
    """Tests for SMTP provider detection."""
    
    def test_detect_gmail(self):
        """Should detect Gmail from SMTP host."""
        config = SMTPConfig(
            host="smtp.gmail.com",
            port=587,
            username="test@gmail.com",
            password="password"
        )
        assert config.provider == "gmail"
    
    def test_detect_outlook(self):
        """Should detect Outlook from SMTP host."""
        config = SMTPConfig(
            host="smtp.office365.com",
            port=587,
            username="test@outlook.com",
            password="password"
        )
        assert config.provider == "outlook"
    
    def test_detect_custom(self):
        """Should return 'custom' for unknown providers."""
        config = SMTPConfig(
            host="mail.mycompany.com",
            port=587,
            username="test@mycompany.com",
            password="password"
        )
        assert config.provider == "custom"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
