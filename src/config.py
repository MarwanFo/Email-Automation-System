"""
Configuration Management

Loads settings from .env and provides sensible defaults.
We validate everything upfront so you don't get cryptic errors
halfway through sending 500 emails.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass
class SMTPConfig:
    """SMTP server configuration with provider detection."""
    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False
    timeout: int = 30
    
    @property
    def provider(self) -> str:
        """
        Detect email provider from host for provider-specific handling.
        
        Different providers have different quirks — Gmail needs app passwords,
        Outlook has specific port requirements, etc.
        """
        host_lower = self.host.lower()
        
        if "gmail" in host_lower:
            return "gmail"
        elif "outlook" in host_lower or "office365" in host_lower:
            return "outlook"
        elif "yahoo" in host_lower:
            return "yahoo"
        elif "zoho" in host_lower:
            return "zoho"
        else:
            return "custom"


@dataclass
class SenderConfig:
    """Who the emails appear to come from."""
    name: str
    email: str
    reply_to: Optional[str] = None
    
    def __post_init__(self):
        if not self.reply_to:
            self.reply_to = self.email


@dataclass
class RateLimitConfig:
    """
    Rate limiting to keep email providers happy.
    
    These defaults are conservative — better to be slow and reliable
    than fast and blocked.
    """
    emails_per_minute: int = 8  # Gmail gets suspicious above 10
    max_retries: int = 3
    retry_delay_seconds: int = 60
    
    @property
    def delay_between_emails(self) -> float:
        """Calculate delay in seconds between emails."""
        return 60.0 / self.emails_per_minute


@dataclass  
class LoggingConfig:
    """Logging preferences."""
    level: str = "INFO"
    file_path: str = "./logs/automation-mail.log"
    rotation_size_mb: int = 10


@dataclass
class SchedulerConfig:
    """Job scheduler settings."""
    timezone: str = "UTC"
    persistence_path: str = "./data/scheduled-jobs.db"


@dataclass
class Config:
    """
    Main configuration container.
    
    Holds all the settings for Automation Mail. Load from environment
    variables or provide directly.
    """
    smtp: SMTPConfig
    sender: SenderConfig
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for display."""
        return {
            "smtp_host": self.smtp.host,
            "smtp_port": self.smtp.port,
            "smtp_username": self.smtp.username,
            "smtp_password": self.smtp.password,
            "smtp_use_tls": self.smtp.use_tls,
            "sender_name": self.sender.name,
            "sender_email": self.sender.email,
            "rate_limit": self.rate_limit.emails_per_minute,
            "max_retries": self.rate_limit.max_retries,
        }


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def load_config(env_path: Optional[str] = None) -> Config:
    """
    Load configuration from environment variables.
    
    Looks for a .env file in the current directory or at the specified path.
    Falls back to system environment variables if .env isn't found.
    
    Raises ConfigurationError with helpful messages if required values are missing.
    """
    # Load .env file if it exists
    if env_path:
        load_dotenv(env_path)
    else:
        # Try common locations
        for candidate in [".env", "../.env", Path.home() / ".automation-mail" / ".env"]:
            if Path(candidate).exists():
                load_dotenv(candidate)
                break
        else:
            load_dotenv()  # Try default behavior
    
    # Collect any missing required values
    missing = []
    
    # SMTP settings
    smtp_host = os.getenv("SMTP_HOST")
    if not smtp_host:
        missing.append("SMTP_HOST")
    
    smtp_port_str = os.getenv("SMTP_PORT", "587")
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        raise ConfigurationError(
            f"SMTP_PORT must be a number, got '{smtp_port_str}'\n"
            f"Common ports: 587 (TLS), 465 (SSL), 25 (insecure)"
        )
    
    smtp_username = os.getenv("SMTP_USERNAME")
    if not smtp_username:
        missing.append("SMTP_USERNAME")
    
    smtp_password = os.getenv("SMTP_PASSWORD")
    if not smtp_password:
        missing.append("SMTP_PASSWORD")
    
    # Sender info
    sender_name = os.getenv("SENDER_NAME")
    if not sender_name:
        missing.append("SENDER_NAME")
    
    sender_email = os.getenv("SENDER_EMAIL")
    if not sender_email:
        missing.append("SENDER_EMAIL")
    
    # Report all missing values at once
    if missing:
        missing_str = ", ".join(missing)
        raise ConfigurationError(
            f"Missing required configuration: {missing_str}\n\n"
            f"Make sure your .env file contains these values.\n"
            f"See .env.example for a template, or run:\n"
            f"  automation-mail configure"
        )
    
    # Build the config object
    smtp_config = SMTPConfig(
        host=smtp_host,
        port=smtp_port,
        username=smtp_username,
        password=smtp_password,
        use_tls=os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes"),
        use_ssl=os.getenv("SMTP_USE_SSL", "false").lower() in ("true", "1", "yes"),
        timeout=int(os.getenv("SMTP_TIMEOUT", "30")),
    )
    
    sender_config = SenderConfig(
        name=sender_name,
        email=sender_email,
        reply_to=os.getenv("REPLY_TO_EMAIL"),
    )
    
    rate_limit_config = RateLimitConfig(
        emails_per_minute=int(os.getenv("RATE_LIMIT_EMAILS_PER_MINUTE", "8")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        retry_delay_seconds=int(os.getenv("RETRY_DELAY_SECONDS", "60")),
    )
    
    logging_config = LoggingConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        file_path=os.getenv("LOG_FILE_PATH", "./logs/automation-mail.log"),
        rotation_size_mb=int(os.getenv("LOG_ROTATION_SIZE_MB", "10")),
    )
    
    scheduler_config = SchedulerConfig(
        timezone=os.getenv("SCHEDULER_TIMEZONE", "UTC"),
        persistence_path=os.getenv("JOB_PERSISTENCE_PATH", "./data/scheduled-jobs.db"),
    )
    
    return Config(
        smtp=smtp_config,
        sender=sender_config,
        rate_limit=rate_limit_config,
        logging=logging_config,
        scheduler=scheduler_config,
    )


