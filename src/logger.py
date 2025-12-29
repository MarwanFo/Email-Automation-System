"""
Logging with Personality

Readable logs that tell a story, not walls of cryptic text.
We include timestamps, context, and enough detail to debug
issues without drowning in noise.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

from rich.logging import RichHandler


class AutomationMailLogger:
    """
    Custom logger that writes to both console (pretty) and file (detailed).
    
    Console output uses Rich for colors and formatting.
    File output is more verbose for debugging.
    """
    
    def __init__(
        self,
        name: str = "automation-mail",
        level: str = "INFO",
        log_file: Optional[str] = None,
        max_size_mb: int = 10,
        backup_count: int = 3
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Clear any existing handlers
        self.logger.handlers = []
        
        # Console handler with Rich (pretty output)
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=False,
            show_path=False,
            markup=True
        )
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler (detailed output)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **context):
        """Log detailed debugging info (file only by default)."""
        formatted = self._format_with_context(message, context)
        self.logger.debug(formatted)
    
    def info(self, message: str, **context):
        """Log general information."""
        formatted = self._format_with_context(message, context)
        self.logger.info(formatted)
    
    def success(self, message: str, **context):
        """Log a success event."""
        formatted = self._format_with_context(f"✓ {message}", context)
        self.logger.info(formatted)
    
    def warning(self, message: str, **context):
        """Log a warning that doesn't stop execution."""
        formatted = self._format_with_context(f"⚠ {message}", context)
        self.logger.warning(formatted)
    
    def error(self, message: str, error: Optional[Exception] = None, **context):
        """Log an error with optional exception details."""
        formatted = self._format_with_context(f"✗ {message}", context)
        if error:
            formatted += f"\n  Exception: {type(error).__name__}: {str(error)}"
        self.logger.error(formatted)
    
    def email_sent(self, recipient: str, subject: str, **context):
        """Log a successful email send."""
        self.info(f"Email sent to {recipient}", subject=subject, **context)
    
    def email_failed(self, recipient: str, reason: str, **context):
        """Log a failed email attempt."""
        self.error(f"Failed to send to {recipient}: {reason}", **context)
    
    def bulk_start(self, count: int, template: Optional[str] = None):
        """Log the start of a bulk send operation."""
        msg = f"Starting bulk send to {count} recipients"
        if template:
            msg += f" using template: {template}"
        self.info(msg)
    
    def bulk_complete(self, sent: int, failed: int, duration_seconds: float):
        """Log the completion of a bulk send operation."""
        self.info(
            f"Bulk send complete",
            sent=sent,
            failed=failed,
            duration=f"{duration_seconds:.1f}s"
        )
    
    def _format_with_context(self, message: str, context: dict) -> str:
        """Add context as key=value pairs for file logging."""
        if not context:
            return message
        
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        return f"{message} [{context_str}]"


# Global logger instance
_logger: Optional[AutomationMailLogger] = None


def get_logger() -> AutomationMailLogger:
    """
    Get the global logger instance.
    
    Creates a default logger if one hasn't been configured yet.
    """
    global _logger
    if _logger is None:
        _logger = AutomationMailLogger()
    return _logger


def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = "./logs/automation-mail.log",
    max_size_mb: int = 10
) -> AutomationMailLogger:
    """
    Configure the global logger.
    
    Call this once at startup with your preferred settings.
    """
    global _logger
    _logger = AutomationMailLogger(
        level=level,
        log_file=log_file,
        max_size_mb=max_size_mb
    )
    return _logger


class EmailLog:
    """
    Detailed log for a specific email sending session.
    
    Creates a separate log file for each bulk send or scheduled
    job so you can easily review what happened.
    """
    
    def __init__(self, session_name: Optional[str] = None):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        name = session_name or "email-session"
        self.log_path = Path(f"./logs/{name}_{timestamp}.log")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.entries = []
    
    def add(self, recipient: str, status: str, details: Optional[str] = None):
        """Add an entry to the log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "recipient": recipient,
            "status": status,
            "details": details or ""
        }
        self.entries.append(entry)
    
    def save(self):
        """Write the log to disk."""
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.write(f"Email Session Log\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n\n")
            
            for entry in self.entries:
                status_icon = "✓" if entry["status"] == "sent" else "✗"
                f.write(f"{status_icon} [{entry['timestamp']}] {entry['recipient']}\n")
                if entry["details"]:
                    f.write(f"   {entry['details']}\n")
                f.write("\n")
            
            # Summary
            sent = sum(1 for e in self.entries if e["status"] == "sent")
            failed = sum(1 for e in self.entries if e["status"] != "sent")
            f.write(f"{'='*60}\n")
            f.write(f"Summary: {sent} sent, {failed} failed\n")
        
        return self.log_path
    
    @property
    def sent_count(self) -> int:
        return sum(1 for e in self.entries if e["status"] == "sent")
    
    @property
    def failed_count(self) -> int:
        return sum(1 for e in self.entries if e["status"] != "sent")
