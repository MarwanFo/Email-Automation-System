"""
Email Sender — The Heart of Automation Mail

Handles the actual sending of emails via SMTP. We've put a lot of
thought into making this reliable:
- Automatic retries with exponential backoff
- Rate limiting to keep providers happy
- Clear error messages for common failure modes
- Attachment support with size validation
"""

import smtplib
import ssl
import time
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr, formatdate
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

from .config import Config, SMTPConfig, SenderConfig
from .validator import EmailValidator, AttachmentValidator
from .logger import get_logger
from .utils import generate_message_id, mask_email


@dataclass
class EmailResult:
    """
    Result of an email send attempt.
    
    Contains everything you need to know about what happened.
    """
    success: bool
    recipient: str
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retry_count: int = 0
    sent_at: Optional[datetime] = None


@dataclass
class Email:
    """
    An email to be sent.
    
    Immutable representation of an email with all its parts.
    """
    to: str
    subject: str
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    reply_to: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        # Ensure we have at least some body content
        if not self.body_html and not self.body_text:
            raise ValueError("Email must have either HTML or plain text body")


class RetryableError(Exception):
    """An error that might succeed if we try again."""
    pass


class PermanentError(Exception):
    """An error that won't be fixed by retrying."""
    pass


class EmailSender:
    """
    Sends emails via SMTP with built-in reliability features.
    
    Usage:
        sender = EmailSender(config)
        result = sender.send(email)
        
        if result.success:
            print(f"Sent! Message ID: {result.message_id}")
        else:
            print(f"Failed: {result.error_message}")
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.smtp_config = config.smtp
        self.sender_config = config.sender
        self.rate_limit = config.rate_limit
        self.logger = get_logger()
        
        self._connection: Optional[smtplib.SMTP] = None
        self._last_send_time: Optional[float] = None
        self._emails_sent_this_session = 0
    
    def send(self, email: Email) -> EmailResult:
        """
        Send a single email.
        
        Handles validation, connection, sending, and retries automatically.
        """
        # Validate recipient
        validation = EmailValidator.validate(email.to)
        if not validation.is_valid:
            return EmailResult(
                success=False,
                recipient=email.to,
                error_message=validation.message,
                error_code="INVALID_EMAIL"
            )
        
        # Validate attachments
        for attachment_path in email.attachments:
            validation = AttachmentValidator.validate(attachment_path)
            if not validation.is_valid:
                return EmailResult(
                    success=False,
                    recipient=email.to,
                    error_message=validation.message,
                    error_code="INVALID_ATTACHMENT"
                )
        
        # Apply rate limiting
        self._apply_rate_limit()
        
        # Try to send with retries
        last_error = None
        for attempt in range(self.rate_limit.max_retries + 1):
            try:
                message_id = self._send_email(email)
                self._emails_sent_this_session += 1
                
                self.logger.email_sent(
                    recipient=email.to,
                    subject=email.subject,
                    message_id=message_id
                )
                
                return EmailResult(
                    success=True,
                    recipient=email.to,
                    message_id=message_id,
                    retry_count=attempt,
                    sent_at=datetime.now()
                )
                
            except RetryableError as e:
                last_error = e
                if attempt < self.rate_limit.max_retries:
                    wait_time = self.rate_limit.retry_delay_seconds * (2 ** attempt)
                    self.logger.warning(
                        f"Retrying in {wait_time}s (attempt {attempt + 1})",
                        recipient=mask_email(email.to), 
                        error=str(e)
                    )
                    time.sleep(wait_time)
                    
            except PermanentError as e:
                self.logger.email_failed(email.to, str(e))
                return EmailResult(
                    success=False,
                    recipient=email.to,
                    error_message=str(e),
                    error_code="PERMANENT_FAILURE",
                    retry_count=attempt
                )
                
            except Exception as e:
                self.logger.email_failed(email.to, str(e))
                return EmailResult(
                    success=False,
                    recipient=email.to,
                    error_message=str(e),
                    error_code="UNEXPECTED_ERROR",
                    retry_count=attempt
                )
        
        # All retries exhausted
        return EmailResult(
            success=False,
            recipient=email.to,
            error_message=f"Failed after {self.rate_limit.max_retries + 1} attempts: {last_error}",
            error_code="MAX_RETRIES_EXCEEDED",
            retry_count=self.rate_limit.max_retries
        )
    
    def send_bulk(
        self,
        emails: List[Email],
        on_progress: Optional[callable] = None,
        on_complete: Optional[callable] = None
    ) -> List[EmailResult]:
        """
        Send multiple emails with progress tracking.
        
        on_progress: Called after each email with (sent_count, total, last_result)
        on_complete: Called when done with (results, stats)
        """
        results = []
        total = len(emails)
        
        for i, email in enumerate(emails, 1):
            result = self.send(email)
            results.append(result)
            
            if on_progress:
                on_progress(i, total, result)
        
        if on_complete:
            stats = {
                "sent": sum(1 for r in results if r.success),
                "failed": sum(1 for r in results if not r.success),
                "total": total
            }
            on_complete(results, stats)
        
        return results
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test SMTP connection without sending anything.
        
        Returns (success, message) tuple.
        """
        try:
            conn = self._create_connection()
            conn.quit()
            return True, "Connection successful! Your SMTP settings look good."
        except smtplib.SMTPAuthenticationError:
            return False, self._get_auth_error_message()
        except smtplib.SMTPConnectError as e:
            return False, f"Couldn't connect to {self.smtp_config.host}:{self.smtp_config.port}. Check host and port settings."
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def _send_email(self, email: Email) -> str:
        """
        Actually send the email. Raises RetryableError or PermanentError.
        """
        message_id = generate_message_id(self.sender_config.email)
        
        # Build the MIME message
        if email.body_html and email.body_text:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(email.body_text, "plain", "utf-8"))
            msg.attach(MIMEText(email.body_html, "html", "utf-8"))
        elif email.body_html:
            msg = MIMEMultipart()
            msg.attach(MIMEText(email.body_html, "html", "utf-8"))
        else:
            msg = MIMEMultipart()
            msg.attach(MIMEText(email.body_text, "plain", "utf-8"))
        
        # Set headers
        msg["From"] = formataddr((self.sender_config.name, self.sender_config.email))
        msg["To"] = email.to
        msg["Subject"] = email.subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = message_id
        
        if email.cc:
            msg["Cc"] = ", ".join(email.cc)
        
        if email.reply_to or self.sender_config.reply_to:
            msg["Reply-To"] = email.reply_to or self.sender_config.reply_to
        
        # Add custom headers
        for key, value in email.headers.items():
            msg[key] = value
        
        # Add attachments
        for attachment_path in email.attachments:
            self._attach_file(msg, attachment_path)
        
        # Calculate all recipients
        all_recipients = [email.to] + email.cc + email.bcc
        
        # Send the message
        try:
            connection = self._get_connection()
            connection.sendmail(
                self.sender_config.email,
                all_recipients,
                msg.as_string()
            )
            return message_id
            
        except smtplib.SMTPRecipientsRefused as e:
            raise PermanentError(f"Recipient refused: {e.recipients}")
            
        except smtplib.SMTPSenderRefused as e:
            raise PermanentError(f"Sender refused: {e.sender}")
            
        except smtplib.SMTPDataError as e:
            if e.smtp_code >= 500:
                raise PermanentError(f"Server rejected message: {e.smtp_error}")
            raise RetryableError(f"Temporary server error: {e.smtp_error}")
            
        except smtplib.SMTPServerDisconnected:
            self._connection = None  # Force reconnection
            raise RetryableError("Server disconnected unexpectedly")
            
        except smtplib.SMTPException as e:
            raise RetryableError(f"SMTP error: {str(e)}")
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach a file to the message."""
        path = Path(file_path)
        
        # Guess the content type
        content_type, encoding = mimetypes.guess_type(str(path))
        if content_type is None:
            content_type = "application/octet-stream"
        
        main_type, sub_type = content_type.split("/", 1)
        
        with open(path, "rb") as f:
            attachment = MIMEBase(main_type, sub_type)
            attachment.set_payload(f.read())
        
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=path.name
        )
        msg.attach(attachment)
    
    def _create_connection(self) -> smtplib.SMTP:
        """Create a new SMTP connection."""
        if self.smtp_config.use_ssl:
            context = ssl.create_default_context()
            connection = smtplib.SMTP_SSL(
                self.smtp_config.host,
                self.smtp_config.port,
                timeout=self.smtp_config.timeout,
                context=context
            )
        else:
            connection = smtplib.SMTP(
                self.smtp_config.host,
                self.smtp_config.port,
                timeout=self.smtp_config.timeout
            )
            
            if self.smtp_config.use_tls:
                context = ssl.create_default_context()
                connection.starttls(context=context)
        
        connection.login(self.smtp_config.username, self.smtp_config.password)
        return connection
    
    def _get_connection(self) -> smtplib.SMTP:
        """Get or create an SMTP connection (with connection pooling)."""
        if self._connection is None:
            try:
                self._connection = self._create_connection()
            except smtplib.SMTPAuthenticationError:
                raise PermanentError(self._get_auth_error_message())
            except smtplib.SMTPConnectError as e:
                raise RetryableError(f"Connection failed: {str(e)}")
        
        return self._connection
    
    def _apply_rate_limit(self):
        """
        Pause if necessary to respect rate limits.
        
        We're being extra careful here because email providers get
        suspicious if you send too fast. Better slow and delivered
        than fast and spam-filtered.
        """
        if self._last_send_time is not None:
            elapsed = time.time() - self._last_send_time
            required_delay = self.rate_limit.delay_between_emails
            
            if elapsed < required_delay:
                sleep_time = required_delay - elapsed
                time.sleep(sleep_time)
        
        self._last_send_time = time.time()
    
    def _get_auth_error_message(self) -> str:
        """Get a helpful error message for authentication failures."""
        provider = self.smtp_config.provider
        
        if provider == "gmail":
            return (
                "Gmail authentication failed. You likely need an App Password.\n"
                "Create one at: https://myaccount.google.com/apppasswords\n"
                "Then update SMTP_PASSWORD in your .env file."
            )
        elif provider == "outlook":
            return (
                "Outlook authentication failed.\n"
                "Make sure you're using an app password and have SMTP enabled."
            )
        else:
            return (
                "SMTP authentication failed.\n"
                "Check your username and password in .env"
            )
    
    def close(self):
        """Close the SMTP connection."""
        if self._connection:
            try:
                self._connection.quit()
            except Exception:
                pass
            self._connection = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    @property
    def emails_sent(self) -> int:
        """Number of emails sent in this session."""
        return self._emails_sent_this_session
