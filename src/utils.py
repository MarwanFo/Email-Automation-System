"""
Utility Functions

Helpful snippets that don't belong anywhere else.
We keep these small, focused, and well-tested.
"""

import os
import re
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


def slugify(text: str) -> str:
    """
    Convert a string to a URL-friendly slug.
    
    "Hello World!" -> "hello-world"
    """
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


def truncate(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Shorten text to a maximum length, adding suffix if truncated.
    
    "This is a very long sentence" -> "This is a very..."
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].rstrip() + suffix


def format_file_size(size_bytes: int) -> str:
    """
    Format bytes as human-readable file size.
    
    1024 -> "1.0 KB"
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_duration(seconds: float) -> str:
    """
    Format seconds as human-readable duration.
    
    125 -> "2 minutes, 5 seconds"
    """
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        if secs == 0:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        return f"{minutes} minute{'s' if minutes != 1 else ''}, {secs} second{'s' if secs != 1 else ''}"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"


def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """
    Parse various datetime string formats into a datetime object.
    
    Supports:
    - "2025-12-30 14:00"
    - "2025-12-30T14:00"
    - "tomorrow 9am"
    - "in 2 hours"
    """
    datetime_str = datetime_str.strip().lower()
    now = datetime.now()
    
    # Handle relative times
    if datetime_str.startswith("in "):
        match = re.match(r'in (\d+) (hour|minute|day)s?', datetime_str)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            if unit == "hour":
                return now + timedelta(hours=amount)
            elif unit == "minute":
                return now + timedelta(minutes=amount)
            elif unit == "day":
                return now + timedelta(days=amount)
    
    # Handle "tomorrow"
    if "tomorrow" in datetime_str:
        tomorrow = now + timedelta(days=1)
        # Try to extract time
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', datetime_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3)
            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)  # Default 9 AM
    
    # Try standard formats
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%m/%d/%Y %H:%M",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    
    return None


def get_first_name(full_name: str) -> str:
    """
    Extract first name from a full name.
    
    "Sarah Chen" -> "Sarah"
    "Dr. James Morrison" -> "James"
    """
    if not full_name:
        return ""
    
    # Remove common prefixes
    prefixes = ["dr.", "mr.", "mrs.", "ms.", "prof."]
    name = full_name.strip()
    name_lower = name.lower()
    
    for prefix in prefixes:
        if name_lower.startswith(prefix):
            name = name[len(prefix):].strip()
            break
    
    # Take the first word
    parts = name.split()
    return parts[0] if parts else ""


def ensure_directory(path: str) -> Path:
    """
    Create a directory if it doesn't exist.
    
    Returns the Path object for chaining.
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def generate_message_id(sender_email: str) -> str:
    """
    Generate a unique Message-ID for email headers.
    
    Follows RFC 5322 format: <unique-id@domain>
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    random_part = hashlib.md5(os.urandom(16)).hexdigest()[:12]
    domain = sender_email.split("@")[1] if "@" in sender_email else "automation-mail.local"
    return f"<{timestamp}.{random_part}@{domain}>"


def mask_email(email: str) -> str:
    """
    Partially mask an email for privacy in logs.
    
    "sarah.chen@example.com" -> "sar***@example.com"
    """
    if "@" not in email:
        return "***"
    
    local, domain = email.split("@")
    if len(local) <= 3:
        masked_local = local[0] + "***"
    else:
        masked_local = local[:3] + "***"
    
    return f"{masked_local}@{domain}"


def mask_password(password: str) -> str:
    """
    Mask most of a password for safe display.
    
    "mysecretpassword" -> "mys***********"
    """
    if len(password) <= 3:
        return "***"
    return password[:3] + "*" * (len(password) - 3)


def is_office_hours() -> bool:
    """
    Check if current time is within typical office hours (9 AM - 6 PM weekdays).
    
    Useful for scheduling emails at appropriate times.
    """
    now = datetime.now()
    # Monday = 0, Sunday = 6
    if now.weekday() >= 5:  # Weekend
        return False
    return 9 <= now.hour < 18


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into smaller chunks.
    
    [1,2,3,4,5], 2 -> [[1,2], [3,4], [5]]
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries, later values overwriting earlier ones.
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result