def get_default_config_template() -> str:
    """
    Return the default .env template with helpful comments.
    
    Used by the configure command to create initial configuration.
    """
    return '''# ========================================
# 📧 Automation Mail Configuration
# ========================================
#
# Quick Start:
# 1. Fill in your email details below
# 2. Save this file as .env
# 3. Run: automation-mail test-connection
#
# Need help? Check docs/SETUP.md
# ========================================

# ========================================
# SMTP Settings (Gmail Example)
# ========================================
# For Gmail:
#   - Enable 2FA: https://myaccount.google.com/security
#   - Create app password: https://myaccount.google.com/apppasswords
#   - Use the 16-character app password below (no spaces)

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your-app-password-here
SMTP_USE_TLS=true

# ========================================
# Your Email Identity
# ========================================
# This is how recipients see you

SENDER_NAME=Your Name
SENDER_EMAIL=your.email@gmail.com
REPLY_TO_EMAIL=your.email@gmail.com

# ========================================
# Sending Behavior
# ========================================
# Be gentle with your email provider!
# Gmail allows ~500/day, Outlook ~300/day

RATE_LIMIT_EMAILS_PER_MINUTE=8
MAX_RETRIES=3
RETRY_DELAY_SECONDS=60

# ========================================
# Logging
# ========================================
# Options: DEBUG, INFO, WARNING, ERROR

LOG_LEVEL=INFO
LOG_FILE_PATH=./logs/automation-mail.log
LOG_ROTATION_SIZE_MB=10

# ========================================
# Scheduling
# ========================================
# Timezone examples: UTC, America/New_York, Europe/London

SCHEDULER_TIMEZONE=UTC
JOB_PERSISTENCE_PATH=./data/scheduled-jobs.db
'''
